#!/usr/bin/env python3
"""Gates for the three.js toon project (computed with evidence; PASS / FAIL / WARN / MANUAL / NOT RUN).

  python toon_qa.py gate1 --project toon/toon_project.json --plan toon/toon_plan.json --clauses work/clauses.json
                          [--scene-map 05-scene-map.json] [--voiceover vo.mp3] [--run RUN] [--out reports/gate1_report.md] [--manual manual1.json]
  python toon_qa.py gate2 --project toon/toon_project.json --plan toon/toon_plan.json --video out/video.mp4 --clauses work/clauses.json
                          [--voiceover vo.mp3] [--preview] [--out reports/gate2_report.md] [--sheet reports/contact_sheet.png] [--manual manual2.json]

Gate 1 (before the render): G1-01 timeline = voiceover (frames), G1-02 one camera shot per clause on its times, G1-03 valid themes / actions / shot
types, G1-04 visible change at least every 4.5 s, G1-05 real section names, G1-06 no more than 4 identical camera set-ups in a row, G1-07 every
overlay_text has a caption inside its clause, G1-08 voiceover duration, G1-09 world clearance and frame settings, G1-10 engine tools (node,
ffmpeg, Xvfb, node_modules), G1-11 intake report, G1-12 scene length cap, G1-13 no open asset gap (the library has everything the map names, or the user accepted the gap), G1-14 embedded grown assets are valid.
Gate 2 (after the render): G2-01 file and streams, G2-02 duration, G2-03 size and fps, G2-04 audio stream, G2-05 .srt captions, G2-06 no blank or
frozen frames (sampled mid-clause), G2-07 a visible change across every clause cut (sampled either side), G2-08 contact sheet written,
G2-09 intake report, G2-10 plan matches project, M-1..M-3 judgement items (MANUAL until a verdict + evidence is recorded with --manual).
Exit code 0 only when nothing is FAIL (NOT RUN and MANUAL are reported, never turned into PASS).
"""
import argparse, glob, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asset_catalog as AC

ROWS = []


def row(i, title, status, ev=""):
    ROWS.append((i, title, status, ev))


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,duration:format=duration",
                        "-of", "json", path], capture_output=True, text=True)
    return json.loads(r.stdout or "{}") if r.returncode == 0 else None


def fps_of(s):
    n, _, d = s.partition("/")
    return float(n) / float(d or 1)


def intake_found(run, project_path):
    cands = []
    for base in filter(None, [run, os.path.dirname(os.path.abspath(project_path)), os.path.dirname(os.path.dirname(os.path.abspath(project_path)))]):
        for sub in ("", "reports", "work", "toon", "toon/reports"):
            cands.append(os.path.join(base, sub, "intake_report.md"))
    return next((c for c in cands if os.path.exists(c)), None)


def load_inputs(a):
    P = json.load(open(a.project, encoding="utf-8"))
    PL = json.load(open(a.plan, encoding="utf-8")) if a.plan and os.path.exists(a.plan) else None
    CL = json.load(open(a.clauses, encoding="utf-8-sig")) if a.clauses and os.path.exists(a.clauses) else None
    return P, PL, CL


