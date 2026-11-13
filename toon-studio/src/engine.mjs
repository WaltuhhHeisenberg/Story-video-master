// Engine core: headless WebGL stage, toon + outline materials, static-geometry batcher.
import * as THREE from 'three';
import { mergeGeometries, mergeVertices } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

export { THREE };
export const lerp = (a, b, t) => a + (b - a) * t;
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export function mulberry(seed) {
  seed = seed | 0;
  return () => { seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

/** Create a headless WebGL context + three.js renderer. Needs a display (Xvfb) on Linux. */
export function createStage(W, H) {
  const createGL = require('gl');
  const gl = createGL(W, H, { preserveDrawingBuffer: true, antialias: false, alpha: false, depth: true });
  if (!gl) throw new Error('Could not create a headless GL context. On Linux run under a display, e.g. `xvfb-run -a node ...` (the CLI does this for you).');
  const canvas = { width: W, height: H, style: {}, addEventListener() {}, removeEventListener() {}, getContext: () => gl, clientWidth: W, clientHeight: H };
  const renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: false });
  renderer.setSize(W, H, false); renderer.setPixelRatio(1);
  const pixels = new Uint8Array(W * H * 4);
  return { gl, renderer, W, H, pixels, readFrame() { gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, pixels); return pixels; } };
}

// ---- toon material (3-step ramp) ----
let _grad;
export function gradientMap() {
  if (_grad) return _grad;
  const d = new Uint8Array([70, 70, 90, 255, 150, 150, 170, 255, 215, 215, 230, 255, 255, 255, 255, 255]);
  _grad = new THREE.DataTexture(d, 4, 1, THREE.RGBAFormat);
  _grad.minFilter = _grad.magFilter = THREE.NearestFilter; _grad.generateMipmaps = false; _grad.needsUpdate = true;
  return _grad;
}
export const toonMat = (o = {}) => new THREE.MeshToonMaterial({ gradientMap: gradientMap(), ...o });

// ---- inverted-hull outline material (cached per thickness/colour) ----
const _ol = new Map();
export function outlineMaterial(thickness = 0.05, color = 0x1b1b2e) {
  const k = thickness + ':' + color; if (_ol.has(k)) return _ol.get(k);
  const m = new THREE.MeshBasicMaterial({ color, side: THREE.BackSide });
  m.onBeforeCompile = s => { s.vertexShader = s.vertexShader.replace('#include <begin_vertex>', `vec3 transformed = position + normal * ${thickness.toFixed(4)};`); };
  m.customProgramCacheKey = () => 'outline' + k; // distinct program per thickness
  m.userData.shared = true; _ol.set(k, m); return m;
}

// ---- shared primitives ----
export const G = {
  sph: new THREE.SphereGeometry(1, 10, 8), cyl: new THREE.CylinderGeometry(1, 1, 1, 8), box: new THREE.BoxGeometry(1, 1, 1),
  cone: new THREE.ConeGeometry(1, 1, 8), dodec: new THREE.DodecahedronGeometry(1, 0), circ: new THREE.CircleGeometry(1, 14),
  oct: new THREE.OctahedronGeometry(1, 0),
};

/** Collects many coloured primitives, merges them into ONE draw call (+ optional outline mesh). */
export class Batch {
  constructor() { this.list = []; this.base = new THREE.Matrix4(); }
  at(x, y, z, yaw = 0, s = 1) { this.base.compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), yaw), new THREE.Vector3(s, s, s)); return this; }
  reset() { this.base = new THREE.Matrix4(); return this; }
  add(geo, color, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, sx = 1, sy = 1, sz = 1) {
    const g = geo.index ? geo.toNonIndexed() : geo.clone();
    g.deleteAttribute('uv');
    const m = new THREE.Matrix4().compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), new THREE.Vector3(sx, sy, sz));
    g.applyMatrix4(new THREE.Matrix4().multiplyMatrices(this.base, m));
    const c = new THREE.Color(color), n = g.attributes.position.count, arr = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) arr.set([c.r, c.g, c.b], i * 3);
    g.setAttribute('color', new THREE.BufferAttribute(arr, 3));
    this.list.push(g); return this;
  }
  build(parent, material, { outline = false, thickness = 0.05 } = {}) {
    if (!this.list.length) return null;
    const geo = mergeGeometries(this.list); const mesh = new THREE.Mesh(geo, material); parent.add(mesh);
    if (outline) {
      const og = geo.clone(); og.deleteAttribute('normal'); og.deleteAttribute('color');
      const sm = mergeVertices(og); sm.computeVertexNormals();
      parent.add(new THREE.Mesh(sm, outlineMaterial(thickness)));
    }
    return mesh;
  }
}

export function disposeScene(scene) {
  scene.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material && o.material.dispose && !o.material.userData?.shared) o.material.dispose(); });
}
