// Project loader: fills defaults, computes the global frame timeline, writes SRT captions.
import fs from 'fs';
import { registerAssets } from './assets.mjs';

export function loadProject(file, o = {}) {
  const p = typeof file === 'string' ? JSON.parse(fs.readFileSync(file, 'utf8')) : file;
  registerAssets(p.assets);
  const pv = !!o.preview, even = n => Math.max(2, Math.round(n / 2) * 2);
  const proj = {
    title: p.title || 'Untitled', fps: p.fps ?? 30, audio: p.audio ?? null, fade: p.fade ?? 0.5, burnCaptions: !!p.burnCaptions,
    width: even(pv ? 640 : (p.width ?? 1280)), height: even(pv ? 360 : (p.height ?? 720)),
    ss: pv ? 1 : (p.supersample ?? 1.5), crf: pv ? 28 : (p.crf ?? 17), scenes: [],
  };
  let f = 0;
  for (const s of p.scenes) { const frames = Math.round(s.duration * proj.fps); proj.scenes.push({ ...s, startFrame: f, frames }); f += frames; }
  proj.totalFrames = f; proj.duration = f / proj.fps;
  proj.sceneAt = frame => { let i = 0; for (let k = 0; k < proj.scenes.length; k++) if (proj.scenes[k].startFrame <= frame) i = k; return i; };
  return proj;
}

export function writeSrt(proj, file) {
  const ts = s => { const ms = Math.round(s * 1000), h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60, sec = Math.floor(ms / 1000) % 60; return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')},${String(ms % 1000).padStart(3, '0')}`; };
  let n = 1, out = '';
  for (const sc of proj.scenes) for (const c of sc.captions || []) { const base = sc.startFrame / proj.fps; out += `${n++}\n${ts(base + c.from)} --> ${ts(base + c.to)}\n${c.text}\n\n`; }
  if (out) fs.writeFileSync(file, out);
  return !!out;
}
