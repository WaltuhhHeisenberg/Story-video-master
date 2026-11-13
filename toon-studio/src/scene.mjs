// Scene = world + actors + camera director. Everything is a pure function of time t (seconds, scene-local).
import { THREE, smooth, clamp, lerp } from './engine.mjs';
import { buildWorld } from './world.mjs';
import { ACTIONS, sample, blend, createStickman } from './characters.mjs';

const UP = new THREE.Vector3(0, 1, 0), BLEND = 0.3, TAU = Math.PI * 2;
const IDLE = { t: -1e9, action: 'idle', speed: 0 };

function compileActor(def, world, byId, scene) {
  const rig = createStickman(def.character || {}); scene.add(rig.root);
  const blob = new THREE.Mesh(new THREE.CircleGeometry(0.7 * (def.character?.scale ?? 1), 16).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0x0a1a10, transparent: true, opacity: 0.3, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
  scene.add(blob);
  const target = def.follow ? byId.get(def.follow.target) : null;
  const src = target || {};
  const segs = (target ? target.segs : (def.timeline?.length ? def.timeline : [{ t: 0, action: 'walk' }]))
    .map(s => ({ t: s.t ?? 0, action: s.action || 'walk', speed: s.speed ?? ACTIONS[s.action || 'walk']?.speed ?? 0 })).sort((a, b) => a.t - b.t);
  const dir = def.reverse ? -1 : 1, s0 = (def.start ?? 0) * world.path.len, phaseOff = def.follow ? (def.follow.phase ?? 0.9) : 0;
  const distAt = t => { let d = 0; for (let i = 0; i < segs.length; i++) { const a = segs[i].t, b = i + 1 < segs.length ? segs[i + 1].t : 1e9; d += segs[i].speed * clamp(t - a, 0, b - a); } return d; };
  const baseDist = target ? target.distAt : distAt;

  const self = {
    segs, distAt: baseDist, rig,
    state(t) {
      let i = -1; for (let k = 0; k < segs.length; k++) if (segs[k].t <= t) i = k;
      const cur = i < 0 ? IDLE : segs[i], prev = i > 0 ? segs[i - 1] : (i === 0 ? IDLE : null);
      const dist = baseDist(t), s = (target ? target.s0 : s0) + (target ? target.dir : dir) * dist;
      const ang = (seg) => sample(seg.action, { p: (ACTIONS[seg.action]?.stride ? (dist / ACTIONS[seg.action].stride) * TAU : 0) + phaseOff, t: t - seg.t });
      const a = prev && t - cur.t < BLEND ? blend(ang(prev), ang(cur), smooth(0, BLEND, t - cur.t)) : ang(cur);
      let P, yaw;
      if (def.at) {
        P = new THREE.Vector3(def.at.x, world.hAt(def.at.x, def.at.z), def.at.z); yaw = def.at.yaw ?? 0;
        if (def.faceTo && byId.get(def.faceTo)) { const q = byId.get(def.faceTo).state(t).P; yaw = Math.atan2(q.x - P.x, q.z - P.z); }
      } else if (target) {
        const ts = target.state(t), T = ts.fwd, S = new THREE.Vector3().crossVectors(T, UP).normalize();
        P = ts.P.clone().addScaledVector(S, def.follow.side ?? 1.6).addScaledVector(T, -(def.follow.back ?? 0.5)); P.y = world.hAt(P.x, P.z); yaw = ts.yaw + (def.follow.yaw ?? 0);
      } else {
        P = world.path.pointAt(s); const T = world.path.tangentAt(s).multiplyScalar(dir); yaw = Math.atan2(T.x, T.z);
      }
      return { P, yaw, fwd: new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw)), angles: a, lift: a.lift };
    },
  };
  self.s0 = s0; self.dir = dir;
  self.apply = t => { const st = self.state(t); rig.pose(st.angles); rig.root.position.set(st.P.x, st.P.y + st.lift, st.P.z); rig.root.rotation.y = st.yaw; blob.position.set(st.P.x, st.P.y + 0.14, st.P.z); };
  return self;
}