def gate1(a):
    P, PL, CL = load_inputs(a)
    lib = AC.load()
    fps = P.get("fps", 30)
    themes, acts, shots_ok = set(AC.names(lib, "theme")) | set(P.get("assets", {}).get("themes", {})), set(AC.names(lib, "action")), set(AC.names(lib, "camera_shot"))
    total_frames = sum(round(s["duration"] * fps) for s in P["scenes"])
    clauses = CL["clauses"] if CL else []
    # G1-01
    if clauses:
        end_frames = round(clauses[-1]["end"] * fps)
        ok = abs(total_frames - end_frames) <= 1 and abs(clauses[0]["start"]) < 1e-6
        row("G1-01", "scene timeline covers the voiceover exactly (frames)", "PASS" if ok else "FAIL", f"project {total_frames} frames, clauses 0 -> {end_frames} frames ({clauses[-1]['end']:.2f}s)")
    else:
        row("G1-01", "scene timeline covers the voiceover exactly (frames)", "NOT RUN", "no clauses.json given")
    # G1-02
    allshots = []
    t = 0
    for sc in P["scenes"]:
        for s in sc["shots"]:
            allshots.append((t + s["from"], t + s["to"], s, sc))
        t += round(sc["duration"] * fps) / fps
    if clauses:
        bad = []
        if len(allshots) != len(clauses):
            bad.append(f"{len(allshots)} camera shots for {len(clauses)} clauses")
        for (f, e, s, sc), c in zip(allshots, clauses):
            if abs(f - c["start"]) > 1.5 / fps or abs(e - c["end"]) > 1.5 / fps:
                bad.append(f"{c['id']}: shot {f:.2f}-{e:.2f} vs clause {c['start']:.2f}-{c['end']:.2f}")
        row("G1-02", "exactly one camera shot per clause, on the clause's times", "PASS" if not bad else "FAIL", "; ".join(bad[:6]) or f"{len(clauses)} clauses = {len(allshots)} shots")
    else:
        row("G1-02", "exactly one camera shot per clause, on the clause's times", "NOT RUN", "no clauses.json given")
    # G1-03
    bad = []
    for sc in P["scenes"]:
        if sc["world"].get("theme") not in themes:
            bad.append(f"{sc['id']}: theme {sc['world'].get('theme')}")
        for ac in sc["actors"]:
            for seg in ac.get("timeline", []):
                if seg["action"] not in acts:
                    bad.append(f"{sc['id']}/{ac['id']}: action {seg['action']}")
        for s in sc["shots"]:
            if s["type"] not in shots_ok:
                bad.append(f"{sc['id']}: shot type {s['type']}")
            if s["type"] == "static" and "pos" not in s:
                bad.append(f"{sc['id']}: static shot without pos")
    row("G1-03", "themes, actions and camera shot types exist in the 3D library (built-in or grown)", "PASS" if not bad else "FAIL", "; ".join(bad[:6]) or f"{len(P['scenes'])} scenes checked")
    # G1-04
    gaps = [e - f for f, e, *_ in allshots]
    row("G1-04", "a visible change at least every 4.5 s (camera set-up changes at every clause)", "PASS" if not gaps or max(gaps) <= 4.5 + 1e-6 else "FAIL", f"longest shot {max(gaps):.2f}s" if gaps else "no shots")
    # G1-05
    names = [s.get("name", s["id"]) for s in CL.get("sections", [])] if CL else []
    auto = [n for n in names if re.fullmatch(r"S\d+", str(n))]
    if CL and CL.get("sections"):
        row("G1-05", "sections have real names (not S01, S02 ...)", "PASS" if not auto else "FAIL", f"auto-named: {auto}" if auto else f"{len(names)} named sections")
    else:
        row("G1-05", "sections have real names (not S01, S02 ...)", "NOT RUN", "no sections")
    # G1-06
    run_, worst, prev = 1, 1, None
    for f, e, s, sc in allshots:
        key = (s["type"], s.get("side"), s.get("camFrom", {}).get("back") if s.get("camFrom") else None, sc["world"]["theme"])
        run_ = run_ + 1 if key == prev else 1
        worst, prev = max(worst, run_), key
    row("G1-06", "no more than 4 identical camera set-ups in a row", "PASS" if worst <= 4 else "FAIL", f"longest repeat {worst}")
    # G1-07
    if a.scene_map and os.path.exists(a.scene_map):
        M = json.load(open(a.scene_map, encoding="utf-8-sig"))
        want = [s.get("overlay_text") for s in M["shots"]]
        have = []
        for sc in P["scenes"]:
            have += [c["text"] for c in sc.get("captions", [])]
        need = [w for w in want if w]
        bad = [w for w in need if w not in have]
        inside = True
        t = 0
        for sc in P["scenes"]:
            for c in sc.get("captions", []):
                if c["from"] < 0 or c["to"] > sc["duration"] + 1e-6 or c["to"] <= c["from"]:
                    inside = False
            t += sc["duration"]
        row("G1-07", "every overlay_text of the map is a caption, inside its scene", "PASS" if not bad and inside and len(have) == len(need) else "FAIL",
            f"{len(need)} wanted, {len(have)} written" + (f"; missing {bad[:3]}" if bad else "") + ("" if inside else "; a caption leaves its scene"))
    else:
        row("G1-07", "every overlay_text of the map is a caption, inside its scene", "NOT RUN", "no scene map given")
    # G1-08
    vo = a.voiceover or P.get("audio")
    if vo and os.path.exists(vo) and shutil.which("ffprobe"):
        pr = probe(vo); d = float(pr["format"]["duration"]) if pr else None
        proj_d = total_frames / fps
        row("G1-08", "voiceover file opens and matches the timeline length (+-1.0 s)", "PASS" if d and abs(d - proj_d) <= 1.0 else "FAIL", f"voiceover {d:.2f}s vs project {proj_d:.2f}s" if d else "ffprobe could not read it")
    elif vo:
        row("G1-08", "voiceover file opens and matches the timeline length (+-1.0 s)", "FAIL", f"{vo} not found")
    else:
        row("G1-08", "voiceover file opens and matches the timeline length (+-1.0 s)", "NOT RUN", "no voiceover given: the render will be silent (say so in the delivery)")
    # G1-09
    bad = []
    if P.get("width", 0) < 640 or P.get("height", 0) < 360:
        bad.append("resolution below 640x360")
    if P.get("fps", 0) not in (24, 25, 30, 48, 50, 60):
        bad.append(f"fps {P.get('fps')}")
    for sc in P["scenes"]:
        if sc["world"].get("clearance", 9) < 9:
            bad.append(f"{sc['id']}: clearance < 9 (trees on the camera path)")
    row("G1-09", "frame settings sane; world clearance >= 9", "PASS" if not bad else "FAIL", "; ".join(bad) or f"{P['width']}x{P['height']} @ {fps} fps")
    # G1-10
    studio = os.path.join(AC.ROOT, "toon-studio")
    miss = [t for t in ("node", "ffmpeg", "ffprobe") if not shutil.which(t)]
    if sys.platform.startswith("linux") and not shutil.which("Xvfb") and not os.environ.get("DISPLAY"):
        miss.append("Xvfb")
    if not os.path.isdir(os.path.join(studio, "node_modules", "gl")) or not os.path.isdir(os.path.join(studio, "node_modules", "three")):
        miss.append("toon-studio/node_modules (run: npm install in toon-studio)")
    row("G1-10", "render tools present (node, ffmpeg, Xvfb, npm packages)", "PASS" if not miss else "FAIL", "missing: " + ", ".join(miss) if miss else "all present")
    # G1-11
    f = intake_found(a.run, a.project)
    row("G1-11", "intake_report.md exists", "PASS" if f else "FAIL", f or "not found in the run, reports/, work/ or toon/")
    # G1-13 / G1-14
    gp = a.gaps or (os.path.join(os.path.dirname(os.path.abspath(a.plan)), "asset_gaps.json") if a.plan else None)
    if gp and os.path.exists(gp):
        G = json.load(open(gp, encoding="utf-8"))
        op = [f"{g['id']} {g['kind']} '{g['name']}'" for g in G["gaps"] if g["status"] == "open"]
        acc = sum(1 for g in G["gaps"] if g["status"] == "accepted")
        row("G1-13", "no open asset gap (every character, prop and world the map names exists in the library, or the user accepted the gap)", "PASS" if not op else "FAIL",
            "; ".join(op[:6]) + (" ... make them with skill make-3d-assets, then run the bridge again" if op else f"{len(G['gaps'])} gap(s) listed, {acc} accepted by the user"))
    else:
        row("G1-13", "no open asset gap", "NOT RUN", "no asset_gaps.json (run the bridge)")
    emb = P.get("assets", {})
    bad = []
    for n, d in emb.get("themes", {}).items():
        e = AC.validate_asset(dict(d, kind="theme", id="THM_" + n, name=n, description="x", keywords=["x"]), None)
        bad += [f"theme {n}: {x}" for x in e if "keywords" not in x and "props" not in x]
    for pid, d in emb.get("props", {}).items():
        e = AC.validate_asset(dict(d, kind="prop", name="x", description="x", keywords=["x"]), None)
        bad += [f"prop {pid}: {x}" for x in e if "keywords" not in x]
    for sc in P["scenes"]:
        for pr in sc["world"].get("props", []):
            pid = pr if isinstance(pr, str) else pr.get("id")
            if pid not in emb.get("props", {}):
                bad.append(f"{sc['id']}: prop {pid} is not embedded in project.assets")
    row("G1-14", "embedded grown assets are valid and every used prop is embedded", "PASS" if not bad else "FAIL", "; ".join(bad[:5]) or f"{len(emb.get('themes', {}))} themes, {len(emb.get('props', {}))} props embedded")
    # G1-12
    long_ = [(sc["id"], sc["duration"]) for sc in P["scenes"] if sc["duration"] > lib["mappings"]["defaults"]["max_scene_seconds"] + 1.5]
    row("G1-12", "no scene (world) longer than the cap", "PASS" if not long_ else "FAIL", f"too long: {long_}" if long_ else f"longest {max(sc['duration'] for sc in P['scenes']):.1f}s")


