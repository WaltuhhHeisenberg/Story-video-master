#!/usr/bin/env python3
"""The OPEN thumbnail icon library (library/thumbnail-icons/*.json): shaded, recognisable objects drawn with the make_thumbnail shape vocabulary.

  python thumbnail_icons.py info                     list icons (id, name, keywords)
  python thumbnail_icons.py find "words"             icons whose name/keywords match the words
  python thumbnail_icons.py validate [FILE ...]      check icon files (default: all)
  python thumbnail_icons.py add FILE [--force]       validate, copy into the library, rebuild the sheet
  python thumbnail_icons.py sheet [--out PNG]        render every icon on a contact sheet (library/thumbnail-icons/_sheet.png)
  python thumbnail_icons.py preview ID [--out PNG]   render one icon large on a neutral background
The library GROWS: when a thumbnail needs an object that is not here, Claude draws it as an icon file (100 x 100 unit space, `$main/$light/$dark/$accent`
palette keys, gradients, bevel, a few shapes), previews it, has it recognised blind (agent thumbnail-reader), and adds it.
"""
import json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import make_thumbnail as MT
DIR = MT.ICON_DIR
TYPES = {"rect", "rrect", "ellipse", "polygon", "path", "line", "arc", "pie", "star", "ngon", "capsule", "ring"}


def load_all():
    out = []
    for f in sorted(os.listdir(DIR)) if os.path.isdir(DIR) else []:
        if f.endswith(".json"):
            out.append((f, json.load(open(os.path.join(DIR, f), encoding="utf-8"))))
    return out


def validate(ic):
    e = []
    if not re.fullmatch(r"ICO_[a-z0-9_]+", str(ic.get("id", ""))):
        e.append("id must look like ICO_lower_case")
    if not ic.get("description"):
        e.append("description missing")
    kw = ic.get("keywords")
    if not (isinstance(kw, list) and kw):
        e.append("keywords: non-empty list of words a thumbnail brief would use for it")
    sz = ic.get("size", [100, 100])
    if not (isinstance(sz, list) and len(sz) == 2):
        e.append("size must be [w, h] in units")
    sh = ic.get("shapes")
    if not (isinstance(sh, list) and 1 <= len(sh) <= 120):
        e.append("shapes: between 1 and 120 shapes (keep it light)")
    else:
        for i, s in enumerate(sh):
            if s.get("type") not in TYPES:
                e.append(f"shapes[{i}]: type must be one of {sorted(TYPES)}")
    if len(set(json.dumps(s, sort_keys=True) for s in (sh or []))) < min(3, len(sh or [])):
        e.append("shapes are all identical")
    pal = ic.get("colors", {})
    for k, v in pal.items():
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(v)):
            e.append(f"colors.{k}: '#RRGGBB'")
    used = set(re.findall(r'"\$(\w+)"', json.dumps(sh or [])))
    miss = used - set(pal)
    if miss:
        e.append(f"colour keys used but not defined in colors: {sorted(miss)}")
    return e


def sheet(out=None):
    icons = load_all()
    cols = 5; cw, ch = 256, 250
    rows = (len(icons) + cols - 1) // cols
    shapes = []
    for i, (f, ic) in enumerate(icons):
        cx, cy = (i % cols) * cw, (i // cols) * ch
        shapes.append({"type": "icon", "id": ic["id"], "box": [cx + 40, cy + 20, cx + cw - 40, cy + 190], "shadow": {"dx": 4, "dy": 8, "blur": 12, "alpha": 0.5}})
        shapes.append({"type": "text", "text": ic["name"], "xy": [cx + cw / 2, cy + 218], "size": 26, "font": "bold", "fill": "#e9eef5"})
    MT.W, MT.H = cols * cw, rows * ch
    try:
        MT.render({"background": {"linear": ["#1b2433", "#2f4059"], "angle": 90}, "post": {}, "shapes": shapes}, out or os.path.join(DIR, "_sheet.png"), None, 2, True)
    finally:
        MT.W, MT.H = 1280, 720


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"; args = sys.argv[2:]
    if cmd == "info":
        for f, ic in load_all():
            print(f"{ic['id']:22} {ic['description'][:60]:60} | {', '.join(ic['keywords'][:5])}")
    elif cmd == "find":
        words = " ".join(args).lower()
        hits = [(sum(1 for k in [ic["name"]] + ic["keywords"] if re.search(r"\b" + re.escape(k.lower()) + r"(s|es)?\b", words)), ic) for f, ic in load_all()]
        for n, ic in sorted(hits, key=lambda x: -x[0]):
            if n:
                print(f"{ic['id']}  ({ic['description']})")
    elif cmd == "validate":
        files = args or [os.path.join(DIR, f) for f, _ in load_all()]
        bad = 0
        for f in files:
            e = validate(json.load(open(f, encoding="utf-8")))
            if e:
                bad += 1; print(f"INVALID {f}:\n  " + "\n  ".join(e))
        print("icons valid" if not bad else f"{bad} invalid"); sys.exit(1 if bad else 0)
    elif cmd == "add" and args:
        ic = json.load(open(args[0], encoding="utf-8")); e = validate(ic)
        if e:
            print("INVALID:\n  " + "\n  ".join(e)); sys.exit(1)
        dst = os.path.join(DIR, re.sub(r"^ICO_", "", ic["id"]) + ".json")
        if os.path.exists(dst) and "--force" not in args:
            print(dst, "exists (use --force)"); sys.exit(1)
        os.makedirs(DIR, exist_ok=True); json.dump(ic, open(dst, "w", encoding="utf-8"), indent=1)
        print("added ->", dst); sheet()
    elif cmd == "sheet":
        sheet(args[args.index("--out") + 1] if "--out" in args else None)
    elif cmd == "preview" and args:
        ic = MT.load_icon(args[0])
        out = args[args.index("--out") + 1] if "--out" in args else os.path.join(DIR, "_preview_" + ic["id"] + ".png")
        MT.render({"background": {"radial": ["#4a5a73", "#1a2231"], "center": [0.5, 0.45], "radius": 0.9}, "post": {},
                   "shapes": [{"type": "icon", "id": ic["id"], "box": [340, 60, 940, 660], "shadow": {"dx": 10, "dy": 24, "blur": 36, "alpha": 0.6}}]}, out, None, 3, True)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
