#!/usr/bin/env python3
"""OPEN 3D asset library: built-in assets (library/library.json) + every asset file in library/assets/{themes,props,characters}/.

  python asset_catalog.py info [--kind theme|prop|character|action|camera_shot]     list everything (built-in and grown)
  python asset_catalog.py schema                                                      print the asset file formats
  python asset_catalog.py validate [FILE ...]                                         validate asset files (default: all in library/assets)
  python asset_catalog.py add FILE [--force]                                          validate + copy a new asset into library/assets/<kind>s/ (+ reindex)
  python asset_catalog.py preview ID [--out PNG]                                      render a still of an asset with the 3D engine (needs node + npm install)
  python asset_catalog.py reindex                                                     rewrite library/INDEX.md (human list with preview links)
  python asset_catalog.py check                                                       built-in items vs toon-studio/src (custom assets are validated, not compared)
Other scripts import load(), match(), embed().
The library is meant to grow: when a shot needs a world, object or look the library does not have, Claude MAKES it (skill make-3d-assets).
"""
import json, os, re, subprocess, sys, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
LIBDIR = os.path.join(ROOT, "library")
LIB = os.path.join(LIBDIR, "library.json")
STUDIO = os.path.join(ROOT, "toon-studio")
KINDS = {"theme": "themes", "prop": "props", "character": "characters"}
SHAPES = {"box", "cyl", "sph", "cone", "dodec", "oct", "tor", "pyr"}
PREFIX = {"theme": "THM_", "prop": "PRP_", "character": "CHR_"}
THEME_COLOR_KEYS = {"fog", "trunk", "dirt", "rock"}
PALETTES = {"walls", "roofs", "leaves", "pine", "grass", "sky"}


def load(libdir=None):
    """Built-in library.json + every custom asset file. Custom items get builtin=False and `file`."""
    libdir = libdir or LIBDIR
    lib = json.load(open(os.path.join(libdir, "library.json"), encoding="utf-8"))
    lib["items"] = [dict(i, builtin=True, id=i.get("lib_id")) for i in lib["items"]]
    for kind, sub in KINDS.items():
        d = os.path.join(libdir, "assets", sub)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".json"):
                    try:
                        a = json.load(open(os.path.join(d, f), encoding="utf-8"))
                    except Exception as e:
                        lib["items"].append({"lib_id": f, "name": f, "kind": kind, "builtin": False, "broken": str(e), "file": os.path.join(d, f)}); continue
                    a["builtin"] = False; a["file"] = os.path.join(d, f); a.setdefault("keywords", []); a.setdefault("name", a.get("id", f)); a["lib_id"] = a.get("id")
                    lib["items"].append(a)
    return lib


def deep_color(v):
    """'#rrggbb' strings -> ints, recursively (what the engine takes)."""
    if isinstance(v, list):
        return [deep_color(x) for x in v]
    if isinstance(v, dict):
        return {k: deep_color(x) for k, x in v.items()}
    return int(v[1:], 16) if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v) else v


def names(lib, kind):
    return [i["name"] for i in lib["items"] if i["kind"] == kind and not i.get("broken")]


def _norm(t):
    return " " + re.sub(r"[^a-z0-9' ]+", " ", str(t).lower()) + " "


def match(text, item):
    """How many of the item's name/keywords occur in text as whole words (s/es/ed/d/ing/ly endings allowed)."""
    t, n = _norm(text), 0
    for w in [item.get("name", "")] + list(item.get("keywords", [])):
        w = _norm(w).strip().replace("_", " ")
        if w and re.search(r"\b" + re.escape(w) + r"(?:s|es|ed|d|ing|ly)?\b", t):
            n += 1
    return n


def used_by(text, lib, kind, only_custom=False):
    r = [(match(text, i), i) for i in lib["items"] if i["kind"] == kind and not i.get("broken") and not (only_custom and i.get("builtin"))]
    return [i for n, i in sorted(r, key=lambda x: -x[0]) if n]


