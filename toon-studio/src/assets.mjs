// Open asset registry. Assets are plain JSON (no engine code needed): custom THEMES (worlds), PROPS (objects built from primitives)
// and character PARTS (accessories). A project carries the assets it uses in its top-level "assets" block, so renders are portable.
import { THREE, G, toonMat } from './engine.mjs';

export const CUSTOM_THEMES = {}, PROPS = {};
const toInt = v => (typeof v === 'string' && v[0] === '#') ? parseInt(v.slice(1), 16) : v;
export const deepColor = v => Array.isArray(v) ? v.map(deepColor) : (v && typeof v === 'object') ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, deepColor(x)])) : toInt(v);

G.tor = new THREE.TorusGeometry(1, 0.3, 6, 14);
G.pyr = new THREE.ConeGeometry(1, 1, 4);
export const SHAPES = { box: G.box, cyl: G.cyl, sph: G.sph, cone: G.cone, dodec: G.dodec, oct: G.oct, tor: G.tor, pyr: G.pyr };

/** assets = { themes: {name: def}, props: {id: def} } (colours may be "#rrggbb" strings or ints). */
export function registerAssets(a = {}) {
  for (const [k, d] of Object.entries(a.themes || {})) CUSTOM_THEMES[k] = deepColor(d);
  for (const [k, d] of Object.entries(a.props || {})) PROPS[k] = deepColor(d);
}

/** Colour of a part: an int, or "$walls" / "$roofs" / "$leaves" / "$pine" (palette of the theme, by instance index), "$trunk", "$rock". */
export function partColor(c, T, i = 0) {
  if (typeof c === 'string' && c[0] === '$') { const v = T[c.slice(1)]; return Array.isArray(v) ? (v.length ? v[i % v.length] : 0x888888) : (v ?? 0x888888); }
  return c ?? 0x888888;
}

/** Add the parts of a prop to the batches at the current Batch base transform. parts: {shape,color,pos,rot,scale,glow} */
export function addParts(def, T, i, props, glow) {
  for (const p of def.parts || []) {
    const geo = SHAPES[p.shape]; if (!geo) throw new Error(`prop ${def.id}: unknown shape ${p.shape}`);
    const [x, y, z] = p.pos || [0, 0, 0], [rx, ry, rz] = p.rot || [0, 0, 0], [sx, sy, sz] = p.scale || [1, 1, 1];
    (p.glow ? glow : props).add(geo, partColor(p.color, T, i), x, y, z, rx, ry, rz, sx, sy, sz);
  }
}

/** Accessories of a character: [{attach:'head'|'body'|'root', shape, color, pos, rot, scale}] -> meshes. */
export function characterParts(parts = [], groups) {
  for (const p of parts) {
    const geo = SHAPES[p.shape], g = groups[p.attach || 'head']; if (!geo || !g) continue;
    const m = new THREE.Mesh(geo, toonMat({ color: toInt(p.color) ?? 0x888888 }));
    m.position.set(...(p.pos || [0, 0, 0])); m.rotation.set(...(p.rot || [0, 0, 0])); m.scale.set(...(p.scale || [1, 1, 1])); g.add(m);
  }
}
