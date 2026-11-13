// Auto-generator: builds a complete multi-scene project of any length from a seed.
import { mulberry } from './engine.mjs';

const WEIGHTS = [['walk', 60], ['run', 14], ['idle', 10], ['wave', 8], ['jump', 4], ['dance', 4]];
const THEME_POOL = ['day', 'day', 'sunset', 'night', 'snow', 'desert', 'day', 'sunset'];
const SCARVES = [0xe63946, 0xffb703, 0x06d6a0, 0x4cc9f0, 0xf72585, 0xff7b00];
const HATS = ['none', 'none', 'cap', 'tophat'], HAT_COL = [0x2a6fdb, 0xd62828, 0x2b9348, 0x7b2cbf];

export function generate({ minutes = 1, seed = 1, width = 1280, height = 720, fps = 30, supersample = 1.5, sceneLen = [30, 60], title = 'Auto-generated toon video' } = {}) {
  const rand = mulberry(seed * 7919 + 3), rr = (a, b) => a + (b - a) * rand(), pick = a => a[Math.floor(rand() * a.length)];
  const weighted = () => { let r = rand() * WEIGHTS.reduce((s, w) => s + w[1], 0); for (const [a, w] of WEIGHTS) if ((r -= w) <= 0) return a; return 'walk'; };
  const total = Math.round(minutes * 60), scenes = []; let used = 0, n = 0, lastTheme = '';
  while (used < total) {
    let dur = Math.round(rr(sceneLen[0], sceneLen[1])); if (total - used - dur < sceneLen[0] / 2) dur = total - used; dur = Math.min(dur, total - used);
    let theme; do theme = pick(THEME_POOL); while (theme === lastTheme && THEME_POOL.length > 1); lastTheme = theme;
    const hero = { id: 'hero', start: rand(), reverse: rand() < 0.2, character: { color: 0x14141f, scarf: pick(SCARVES), hat: pick(HATS), hatColor: pick(HAT_COL) }, timeline: [{ t: 0, action: 'walk' }] };
    for (let t = rr(4, 8); t < dur - 2; t += rr(4, 10)) hero.timeline.push({ t: Math.round(t * 10) / 10, action: weighted() });
    const actors = [hero];
    if (rand() < 0.45) actors.push({ id: 'buddy', follow: { target: 'hero', side: pick([-1.7, 1.7]), back: rr(-0.3, 0.8) }, character: { color: 0x2b2d42, scarf: pick(SCARVES), scale: 0.82, hat: pick(HATS), hatColor: pick(HAT_COL) } });
    const shots = []; let last = '';
    for (let t = 0; t < dur;) {
      const len = Math.min(rr(5, 9), dur - t), type = (() => { let k; do k = pick(['follow', 'follow', 'side', 'orbit', 'closeup', 'fixed', 'crane', 'topdown']); while (k === last); return k; })(); last = type;
      const sg = pick([-1, 1]), sh = { from: Math.round(t * 10) / 10, to: Math.round((t + len) * 10) / 10, type, target: 'hero' };
      if (type === 'side') { sh.side = 6 * sg; sh.ahead = rr(3, 6); }
      if (type === 'orbit') { sh.speed = 0.3 * sg; sh.angle = rr(0, 6.28); sh.radius = rr(12, 17); sh.height = rr(6, 9.5); }
      if (type === 'closeup') { sh.side = 1.4 * sg; }
      if (type === 'fixed') { sh.side = rr(4, 6) * sg; sh.ahead = rr(8, 12); }
      if (type === 'follow') { sh.side = rr(1.5, 3.2) * sg; sh.back = rr(5.5, 7.5); }
      if (type === 'crane') { sh.camFrom = { back: rr(7, 9), side: 3 * sg, up: 1 }; sh.camTo = { back: 3, side: 2 * sg, up: rr(6, 9) }; }
      shots.push(sh); t += len;
    }
    scenes.push({ id: `scene${++n}`, duration: dur, world: { theme, seed: Math.floor(rand() * 1e6), houses: 4 + Math.floor(rand() * 5) }, actors, shots, captions: [] });
    used += dur;
  }
  return { title, width, height, fps, supersample, fade: 0.5, scenes };
}