# ------------------------------------------------------------------ validation
def _color(c, where, errs, allow_palette=False):
    if isinstance(c, int) or (isinstance(c, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", c)):
        return
    if allow_palette and isinstance(c, str) and re.fullmatch(r"\$(walls|roofs|leaves|pine|trunk|rock)", c):
        return
    errs.append(f"{where}: colour must be '#rrggbb'" + (" or '$walls|$roofs|$leaves|$pine|$trunk|$rock'" if allow_palette else "") + f", got {c!r}")


def _vec(v, n, where, errs):
    if not (isinstance(v, list) and len(v) == n and all(isinstance(x, (int, float)) for x in v)):
        errs.append(f"{where}: must be a list of {n} numbers")


def _parts(parts, where, errs, character=False):
    if not isinstance(parts, list) or not parts:
        errs.append(f"{where}: needs a non-empty list"); return
    if len(parts) > 80:
        errs.append(f"{where}: more than 80 parts (keep assets light)")
    for i, p in enumerate(parts):
        w = f"{where}[{i}]"
        if p.get("shape") not in SHAPES:
            errs.append(f"{w}: shape must be one of {sorted(SHAPES)}")
        _color(p.get("color"), w + ".color", errs, allow_palette=not character)
        for k in ("pos", "rot", "scale"):
            if k in p:
                _vec(p[k], 3, f"{w}.{k}", errs)
        if character and p.get("attach", "head") not in ("head", "body", "root"):
            errs.append(f"{w}.attach must be head|body|root")
        if "scale" in p and any(abs(x) > 60 for x in p["scale"] if isinstance(x, (int, float))):
            errs.append(f"{w}.scale looks too large (units are metres; a house is about 3)")


def validate_asset(a, lib=None):
    errs = []
    kind = a.get("kind")
    if kind not in KINDS:
        return [f"kind must be one of {sorted(KINDS)}"]
    if not re.fullmatch(PREFIX[kind] + r"[a-z0-9_]+", str(a.get("id", ""))):
        errs.append(f"id must look like {PREFIX[kind]}lower_case_name")
    if not re.fullmatch(r"[a-z0-9_ ]+", str(a.get("name", ""))):
        errs.append("name: lower case letters, digits, spaces, underscores")
    if not a.get("description"):
        errs.append("description: one line saying what it is")
    kw = a.get("keywords")
    if not (isinstance(kw, list) and kw and all(isinstance(k, str) and k.strip() for k in kw)):
        errs.append("keywords: a non-empty list of words/phrases a shot's text would use (the bridge matches them)")
    if kind == "prop":
        _parts(a.get("parts"), "parts", errs)
        pl = a.get("place", {})
        if pl.get("mode", "scatter") not in ("scatter", "path_edge", "at"):
            errs.append("place.mode must be scatter|path_edge|at")
        if pl.get("area", "near_path") not in ("near_path", "field", "far"):
            errs.append("place.area must be near_path|field|far")
        if not (0 < a.get("radius", 1.2) <= 12):
            errs.append("radius must be 0..12")
    elif kind == "character":
        c = a.get("character")
        if not isinstance(c, dict):
            errs.append("character: an object {color, scarf, hat, hatColor, scale, parts}")
        else:
            for k in ("color", "scarf", "hatColor"):
                if k in c:
                    _color(c[k], "character." + k, errs)
            if c.get("hat", "none") not in ("none", "cap", "tophat"):
                errs.append("character.hat must be none|cap|tophat (use parts for other hats)")
            if "scale" in c and not (0.3 <= c["scale"] <= 3):
                errs.append("character.scale must be 0.3..3")
            if "parts" in c:
                _parts(c["parts"], "character.parts", errs, character=True)
    elif kind == "theme":
        base = a.get("extends", "day")
        if lib is not None and base not in names(lib, "theme"):
            errs.append(f"extends: unknown theme '{base}'")
        if a.get("name") in ("day", "sunset", "night", "snow", "desert"):
            errs.append("name collides with a built-in theme")
        for k in ("fog", "trunk", "dirt", "rock"):
            if k in a:
                _color(a[k], k, errs)
        for k in ("sky", "grass"):
            if k in a:
                if not (isinstance(a[k], list) and len(a[k]) == 2):
                    errs.append(f"{k}: two colours [top/bottom] or [a, b]")
                else:
                    for c in a[k]:
                        _color(c, k, errs)
        for k in ("leaves", "pine", "walls", "roofs"):
            if k in a:
                if not isinstance(a[k], list):
                    errs.append(f"{k}: a list of colours")
                else:
                    for c in a[k]:
                        _color(c, k, errs)
        if "hemi" in a and not (isinstance(a["hemi"], list) and len(a["hemi"]) == 3):
            errs.append("hemi: [skyColour, groundColour, intensity]")
        if "sun" in a:
            s = a["sun"]
            if "color" in s:
                _color(s["color"], "sun.color", errs)
            if "dir" in s:
                _vec(s["dir"], 3, "sun.dir", errs)
        if lib is not None:
            allp = [i["lib_id"] for i in lib["items"] if i["kind"] == "prop"]
            for p in a.get("props", []):
                if (p if isinstance(p, str) else p.get("id")) not in allp:
                    errs.append(f"props: unknown prop '{p}' (make it first)")
        unknown = set(a) - {"id", "lib_id", "kind", "name", "extends", "description", "keywords", "props", "created", "made_for", "builtin", "file",
                            "sky", "fog", "fogN", "fogF", "grass", "dirt", "hemi", "sun", "leaves", "pine", "trunk", "walls", "roofs", "cloud",
                            "features", "glowWindows", "stars", "lamps", "snowfall", "snowCap", "rock"}
        if unknown:
            errs.append(f"unknown theme fields: {sorted(unknown)}")
    return errs


def validate_all(libdir=None):
    lib = load(libdir)
    out = []
    ids = {}
    for i in lib["items"]:
        if i.get("builtin"):
            continue
        if i.get("broken"):
            out.append((i["file"], ["not valid JSON: " + i["broken"]])); continue
        e = validate_asset(i, lib)
        aid = i.get("id")
        if aid in ids:
            e.append(f"duplicate id (also in {ids[aid]})")
        ids[aid] = i["file"]
        if e:
            out.append((i["file"], e))
    return out


# ------------------------------------------------------------------ embedding into a project
def strip(a):
    return {k: v for k, v in a.items() if k not in ("builtin", "file", "created", "made_for", "keywords", "description", "kind", "id", "name") or k == "name"}


def embed(lib, theme_names, prop_ids):
    """Assets block for toon_project.json: only the custom themes (with their custom `extends` chain) and props that are used."""
    themes, props, seen = {}, {}, set()
    by_name = {i["name"]: i for i in lib["items"] if i["kind"] == "theme" and not i.get("builtin")}
    by_id = {i["id"]: i for i in lib["items"] if i["kind"] == "prop" and not i.get("builtin")}
    todo = list(theme_names)
    while todo:
        n = todo.pop()
        if n in themes or n not in by_name:
            continue
        d = by_name[n]
        themes[n] = {k: v for k, v in d.items() if k not in ("builtin", "file", "created", "made_for", "keywords", "description", "kind", "id", "lib_id", "name")}
        todo.append(d.get("extends", "day"))
        prop_ids = list(prop_ids) + [p if isinstance(p, str) else p["id"] for p in d.get("props", [])]
    for pid in prop_ids:
        if pid in by_id and pid not in props:
            d = by_id[pid]
            props[pid] = {k: v for k, v in d.items() if k not in ("builtin", "file", "created", "made_for", "keywords", "description", "kind", "name", "lib_id")}
    return {"themes": themes, "props": props}


# ------------------------------------------------------------------ commands
def check():
    lib = load()
    bad = []
    b = lambda kind: sorted(i["name"] for i in lib["items"] if i["kind"] == kind and i.get("builtin"))
    w = open(os.path.join(STUDIO, "src", "world.mjs"), encoding="utf-8").read()
    m = re.search(r"export const THEMES = \{(.*?)\n\};", w, re.S)
    eng = sorted(set(re.findall(r"(?m)^  (\w+): \{", m.group(1)))) if m else []
    if eng != b("theme"):
        bad.append(f"built-in themes differ: engine {eng} vs library {b('theme')}")
    c = open(os.path.join(STUDIO, "src", "characters.mjs"), encoding="utf-8").read()
    m = re.search(r"export const ACTIONS = \{(.*?)\};", c, re.S)
    eng = sorted(set(re.findall(r"(\w+):\s*\{", m.group(1)))) if m else []
    if eng != b("action"):
        bad.append(f"actions differ: engine {eng} vs library {b('action')}")
    s = open(os.path.join(STUDIO, "src", "scene.mjs"), encoding="utf-8").read()
    eng = set(re.findall(r"case '(\w+)':", s[s.index("function pose"):])); eng.add("follow")
    if sorted(eng) != b("camera_shot"):
        bad.append(f"camera shots differ: engine {sorted(eng)} vs library {b('camera_shot')}")
    mp = lib["mappings"]
    for k, v in mp["camera_move_to_shot"].items():
        if v["type"] not in eng:
            bad.append(f"mapping camera_move {k} -> unknown shot {v['type']}")
    for k, v in mp["scene_type_default_shot"].items():
        if v["type"] not in eng:
            bad.append(f"mapping scene_type {k} -> unknown shot {v['type']}")
    for k, v in mp["scene_type_default_action"].items():
        if v not in b("action"):
            bad.append(f"mapping scene_type {k} -> unknown action {v}")
    for f, e in validate_all():
        bad.append(f"{os.path.relpath(f, ROOT)}: " + "; ".join(e))
    return bad


def preview_project(a, lib):
    """A tiny project that shows one asset."""
    kind = a["kind"]
    emb = embed(lib, [a["name"]] if kind == "theme" else [], [a["id"]] if kind == "prop" else [])
    hero = {"id": "hero", "at": {"x": 30, "z": 30, "yaw": 0}, "timeline": [{"t": 0, "action": "idle"}]}
    world = {"theme": "day", "seed": 3, "houses": 0, "density": 0.05, "features": {"houses": False, "trees": False, "pines": False, "flowers": False, "rocks": False, "windmill": False}}
    shot = {"from": 0, "to": 2, "type": "static", "pos": [3.6, 2.0, 5.0], "look": [0, 0.9, 0], "target": "hero"}
    if kind == "theme":
        world = {"theme": a["name"], "seed": 7}
        hero = {"id": "hero", "start": 0.05, "timeline": [{"t": 0, "action": "walk"}]}
        shot = {"from": 0, "to": 2, "type": "follow", "target": "hero", "back": 7, "up": 3.2}
    elif kind == "prop":
        world["props"] = [{"id": a["id"], "place": {"mode": "at", "at": {"x": 0, "z": 0, "yaw": 0.5}}}]
    else:
        c = dict(a["character"]); hero = {"id": "hero", "at": {"x": 0, "z": 0, "yaw": 0.4}, "character": c, "timeline": [{"t": 0, "action": "idle"}]}
        shot = {"from": 0, "to": 2, "type": "static", "pos": [3.2, 2.2, 4.2], "look": [0, 1.3, 0], "target": "hero"}
    return {"title": "preview", "width": 640, "height": 360, "fps": 30, "supersample": 1, "fade": 0, "assets": emb,
            "scenes": [{"id": "p", "duration": 2, "world": world, "actors": [hero], "shots": [shot], "captions": []}]}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"
    args = sys.argv[2:]
    if cmd == "info":
        kind = args[args.index("--kind") + 1] if "--kind" in args else None
        for i in load()["items"]:
            if kind and i["kind"] != kind:
                continue
            tag = "built-in" if i.get("builtin") else ("BROKEN " if i.get("broken") else "grown   ")
            print(f"{tag} {i['kind']:11} {i.get('lib_id', i.get('id', '?')):26} {i.get('description', i.get('broken', ''))[:80]}")
    elif cmd == "schema":
        print(open(os.path.join(ROOT, "skills", "make-3d-assets", "references", "asset-schema.md"), encoding="utf-8").read())
    elif cmd == "validate":
        if args:
            lib, bad = load(), []
            for f in args:
                e = validate_asset(json.load(open(f, encoding="utf-8")), lib)
                if e:
                    bad.append((f, e))
        else:
            bad = validate_all()
        for f, e in bad:
            print(f"INVALID {f}:\n  " + "\n  ".join(e))
        print("assets valid" if not bad else f"{len(bad)} invalid file(s)")
        sys.exit(1 if bad else 0)
    elif cmd == "add" and args:
        a = json.load(open(args[0], encoding="utf-8")); lib = load()
        e = validate_asset(a, lib)
        if e:
            print("INVALID:\n  " + "\n  ".join(e)); sys.exit(1)
        dst = os.path.join(LIBDIR, "assets", KINDS[a["kind"]], re.sub(r"^[A-Z]{3}_", "", a["id"]) + ".json")
        if os.path.exists(dst) and "--force" not in args:
            print(f"{dst} exists (use --force to replace)"); sys.exit(1)
        a.setdefault("created", datetime.date.today().isoformat())
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        json.dump(a, open(dst, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("added ->", os.path.relpath(dst, ROOT)); reindex()
    elif cmd == "preview" and args:
        lib = load()
        a = next((i for i in lib["items"] if i.get("lib_id", i.get("id")) == args[0] and not i.get("builtin")), None)
        if not a:
            print("no grown asset with id", args[0]); sys.exit(1)
        out = args[args.index("--out") + 1] if "--out" in args else os.path.join(LIBDIR, "assets", "previews", a["id"] + ".png")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        pj = os.path.join(os.path.dirname(os.path.abspath(out)), ".preview_" + a["id"] + ".json")
        json.dump(preview_project(a, lib), open(pj, "w"))
        if not os.path.isdir(os.path.join(STUDIO, "node_modules", "gl")):
            subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=STUDIO, check=True)
        r = subprocess.run(["node", "cli.mjs", "still", pj, "--t", "1", "--out", os.path.abspath(out)], cwd=STUDIO, capture_output=True, text=True)
        os.remove(pj)
        print((r.stdout + r.stderr).strip()[-600:]); sys.exit(r.returncode)
    elif cmd == "reindex":
        reindex()
    elif cmd == "check":
        b = check()
        print("asset library ok" if not b else "ASSET LIBRARY PROBLEMS:\n  " + "\n  ".join(b))
        sys.exit(1 if b else 0)
    else:
        print(__doc__)


def reindex():
    lib = load()
    L = ["# Asset library index (generated by `asset_catalog.py reindex`)", "", "Built-in assets live in `library.json`; grown assets are the JSON files in `assets/`. Previews: `assets/previews/<id>.png`.", ""]
    for kind in ("theme", "prop", "character"):
        L += [f"## {kind}s", "", "| id | name | keywords | description | preview |", "|---|---|---|---|---|"]
        for i in lib["items"]:
            if i["kind"] == kind:
                pv = f"assets/previews/{i['id']}.png" if not i.get("builtin") and os.path.exists(os.path.join(LIBDIR, "assets", "previews", i.get("id", "") + ".png")) else ""
                L.append(f"| {i.get('lib_id', i.get('id'))}{' (built-in)' if i.get('builtin') else ''} | {i['name']} | {', '.join(i.get('keywords', [])[:6])} | {i.get('description', '')[:70]} | {pv} |")
        L.append("")
    open(os.path.join(LIBDIR, "INDEX.md"), "w", encoding="utf-8").write("\n".join(L))
    print("library/INDEX.md written")


if __name__ == "__main__":
    main()
