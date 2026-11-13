#!/usr/bin/env python3
"""Bridge: scene-mapping output (skills/scene-mapping) -> a three.js toon-studio project (toon_project.json).

  python scene_map_to_toon.py --scene-map 05-scene-map.json --clauses work/clauses.json --out toon/toon_project.json
        [--audio voiceover.mp3] [--plan work/toon_plan.json] [--report reports/scene_map_bridge_report.md]
        [--title "..."] [--width 1280 --height 720 --fps 30] [--no-burn] [--max-scene 40] [--tolerance 0.06]
        [--library LIBDIR] [--gaps work/asset_gaps.json] [--accept-gaps]

The scene map must have been written on the voiceover's clauses: ONE shot per clause, shot start/end = clause start/end. If counts or
times do not line up nothing is written and every mismatch is listed (never guessed, never merged, never split).

The library is OPEN (library/library.json built-ins + library/assets/**.json grown assets): the bridge uses grown themes, props and character looks
whenever the shots' words match their keywords, embeds the ones it used into the project (`assets` block), and writes `asset_gaps.json` /
`reports/asset_gaps.md` for everything the map names (characters, props, new_assets, backgrounds) that the library does not have yet.
Claude then MAKES those assets (skill make-3d-assets) and runs the bridge again; Gate 1 G1-13 fails while a gap is open.

Mapping (all rules come from library/library.json -> mappings; nothing is invented that is not in the map):
  section             -> one toon SCENE (a world). A section longer than --max-scene seconds is cut at clause boundaries into equal parts.
  shot (per clause)   -> one camera SHOT of its clause (from/to = clause start/end on the frame grid). camera_move picks the shot type;
                         with no camera_move the scene_type picks it. transition_out.type of the previous shot sets the blend.
  literal + mood      -> world THEME (keyword score against the theme keywords; no hit -> the previous scene's theme, else day).
                         Same `background` name or same section name -> same world seed, so a place can come back.
  literal + scene_type-> hero ACTION per clause (keyword score; else the scene_type default). A pause_after >= 0.6 s becomes `idle`.
  characters / literal-> a companion actor when the shots name 2+ characters or the text says a group; hat from keywords.
  overlay_text        -> one caption (burned into the picture unless --no-burn; always also written as .srt).
  ambient_visual/audio-> not produced by the studio (it makes picture only): listed in the report, never dropped silently.
  audio               -> --audio file is muxed as delivered (never processed).
"""
import argparse, hashlib, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asset_catalog as AC


