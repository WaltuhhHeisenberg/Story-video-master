#!/usr/bin/env node
// three-toon-studio CLI
import fs from 'fs'; import os from 'os'; import path from 'path';
import { spawn, spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import { loadProject, writeSrt } from './src/project.mjs';
import { generate } from './src/autogen.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url)), WORKER = path.join(HERE, 'src', 'render-chunk.mjs');
const [cmd, ...rest] = process.argv.slice(2), A = { _: [] };
for (let i = 0; i < rest.length; i++) { if (rest[i].startsWith('--')) { const k = rest[i].slice(2); A[k] = (rest[i + 1] && !rest[i + 1].startsWith('--')) ? rest[++i] : true; } else A._.push(rest[i]); }
const sleep = ms => new Promise(r => setTimeout(r, ms));
const fmt = s => { s = Math.round(s); const h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60; return h ? `${h}h ${m}m` : m ? `${m}m ${s % 60}s` : `${s}s`; };

async function display() {
  if (process.env.DISPLAY) return { env: process.env, stop() {} };
  const num = 100 + Math.floor(Math.random() * 800), p = spawn('Xvfb', [`:${num}`, '-screen', '0', '640x480x24', '-nolisten', 'tcp'], { stdio: 'ignore' });
  await sleep(900); return { env: { ...process.env, DISPLAY: `:${num}` }, stop() { p.kill(); } };
}
const run = (file, args, env) => new Promise((res, rej) => { const p = spawn(process.execPath, [file, ...args], { env, stdio: ['ignore', 'pipe', 'inherit'] }); let out = ''; p.stdout.on('data', d => out += d); p.on('close', c => c ? rej(new Error('worker exit ' + c)) : res(out)); });

async function render(file) {
  const preview = !!A.preview, proj = loadProject(file, { preview });
  const out = path.resolve(A.out || file.replace(/\.json$/, '') + (preview ? '.preview' : '') + '.mp4');
  const dir = path.resolve(A.build || path.join(path.dirname(path.resolve(file)), '.build-' + path.basename(file, '.json') + (preview ? '-preview' : '')));
  fs.mkdirSync(dir, { recursive: true });
  const chunk = +A.chunk || 300, from = Math.max(0, Math.round((+A.from || 0) * proj.fps)), to = Math.min(proj.totalFrames, A.to ? Math.round(+A.to * proj.fps) : proj.totalFrames);
  const jobs = []; for (let f = from; f < to; f += chunk) jobs.push({ f0: f, f1: Math.min(to, f + chunk), file: path.join(dir, `chunk_${String(f).padStart(7, '0')}.mp4`) });
  const workers = Math.max(1, +A.workers || (os.availableParallelism ? os.availableParallelism() : os.cpus().length));
  const d = await display(), env = { ...d.env, ...(workers > 1 ? { LP_NUM_THREADS: '1' } : {}) };
  console.log(`${proj.title}: ${proj.scenes.length} scenes, ${fmt((to - from) / proj.fps)} @ ${proj.width}x${proj.height} ${proj.fps}fps (ss ${proj.ss}) -> ${jobs.length} chunks, ${workers} workers`);
  const t0 = Date.now(); let done = 0, doneFrames = 0, idx = 0;
  const todo = jobs.filter(j => { if (fs.existsSync(j.file + '.done')) { done++; doneFrames += j.f1 - j.f0; return false; } return true; });
  const tick = () => { const el = (Date.now() - t0) / 1000, rate = (doneFrames - (jobs.length - todo.length ? 0 : 0)) / Math.max(1, el); process.stdout.write(`\r  ${done}/${jobs.length} chunks  ${(100 * doneFrames / (to - from)).toFixed(1)}%  elapsed ${fmt(el)}  `); };
  const pool = Array.from({ length: Math.min(workers, todo.length) }, async () => {
    while (idx < todo.length) { const j = todo[idx++]; const tmp = j.file + '.part.mp4';
      await run(WORKER, ['--project', path.resolve(file), '--out', tmp, '--from', j.f0, '--to', j.f1, ...(preview ? ['--preview'] : [])], env);
      fs.renameSync(tmp, j.file); fs.writeFileSync(j.file + '.done', ''); done++; doneFrames += j.f1 - j.f0; tick(); }
  });
  await Promise.all(pool); d.stop(); console.log();
  const list = path.join(dir, 'list.txt'); fs.writeFileSync(list, jobs.map(j => `file '${j.file}'`).join('\n'));
  // captions: always written as .srt; burned into the picture when the project says "burnCaptions": true (or --burn). --no-burn wins.
  const srt = out.replace(/\.mp4$/, '.srt'), hasSrt = writeSrt(proj, srt), burn = hasSrt && !A['no-burn'] && (A.burn || proj.burnCaptions);
  const ffargs = ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list];
  const vcodec = burn
    ? ['-vf', `subtitles='${srt.replace(/\\/g, '/').replace(/:/g, '\\:').replace(/'/g, "\\'")}':force_style='FontName=DejaVu Sans,FontSize=16,Bold=1,Outline=3,Shadow=1,Alignment=2,MarginV=36'`, '-c:v', 'libx264', '-crf', String(proj.crf), '-preset', 'medium', '-pix_fmt', 'yuv420p']
    : ['-c:v', 'copy'];
  if (proj.audio) ffargs.push('-i', path.resolve(proj.audio), '-map', '0:v', '-map', '1:a', ...vcodec, '-c:a', 'aac', '-b:a', '192k', '-shortest'); else ffargs.push(...(burn ? vcodec : ['-c', 'copy']));
  ffargs.push('-movflags', '+faststart', out);
  const r = spawnSync('ffmpeg', ffargs, { stdio: 'inherit' }); if (r.status) process.exit(r.status);
  if (hasSrt) console.log(burn ? 'captions burned in + ' + srt : 'captions -> ' + srt);
  console.log(`done: ${out}  (render time ${fmt((Date.now() - t0) / 1000)})`);
}

