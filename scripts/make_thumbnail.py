#!/usr/bin/env python3
"""Render a detailed, realistic-looking thumbnail (1280x720 PNG) from a scene file: anti-aliased vector shapes with gradients, bevel lighting,
soft shadows and glows, a library of shaded icons, real fonts, an optional 3D-rendered background from the plugin's three.js studio, and
a photographic finish (vignette, bloom, contrast, grain). No flat-fill / MS Paint look.

  python make_thumbnail.py --scene scene.json --out thumb.png [--phone thumb_phone.png] [--supersample 3]

Scene (JSON), pixels on the 1280x720 canvas, origin top-left:
{
  "background": "#101826" | {"linear": ["#0b1020", "#26406b"], "angle": 90} | {"radial": [...], "center": [0.5, 0.4], "radius": 0.8},
  "background_3d": { "world": {"theme": "night", "seed": 5, "props": ["PRP_hospital_bed"]}, "actors": [...], "shot": {...}, "assets": {...} },   # lit 3D render of the plugin's studio
  "background_image": "path.png",                       # or any image you already have (cover-fitted)
  "post": {"vignette": 0.45, "bloom": 0.25, "contrast": 1.08, "saturation": 1.1, "grain": 0.02, "blur_bg": 0, "bg_dim": 0},   # blur_bg/bg_dim soften and darken the background image/3D render so the icons pop
  "shapes": [ ... drawn in order ... ]
}
Shapes (all accept: fill, outline, width, shadow, glow, bevel, opacity, rotate [degrees about the shape centre or "pivot": [x, y]]):
  rect {box} | rrect {box, r} | ellipse {box} | polygon {points} | path {points, closed, smooth (0-4)} | line {points, width, cap:"round"} |
  ring {box, thickness} (a true ring with a hole) | arc {box, from, to, thickness} (ring segment, degrees, 0 = right, clockwise) | pie {box, from, to} | star {center, r, r_in, n, rot} |
  ngon {center, r, n, rot} | capsule {p0, p1, r} | text {text, xy, size, anchor, font, fill, stroke, stroke_width, shadow, rotate, line_spacing} |
  icon {id, box, colors:{main, dark, light, accent, ...}, flip, rotate, shadow, glow}  (library/thumbnail-icons/*.json; see thumbnail_icons.py) |
  image {path, box, fit: cover|contain, opacity, blur} | spotlight {center, radius, color, alpha, squash}  (soft light pool; use it instead of a filled circle for light)
Colours: "#rrggbb". fill may be a colour or {"linear": [c1, c2 | [pos, colour]...], "angle": deg (0 = left to right, 90 = top to bottom)} or {"radial": [...], "center": [.5,.5], "radius": .7}.
  outline: a colour, "auto" (a darker shade of the fill) or null (default for the scene: null). shadow: {"dx": 8, "dy": 14, "blur": 22, "color": "#000000", "alpha": 0.55}.
  glow: {"color": "#ffd34d", "blur": 40, "alpha": 0.8}. bevel: 0-1 (rounded, lit-from-top-left volume on any shape).
Writes the PNG and a 320x180 phone preview; prints checks: words (max 2), smallest text, text contrast, focal size, empty rings, shapes off canvas.
Exit 0 = rendered (checks may WARN), 2 = scene invalid.
"""
import argparse, json, math, os, re, subprocess, sys, tempfile

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
except ImportError:
    sys.exit("Pillow and numpy are required: pip install pillow numpy")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
W, H = 1280, 720
S = 3                                                  # supersample factor (anti-aliasing)
ICON_DIR = os.path.join(ROOT, "library", "thumbnail-icons")
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
FONTS = {"black": ["Inter-Black.otf", "DejaVuSans-Bold.ttf"], "bold": ["Inter-ExtraBold.otf", "DejaVuSans-Bold.ttf"],
         "regular": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]}


def die(m):
    sys.stderr.write("SCENE INVALID: " + m + "\n"); sys.exit(2)


