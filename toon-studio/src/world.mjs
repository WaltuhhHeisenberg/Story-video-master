// World builder: terrain, path, props, sky, clouds, weather. Fully seeded => deterministic per frame.
import { THREE, Batch, G, toonMat, mulberry, smooth } from './engine.mjs';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { CUSTOM_THEMES, PROPS, addParts } from './assets.mjs';

const F_ALL = { trees: true, pines: true, houses: true, windmill: true, flowers: true, rocks: true };
export const THEMES = {
  day: {
    sky: [0x4aa8ff, 0xcdeeff], fog: 0xcdeeff, grass: [0x7ed957, 0x5cc04a], dirt: 0xe8c98a,
    hemi: [0xdff3ff, 0x8fcf6a, 1.1], sun: { color: 0xfff3a0, dir: [-0.5, 0.45, -0.75], int: 2.2 },
    leaves: [0x3fae49, 0x2f9e44, 0x57c84d, 0x6fd45a], pine: [0x2a9d5c, 0x34b36a, 0x40c879], trunk: 0x8b5a2b,
    walls: [0xff8fa3, 0xffd166, 0x8ecae6, 0xb8f2a0, 0xffadad], roofs: [0xe63946, 0xf77f00, 0x7b2cbf, 0x2a9d8f],
    cloud: { color: 0xffffff, emissive: 0x9aa3b5, count: 16 }, features: { ...F_ALL },
  },
  sunset: {
    sky: [0x3b2a6b, 0xff9a62], fog: 0xffb48a, fogN: 40, fogF: 140, grass: [0x9ccf4a, 0x6aa83f], dirt: 0xd9a066,
    hemi: [0xffd2a8, 0x7a6a8a, 0.95], sun: { color: 0xffd27a, dir: [-0.15, 0.1, -0.95], int: 2.0 },
    leaves: [0x8ab83a, 0x6aa83f, 0xc9a227, 0xd9822b], pine: [0x2f7d52, 0x3a9266, 0x48a877], trunk: 0x7a4b2a,
    walls: [0xffa69e, 0xffd6a5, 0xcdb4db, 0xbde0fe], roofs: [0xc1121f, 0xe85d04, 0x6a4c93],
    cloud: { color: 0xffd9c2, emissive: 0xb0707a, count: 14 }, features: { ...F_ALL }, glowWindows: true,
  },
  night: {
    sky: [0x070a24, 0x2a3a7a], fog: 0x1a2255, fogN: 30, fogF: 120, grass: [0x2f6b4a, 0x275a3f], dirt: 0x6b5b7b,
    hemi: [0x7788cc, 0x223355, 0.8], sun: { color: 0xdfe8ff, dir: [0.4, 0.5, -0.7], int: 0.9, moon: true },
    leaves: [0x2a7a58, 0x236b4d, 0x2f8a63], pine: [0x1f6b55, 0x25805f, 0x2c9370], trunk: 0x4a3626,
    walls: [0x9a8fc7, 0xc7a0b8, 0x8fb4c7], roofs: [0x5a3d8a, 0x7a2e4d, 0x2e5a7a],
    cloud: { color: 0x9aa7d6, emissive: 0x2a3566, count: 8 }, features: { ...F_ALL, windmill: false }, glowWindows: true, stars: true, lamps: true,
  },
  snow: {
    sky: [0x8fb8e8, 0xeaf4ff], fog: 0xeaf4ff, fogN: 35, fogF: 120, grass: [0xffffff, 0xe3f0ff], dirt: 0xc7d3e6,
    hemi: [0xeef6ff, 0xbcd0e8, 1.25], sun: { color: 0xffffff, dir: [-0.4, 0.5, -0.7], int: 1.6 },
    leaves: [0x9bb8d3], pine: [0x3f7f6a, 0x4a9179, 0x58a38a], trunk: 0x7a5a40, snowCap: true,
    walls: [0xc77d5a, 0xb85c38, 0xd9a066], roofs: [0xffffff, 0xeef4ff], rock: 0xaab4c4,
    cloud: { color: 0xf4f8ff, emissive: 0xaab6cc, count: 20 }, features: { ...F_ALL, trees: false, flowers: false, windmill: false, snowmen: true }, snowfall: true,
  },
  desert: {
    sky: [0x59b8ff, 0xffe9b8], fog: 0xffe9b8, fogN: 50, fogF: 170, grass: [0xf2d48f, 0xe6c277], dirt: 0xd9a35f,
    hemi: [0xfff0cc, 0xd9a35f, 1.15], sun: { color: 0xfff1a8, dir: [-0.3, 0.7, -0.6], int: 2.3 },
    leaves: [], pine: [], trunk: 0x8b5a2b, walls: [0xe8c39e, 0xf1d3b3, 0xd9a47a], roofs: [0xb8693d, 0xa05a2c], rock: 0xc98b5a,
    cloud: { color: 0xffffff, emissive: 0xc9b89a, count: 6 }, features: { ...F_ALL, trees: false, pines: false, flowers: false, windmill: false, cacti: true, mesas: true },
  },
};

