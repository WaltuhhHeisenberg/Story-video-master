// Stickman rig + procedural animation clips. Clips are pure functions of time/phase (stateless),
// so any frame can be rendered independently -> perfect for parallel rendering.
import { THREE, toonMat, lerp } from './engine.mjs';
import { characterParts } from './assets.mjs';

export const ACTIONS = { idle: { speed: 0 }, walk: { speed: 2.9, stride: 1.7 }, run: { speed: 5.6, stride: 2.6 }, wave: { speed: 0 }, jump: { speed: 0 }, dance: { speed: 0 } };

const neutral = () => ({ hipL: 0, kneeL: 0.05, hipR: 0, kneeR: 0.05, shL: 0, elL: -0.2, shR: 0, elR: -0.2, abdL: -0.08, abdR: -0.08, bodyX: 0, bodyY: 0, bodyZ: 0, headX: 0, headY: 0, headZ: 0, bob: 0, lift: 0, tail: 0.7 });

/** c = { p: phase radians (distance-based for walk/run), t: seconds since action start } */
export function sample(action, c) {
  const a = neutral(), { p, t } = c, S = Math.sin, C = Math.cos, mx = Math.max;
  switch (action) {
    case 'walk':
      a.hipL = -0.6 * S(p); a.hipR = -0.6 * S(p + Math.PI); a.kneeL = 0.15 + 0.85 * mx(0, C(p)); a.kneeR = 0.15 + 0.85 * mx(0, C(p + Math.PI));
      a.shL = 0.55 * S(p); a.shR = 0.55 * S(p + Math.PI); a.elL = -0.45 - 0.3 * mx(0, S(p)); a.elR = -0.45 - 0.3 * mx(0, S(p + Math.PI));
      a.bodyX = 0.09; a.bodyZ = 0.03 * S(p); a.bodyY = 0.12 * S(p); a.headY = 0.15 * S(p * 0.5); a.headZ = 0.04 * S(p); a.bob = 0.04 * C(2 * p) - 0.02; a.tail = 0.7 + 0.25 * S(t * 9) + 0.1 * S(p * 2); break;
    case 'run':
      a.hipL = -1.0 * S(p); a.hipR = -1.0 * S(p + Math.PI); a.kneeL = 0.3 + 1.4 * mx(0, C(p)); a.kneeR = 0.3 + 1.4 * mx(0, C(p + Math.PI));
      a.shL = 1.0 * S(p); a.shR = 1.0 * S(p + Math.PI); a.elL = -1.5; a.elR = -1.5;
      a.bodyX = 0.28; a.bodyZ = 0.04 * S(p); a.bodyY = 0.18 * S(p); a.bob = 0.1 * Math.abs(C(p)) - 0.04; a.tail = 1.1 + 0.2 * S(t * 14); break;
    case 'wave':
      a.abdR = 2.5 + 0.2 * S(t * 3); a.elR = -0.5 + 0.55 * S(t * 10); a.headZ = 0.1; a.bob = 0.01 * S(t * 2); a.bodyZ = 0.03 * S(t * 2); a.tail = 0.5 + 0.1 * S(t * 2); break;
    case 'jump': {
      const q = (t % 1.1) / 1.1, tk = S(q * Math.PI);
      a.lift = 0.8 * 4 * q * (1 - q); a.hipL = -0.7 * tk; a.hipR = -0.4 * tk; a.kneeL = 1.2 * tk; a.kneeR = 1.0 * tk; a.abdL = 2.3 * tk - 0.08; a.abdR = 2.3 * tk - 0.08; a.elL = -0.2; a.elR = -0.2; a.tail = 0.3 + 0.5 * (1 - tk); break;
    }
    case 'dance': {
      const q = t * 7;
      a.bob = 0.06 * Math.abs(S(q)); a.bodyZ = 0.15 * S(q); a.bodyY = 0.3 * S(q * 0.5); a.headZ = 0.2 * S(q);
      a.abdR = 1.6 + 0.5 * S(q); a.abdL = 1.6 + 0.5 * S(q + Math.PI); a.elL = -0.6; a.elR = -0.6;
      a.hipL = -0.3 * S(q); a.hipR = 0.3 * S(q); a.kneeL = 0.3 + 0.5 * mx(0, S(q)); a.kneeR = 0.3 + 0.5 * mx(0, -S(q)); a.tail = 0.7 + 0.3 * S(q * 2); break;
    }
    default: // idle
      a.bob = 0.01 * S(t * 2); a.headY = 0.25 * S(t * 0.7); a.shL = 0.05 * S(t * 1.3); a.shR = -0.05 * S(t * 1.3); a.bodyZ = 0.01 * S(t * 1.1); a.tail = 0.5 + 0.1 * S(t * 2);
  }
  return a;
}
export function blend(a, b, w) { const o = {}; for (const k in a) o[k] = lerp(a[k], b[k], w); return o; }

