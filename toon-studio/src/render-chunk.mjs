// Worker: renders a frame range [from,to) of a project into an mp4 segment (or a PNG / benchmark).
// Usage: node render-chunk.mjs --project p.json --out seg.mp4 --from 0 --to 300 [--preview] [--png] [--bench N]
import { spawn } from 'child_process';
import { createStage, disposeScene } from './engine.mjs';
import { buildScene } from './scene.mjs';
import { loadProject } from './project.mjs';

const args = {}; const av = process.argv.slice(2);
for (let i = 0; i < av.length; i++) if (av[i].startsWith('--')) { const k = av[i].slice(2); args[k] = (av[i + 1] && !av[i + 1].startsWith('--')) ? av[++i] : true; }
const proj = loadProject(args.project, { preview: !!args.preview });
const W = Math.round(proj.width * proj.ss), H = Math.round(proj.height * proj.ss);
const stage = createStage(W, H);

const vf = `vflip${W !== proj.width ? `,scale=${proj.width}:${proj.height}:flags=lanczos` : ''}`;
const enc = args.png ? ['-frames:v', '1', args.out]
  : args.bench ? ['-c:v', 'libx264', '-preset', 'medium', '-crf', String(proj.crf), '-pix_fmt', 'yuv420p', '-f', 'null', '-']
  : ['-c:v', 'libx264', '-preset', 'medium', '-crf', String(proj.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', args.out];
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(proj.fps), '-i', '-', '-vf', vf, ...enc], { stdio: ['pipe', 'inherit', 'inherit'] });

function fade(buf, f) {
  const sc = proj.scenes[proj.sceneAt(f)], local = (f - sc.startFrame) / proj.fps, fd = proj.fade;
  if (!fd) return; const k = Math.min(1, local / fd, (sc.duration - local) / fd); if (k >= 1) return;
  const kk = Math.max(0, k); for (let i = 0; i < buf.length; i += 4) { buf[i] *= kk; buf[i + 1] *= kk; buf[i + 2] *= kk; }
}
const write = async buf => { if (!ff.stdin.write(Buffer.from(buf))) await new Promise(r => ff.stdin.once('drain', r)); };

let built = null, cur = -1;
async function renderFrame(f) {
  const si = proj.sceneAt(f), sc = proj.scenes[si];
  if (si !== cur) { if (built) disposeScene(built.scene); built = buildScene(stage, sc); cur = si; }
  built.update((f - sc.startFrame) / proj.fps);
  stage.renderer.render(built.scene, built.camera);
  const buf = stage.readFrame(); fade(buf, f); await write(buf);
}

if (args.bench) { // timing probe across scenes
  const n = +args.bench, picks = []; const step = Math.max(1, Math.floor(proj.scenes.length / 6));
  for (let i = 0; i < proj.scenes.length && picks.length < 6; i += step) picks.push(i);
  let setup = 0, frames = 0, ms = 0;
  for (const si of picks) { const sc = proj.scenes[si], t0 = Date.now(); cur = -1; await renderFrame(sc.startFrame + Math.floor(sc.frames / 2)); setup += Date.now() - t0;
    const t1 = Date.now(); for (let k = 1; k <= n; k++) await renderFrame(sc.startFrame + Math.floor(sc.frames / 2) + k); ms += Date.now() - t1; frames += n; }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log(JSON.stringify({ msPerFrame: ms / frames, setupMsPerScene: setup / picks.length, sampledScenes: picks.length, W, H }));
} else {
  const f0 = +args.from || 0, f1 = Math.min(+args.to || proj.totalFrames, proj.totalFrames);
  for (let f = f0; f < f1; f++) await renderFrame(f);
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
process.exit(0);