async function estimate(file) {
  const proj = loadProject(file, { preview: !!A.preview }), d = await display();
  console.log('benchmarking (this builds a few scenes and renders sample frames)...');
  const r = JSON.parse((await run(WORKER, ['--project', path.resolve(file), '--bench', '8', ...(A.preview ? ['--preview'] : [])], d.env)).trim().split('\n').pop()); d.stop();
  const frameS = r.msPerFrame / 1000, setupS = (r.setupMsPerScene / 1000) * proj.scenes.length, cpu = frameS * proj.totalFrames + setupS;
  console.log(`\nMeasured on this machine (1 core/worker): ${r.msPerFrame.toFixed(0)} ms/frame at ${r.W}x${r.H} internal -> ${proj.width}x${proj.height} out (${(1000 / r.msPerFrame).toFixed(1)} fps)`);
  console.log(`Project: ${fmt(proj.duration)} = ${proj.totalFrames} frames, ${proj.scenes.length} scenes`);
  console.log(`Total CPU time: ${fmt(cpu)}\n\n  workers | wall-clock render time`);
  for (const w of [1, 2, 4, 8, 16, 32]) console.log(`  ${String(w).padStart(7)} | ${fmt(cpu / (w * (w === 1 ? 1 : 0.9)))}`);
  console.log('\n(Assumes ~90% parallel efficiency. Software GL; a GPU box renders several times faster.)');
}

(async () => {
  if (cmd === 'generate') {
    const p = generate({ minutes: +A.minutes || 1, seed: +A.seed || 1, width: +A.width || 1280, height: +A.height || 720, fps: +A.fps || 30, supersample: A.ss ? +A.ss : 1.5, title: A.title || 'Auto-generated toon video' });
    const out = A.out || 'project.json'; fs.writeFileSync(out, JSON.stringify(p, null, 2)); console.log(`wrote ${out}: ${p.scenes.length} scenes, ${p.scenes.reduce((s, x) => s + x.duration, 0)}s`);
  } else if (cmd === 'render') await render(A._[0]);
  else if (cmd === 'estimate') await estimate(A._[0]);
  else if (cmd === 'still') {
    const proj = loadProject(A._[0], { preview: !!A.preview }), f = Math.round((+A.t || 0) * proj.fps), d = await display(), out = path.resolve(A.out || 'still.png');
    await run(WORKER, ['--project', path.resolve(A._[0]), '--png', '--out', out, '--from', f, '--to', f + 1, ...(A.preview ? ['--preview'] : [])], d.env); d.stop(); console.log('wrote', out);
  } else console.log(`three-toon-studio
  generate --minutes 20 [--seed N --width 1920 --height 1080 --fps 30 --ss 1.5 --out project.json]
  render   <project.json> [--out v.mp4 --workers N --preview --chunk 300 --from SEC --to SEC]   (resumable)
  still    <project.json> --t 12.5 [--out frame.png --preview]
  estimate <project.json> [--preview]`);
})().catch(e => { console.error(e); process.exit(1); });