/** Built-in theme, or a custom theme (JSON asset) that `extends` another theme and overrides any of its fields. */
export function themeOf(name = 'day', depth = 0) {
  const c = CUSTOM_THEMES[name];
  if (!c) return THEMES[name] || THEMES.day;
  if (depth > 6) throw new Error(`theme ${name}: extends chain too deep`);
  const b = themeOf(c.extends || 'day', depth + 1);
  return { ...b, ...c, sun: { ...b.sun, ...(c.sun || {}) }, cloud: { ...b.cloud, ...(c.cloud || {}) }, features: { ...b.features, ...(c.features || {}) } };
}

export function buildWorld(scene, cfg = {}) {
  const T = { ...themeOf(cfg.theme || 'day'), ...(cfg.override || {}) };
  const F = { ...T.features, ...(cfg.features || {}) };
  const rand = mulberry((cfg.seed ?? 1) * 9973 + 17), rr = (a, b) => a + (b - a) * rand();
  const pick = a => a[Math.floor(rand() * a.length)];
  const density = cfg.density ?? 1, clearance = cfg.clearance ?? 9;
  scene.background = new THREE.Color(T.fog);
  scene.fog = new THREE.Fog(T.fog, T.fogN ?? 45, T.fogF ?? 150);

  // ---- terrain height + path ----
  const amp = cfg.hills ?? 1, ph = [rr(0, 6), rr(0, 6), rr(0, 6)];
  const hAt = (x, z) => amp * (1.4 * Math.sin(x * 0.05 + ph[0]) * Math.cos(z * 0.045 + ph[1]) + 0.7 * Math.sin(x * 0.12 + z * 0.09 + ph[2]) + 0.25 * Math.sin(z * 0.25));
  const prx = cfg.path?.rx ?? 42, prz = cfg.path?.rz ?? 28, wob = cfg.path?.wobble ?? 0.25, pn = cfg.path?.points ?? 10, pph = rr(0, 6);
  const pts = [];
  for (let i = 0; i < pn; i++) { const a = (i / pn) * Math.PI * 2, r = 1 + wob * Math.sin(a * 3 + pph); pts.push(new THREE.Vector3(Math.cos(a) * prx * r, 0, Math.sin(a) * prz * r)); }
  const curve = new THREE.CatmullRomCurve3(pts, true, 'catmullrom', 0.5);
  const len = curve.getLength(), samples = curve.getSpacedPoints(400);
  const dist = (x, z) => { let m = 1e9; for (const p of samples) { const d = (p.x - x) ** 2 + (p.z - z) ** 2; if (d < m) m = d; } return Math.sqrt(m); };
  const uOf = s => ((s / len) % 1 + 1) % 1;
  const path = {
    len, dist,
    pointAt: s => { const p = curve.getPointAt(uOf(s)); return new THREE.Vector3(p.x, hAt(p.x, p.z), p.z); },
    tangentAt: s => curve.getTangentAt(uOf(s)).setY(0).normalize(),
  };

  // ---- terrain mesh ----
  {
    const size = cfg.size ?? 420, seg = cfg.segments ?? 210;
    const g = new THREE.PlaneGeometry(size, size, seg, seg); g.rotateX(-Math.PI / 2);
    const pos = g.attributes.position, col = new Float32Array(pos.count * 3);
    const gA = new THREE.Color(T.grass[0]), gB = new THREE.Color(T.grass[1]), dirt = new THREE.Color(T.dirt), tmp = new THREE.Color();
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), z = pos.getZ(i); pos.setY(i, hAt(x, z));
      tmp.copy(gA).lerp(gB, 0.5 + 0.5 * Math.sin(x * 0.11) * Math.cos(z * 0.13) + 0.3 * Math.sin(x * 0.5 + z * 0.4));
      tmp.lerp(dirt, 1 - smooth(1.9, 2.6, dist(x, z)));
      col.set([tmp.r, tmp.g, tmp.b], i * 3);
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.computeVertexNormals();
    scene.add(new THREE.Mesh(g, toonMat({ vertexColors: true })));
  }

  // ---- props ----
  const props = new Batch(), tiny = new Batch(), glow = new Batch(), shadows = new Batch();
  const occupied = [];
  const clear = (x, z, r, minPath) => dist(x, z) > minPath && occupied.every(o => Math.hypot(o.x - x, o.z - z) > o.r + r);
  const place = (x, z, r) => occupied.push({ x, z, r });
  const shadowAt = (x, z, r) => shadows.add(G.circ, 0x000000, x, hAt(x, z) + 0.14, z, -Math.PI / 2, 0, 0, r, r, r);
  const onPath = (u, side, d) => { const s = u * len, P = path.pointAt(s), t = path.tangentAt(s), N = new THREE.Vector3(-t.z, 0, t.x).multiplyScalar(side); return { x: P.x + N.x * d, z: P.z + N.z * d, N }; };

  let windmill = null;
  if (F.houses) {
    const n = cfg.houses ?? 7;
    for (let i = 0; i < n; i++) {
      const { x, z, N } = onPath((i + 0.5 + rr(-0.2, 0.2)) / n, i % 2 ? 1 : -1, rr(9, 13));
      if (!clear(x, z, 3, 5.2)) continue; place(x, z, 3.5);
      const wall = T.walls[i % T.walls.length], roof = T.roofs[i % T.roofs.length], yaw = Math.atan2(-N.x, -N.z), s = rr(0.9, 1.2);
      props.at(x, hAt(x, z), z, yaw, s);
      props.add(G.box, wall, 0, 1.2, 0, 0, 0, 0, 3.2, 2.4, 3).add(G.cone, roof, 0, 3.2, 0, 0, Math.PI / 4, 0, 3, 1.8, 3).add(G.box, 0x7a4b2a, 0, 0.8, 1.51, 0, 0, 0, 0.8, 1.6, 0.1).add(G.box, 0xb0b0b0, 0.9, 3.7, -0.5, 0, 0, 0, 0.5, 1.2, 0.5);
      const wb = T.glowWindows ? glow : props, wc = T.glowWindows ? 0xffe08a : 0xcdefff;
      wb.at(x, hAt(x, z), z, yaw, s).add(G.box, wc, -1.0, 1.5, 1.52, 0, 0, 0, 0.6, 0.6, 0.1).add(G.box, wc, 1.0, 1.5, 1.52, 0, 0, 0, 0.6, 0.6, 0.1);
      props.reset(); wb.reset(); shadowAt(x, z, 3.4);
    }
  }
  if (F.windmill) {
    const { x, z, N } = onPath(0.17, -1, 14), yaw = Math.atan2(-N.x, -N.z); place(x, z, 4);
    props.at(x, hAt(x, z), z, yaw).add(new THREE.CylinderGeometry(0.9, 1.5, 6, 10), 0xfff1d6, 0, 3, 0).add(new THREE.ConeGeometry(1.3, 1.6, 10), 0xd1495b, 0, 6.8, 0).add(G.box, 0x7a4b2a, 0, 0.7, 1.4, 0, 0, 0, 0.8, 1.4, 0.2).reset();
    shadowAt(x, z, 3.2);
    const hub = new THREE.Group(); hub.position.set(x, hAt(x, z) + 5.6, z); hub.rotation.y = yaw;
    windmill = new THREE.Group(); windmill.position.z = 1.1; hub.add(windmill);
    for (let k = 0; k < 4; k++) {
      const arm = new THREE.Group(); arm.rotation.z = k * Math.PI / 2;
      const b = new THREE.Mesh(new THREE.BoxGeometry(0.9, 3.4, 0.12), toonMat({ color: 0xffffff })); b.position.y = 2.1; arm.add(b);
      const s = new THREE.Mesh(new THREE.BoxGeometry(0.16, 3.6, 0.2), toonMat({ color: 0x7a4b2a })); s.position.set(-0.5, 2.0, 0); arm.add(s); windmill.add(arm);
    }
    windmill.add(new THREE.Mesh(new THREE.SphereGeometry(0.35, 10, 8), toonMat({ color: 0xd1495b }))); scene.add(hub);
  }
  // trees / pines / cacti / snowmen
  const nTrees = Math.round(170 * density);
  if (F.trees || F.pines || F.cacti || F.snowmen) {
    let n = 0;
    for (let tries = 0; tries < nTrees * 5 && n < nTrees; tries++) {
      const a = rand() * Math.PI * 2, r = Math.sqrt(rand()) * 105, x = Math.cos(a) * r * 1.2, z = Math.sin(a) * r * 0.9;
      if (!clear(x, z, 1.6, clearance)) continue; place(x, z, 1.6);
      const s = rr(0.8, 1.5), y = hAt(x, z), i = n++;
      props.at(x, y, z, rand() * 6.28, s);
      if (F.cacti) {
        props.add(G.cyl, 0x4caf50, 0, 1.4, 0, 0, 0, 0, 0.4, 2.8, 0.4).add(G.sph, 0x4caf50, 0, 2.8, 0, 0, 0, 0, 0.4, 0.4, 0.4)
          .add(G.cyl, 0x4caf50, 0.7, 1.7, 0, 0, 0, Math.PI / 2, 0.25, 0.9, 0.25).add(G.cyl, 0x4caf50, 1.1, 2.2, 0, 0, 0, 0, 0.25, 1.0, 0.25).add(G.sph, 0x4caf50, 1.1, 2.7, 0, 0, 0, 0, 0.25, 0.25, 0.25);
      } else if (F.snowmen && i % 5 === 0) {
        props.add(G.sph, 0xffffff, 0, 0.7, 0, 0, 0, 0, 0.8, 0.7, 0.8).add(G.sph, 0xffffff, 0, 1.65, 0, 0, 0, 0, 0.6, 0.55, 0.6).add(G.sph, 0xffffff, 0, 2.4, 0, 0, 0, 0, 0.45, 0.45, 0.45)
          .add(G.cone, 0xff8c1a, 0, 2.4, 0.5, Math.PI / 2, 0, 0, 0.09, 0.45, 0.09).add(G.cyl, 0x222222, 0, 2.85, 0, 0, 0, 0, 0.35, 0.35, 0.35).add(G.cyl, 0x222222, 0, 2.7, 0, 0, 0, 0, 0.55, 0.05, 0.55);
      } else if ((F.pines && (!F.trees || i % 3 === 0)) && T.pine.length) {
        const [c1, c2, c3] = T.pine;
        props.add(G.cyl, T.trunk, 0, 0.7, 0, 0, 0, 0, 0.3, 1.4, 0.3).add(G.cone, c1, 0, 2.3, 0, 0, 0, 0, 1.6, 2.2, 1.6).add(G.cone, c2, 0, 3.6, 0, 0, 0, 0, 1.3, 2.0, 1.3).add(G.cone, c3, 0, 4.8, 0, 0, 0, 0, 0.9, 1.7, 0.9);
        if (T.snowCap) props.add(G.cone, 0xffffff, 0, 3.0, 0, 0, 0, 0, 1.2, 1.1, 1.2).add(G.cone, 0xffffff, 0, 4.3, 0, 0, 0, 0, 0.95, 1.0, 0.95).add(G.cone, 0xffffff, 0, 5.4, 0, 0, 0, 0, 0.6, 0.8, 0.6);
      } else if (F.trees && T.leaves.length) {
        const lc = T.leaves[i % T.leaves.length];
        props.add(G.cyl, T.trunk, 0, 1.2, 0, 0, 0, 0, 0.32, 2.4, 0.32).add(G.sph, lc, 0, 3.5, 0, 0, 0, 0, 1.7, 1.5, 1.7).add(G.sph, lc, 1.0, 4.3, 0.3, 0, 0, 0, 1.2, 1.1, 1.2).add(G.sph, lc, -0.9, 4.1, -0.4, 0, 0, 0, 1.1, 1.0, 1.1);
      }
      props.reset(); shadowAt(x, z, 1.9 * s);
    }
  }
  if (F.mesas) for (let i = 0; i < 14; i++) {
    const a = rr(0, 6.28), r = rr(95, 150), x = Math.cos(a) * r, z = Math.sin(a) * r, h = rr(10, 22), w = rr(7, 13), y = hAt(x, z);
    props.add(G.cyl, 0xc9784a, x, y + h / 2, z, 0, 0, 0, w, h, w).add(G.cyl, 0xe0956a, x, y + h + 0.6, z, 0, 0, 0, w * 0.95, 1.2, w * 0.95);
  }
  if (F.rocks) for (let i = 0, n = 0; i < 300 && n < 40; i++) {
    const x = rr(-80, 80), z = rr(-60, 60); if (!clear(x, z, 1, 5)) continue; n++; place(x, z, 1);
    const s = rr(0.4, 1.1); props.at(x, hAt(x, z), z).add(G.dodec, T.rock ?? 0xb7bcc7, 0, s * 0.4, 0, rand(), rand(), 0, s * 1.2, s * 0.8, s).reset();
  }
  if (T.lamps) for (let k = 0; k < 16; k++) {
    const { x, z } = onPath(k / 16, k % 2 ? 1 : -1, 2.8), y = hAt(x, z);
    props.add(G.cyl, 0x2b2b3a, x, y + 1.3, z, 0, 0, 0, 0.07, 2.6, 0.07); glow.add(G.sph, 0xfff0a0, x, y + 2.7, z, 0, 0, 0, 0.3, 0.3, 0.3);
  }
  if (F.flowers) {
    const fc = [0xff5d8f, 0xffd23f, 0xffffff, 0xff9f1c, 0xb388eb, 0xff6b6b], nF = Math.round(360 * density);
    for (let i = 0, n = 0; i < nF * 3 && n < nF; i++) {
      const x = rr(-85, 85), z = rr(-65, 65), d = dist(x, z); if (d < 2.6 || d > 14 || !occupied.every(o => Math.hypot(o.x - x, o.z - z) > o.r + 0.3)) continue;
      n++; const y = hAt(x, z);
      tiny.add(G.cyl, 0x3a9d3a, x, y + 0.25, z, 0, 0, 0, 0.025, 0.5, 0.025).add(G.sph, fc[n % fc.length], x, y + 0.55, z, 0, 0, 0, 0.16, 0.12, 0.16);
      if (n % 4 === 0) tiny.add(G.sph, 0x4cc24c, x + 0.5, y + 0.25, z, 0, 0, 0, 0.45, 0.35, 0.45);
    }
  }
  // ---- custom props (JSON assets): theme.props + scene world.props. Own seeded generator per prop: adding a prop never moves anything else. ----
  const hashS = s => { let h = 2166136261; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return h >>> 0; };
  const wanted = [...(T.props || []), ...(cfg.props || [])].map(e => typeof e === 'string' ? { id: e } : e);
  for (const ent of wanted) {
    const def = PROPS[ent.id]; if (!def) throw new Error(`unknown prop "${ent.id}" (add it to project.assets.props or library/assets/props)`);
    const pl = { ...(def.place || {}), ...(ent.place || {}) }, mode = pl.mode || 'scatter', rnd = mulberry(hashS(ent.id) ^ ((cfg.seed ?? 1) * 7919));
    const rg = (a, b) => a + (b - a) * rnd(), pr = (k, d) => Array.isArray(pl[k]) ? pl[k] : [d, d], rad = def.radius ?? 1.2, count = ent.count ?? pl.count ?? 1;
    const spots = [];
    if (mode === 'at') {
      const a = pl.at || { u: 0.1, side: 1, d: 6 };
      if (a.x !== undefined) spots.push({ x: a.x, z: a.z, yaw: a.yaw ?? pl.yaw ?? 0 });
      else { const o = onPath(a.u ?? 0.1, a.side ?? 1, a.d ?? 6); spots.push({ x: o.x, z: o.z, yaw: a.yaw ?? pl.yaw ?? Math.atan2(-o.N.x, -o.N.z) }); }
    } else if (mode === 'path_edge') {
      const [d0, d1] = Array.isArray(pl.d) ? pl.d : [pl.d ?? 6, pl.d ?? 6];
      for (let i = 0; i < count; i++) { const o = onPath((i + 0.5 + rg(-0.15, 0.15)) / count, (pl.sides === 'one' ? 1 : (i % 2 ? 1 : -1)), rg(d0, d1)); spots.push({ x: o.x, z: o.z, yaw: Math.atan2(-o.N.x, -o.N.z) }); }
    } else {
      const area = pl.area || 'near_path', [d0, d1] = Array.isArray(pl.d) ? pl.d : (area === 'near_path' ? [4, 14] : [clearance, 999]);
      for (let tries = 0; tries < count * 40 && spots.length < count; tries++) {
        let x, z; if (area === 'far') { const a = rg(0, 6.283), r = rg(95, 150); x = Math.cos(a) * r; z = Math.sin(a) * r; } else { x = rg(-85, 85); z = rg(-65, 65); }
        const d = dist(x, z); if (area !== 'far' && (d < d0 || d > d1)) continue;
        if (area !== 'far' && !occupied.every(o => Math.hypot(o.x - x, o.z - z) > o.r + rad)) continue;
        spots.push({ x, z, yaw: pl.yaw ?? rg(0, 6.283) });
      }
    }
    const [s0, s1] = Array.isArray(pl.scale) ? pl.scale : [1, 1];
    spots.forEach((p, i) => {
      const s = s0 === s1 ? s0 : rg(s0, s1), y = hAt(p.x, p.z);
      props.at(p.x, y, p.z, p.yaw, s); glow.at(p.x, y, p.z, p.yaw, s);
      addParts({ ...def, id: ent.id }, T, i, props, glow);
      props.reset(); glow.reset(); place(p.x, p.z, rad * s); if (def.shadow !== false) shadowAt(p.x, p.z, rad * s * 1.1);
    });
  }
  props.build(scene, toonMat({ vertexColors: true }), { outline: true });
  tiny.build(scene, toonMat({ vertexColors: true }));
  glow.build(scene, new THREE.MeshBasicMaterial({ vertexColors: true }));
  const sg = shadows.list.length ? mergeGeometries(shadows.list.map(g => { g.deleteAttribute('color'); return g; })) : null;
  if (sg) scene.add(new THREE.Mesh(sg, new THREE.MeshBasicMaterial({ color: 0x0a1a10, transparent: true, opacity: 0.28, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 })));

  // ---- sky ----
  const domeG = new THREE.SphereGeometry(500, 24, 16), dp = domeG.attributes.position, dc = new Float32Array(dp.count * 3);
  const top = new THREE.Color(T.sky[0]), hor = new THREE.Color(T.sky[1]), tc = new THREE.Color();
  for (let i = 0; i < dp.count; i++) { tc.copy(hor).lerp(top, Math.pow(Math.max(0, dp.getY(i) / 500), 0.6)); dc.set([tc.r, tc.g, tc.b], i * 3); }
  domeG.setAttribute('color', new THREE.BufferAttribute(dc, 3));
  const dome = new THREE.Mesh(domeG, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false })); dome.renderOrder = -2; scene.add(dome);
  const sunDir = new THREE.Vector3(...T.sun.dir).normalize();
  const sunM = new THREE.Mesh(new THREE.SphereGeometry(T.sun.moon ? 18 : 28, 20, 14), new THREE.MeshBasicMaterial({ color: T.sun.color, fog: false }));
  const glowM = new THREE.Mesh(new THREE.SphereGeometry(T.sun.moon ? 28 : 40, 20, 14), new THREE.MeshBasicMaterial({ color: T.sun.color, fog: false, transparent: true, opacity: 0.28, depthWrite: false }));
  scene.add(sunM, glowM);
  let stars = null;
  if (T.stars) { const sb = new Batch(); for (let i = 0; i < 260; i++) { const a = rand() * 6.28, e = Math.acos(rr(0.05, 1)), r = 470; sb.add(G.oct, 0xffffff, Math.cos(a) * Math.sin(e) * r, Math.cos(e) * r, Math.sin(a) * Math.sin(e) * r, 0, 0, 0, 1.3, 1.3, 1.3); } stars = sb.build(scene, new THREE.MeshBasicMaterial({ vertexColors: true, fog: false })); }

  const clouds = [], cb = T.cloud ?? { count: 0 };
  const cm = toonMat({ color: cb.color, emissive: cb.emissive, fog: false });
  for (let i = 0; i < (cb.count ?? 0); i++) {
    const b = new Batch(), n = 4 + Math.floor(rand() * 3);
    for (let k = 0; k < n; k++) b.add(G.sph, 0xffffff, (k - n / 2) * 3.2, rr(-0.8, 1.2), rr(-1, 1), 0, 0, 0, rr(3, 4.5), rr(2.4, 3.4), rr(2.5, 3.5));
    const m = new THREE.Mesh(mergeGeometries(b.list), cm), a = rand() * 6.28, r = rr(60, 150);
    m.userData = { x: Math.cos(a) * r, z: Math.sin(a) * r, y: rr(32, 48) }; scene.add(m); clouds.push(m);
  }
  const flakes = [];
  if (T.snowfall) { const fm = new THREE.MeshBasicMaterial({ color: 0xffffff }), fg = new THREE.SphereGeometry(0.07, 4, 3); for (let i = 0; i < 220; i++) { const m = new THREE.Mesh(fg, fm); m.userData = { x: rand() * 60, y: rand() * 30, z: rand() * 60, v: rr(1.2, 2.6) }; scene.add(m); flakes.push(m); } }

  // ---- lights ----
  scene.add(new THREE.HemisphereLight(T.hemi[0], T.hemi[1], T.hemi[2]));
  const dl = new THREE.DirectionalLight(T.sun.color, T.sun.int); dl.position.copy(sunDir).multiplyScalar(60); scene.add(dl);

  return {
    hAt, path, theme: T,
    update(t, cam) {
      dome.position.copy(cam.position);
      sunM.position.copy(cam.position).addScaledVector(sunDir, 420); glowM.position.copy(sunM.position);
      if (stars) stars.position.copy(cam.position);
      clouds.forEach(c => c.position.set(((c.userData.x + t * 0.8 + 200) % 400) - 200, c.userData.y, c.userData.z));
      if (windmill) windmill.rotation.z = -t * 1.2;
      flakes.forEach((f, i) => { const u = f.userData, w = (v, m) => ((v % m) + m) % m; f.position.set(cam.position.x + w(u.x + Math.sin(t * 0.7 + i) * 1.2, 60) - 30, cam.position.y + 12 - w(u.y + t * u.v, 30), cam.position.z + w(u.z, 60) - 30); });
    },
  };
}