/** Build a stickman. opts: { color, scarf, hat: 'none'|'cap'|'tophat', scale } */
export function createStickman(opts = {}) {
  const ink = toonMat({ color: opts.color ?? 0x14141f }), white = new THREE.MeshBasicMaterial({ color: 0xffffff }), red = toonMat({ color: opts.scarf ?? 0xe63946 });
  const limb = (len, r) => new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 10).translate(0, -len / 2, 0), ink);
  const joint = r => new THREE.Mesh(new THREE.SphereGeometry(r, 10, 8), ink);
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.95, 10).translate(0, 0.475, 0), ink); torso.position.y = 1.0; body.add(torso);
  const head = new THREE.Group(); head.position.y = 2.22; body.add(head);
  head.add(new THREE.Mesh(new THREE.SphereGeometry(0.3, 16, 12), ink));
  for (const sx of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 6), white); e.position.set(sx * 0.11, 0.05, 0.27); head.add(e); }
  const smile = new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.015, 6, 12, Math.PI), white); smile.position.set(0, -0.06, 0.28); smile.rotation.z = Math.PI; head.add(smile);
  if (opts.hat === 'tophat') { const hm = toonMat({ color: opts.hatColor ?? 0x2b2b3a }); const c = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.38, 14), hm); c.position.y = 0.46; const br = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.04, 14), hm); br.position.y = 0.28; head.add(c, br); }
  if (opts.hat === 'cap') { const hm = toonMat({ color: opts.hatColor ?? 0x2a6fdb }); const d = new THREE.Mesh(new THREE.SphereGeometry(0.31, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), hm); d.position.y = 0.06; const br = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.03, 0.3), hm); br.position.set(0, 0.1, 0.34); head.add(d, br); }
  const scarf = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.05, 8, 16), red); scarf.rotation.x = Math.PI / 2; scarf.position.y = 1.92; body.add(scarf);
  const tailP = new THREE.Group(); tailP.position.set(0, 1.92, -0.18); body.add(tailP); tailP.add(new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.7, 0.03).translate(0, -0.35, 0), red));
  const leg = x => { const hip = new THREE.Group(); hip.position.set(x, 1.0, 0); body.add(hip); hip.add(joint(0.085), limb(0.5, 0.07)); const knee = new THREE.Group(); knee.position.y = -0.5; hip.add(knee); knee.add(joint(0.08), limb(0.5, 0.065), new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.28, 8).rotateX(Math.PI / 2).translate(0, -0.5, 0.1), ink)); return { hip, knee }; };
  const arm = x => { const sh = new THREE.Group(); sh.position.set(x, 1.82, 0); body.add(sh); sh.add(joint(0.075), limb(0.42, 0.06)); const el = new THREE.Group(); el.position.y = -0.42; sh.add(el); const hand = new THREE.Mesh(new THREE.SphereGeometry(0.085, 8, 6), ink); hand.position.y = -0.42; el.add(joint(0.065), limb(0.4, 0.055), hand); return { sh, el }; };
  const lL = leg(-0.12), lR = leg(0.12), aL = arm(-0.17), aR = arm(0.17);
  characterParts(opts.parts, { head, body, root });
  root.scale.setScalar(opts.scale ?? 1);
  return {
    root,
    pose(a) {
      body.position.y = a.bob; body.rotation.set(a.bodyX, a.bodyY, a.bodyZ);
      lL.hip.rotation.x = a.hipL; lL.knee.rotation.x = a.kneeL; lR.hip.rotation.x = a.hipR; lR.knee.rotation.x = a.kneeR;
      aL.sh.rotation.x = a.shL; aL.sh.rotation.z = -a.abdL; aL.el.rotation.x = a.elL; aR.sh.rotation.x = a.shR; aR.sh.rotation.z = a.abdR; aR.el.rotation.x = a.elR;
      head.rotation.set(a.headX, a.headY, a.headZ); tailP.rotation.x = a.tail; tailP.rotation.z = 0.15 * Math.sin(a.tail * 9);
    },
  };
}
