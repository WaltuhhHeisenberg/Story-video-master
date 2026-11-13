#!/usr/bin/env python3
"""One command for everything mechanical in Run B (voiceover + transcript + scene map -> 3D video made with the three.js toon studio).

  python run_toon.py --project DIR --audio voiceover.mp3 [--transcript words.csv] [--scene-map 05-scene-map.json] [--sections sections.json]
                     [--name "My Video"] [--stage prepare|bridge|gate1|stills|render|gate2|all] [--preview] [--workers N] [--no-burn] [--accept-gaps]
                     [--width 1280 --height 720 --fps 30]

DIR layout (created as needed):  DIR/work/ (clauses.json, transcript, toon_plan.json)  DIR/reports/  DIR/render/ (video.mp4, video.srt)  DIR/toon_project.json
Stages (re-runnable; every failure stops with the exact next action; every command is logged in DIR/reports/pipeline_log.json):
  prepare : (transcribe if no --transcript) -> split clauses (the voiceover is used exactly as delivered) -> reports/clause_sheet.md
            ===> then the scene-mapping stage writes 05-scene-map.json (ONE shot per clause)
  bridge  : scene map + clauses -> toon_project.json + work/toon_plan.json + reports/scene_map_bridge_report.md   (scripts/scene_map_to_toon.py)
            Also writes work/asset_gaps.json: everything the map names that the OPEN asset library lacks (characters, props, worlds).
            ===> PAUSE while gaps are open: Claude MAKES the assets (skill make-3d-assets), then run the bridge again (or --accept-gaps if the user agrees to the default look)
  gate1   : computed checks on the project before any render (scripts/toon_qa.py gate1)
  stills  : one preview still per scene (middle of its first clause) -> reports/stills/  (look at them before the long render)
  render  : toon-studio/cli.mjs render (parallel, resumable, voiceover muxed, captions burned in) -> render/video.mp4 (+ .srt)
  gate2   : computed checks on the video (scripts/toon_qa.py gate2) + reports/contact_sheet.png
  all     : bridge, gate1, stills, render, gate2 in order
Needs: node 18+, ffmpeg/ffprobe, Xvfb on Linux, and `npm install` once in toon-studio/ (done here automatically when node_modules is missing).
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STUDIO = os.path.join(ROOT, "toon-studio")
PY = sys.executable


def sh(cmd, log, allow_fail=False, cwd=None, out_file=None):
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    text = (p.stdout + p.stderr).strip()
    tail = text.splitlines()[-14:]
    log.append({"cmd": " ".join(os.path.basename(x) if i < 2 and os.sep in x else x for i, x in enumerate(cmd))[:240], "rc": p.returncode, "sec": round(time.time() - t, 1), "tail": tail})
    if out_file:
        open(out_file, "w", encoding="utf-8").write(text + "\n")
    if p.returncode and not allow_fail:
        raise SystemExit("\n".join(["STOPPED: " + log[-1]["cmd"] + f" (exit {p.returncode})"] + tail))
    return p


def ensure_engine(log):
    if os.path.isdir(os.path.join(STUDIO, "node_modules", "gl")) and os.path.isdir(os.path.join(STUDIO, "node_modules", "three")):
        return
    if not shutil.which("npm"):
        raise SystemExit("STOPPED: npm not found - install Node 18+ (then run `npm install` in toon-studio/)")
    sh(["npm", "install", "--no-audit", "--no-fund"], log, cwd=STUDIO)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--audio")
    ap.add_argument("--transcript")
    ap.add_argument("--scene-map")
    ap.add_argument("--sections")
    ap.add_argument("--name", default="My Video")
    ap.add_argument("--stage", default="all", choices=["prepare", "bridge", "gate1", "stills", "render", "gate2", "all"])
    ap.add_argument("--preview", action="store_true", help="640x360 draft render (fast); gate2 then expects 640x360")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--no-burn", action="store_true")
    ap.add_argument("--accept-gaps", action="store_true", help="the user accepts the current asset gaps (default look is used)")
    ap.add_argument("--width", type=int); ap.add_argument("--height", type=int); ap.add_argument("--fps", type=int)
    ap.add_argument("--whisper-model", default="small"); ap.add_argument("--language", default="auto")
    a = ap.parse_args()
    P = os.path.abspath(a.project)
    D = {k: os.path.join(P, k) for k in ("work", "reports", "render")}
    for d in D.values():
        os.makedirs(d, exist_ok=True)
    S = lambda n: os.path.join(HERE, n)
    clauses = os.path.join(D["work"], "clauses.json")
    plan = os.path.join(D["work"], "toon_plan.json")
    proj = os.path.join(P, "toon_project.json")
    video = os.path.join(D["render"], "video_preview.mp4" if a.preview else "video.mp4")
    smap = a.scene_map or os.path.join(P, "05-scene-map.json")
    log = []
    log_p = os.path.join(D["reports"], "pipeline_log.json")
    if os.path.exists(log_p):
        try:
            log = json.load(open(log_p))
        except Exception:
            log = []
    order = {"all": ["bridge", "gate1", "stills", "render", "gate2"]}.get(a.stage, [a.stage])
    try:
        if "prepare" in order:
            if not a.audio:
                raise SystemExit("STOPPED: --audio (the voiceover exactly as delivered) is required for prepare")
            tr = a.transcript or os.path.join(D["work"], "transcript_words.csv")
            if not a.transcript and not os.path.exists(tr):
                sh([PY, S("transcribe.py"), "--audio", a.audio, "--out", tr, "--model", a.whisper_model, "--language", a.language], log)
                raise SystemExit("PAUSE: transcript made by speech recognition. Read " + tr + " once, fix mis-heard words (keep start/end), then run again.")
            cmd = [PY, S("split_clauses.py"), "--transcript", tr, "--audio", a.audio, "--out", clauses, "--name", a.name]
            if a.sections:
                cmd += ["--sections", a.sections]
            sh(cmd, log)
            sh([PY, S("mapping_tools.py"), "sheet", "--clauses", clauses, "--out", os.path.join(D["reports"], "clause_sheet.md")], log)
            print("prepare: done ->", clauses, "and reports/clause_sheet.md. Next: the scene-mapping stage (one shot per clause) -> 05-scene-map.json")
        if "bridge" in order:
            for need, hint in ((clauses, "run --stage prepare first"), (smap, "run the scene-mapping stage first (05-scene-map.json)")):
                if not os.path.exists(need):
                    raise SystemExit(f"STOPPED: {need} missing - {hint}")
            gaps_p = os.path.join(D["work"], "asset_gaps.json")
            cmd = [PY, S("scene_map_to_toon.py"), "--scene-map", smap, "--clauses", clauses, "--out", proj, "--plan", plan, "--gaps", gaps_p,
                   "--report", os.path.join(D["reports"], "scene_map_bridge_report.md"), "--title", a.name]
            if a.audio:
                cmd += ["--audio", a.audio]
            for k in ("width", "height", "fps"):
                if getattr(a, k):
                    cmd += ["--" + k, str(getattr(a, k))]
            if a.no_burn:
                cmd.append("--no-burn")
            if a.accept_gaps:
                cmd.append("--accept-gaps")
            sh(cmd, log)
            print("bridge: done ->", proj)
            gj = json.load(open(gaps_p, encoding="utf-8")) if os.path.exists(gaps_p) else {"gaps": []}
            opn = [g for g in gj["gaps"] if g["status"] == "open"]
            if opn:
                raise SystemExit(f"PAUSE: {len(opn)} asset gap(s) open (reports/asset_gaps in scene_map_bridge_report.md). Make the assets (skill make-3d-assets: "
                                 "asset_catalog.py add / preview), then run the bridge again; or --accept-gaps if the user accepts the default look.")
        if "gate1" in order:
            r = sh([PY, S("toon_qa.py"), "gate1", "--project", proj, "--plan", plan, "--clauses", clauses, "--scene-map", smap, "--run", P, "--gaps", os.path.join(D["work"], "asset_gaps.json"),
                    "--out", os.path.join(D["reports"], "gate1_report.md")] + (["--voiceover", a.audio] if a.audio else []), log, allow_fail=True)
            print(r.stdout.strip().splitlines()[-1])
            if r.returncode:
                raise SystemExit("STOPPED: Gate 1 has FAIL rows (reports/gate1_report.md). Fix the cause (map, clauses, library), run the bridge and Gate 1 again. No render before Gate 1 passes.")
        if "stills" in order or "render" in order:
            ensure_engine(log)
        if "stills" in order:
            pj = json.load(open(proj, encoding="utf-8"))
            sd = os.path.join(D["reports"], "stills"); os.makedirs(sd, exist_ok=True)
            t = 0.0
            for i, sc in enumerate(pj["scenes"]):
                mid = t + min(sc["duration"] / 2, 2.0)
                sh(["node", os.path.join(STUDIO, "cli.mjs"), "still", proj, "--t", f"{mid:.2f}", "--preview", "--out", os.path.join(sd, f"scene_{i + 1:02d}.png")], log, cwd=STUDIO)
                t += round(sc["duration"] * pj["fps"]) / pj["fps"]
            print(f"stills: {len(pj['scenes'])} preview frames in {sd} - LOOK at them before the render")
        if "render" in order:
            cmd = ["node", os.path.join(STUDIO, "cli.mjs"), "render", proj, "--out", video]
            if a.preview:
                cmd.append("--preview")
            if a.workers:
                cmd += ["--workers", str(a.workers)]
            if a.no_burn:
                cmd.append("--no-burn")
            sh(cmd, log, cwd=STUDIO, out_file=os.path.join(D["reports"], "render_log.txt"))
            print("render: done ->", video, "(re-run the same command to resume after an interruption)")
        if "gate2" in order:
            r = sh([PY, S("toon_qa.py"), "gate2", "--project", proj, "--plan", plan, "--clauses", clauses, "--video", video, "--run", P,
                    "--out", os.path.join(D["reports"], "gate2_report.md"), "--sheet", os.path.join(D["reports"], "contact_sheet.png")]
                   + (["--preview"] if a.preview else []) + (["--voiceover", a.audio] if a.audio else []), log, allow_fail=True)
            print(r.stdout.strip().splitlines()[-1])
            if r.returncode:
                raise SystemExit("STOPPED: Gate 2 has FAIL rows (reports/gate2_report.md).")
    finally:
        json.dump(log, open(log_p, "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