def secs(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if ":" in s:
        p = s.split(":")
        return float(p[0]) * 60 + float(p[1]) if len(p) == 2 else float(p[0]) * 3600 + float(p[1]) * 60 + float(p[2])
    return float(s)


def h32(s):
    return int(hashlib.sha256(s.encode("utf-8")).hexdigest()[:8], 16)


def score(text, words):
    t = " " + re.sub(r"[^a-z0-9' ]+", " ", text.lower()) + " "
    n, first = 0, 10 ** 9
    for w in words:
        for m in re.finditer(r"\b" + re.escape(w) + r"(?:s|es|ed|d|ing|ly)?\b", t):
            n += 1
            first = min(first, m.start())
    return n, first


def best(text, table, default):
    """table: {name: [keywords]} -> name with most hits (earliest hit breaks ties); default when nothing hits."""
    scored = []
    for name, words in table.items():
        n, first = score(text, words)
        if n:
            scored.append((-n, first, name))
    return sorted(scored)[0][2] if scored else default


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene-map", required=True)
    ap.add_argument("--clauses", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio")
    ap.add_argument("--plan", help="write the clause -> scene/shot plan here (default: <out dir>/toon_plan.json)")
    ap.add_argument("--report")
    ap.add_argument("--title")
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--fps", type=int)
    ap.add_argument("--no-burn", action="store_true")
    ap.add_argument("--max-scene", type=float)
    ap.add_argument("--tolerance", type=float, default=0.06)
    ap.add_argument("--library", help="library folder (default: the plugin's library/)")
    ap.add_argument("--gaps", help="asset gap file (default: <out dir>/work/asset_gaps.json, else <out dir>/asset_gaps.json)")
    ap.add_argument("--accept-gaps", action="store_true", help="the user accepts every current gap (default look is used); recorded in the gap file")
    a = ap.parse_args()

    lib = AC.load(a.library)
    mp, df = lib["mappings"], lib["mappings"]["defaults"]
    M = json.load(open(a.scene_map, encoding="utf-8-sig"))
    CL = json.load(open(a.clauses, encoding="utf-8-sig"))
    shots, clauses = M.get("shots", []), CL["clauses"]
    probs = []
    if len(shots) != len(clauses):
        probs.append(f"shot count {len(shots)} != clause count {len(clauses)} (the map must have exactly one shot per clause)")
    for i, (s, c) in enumerate(zip(shots, clauses)):
        try:
            ds, de = abs(secs(s["start"]) - c["start"]), abs(secs(s["end"]) - c["end"])
        except Exception as e:
            probs.append(f"{s.get('id', i)}: unreadable time ({e})"); continue
        if ds > a.tolerance or de > a.tolerance:
            probs.append(f"{s.get('id')} ({s['start']}-{s['end']}) does not match {c['id']} ({c['start']:.2f}-{c['end']:.2f})")
    if probs:
        sys.stderr.write("BRIDGE STOPPED - the scene map is not aligned to the clauses:\n  " + "\n  ".join(probs[:40]) +
                         "\nRe-run scene-mapping on clauses.json (one shot per clause), then run this again.\n")
        return 2

    W, H, FPS = a.width or df["width"], a.height or df["height"], a.fps or df["fps"]
    max_scene = a.max_scene or df["max_scene_seconds"]
    fr = lambda t: int(round(t * FPS))
    names = {s["id"]: s.get("name", s["id"]) for s in CL.get("sections", [])}

    # ---- group clauses into scenes (one per section; long sections cut at clause boundaries) ----
    groups, cur = [], []
    for i, c in enumerate(clauses):
        if cur and c["section"] != clauses[cur[-1]]["section"]:
            groups.append(cur); cur = []
        cur.append(i)
    groups.append(cur)
    scenes_idx = []
    for g in groups:
        total = clauses[g[-1]]["end"] - clauses[g[0]]["start"]
        n = max(1, math.ceil(total / max_scene))
        target, part, acc, made = total / n, [], 0.0, 0
        for i in g:
            part.append(i); acc += clauses[i]["end"] - clauses[i]["start"]
            if n > 1 and acc >= target and made < n - 1:
                scenes_idx.append(part); part, acc, made = [], 0.0, made + 1
        if part:
            scenes_idx.append(part)

    unsupported, notes, plan_rows, scenes = [], [], [], []
    prev_theme, theme_names = "day", [i["name"] for i in lib["items"] if i["kind"] == "theme"]
    theme_kw = {i["name"]: i["keywords"] for i in lib["items"] if i["kind"] == "theme"}
    custom_props = [i for i in lib["items"] if i["kind"] == "prop" and not i.get("builtin") and i.get("auto", True) and not i.get("broken")]
    theme_items = [i for i in lib["items"] if i["kind"] == "theme" and not i.get("broken")]
    gaps = {}                                         # (kind, normalised name) -> {kind, name, clauses, context}

    def gap(kind, name, cid, ctx):
        g = gaps.setdefault((kind, re.sub(r"\s+", " ", str(name).strip().lower())), {"kind": kind, "name": str(name).strip(), "clauses": [], "context": ctx})
        if cid not in g["clauses"]:
            g["clauses"].append(cid)
    used_themes, used_props = set(), []
    act_kw = {i["name"]: i["keywords"] for i in lib["items"] if i["kind"] == "action"}
    last_boundary_frame = 0
    for si, idxs in enumerate(scenes_idx):
        cs, ss = [clauses[i] for i in idxs], [shots[i] for i in idxs]
        f0 = last_boundary_frame if si == 0 else fr(cs[0]["start"])
        f1 = fr(cs[-1]["end"])
        sec = cs[0]["section"]
        sec_name = names.get(sec, sec)
        text = " ".join(" ".join(str(s.get(k, "")) for k in ("literal", "mood_target", "ambient_visual", "background")) for s in ss)
        scored = sorted(((AC.match(text, i), 0 if not i.get("builtin") else 1, i["name"]) for i in theme_items), key=lambda x: (-x[0], x[1]))
        theme = scored[0][2] if scored and scored[0][0] else None
        if theme is None:
            theme = prev_theme
            notes.append(f"scene {si + 1} ({sec_name}): no theme keyword in the shots -> kept '{theme}'")
        prev_theme = theme
        used_themes.add(theme)
        bgs = [s["background"] for s in ss if s.get("background")]
        seed_key = (max(set(bgs), key=bgs.count) if bgs else sec_name) + "|" + theme
        seed = h32(seed_key) % 1000000
        names_chars = [c for s in ss for c in (s.get("characters") or [])]
        crowd = len(set(names_chars)) >= 2 or any(score(str(s.get("literal", "")), mp["plural_cast_keywords"])[0] for s in ss)
        prop_txt = text + " " + " ".join(str(x) for s_ in ss for x in (s_.get("props") or []) + (s_.get("new_assets") or []))
        scene_props = [i["id"] for i in sorted(custom_props, key=lambda i: -AC.match(prop_txt, i)) if AC.match(prop_txt, i)][:8]
        used_props += scene_props
        presets = []
        for nm in dict.fromkeys(names_chars):
            pr_ = AC.used_by(nm, lib, "character", only_custom=True)
            if pr_:
                presets.append(pr_[0])
        if not presets:
            pr_ = AC.used_by(text, lib, "character", only_custom=True)
            presets = pr_[:1]
        look_txt = (" ".join(names_chars) + " " + text).lower()
        hat = best(look_txt, mp["hat_keywords"], "none")
        scarf = mp["scarf_palette"][h32((names_chars[0] if names_chars else "hero")) % len(mp["scarf_palette"])]
        hero = {"id": "hero", "start": round((h32(seed_key + "s") % 1000) / 1000, 3), "character": {"scarf": scarf, "hat": hat}, "timeline": []}
        if hat == "tophat":
            hero["character"]["hatColor"] = 0x2b2b3a
        if presets:
            hero["character"] = dict(AC.deep_color(presets[0]["character"]))
        actors = [hero]
        if crowd or len(presets) > 1:
            actors.append({"id": "buddy", "follow": {"target": "hero", "side": 1.7 if si % 2 == 0 else -1.7, "back": 0.4},
                           "character": dict(AC.deep_color(presets[1]["character"])) if len(presets) > 1 else {"scale": 0.85, "color": 0x2b2d42, "scarf": mp["scarf_palette"][(h32(seed_key) + 2) % len(mp["scarf_palette"])]}})
        t0 = f0 / FPS
        timeline, shot_list, caps = [], [], []
        last_act = None
        for k, (c, s) in enumerate(zip(cs, ss)):
            cf0 = f0 if k == 0 else fr(c["start"])
            cf1 = fr(c["end"])
            lt0, lt1 = (cf0 - f0) / FPS, (cf1 - f0) / FPS
            # action
            stype = s.get("scene_type", "environment")
            act = best(str(s.get("literal", "")), act_kw, mp["scene_type_default_action"].get(stype, "walk"))
            if act != last_act:
                timeline.append({"t": round(lt0, 3), "action": act}); last_act = act
            pa = float(c.get("pause_after") or 0.0)
            if pa >= 0.6 and last_act != "idle":
                timeline.append({"t": round(max(lt0 + 0.5, lt1 - pa), 3), "action": "idle"}); last_act = "idle"
            # camera
            cm = s.get("camera_move")
            if cm in mp["camera_move_to_shot"]:
                sh = dict(mp["camera_move_to_shot"][cm]); src = f"camera_move {cm}"
            else:
                sh = dict(mp["scene_type_default_shot"].get(stype, {"type": "follow"})); src = f"scene_type {stype}"
                if cm:
                    unsupported.append(f"{c['id']}: camera_move '{cm}' unknown -> default for scene_type {stype}")
            if sh["type"] == "crane" and "camFrom" not in sh:
                sh["camFrom"], sh["camTo"] = {"back": 8, "side": 3, "up": 1}, {"back": 3, "side": 2, "up": 7}
            sg = 1 if (si + k) % 2 == 0 else -1
            if sh["type"] == "follow":
                sh["side"] = round(2.6 * sg, 2)
            elif sh["type"] == "closeup":
                sh["side"] = round(1.3 * sg, 2)
            elif sh["type"] == "orbit":
                sh["angle"] = round((k * 1.1 + si) % 6.28, 2); sh["speed"] = round(abs(sh.get("speed", 0.3)) * sg, 2)
            elif sh["type"] == "fixed" and cm != "static":
                sh["side"] = round(4 * sg, 2)
            prev_t = (ss[k - 1].get("transition_out") or {}) if k else {}
            ttype = prev_t.get("type") or "hard_cut"
            blend = mp["transition_to_blend"].get(ttype, 0.5)
            if ttype not in mp["transition_to_blend"]:
                unsupported.append(f"{c['id']}: transition '{ttype}' unknown -> blend {blend}")
            blend = round(min(blend, 0.45 * (lt1 - lt0)), 2)
            shot = {"from": round(lt0, 4), "to": round(lt1, 4), "target": "hero", "blend": blend, **sh}
            shot_list.append(shot)
            # caption
            cap = None
            if s.get("overlay_text"):
                d = lt1 - lt0
                at = 0.3 if d <= 4.0 else round(d / 2 - 0.3, 2)
                dur = round(min(2.5, max(0.8, d - at - 0.2 if d > 4.0 else d - 0.9)), 2)
                cap = {"from": round(lt0 + at, 3), "to": round(lt0 + at + dur, 3), "text": str(s["overlay_text"])}
                caps.append(cap)
            if s.get("ambient_visual"):
                unsupported.append(f"{c['id']}: ambient_visual (not produced by the studio): {s['ambient_visual']}")
            if s.get("ambient_audio"):
                unsupported.append(f"{c['id']}: ambient_audio (the studio makes picture only; add in your audio editor): {s['ambient_audio']}")
            # ---- what the map names that the library does not have yet ----
            bg_ = s.get("background")
            chars_ = s.get("characters") or []
            for ch in chars_:
                if not AC.used_by(ch, lib, "character", only_custom=True):
                    gap("character", ch, c["id"], str(s.get("literal", ""))[:140])
            if bg_ and not AC.used_by(bg_, lib, "theme"):
                gap("theme", bg_, c["id"], str(s.get("literal", ""))[:140])
            for o in list(s.get("props") or []) + list(s.get("new_assets") or []):
                if o in chars_ or o == bg_ or any(AC.match(o, i) for i in lib["items"] if i["kind"] in ("character",) and not i.get("builtin")):
                    continue
                if not AC.used_by(o, lib, "prop") and not AC.used_by(o, lib, "theme"):
                    gap("prop", o, c["id"], str(s.get("literal", ""))[:140])
            plan_rows.append({"clause": c["id"], "shot": s["id"], "scene": si + 1, "section": sec_name, "theme": theme, "seed": seed, "action": act,
                              "props": scene_props, "look": presets[0]["id"] if presets else None, "camera": sh["type"], "camera_source": src, "blend": blend, "caption": cap["text"] if cap else None,
                              "start": c["start"], "end": c["end"], "frames": [cf0, cf1]})
        hero["timeline"] = timeline or [{"t": 0, "action": "walk"}]
        last_boundary_frame = f1
        world = {"theme": theme, "seed": seed, "houses": 4 + seed % 5, "clearance": df["clearance"]}
        if scene_props:
            world["props"] = scene_props
        scenes.append({"id": f"s{si + 1:02d}_{re.sub(r'[^a-z0-9]+', '_', sec_name.lower()).strip('_')[:24]}", "duration": round((f1 - f0) / FPS, 4),
                       "world": world,
                       "actors": actors, "shots": shot_list, "captions": caps})

    proj = {"title": a.title or CL.get("project", {}).get("name") or "Story video", "width": W, "height": H, "fps": FPS,
            "supersample": df["supersample"], "crf": df["crf"], "fade": df["fade"], "burnCaptions": bool(df["burnCaptions"] and not a.no_burn),
            "scenes": scenes}
    emb = AC.embed(lib, used_themes, list(dict.fromkeys(used_props)))
    if emb["themes"] or emb["props"]:
        proj["assets"] = emb
    if a.audio:
        proj["audio"] = os.path.abspath(a.audio)
    out_dir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(out_dir, exist_ok=True)
    json.dump(proj, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    plan_path = a.plan or os.path.join(out_dir, "toon_plan.json")
    json.dump({"project": proj["title"], "fps": FPS, "rows": plan_rows}, open(plan_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # ---- asset gaps: persisted so the user's acceptance survives re-runs ----
    out_dir_ = os.path.dirname(os.path.abspath(a.out))
    gpath = a.gaps or (os.path.join(out_dir_, "work", "asset_gaps.json") if os.path.isdir(os.path.join(out_dir_, "work")) else os.path.join(out_dir_, "asset_gaps.json"))
    prev = json.load(open(gpath, encoding="utf-8")) if os.path.exists(gpath) else {}
    accepted = set(prev.get("accepted", []))
    if a.accept_gaps:
        accepted |= {f"{k[0]}:{k[1]}" for k in gaps}
    glist = []
    for n_, (k, g) in enumerate(sorted(gaps.items()), 1):
        g = dict(g, id=f"GAP{n_:03d}", status="accepted" if f"{k[0]}:{k[1]}" in accepted else "open")
        glist.append(g)
    os.makedirs(os.path.dirname(os.path.abspath(gpath)), exist_ok=True)
    json.dump({"gaps": glist, "accepted": sorted(accepted)}, open(gpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    n_open = sum(1 for g in glist if g["status"] == "open")

    rep = ["# Scene map -> three.js toon project (bridge report)", "",
           f"- shots = clauses = {len(shots)}; alignment tolerance {a.tolerance}s: OK",
           f"- scenes (worlds): {len(scenes)}; total {sum(s['duration'] for s in scenes):.2f} s = {sum(fr(s['duration']) for s in scenes)} frames @ {FPS} fps, {W}x{H}",
           f"- audio: {proj.get('audio', 'none - the render is silent; mux the voiceover later or re-run with --audio')}",
           f"- captions: {sum(len(s['captions']) for s in scenes)} ({'burned in + .srt' if proj['burnCaptions'] else '.srt only'})", "",
           "## Plan (clause -> world, action, camera)", "", "| clause | scene | theme | action | camera (source) | blend | caption |", "|---|---|---|---|---|---|---|"]
    for r in plan_rows:
        rep.append(f"| {r['clause']} | {r['scene']} {r['section']} | {r['theme']} | {r['action']} | {r['camera']} ({r['camera_source']}) | {r['blend']} | {r['caption'] or ''} |")
    if glist:
        rep += ["", f"## Asset gaps ({n_open} open, {len(glist) - n_open} accepted) - the library does not have these yet: MAKE them (skill make-3d-assets)", "",
                "| id | kind | name | clauses | context | status |", "|---|---|---|---|---|---|"]
        rep += [f"| {g['id']} | {g['kind']} | {g['name']} | {', '.join(g['clauses'][:6])} | {g['context'][:70]} | {g['status']} |" for g in glist]
    if notes:
        rep += ["", "## Notes", *[f"- {n}" for n in notes]]
    if unsupported:
        rep += ["", f"## Not produced / defaulted ({len(unsupported)})", *[f"- {u}" for u in unsupported]]
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        open(a.report, "w", encoding="utf-8").write("\n".join(rep))
    print(f"bridge ok: {len(clauses)} clauses -> {len(scenes)} scenes -> {a.out}; plan {plan_path}; not produced/defaulted rows {len(unsupported)}; "
          f"custom assets used: {len(emb['themes'])} themes, {len(emb['props'])} props; asset gaps: {n_open} open, {len(glist) - n_open} accepted ({gpath})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