def frames_at(video, times, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for i, t in enumerate(times):
        p = os.path.join(outdir, f"f{i:04d}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0, t):.3f}", "-i", video, "-frames:v", "1", "-vf", "scale=320:-1", p], capture_output=True)
        paths.append(p if os.path.exists(p) else None)
    return paths


def gate2(a):
    P, PL, CL = load_inputs(a)
    fps = P.get("fps", 30)
    total = sum(round(s["duration"] * fps) for s in P["scenes"]) / fps
    v = a.video
    pr = probe(v) if v and os.path.exists(v) and shutil.which("ffprobe") else None
    if not pr:
        row("G2-01", "video file exists and opens", "FAIL", f"{v} missing or unreadable")
        return
    vs = [s for s in pr["streams"] if s["codec_type"] == "video"]
    au = [s for s in pr["streams"] if s["codec_type"] == "audio"]
    row("G2-01", "video file exists and opens", "PASS" if vs else "FAIL", f"{os.path.getsize(v) / 1e6:.1f} MB, {len(vs)} video / {len(au)} audio stream(s)")
    d = float(pr["format"]["duration"])
    row("G2-02", "video duration equals the project (+-0.15 s)", "PASS" if abs(d - total) <= 0.15 else "FAIL", f"video {d:.2f}s vs project {total:.2f}s")
    W_, H_ = (640, 360) if a.preview else (P["width"], P["height"])        # --preview renders are 640x360 by design
    ok = vs and vs[0]["width"] == W_ and vs[0]["height"] == H_ and abs(fps_of(vs[0]["r_frame_rate"]) - fps) < 0.01
    row("G2-03", "size and frame rate equal the project" + (" (preview 640x360)" if a.preview else ""), "PASS" if ok else "FAIL", f"{vs[0]['width']}x{vs[0]['height']} @ {fps_of(vs[0]['r_frame_rate']):.2f}" if vs else "")
    if P.get("audio"):
        ad = float(au[0].get("duration") or d) if au else None
        row("G2-04", "audio stream present and as long as the video (+-0.5 s)", "PASS" if au and abs(ad - d) <= 0.5 else "FAIL", f"audio {ad:.2f}s vs video {d:.2f}s" if au else "no audio stream")
    else:
        row("G2-04", "audio stream present and as long as the video (+-0.5 s)", "NOT RUN", "project has no audio: silent render (state it in the delivery)")
    ncap = sum(len(s.get("captions", [])) for s in P["scenes"])
    srt = os.path.splitext(v)[0] + ".srt"
    if ncap:
        n = len(re.findall(r"-->", open(srt, encoding="utf-8").read())) if os.path.exists(srt) else -1
        row("G2-05", ".srt captions written, one cue per caption", "PASS" if n == ncap else "FAIL", f"{n} cues for {ncap} captions")
    else:
        row("G2-05", ".srt captions written, one cue per caption", "NOT RUN", "no captions in the project")
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        for i, t in (("G2-06", "no blank or frozen frames"), ("G2-07", "visible change across every clause cut"), ("G2-08", "contact sheet written")):
            row(i, t, "NOT RUN", "Pillow/numpy missing")
        return
    clauses = CL["clauses"] if CL else [{"id": f"scene {i}", "start": 0, "end": total} for i in range(1)]
    tmp = os.path.join(os.path.dirname(os.path.abspath(v)), ".qa_frames")
    mids = [(c["start"] + c["end"]) / 2 for c in clauses]
    paths = frames_at(v, mids, os.path.join(tmp, "mid"))
    blank = []
    for c, p in zip(clauses, paths):
        if not p:
            blank.append(f"{c['id']}: no frame"); continue
        arr = np.asarray(Image.open(p).convert("L"), dtype=float)
        if arr.std() < 6:
            blank.append(f"{c['id']}: std {arr.std():.1f}")
    row("G2-06", "no blank or flat frames (sampled mid-clause)", "PASS" if not blank else "FAIL", "; ".join(blank[:6]) or f"{len(paths)} frames sampled")
    pairs = []
    for c in clauses[:-1]:
        pairs += [c["end"] - 0.25, c["end"] + 0.25]
    pp = frames_at(v, pairs, os.path.join(tmp, "cut"))
    same = []
    for i, c in enumerate(clauses[:-1]):
        x, y = pp[2 * i], pp[2 * i + 1]
        if not x or not y:
            same.append(f"{c['id']}: no frame"); continue
        diff = np.abs(np.asarray(Image.open(x).convert("L"), dtype=float) - np.asarray(Image.open(y).convert("L"), dtype=float)).mean()
        if diff < 2.0:
            same.append(f"{c['id']}->{clauses[i + 1]['id']}: diff {diff:.1f}")
    row("G2-07", "the picture changes visibly across every clause cut", "PASS" if not same else "FAIL", "; ".join(same[:6]) or f"{len(clauses) - 1} cuts compared")
    sheet = a.sheet or os.path.join(os.path.dirname(os.path.abspath(a.out or v)), "contact_sheet.png")
    ims = [Image.open(p) for p in paths if p]
    if ims:
        cols = 6
        w, h = ims[0].size
        rows_ = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * w, rows_ * h), (20, 20, 20))
        for i, im in enumerate(ims):
            sh.paste(im, ((i % cols) * w, (i // cols) * h))
        os.makedirs(os.path.dirname(os.path.abspath(sheet)), exist_ok=True)
        sh.save(sheet)
        row("G2-08", "contact sheet written (one frame per clause)", "PASS", f"{sheet} ({len(ims)} frames)")
    else:
        row("G2-08", "contact sheet written (one frame per clause)", "FAIL", "no frames")
    f = intake_found(a.run, a.project)
    row("G2-09", "intake_report.md exists", "PASS" if f else "FAIL", f or "not found")
    if PL:
        n_sc = len(set(r["scene"] for r in PL["rows"]))
        row("G2-10", "plan matches project (scenes, clause count)", "PASS" if n_sc == len(P["scenes"]) and len(PL["rows"]) == len(CL["clauses"] if CL else PL["rows"]) else "FAIL", f"plan {len(PL['rows'])} clauses / {n_sc} scenes; project {len(P['scenes'])} scenes")
    else:
        row("G2-10", "plan matches project (scenes, clause count)", "NOT RUN", "no plan")
    shutil.rmtree(tmp, ignore_errors=True)
    for k, t in (("M-1", "the contact sheet reads as the story (looked at it)"), ("M-2", "captions legible at phone size (looked at 3 frames)"), ("M-3", "no camera clipping through props / actor off screen (looked at the cut frames)")):
        row(k, t, "MANUAL", "needs a human verdict + evidence (--manual)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gate", choices=["gate1", "gate2"])
    ap.add_argument("--preview", action="store_true", help="gate2: the video is a --preview render (640x360)")
    for k in ("project", "plan", "clauses", "scene-map", "voiceover", "run", "out", "video", "sheet", "manual", "gaps"):
        ap.add_argument("--" + k)
    a = ap.parse_args()
    a.scene_map = getattr(a, "scene_map", None)
    (gate1 if a.gate == "gate1" else gate2)(a)
    if a.manual and os.path.exists(a.manual):
        man = json.load(open(a.manual, encoding="utf-8"))
        for i, (rid, t, st, ev) in enumerate(ROWS):
            if rid in man and st == "MANUAL":
                v = man[rid]
                ROWS[i] = (rid, t, v.get("status", "MANUAL"), v.get("evidence", ""))
    lines = [f"# {a.gate.upper()} report", "", "| id | check | status | evidence |", "|---|---|---|---|"]
    lines += [f"| {i} | {t} | **{s}** | {str(e).replace('|', '/')} |" for i, t, s, e in ROWS]
    c = {s: sum(1 for r in ROWS if r[2] == s) for s in ("PASS", "FAIL", "NOT RUN", "MANUAL", "WARN")}
    lines += ["", "PASS %(PASS)d, FAIL %(FAIL)d, NOT RUN %(NOT RUN)d, MANUAL %(MANUAL)d" % c]
    txt = "\n".join(lines)
    if a.out:                      # every run is kept as "## Run N" (finish_project.py learns from the failed ones too)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        old = open(a.out, encoding="utf-8").read() if os.path.exists(a.out) else ""
        n = len(re.findall(r"(?m)^## Run \d+", old)) + 1
        open(a.out, "w", encoding="utf-8").write((old.rstrip() + "\n\n" if old else "") + f"## Run {n}\n\n" + txt.split("\n", 2)[2] + "\n")
    print(txt)
    return 1 if c["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