# ------------------------------------------------------------------ colour
def rgb(c, what="colour"):
    if isinstance(c, (list, tuple)) and len(c) >= 3:
        return tuple(int(v) for v in c[:3])
    if not (isinstance(c, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", c)):
        die(f"{what}: colour must be '#RRGGBB', got {c!r}")
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def shade(c, f):
    """f<1 darker, f>1 lighter (towards white)."""
    if f <= 1:
        return tuple(int(v * f) for v in c)
    return tuple(int(v + (255 - v) * (f - 1)) for v in c)


def lum(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


_fc = {}


def font(kind, size):
    k = (kind, size)
    if k not in _fc:
        for n in FONTS.get(kind, FONTS["black"]):
            for p in (os.path.join(FONT_DIR, n), n, "/usr/share/fonts/truetype/dejavu/" + n):
                try:
                    _fc[k] = ImageFont.truetype(p, size); break
                except Exception:
                    continue
            if k in _fc:
                break
        if k not in _fc:
            try:
                _fc[k] = ImageFont.load_default(size=size)
            except TypeError:
                _fc[k] = ImageFont.load_default()
    return _fc[k]


# ------------------------------------------------------------------ gradients
def stops(spec):
    out = []
    n = len(spec)
    for i, s in enumerate(spec):
        if isinstance(s, (list, tuple)) and len(s) == 2 and not isinstance(s[0], str):
            out.append((float(s[0]), rgb(s[1])))
        else:
            out.append((i / max(1, n - 1), rgb(s)))
    return sorted(out)


def gradient_image(size, bbox, spec):
    """RGB image of `size` filled with a linear/radial gradient mapped onto bbox=(x0,y0,x1,y1) (crop pixels)."""
    w, h = size
    x0, y0, x1, y1 = bbox
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if "radial" in spec:
        st = stops(spec["radial"]); cx, cy = spec.get("center", [0.5, 0.5]); r = spec.get("radius", 0.7)
        t = np.hypot((xx - (x0 + cx * bw)) / (bw * r), (yy - (y0 + cy * bh)) / (bh * r))
    else:
        st = stops(spec["linear"]); a = math.radians(spec.get("angle", 90))
        dx, dy = math.cos(a), math.sin(a)
        ext = abs(bw * dx) + abs(bh * dy) or 1
        t = ((xx - (x0 + bw / 2)) * dx + (yy - (y0 + bh / 2)) * dy) / ext + 0.5
    t = np.clip(t, 0, 1)
    pos = [s[0] for s in st]
    ch = [np.interp(t, pos, [s[1][k] for s in st]) for k in range(3)]
    return Image.fromarray(np.stack(ch, -1).astype(np.uint8), "RGB")


def solid_or_grad(fill, size, bbox):
    if isinstance(fill, dict):
        return gradient_image(size, bbox, fill)
    return Image.new("RGB", size, rgb(fill))


def mean_color(fill):
    if isinstance(fill, dict):
        st = stops(fill.get("linear") or fill.get("radial"))
        return tuple(int(sum(s[1][k] for s in st) / len(st)) for k in range(3))
    return rgb(fill)


# ------------------------------------------------------------------ geometry (all return polygons: lists of (x, y))
def ell(cx, cy, rx, ry, n=96, a0=0.0, a1=360.0):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def rrect_poly(b, r):
    x0, y0, x1, y1 = b
    r = max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    if r == 0:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    p = []
    for cx, cy, a in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        p += ell(cx, cy, r, r, 14, a, a + 90)
    return p


def chaikin(pts, closed, it):
    for _ in range(it):
        q = []
        n = len(pts)
        rng = range(n) if closed else range(n - 1)
        if not closed:
            q.append(pts[0])
        for i in rng:
            a, b = pts[i], pts[(i + 1) % n]
            q += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        if not closed:
            q.append(pts[-1])
        pts = q
    return pts


def stroke_polys(pts, w, cap="round"):
    """A thick polyline as a union of capsules (list of polygons)."""
    out = []
    r = w / 2
    for a, b in zip(pts, pts[1:]):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        nx, ny = -math.sin(ang) * r, math.cos(ang) * r
        out.append([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)])
    if cap == "round":
        for p in pts:
            out.append(ell(p[0], p[1], r, r, 24))
    return out


def box4(sh, key="box"):
    b = sh.get(key)
    if not (isinstance(b, list) and len(b) == 4):
        die(f"{sh.get('type')}: '{key}' must be [x0, y0, x1, y1]")
    return [float(v) for v in b]


def pts_of(sh, key="points", need=2):
    p = sh.get(key)
    if not (isinstance(p, list) and len(p) >= need and all(isinstance(q, (list, tuple)) and len(q) == 2 for q in p)):
        die(f"{sh.get('type')}: '{key}' must be a list of at least {need} [x, y] points")
    return [(float(q[0]), float(q[1])) for q in p]


def shape_polys(sh):
    """(polys, is_stroke). Coordinates are in the shape's own space."""
    t = sh.get("type")
    if t == "rect":
        x0, y0, x1, y1 = box4(sh); return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], False
    if t == "rrect":
        return [rrect_poly(box4(sh), float(sh.get("r", 20)))], False
    if t == "ellipse":
        x0, y0, x1, y1 = box4(sh); return [ell((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2)], False
    if t == "polygon":
        return [pts_of(sh, "points", 3)], False
    if t == "path":
        closed = sh.get("closed", True)
        p = chaikin(pts_of(sh, "points", 3), closed, int(sh.get("smooth", 2)))
        if closed:
            return [p], False
        return stroke_polys(p, float(sh.get("width", 8)), sh.get("cap", "round")), True
    if t == "line":
        return stroke_polys(pts_of(sh, "points", 2), float(sh.get("width", 8)), sh.get("cap", "round")), True
    if t in ("arc", "pie"):
        x0, y0, x1, y1 = box4(sh); cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        a0, a1 = float(sh.get("from", 0)), float(sh.get("to", 90))
        if t == "pie":
            return [[(cx, cy)] + ell(cx, cy, rx, ry, 64, a0, a1)], False
        th = float(sh.get("thickness", 20))
        return [ell(cx, cy, rx, ry, 64, a0, a1) + ell(cx, cy, max(1, rx - th), max(1, ry - th), 64, a1, a0)], False
    if t in ("star", "ngon"):
        cx, cy = sh["center"]; r = float(sh["r"]); n = int(sh.get("n", 5)); rot = math.radians(float(sh.get("rot", -90)))
        if t == "ngon":
            return [[(cx + r * math.cos(rot + 2 * math.pi * i / n), cy + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]], False
        ri = float(sh.get("r_in", r * 0.45))
        return [[(cx + (r if i % 2 == 0 else ri) * math.cos(rot + math.pi * i / n), cy + (r if i % 2 == 0 else ri) * math.sin(rot + math.pi * i / n)) for i in range(2 * n)]], False
    if t == "capsule":
        (x0, y0), (x1, y1) = sh["p0"], sh["p1"]; r = float(sh["r"])
        return stroke_polys([(x0, y0), (x1, y1)], 2 * r, "round"), False
    die(f"unknown shape type '{t}'")


# ------------------------------------------------------------------ painting onto an RGBA target
class Tx:
    """Affine map: unit/icon space -> canvas pixels (supersampled), with scale for widths."""
    def __init__(self, sx=1.0, sy=1.0, tx=0.0, ty=0.0, rot=0.0, flip=False):
        self.sx, self.sy, self.tx, self.ty, self.rot, self.flip = sx, sy, tx, ty, math.radians(rot), flip

    def __call__(self, p):
        x, y = p
        if self.flip:
            x = -x
        return (self.sx * x + self.tx, self.sy * y + self.ty)

    @property
    def scale(self):
        return (abs(self.sx) + abs(self.sy)) / 2


def rotate_pts(pts, ang_deg, pivot):
    if not ang_deg:
        return pts
    a = math.radians(ang_deg); c, s = math.cos(a), math.sin(a)
    return [(pivot[0] + (x - pivot[0]) * c - (y - pivot[1]) * s, pivot[1] + (x - pivot[0]) * s + (y - pivot[1]) * c) for x, y in pts]


def bbox_of(polys):
    xs = [p[0] for poly in polys for p in poly]; ys = [p[1] for poly in polys for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def composite(target, box, layer_rgb, mask, opacity=1.0):
    """Composite layer_rgb through mask (L) onto target (RGBA) inside box=(x0,y0,x1,y1) in target pixels."""
    if opacity < 1:
        mask = mask.point(lambda v: int(v * opacity))
    crop = target.crop(box)
    over = layer_rgb.convert("RGBA"); over.putalpha(mask)
    target.paste(Image.alpha_composite(crop, over), box)


def fblur(a, r):
    """Gaussian-like blur of a float array (three box blurs per axis), no 8-bit banding."""
    n = max(1, int(round(r * 0.9)))
    out = a.astype(np.float32)
    for axis in (0, 1):
        for _ in range(3):
            pad = [(0, 0), (0, 0)]; pad[axis] = (n + 1, n)
            c = np.cumsum(np.pad(out, pad, mode="edge"), axis=axis, dtype=np.float64)
            hi = np.take(c, range(2 * n + 1, c.shape[axis]), axis=axis); lo = np.take(c, range(0, c.shape[axis] - 2 * n - 1), axis=axis)
            out = ((hi - lo) / (2 * n + 1)).astype(np.float32)
    return out


def bevel_shade(rgb_img, mask, k, size_hint):
    m = np.asarray(mask, dtype=np.float32) / 255
    b = fblur(m, max(2.0, size_hint * 0.14))
    gy, gx = np.gradient(b)
    mag = np.sqrt(gx * gx + gy * gy) + 1e-9
    lit = -(gx * -0.55 + gy * -0.83) / mag * np.clip(mag / (mag.max() + 1e-9) * 2.5, 0, 1)
    lit = fblur(lit, 1.5)
    arr = np.asarray(rgb_img, dtype=np.float32)
    arr = arr * (1 + k * 0.7 * lit[..., None]) + np.clip(lit[..., None], 0, 1) * k * 26
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def paint(target, polys, style, stroke_only=False, mask_img=None, mask_origin=(0, 0), outline_mask_img=None):
    """Draw one shape (polys in target pixels) with fill, bevel, outline, shadow, glow, opacity."""
    sh_ = style.get("shadow"); gl_ = style.get("glow")
    pad = 4 * S
    if sh_:
        pad = max(pad, int((abs(sh_.get("dx", 0)) + abs(sh_.get("dy", 0)) + sh_.get("blur", 20) * 3) * S))
    if gl_:
        pad = max(pad, int(gl_.get("blur", 30) * 3 * S))
    ow = float(style.get("_ow", 0))
    pad += int(ow * S)
    if mask_img is not None:
        x0, y0 = mask_origin; x1, y1 = x0 + mask_img.width, y0 + mask_img.height
    else:
        x0, y0, x1, y1 = bbox_of(polys)
    bx = (max(0, int(x0 - pad)), max(0, int(y0 - pad)), min(target.width, int(x1 + pad) + 1), min(target.height, int(y1 + pad) + 1))
    if bx[2] <= bx[0] or bx[3] <= bx[1]:
        return
    size = (bx[2] - bx[0], bx[3] - bx[1])
    if mask_img is not None:
        mask = Image.new("L", size, 0); mask.paste(mask_img, (int(x0) - bx[0], int(y0) - bx[1]))
    else:
        mask = Image.new("L", size, 0); d = ImageDraw.Draw(mask)
        for p in polys:
            d.polygon([(x - bx[0], y - bx[1]) for x, y in p], fill=255)
    op = float(style.get("opacity", 1))
    if gl_:
        gm = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(gl_.get("blur", 30) * S / 2))
        composite(target, bx, Image.new("RGB", size, rgb(gl_.get("color", "#ffffff"))), gm, gl_.get("alpha", 0.8) * op)
    if sh_:
        dx, dy = int(sh_.get("dx", 6) * S), int(sh_.get("dy", 10) * S)
        sm = ImageChops.offset(mask, dx, dy).filter(ImageFilter.GaussianBlur(sh_.get("blur", 18) * S / 2))
        composite(target, bx, Image.new("RGB", size, rgb(sh_.get("color", "#000000"))), sm, sh_.get("alpha", 0.5) * op)
    fill = style.get("fill")
    if fill is not None:
        gb = (int(x0 - bx[0]), int(y0 - bx[1]), int(x1 - bx[0]), int(y1 - bx[1]))
        img = solid_or_grad(fill, size, gb)
        if style.get("bevel"):
            img = bevel_shade(img, mask, float(style["bevel"]), min(gb[2] - gb[0], gb[3] - gb[1]))
        composite(target, bx, img, mask, op)
    ol = style.get("outline")
    if ol and ow > 0:
        col = shade(mean_color(fill), 0.42) if ol == "auto" and fill is not None else rgb(ol if ol != "auto" else "#000000")
        if outline_mask_img is not None:
            om = Image.new("L", size, 0); om.paste(outline_mask_img, (int(x0) - bx[0], int(y0) - bx[1]))
        else:
            om = Image.new("L", size, 0); d = ImageDraw.Draw(om)
            for p in polys:
                q = [(x - bx[0], y - bx[1]) for x, y in p]
                d.line(q + [q[0]], fill=255, width=max(1, int(ow * S)), joint="curve")
        composite(target, bx, Image.new("RGB", size, col), om, op)


# ------------------------------------------------------------------ icons
def load_icon(iid):
    p = os.path.join(ICON_DIR, re.sub(r"^ICO_", "", iid) + ".json")
    if not os.path.exists(p):
        die(f"icon '{iid}' not found in library/thumbnail-icons (python scripts/thumbnail_icons.py info)")
    return json.load(open(p, encoding="utf-8"))


def resolve_color(c, pal):
    """'$main' -> palette colour, gradients may contain $refs."""
    if isinstance(c, str) and c.startswith("$"):
        return pal.get(c[1:], "#888888")
    if isinstance(c, dict):
        return {k: ([[s[0], resolve_color(s[1], pal)] if isinstance(s, list) and len(s) == 2 and not isinstance(s[0], str) else resolve_color(s, pal) for s in v]
                    if k in ("linear", "radial") else v) for k, v in c.items()}
    return c


def draw_shapes(target, shapes, tx, defaults, pal=None, scale_w=1.0):
    pal = pal or {}
    for sh in shapes:
        t = sh.get("type")
        if t == "text":
            draw_text(target, sh, defaults); continue
        if t == "image":
            draw_image(target, sh); continue
        if t == "icon":
            draw_icon(target, sh, defaults); continue
        if t == "spotlight":
            draw_spotlight(target, sh); continue
        if t == "ring":
            draw_ring(target, sh, tx, defaults, pal, scale_w); continue
        polys, is_stroke = shape_polys(sh)
        piv = sh.get("pivot")
        if sh.get("rotate"):
            c = piv or ((bbox_of(polys)[0] + bbox_of(polys)[2]) / 2, (bbox_of(polys)[1] + bbox_of(polys)[3]) / 2)
            polys = [rotate_pts(p, sh["rotate"], c) for p in polys]
        polys = [[tx(p) for p in poly] for poly in polys]
        st = dict(defaults)
        for k in ("fill", "outline", "shadow", "glow", "bevel", "opacity"):
            if k in sh:
                st[k] = sh[k]
        st["fill"] = resolve_color(st.get("fill"), pal)
        if is_stroke:
            st["fill"] = resolve_color(sh.get("color", sh.get("fill", "#000000")), pal); st["outline"] = None
        if isinstance(st.get("outline"), str) and st["outline"].startswith("$"):
            st["outline"] = resolve_color(st["outline"], pal)
        st["_ow"] = float(sh.get("width", defaults.get("width", 0))) * scale_w if st.get("outline") and not is_stroke else 0
        if sh.get("shadow") is None and "shadow" in sh:
            st["shadow"] = None
        paint(target, polys, st, stroke_only=is_stroke)


def draw_icon(target, sh, defaults):
    ic = load_icon(sh["id"])
    x0, y0, x1, y1 = box4(sh)
    iw, ih = ic.get("size", [100, 100])
    s = min((x1 - x0) / iw, (y1 - y0) / ih)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    tx = Tx(s * S, s * S, (cx - iw * s / 2) * S, (cy - ih * s / 2) * S, 0, sh.get("flip", False))
    if sh.get("flip"):
        tx.tx = (cx + iw * s / 2) * S
    pal = dict(ic.get("colors", {})); pal.update(sh.get("colors", {}))
    # draw the icon on its own transparent layer so the whole silhouette gets one shadow / glow / rotation
    pad = int(60 * S + 2 * max(abs(sh.get("shadow", {}).get("dy", 0)), 40) * S)
    bx = (max(0, int((x0 - 60) * S)), max(0, int((y0 - 60) * S)), min(target.width, int((x1 + 60) * S)), min(target.height, int((y1 + 60) * S)))
    layer = Image.new("RGBA", (bx[2] - bx[0], bx[3] - bx[1]), (0, 0, 0, 0))
    tx.tx -= bx[0]; tx.ty -= bx[1]
    d = {"outline": "auto", "width": 2.2, "opacity": 1}
    draw_shapes(layer, ic["shapes"], tx, d, pal, scale_w=s)
    if sh.get("rotate"):
        layer = layer.rotate(-sh["rotate"], resample=Image.BICUBIC, center=((cx * S - bx[0]), (cy * S - bx[1])))
    alpha = layer.split()[3]
    st = {}
    gl_, sh_ = sh.get("glow"), sh.get("shadow")
    size = layer.size
    if gl_:
        gm = alpha.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(gl_.get("blur", 40) * S / 2))
        composite(target, bx, Image.new("RGB", size, rgb(gl_.get("color", "#fff2a8"))), gm, gl_.get("alpha", 0.8))
    if sh_:
        sm = ImageChops.offset(alpha, int(sh_.get("dx", 6) * S), int(sh_.get("dy", 14) * S)).filter(ImageFilter.GaussianBlur(sh_.get("blur", 20) * S / 2))
        composite(target, bx, Image.new("RGB", size, rgb(sh_.get("color", "#000000"))), sm, sh_.get("alpha", 0.5))
    crop = target.crop(bx)
    target.paste(Image.alpha_composite(crop, layer), bx)


def draw_ring(target, sh, tx, defaults, pal, scale_w):
    """A real ring (hole in the middle): {box, thickness, fill, outline, bevel, shadow...}."""
    x0, y0, x1, y1 = box4(sh); th = float(sh.get("thickness", 12))
    outer = [tx(p) for p in ell((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, 120)]
    inner = [tx(p) for p in ell((x0 + x1) / 2, (y0 + y1) / 2, max(1, (x1 - x0) / 2 - th), max(1, (y1 - y0) / 2 - th), 120)]
    bx0, by0, bx1, by1 = bbox_of([outer]); ox, oy = int(bx0) - 1, int(by0) - 1
    size = (int(bx1 - bx0) + 3, int(by1 - by0) + 3)
    m = Image.new("L", size, 0); d = ImageDraw.Draw(m)
    d.polygon([(x - ox, y - oy) for x, y in outer], fill=255); d.polygon([(x - ox, y - oy) for x, y in inner], fill=0)
    st = dict(defaults)
    for k in ("fill", "outline", "shadow", "glow", "bevel", "opacity"):
        if k in sh:
            st[k] = sh[k]
    st["fill"] = resolve_color(st.get("fill"), pal)
    ow = float(sh.get("width", defaults.get("width", 0))) * scale_w if st.get("outline") else 0
    st["_ow"] = ow
    om = None
    if st.get("outline") and ow > 0:
        om = Image.new("L", size, 0); d2 = ImageDraw.Draw(om)
        for poly in (outer, inner):
            q = [(x - ox, y - oy) for x, y in poly]; d2.line(q + [q[0]], fill=255, width=max(1, int(ow * S)), joint="curve")
    paint(target, None, st, mask_img=m, mask_origin=(ox, oy), outline_mask_img=om)


def draw_spotlight(target, sh):
    """Soft round light (no hard edge): {center:[x,y], radius, color, alpha, squash (0.3-1, vertical squash)}."""
    cx, cy = sh["center"]; r = float(sh["radius"]) * S; sq = float(sh.get("squash", 1.0))
    x0, y0, x1, y1 = int(cx * S - r), int(cy * S - r * sq), int(cx * S + r), int(cy * S + r * sq)
    bx = (max(0, x0), max(0, y0), min(target.width, x1), min(target.height, y1))
    if bx[2] <= bx[0] or bx[3] <= bx[1]:
        return
    yy, xx = np.mgrid[bx[1]:bx[3], bx[0]:bx[2]].astype(np.float32)
    d = np.clip(np.hypot((xx - cx * S) / r, (yy - cy * S) / (r * sq)), 0, 1)
    a = (1 - d) ** 2.2 * float(sh.get("alpha", 0.5)) * 255
    size = (bx[2] - bx[0], bx[3] - bx[1])
    composite(target, bx, Image.new("RGB", size, rgb(sh.get("color", "#ffffff"))), Image.fromarray(a.astype(np.uint8), "L"))


def draw_image(target, sh):
    p = sh.get("path")
    if not p or not os.path.exists(p):
        die(f"image: file '{p}' not found")
    im = Image.open(p).convert("RGBA")
    x0, y0, x1, y1 = [v * S for v in box4(sh)] if "box" in sh else (0, 0, target.width, target.height)
    bw, bh = int(x1 - x0), int(y1 - y0)
    k = (max if sh.get("fit", "cover") == "cover" else min)(bw / im.width, bh / im.height)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    if sh.get("blur"):
        im = im.filter(ImageFilter.GaussianBlur(sh["blur"] * S))
    l = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); l.paste(im, ((bw - im.width) // 2, (bh - im.height) // 2))
    if sh.get("opacity", 1) < 1:
        l.putalpha(l.split()[3].point(lambda v: int(v * sh["opacity"])))
    crop = target.crop((int(x0), int(y0), int(x0) + bw, int(y0) + bh))
    target.paste(Image.alpha_composite(crop, l), (int(x0), int(y0)))


def draw_text(target, sh, defaults, info=None):
    txt = str(sh.get("text", ""))
    if not txt.strip():
        die("text: empty")
    size = int(sh.get("size", 170)) * S
    sw = int(sh.get("stroke_width", 0)) * S
    f = font(sh.get("font", "black"), size)
    xy = sh.get("xy")
    if not (isinstance(xy, list) and len(xy) == 2):
        die("text: 'xy' must be [x, y]")
    anchor = sh.get("anchor", "mm")
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    kw = dict(font=f, anchor=anchor, align=sh.get("align", "center"), spacing=int(sh.get("line_spacing", 8)) * S)
    bb = probe.multiline_textbbox((xy[0] * S, xy[1] * S), txt, stroke_width=sw, **kw)
    pad = 40 * S + (int(sh.get("shadow", {}).get("blur", 0)) * 3 * S if sh.get("shadow") else 0)
    ox, oy = int(bb[0] - pad), int(bb[1] - pad)
    size_ = (int(bb[2] - bb[0] + 2 * pad), int(bb[3] - bb[1] + 2 * pad))
    def tmask(stroke):
        m = Image.new("L", size_, 0)
        ImageDraw.Draw(m).multiline_text((xy[0] * S - ox, xy[1] * S - oy), txt, fill=255, stroke_width=stroke, stroke_fill=255, **kw)
        return m
    fm = tmask(0)
    om = tmask(sw) if sw else None
    if sh.get("rotate"):
        cx, cy = (bb[0] + bb[2]) / 2 - ox, (bb[1] + bb[3]) / 2 - oy
        fm = fm.rotate(-sh["rotate"], resample=Image.BICUBIC, center=(cx, cy))
        om = om.rotate(-sh["rotate"], resample=Image.BICUBIC, center=(cx, cy)) if om else None
    fill = sh.get("fill", "#FFFFFF")
    st = {"fill": fill, "outline": sh.get("stroke") if sw else None, "_ow": 0, "shadow": sh.get("shadow"), "glow": sh.get("glow"), "bevel": sh.get("bevel")}
    # stroke first (as the "fill" of the bigger mask), then the text on top
    base_mask = om if om is not None else fm
    if sw:
        paint(target, None, {"fill": sh.get("stroke", "#000000"), "shadow": sh.get("shadow"), "glow": sh.get("glow")}, mask_img=base_mask, mask_origin=(ox, oy))
        paint(target, None, {"fill": fill, "bevel": sh.get("bevel")}, mask_img=fm, mask_origin=(ox, oy))
    else:
        paint(target, None, st, mask_img=fm, mask_origin=(ox, oy))
    if info is not None:
        info.append({"text": txt, "size": size // S, "bbox": [v / S for v in bb], "fill": fill, "stroke": sh.get("stroke") if sw else None})


# ------------------------------------------------------------------ 3D background (the plugin's own three.js studio)
def render_3d_background(spec, out_png):
    studio = os.path.join(ROOT, "toon-studio")
    scene = {"id": "bg", "duration": 2, "world": spec.get("world", {"theme": "day", "seed": 1}), "actors": spec.get("actors", []),
             "shots": [dict({"from": 0, "to": 2, "type": "follow", "target": "hero"}, **spec.get("shot", {}))], "captions": []}
    proj = {"title": "thumb-bg", "width": W, "height": H, "fps": 30, "supersample": spec.get("supersample", 2), "fade": 0, "assets": spec.get("assets", {}), "scenes": [scene]}
    if not os.path.isdir(os.path.join(studio, "node_modules", "gl")):
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=studio, check=True, capture_output=True)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(proj, f); pj = f.name
    r = subprocess.run(["node", "cli.mjs", "still", pj, "--t", str(spec.get("t", 1)), "--out", out_png], cwd=studio, capture_output=True, text=True)
    os.unlink(pj)
    if r.returncode or not os.path.exists(out_png):
        die("3D background failed: " + (r.stdout + r.stderr)[-400:])


# ------------------------------------------------------------------ finish
def finish(img, post):
    arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255
    h, w = arr.shape[:2]
    if post.get("bloom"):
        br = np.clip(arr - 0.72, 0, 1) * 3
        bl = np.asarray(Image.fromarray((br * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(w / 60)), dtype=np.float32) / 255
        arr = np.clip(arr + bl * post["bloom"], 0, 1)
    if post.get("saturation", 1) != 1:
        g = arr.mean(-1, keepdims=True); arr = np.clip(g + (arr - g) * post["saturation"], 0, 1)
    if post.get("contrast", 1) != 1:
        arr = np.clip((arr - 0.5) * post["contrast"] + 0.5, 0, 1)
    if post.get("vignette"):
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / 1.414
        arr = arr * (1 - post["vignette"] * np.clip(d, 0, 1) ** 2.2)[..., None]
    if post.get("grain"):
        rng = np.random.default_rng(7); arr = np.clip(arr + rng.normal(0, post["grain"], arr.shape[:2])[..., None], 0, 1)
    return Image.fromarray((arr * 255).astype(np.uint8), "RGB")


def render(scene, out, phone=None, ss=None, quiet=False):
    global S
    S = ss or scene.get("supersample", 3)
    bgspec = scene.get("background", "#101826")
    canvas = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))
    if isinstance(bgspec, dict):
        canvas.paste(gradient_image(canvas.size, (0, 0, canvas.width, canvas.height), bgspec).convert("RGBA"))
    else:
        canvas.paste(Image.new("RGBA", canvas.size, rgb(bgspec) + (255,)))
    tmp = None
    if scene.get("background_3d"):
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
        render_3d_background(scene["background_3d"], tmp); scene["background_image"] = tmp
    if scene.get("background_image"):
        draw_image(canvas, {"path": scene["background_image"], "fit": "cover", "blur": scene.get("post", {}).get("blur_bg", 0)})
        dim = scene.get("post", {}).get("bg_dim", 0)
        if dim:
            canvas.alpha_composite(Image.new("RGBA", canvas.size, (0, 0, 0, int(255 * dim))))
    shapes = scene.get("shapes")
    if not isinstance(shapes, list):
        die("'shapes' must be a list")
    defaults = {"outline": scene.get("outline"), "width": scene.get("outline_width", 0), "opacity": 1}
    tinfo = []
    tx = Tx(S, S, 0, 0)
    warn, words, min_text, outside = [], 0, 10 ** 9, 0
    for i, sh in enumerate(shapes, 1):
        if sh.get("type") == "text":
            draw_text(canvas, sh, defaults, tinfo)
        else:
            draw_shapes(canvas, [sh], tx, defaults)
    img = canvas.convert("RGB").resize((W, H), Image.LANCZOS)
    img = finish(img, scene.get("post", {"vignette": 0.35, "contrast": 1.05, "saturation": 1.05, "grain": 0.012}))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out, "PNG")
    phone = phone or os.path.splitext(out)[0] + "_phone.png"
    if not quiet:
        img.resize((320, 180), Image.LANCZOS).save(phone, "PNG")
    # ---- checks
    arr = np.asarray(img, dtype=np.float32)
    for t in tinfo:
        words += len(re.findall(r"\w+", t["text"])); min_text = min(min_text, t["size"])
        bb = [int(max(0, min(v, lim))) for v, lim in zip(t["bbox"], (W, H, W, H))]
        reg = arr[bb[1]:max(bb[1] + 1, bb[3]), bb[0]:max(bb[0] + 1, bb[2])]
        fl = rgb(t["fill"]) if not isinstance(t["fill"], dict) else mean_color(t["fill"])
        ref = rgb(t["stroke"]) if t["stroke"] else tuple(int(v) for v in reg.reshape(-1, 3).mean(0))
        c_ = contrast(fl, ref)
        if c_ < 4.5:
            warn.append(f"text '{t['text']}': contrast {c_:.1f}:1 (need 4.5+ to read in half a second); add a dark stroke or a shadow")
        if t["bbox"][0] < 0 or t["bbox"][1] < 0 or t["bbox"][2] > W or t["bbox"][3] > H:
            warn.append(f"text '{t['text']}' runs off the canvas")
        if t["bbox"][2] > W - 40 - 0 and t["bbox"][3] > H - 80:
            warn.append(f"text '{t['text']}' sits in the bottom-right corner where YouTube puts the duration badge")
    if words > 2:
        warn.append(f"{words} words of text on the image; the channel rule is one or two words")
    if min_text < 10 ** 9 and min_text < 120:
        warn.append(f"smallest text is {min_text}px; below 120px it is hard to read at feed size")
    for sh in shapes:
        if sh.get("type") == "ellipse" and not sh.get("fill") and sh.get("outline"):
            warn.append("an unfilled ring is on the image: make sure it circles something that is really there (a ring around nothing confuses the viewer)")
    sat = arr.std()
    if sat < 28:
        warn.append(f"low overall contrast (std {sat:.0f}); the focal element will not pop at phone size")
    if not quiet:
        print(f"rendered {out} ({W}x{H}, supersample {S}) and {phone} (320x180)")
        print(f"checks: shapes={len(shapes)} words_on_image={words} smallest_text={min_text if min_text < 10 ** 9 else 'n/a'} contrast_std={sat:.0f}")
        for w_ in warn:
            print("WARN:", w_)
        print("Now OPEN BOTH PNGs with Read, then run the blind recognition test (agent thumbnail-reader): the picture must be understood by someone who has not seen the brief.")
    if tmp and os.path.exists(tmp):
        os.unlink(tmp)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene", required=True); ap.add_argument("--out", required=True); ap.add_argument("--phone"); ap.add_argument("--supersample", type=int)
    a = ap.parse_args()
    try:
        sc = json.load(open(a.scene, encoding="utf-8-sig"))
    except Exception as e:
        die(f"cannot read {a.scene}: {e}")
    return render(sc, a.out, a.phone, a.supersample)


if __name__ == "__main__":
    sys.exit(main())