export function buildScene(stage, cfg) {
  const scene = new THREE.Scene(), world = buildWorld(scene, cfg.world || {});
  const camera = new THREE.PerspectiveCamera(50, stage.W / stage.H, 0.1, 1000);
  const actors = new Map();
  for (const def of cfg.actors || [{ id: 'hero' }]) actors.set(def.id, compileActor(def, world, actors, scene));
  const first = actors.keys().next().value;
  const shots = (cfg.shots?.length ? cfg.shots : [{ from: 0, to: cfg.duration, type: 'follow' }]).map(s => ({ ...s, from: s.from ?? 0, to: s.to ?? cfg.duration })).sort((a, b) => a.from - b.from);

  function pose(sh, t) {
    const a = actors.get(sh.target ?? first) || actors.get(first), st = a.state(t), P = st.P, T = st.fwd;
    const S = new THREE.Vector3().crossVectors(T, UP).normalize(), o = (k, d) => sh[k] ?? d;
    const lt = t - sh.from, k = clamp(lt / Math.max(0.001, sh.to - sh.from)), ek = k * k * (3 - 2 * k);
    let look = P.clone().addScaledVector(UP, o('lookHeight', 1.2)), fov = o('fov', 50);
    const at = (back, side, up, ahead = 0) => P.clone().addScaledVector(T, ahead - back).addScaledVector(S, side).addScaledVector(UP, up);
    let pos;
    switch (sh.type) {
      case 'side': pos = at(-o('ahead', 4.5), o('side', -6), o('up', 1.1)); fov = o('fov', 44); break;
      case 'orbit': { const ang = o('angle', 0.6) + o('speed', 0.32) * lt, r = o('radius', 15); pos = new THREE.Vector3(P.x + Math.cos(ang) * r, P.y + o('height', 8.5), P.z + Math.sin(ang) * r); break; }
      case 'closeup': pos = at(-o('ahead', 2.2), o('side', 1.2), o('up', 1.4)); look = P.clone().addScaledVector(UP, o('lookHeight', 1.6)); fov = o('fov', 40); break;
      case 'crane': { const f = sh.camFrom || { back: 8, side: 3, up: 1 }, e = sh.camTo || { back: 3, side: 2, up: 7 }; pos = at(lerp(f.back, e.back, ek), lerp(f.side, e.side, ek), lerp(f.up, e.up, ek)); break; }
      case 'topdown': pos = at(3, 0, o('height', 22)); break;
      case 'fixed': { const s0 = a.state(sh.from); const T0 = s0.fwd, S0 = new THREE.Vector3().crossVectors(T0, UP).normalize(); pos = s0.P.clone().addScaledVector(T0, o('ahead', 10)).addScaledVector(S0, o('side', 4)).addScaledVector(UP, o('up', 1.6)); break; }
      case 'static': pos = new THREE.Vector3(...sh.pos); if (sh.look) look = new THREE.Vector3(...sh.look); break;
      default: pos = at(o('back', 6.5), o('side', 2.6), o('up', 2.8)); look.addScaledVector(T, o('lookAhead', 2)); // follow
    }
    pos.y = Math.max(pos.y, world.hAt(pos.x, pos.z) + 0.9);
    return { pos, look, fov };
  }

  return {
    scene, camera, world,
    update(t) {
      for (const a of actors.values()) a.apply(t);
      let i = 0; for (let k = 0; k < shots.length; k++) if (shots[k].from <= t) i = k;
      let p = pose(shots[i], t); const bl = shots[i].blend ?? 0.8;
      if (i > 0 && t - shots[i].from < bl) { const q = pose(shots[i - 1], t), w = smooth(0, bl, t - shots[i].from); p = { pos: q.pos.lerp(p.pos, w), look: q.look.lerp(p.look, w), fov: lerp(q.fov, p.fov, w) }; }
      camera.position.copy(p.pos); camera.lookAt(p.look); camera.fov = p.fov; camera.updateProjectionMatrix();
      world.update(t, camera);
    },
  };
}
