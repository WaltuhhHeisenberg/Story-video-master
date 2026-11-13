#!/usr/bin/env python3
"""Export a scene map JSON into files a person can work from.

Usage:
    python export_csv.py map.json --out exports/ --fps 24

Writes:
    scene_map.csv    flat, one row per shot (literal, ambient, transition columns)
    scene_map.md     readable table
    asset_list.csv   every character/prop/background with first shot and number of uses
    audio_cues.csv   ambient audio notes and transition audio bridges with timecodes
    markers.csv      generic marker list (hero shots, interrupts, hooks, loops, dips to black)

markers.csv is a plain CSV (timecode, name, note). Editors differ in what marker
formats they import, so you may need to convert it for your software.
"""
import argparse
import csv
import json
from pathlib import Path


def parse_time(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    total = 0.0
    for part in str(value).strip().split(":"):
        total = total * 60 + float(part)
    return total


def mmss(sec):
    m = int(sec // 60)
    return f"{m}:{sec - 60 * m:04.1f}"


def timecode(sec, fps):
    frames = round(sec * fps)
    f = frames % fps
    s_total = frames // fps
    return f"{s_total // 3600:02d}:{(s_total // 60) % 60:02d}:{s_total % 60:02d}:{f:02d}"


def cell(value):
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if value is None:
        return ""
    return str(value)


def md_escape(value):
    return cell(value).replace("|", "\\|").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map")
    ap.add_argument("--out", default="exports")
    ap.add_argument("--fps", type=int, default=None, help="Frame rate for timecodes (default: meta.fps or 24)")
    args = ap.parse_args()

    data = json.loads(Path(args.map).read_text())
    meta = data.get("meta", {})
    fps = args.fps or int(meta.get("fps", 24))
    shots = data["shots"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for s in shots:
        s["_start"], s["_end"] = parse_time(s["start"]), parse_time(s["end"])

    # ---- scene_map.csv -------------------------------------------------------------
    cols = ["id", "beat_id", "start", "end", "duration", "story_function", "job", "scene_type",
            "narration", "literal", "camera_move", "characters", "background", "props", "overlay_text",
            "mood_target", "ambient_visual", "ambient_audio", "ambient_intensity", "motif_id", "motif_event",
            "pattern_interrupt", "loop_opened", "loop_closed", "complexity", "hero", "new_assets",
            "reused_assets", "transition_type", "out_frame", "in_frame", "bridge", "audio_bridge",
            "transition_frames"]
    with open(out / "scene_map.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for s in shots:
            t = s.get("transition_out") or {}
            row = {**s,
                   "start": mmss(s["_start"]), "end": mmss(s["_end"]),
                   "duration": round(s["_end"] - s["_start"], 2),
                   "transition_type": t.get("type", ""), "out_frame": t.get("out_frame", ""),
                   "in_frame": t.get("in_frame", ""), "bridge": t.get("bridge", ""),
                   "audio_bridge": t.get("audio_bridge", ""), "transition_frames": t.get("duration_frames", "")}
            w.writerow([cell(row.get(c)) for c in cols])

    # ---- scene_map.md --------------------------------------------------------------
    lines = [f"# Scene map: {meta.get('title', 'untitled')}", ""]
    if meta.get("timing_source") == "estimated":
        lines += ["> Timing is estimated from the script. Replace with real timestamps when available.", ""]
    lines += ["| Time | Narration | Literal | Camera | Ambient (visual / audio) | Int | Cx | Transition out |",
              "|---|---|---|---|---|---|---|---|"]
    for s in shots:
        t = s.get("transition_out") or {}
        ambient = " / ".join(x for x in (cell(s.get("ambient_visual")), cell(s.get("ambient_audio"))) if x)
        trans = t.get("type", "")
        if t.get("bridge") and trans not in ("hard_cut", "audio_lead"):
            trans += f": {t['bridge']}"
        hero = " ★" if s.get("hero") else ""
        lines.append("| " + " | ".join([
            f"{mmss(s['_start'])}-{mmss(s['_end'])}{hero}", md_escape(s.get("narration")),
            md_escape(s.get("literal")), md_escape(s.get("camera_move")), md_escape(ambient),
            md_escape(s.get("ambient_intensity")), md_escape(s.get("complexity")), md_escape(trans)]) + " |")
    if data.get("assumptions"):
        lines += ["", "## Assumptions to check against references", ""]
        lines += [f"- {a}" for a in data["assumptions"]]
    (out / "scene_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- asset_list.csv ------------------------------------------------------------
    assets = {}
    def note(name, kind, shot):
        key = str(name).strip().lower()
        a = assets.setdefault(key, {"asset": name, "kind": kind, "first_shot": shot["id"],
                                    "first_time": mmss(shot["_start"]), "uses": 0, "hero_uses": 0, "max_complexity": 0})
        a["uses"] += 1
        a["hero_uses"] += 1 if shot.get("hero") else 0
        a["max_complexity"] = max(a["max_complexity"], shot.get("complexity", 0))
    for s in shots:
        for c in s.get("characters") or []:
            note(c, "character", s)
        for p in s.get("props") or []:
            note(p, "prop", s)
        if s.get("background"):
            note(s["background"], "background", s)
        for n in s.get("new_assets") or []:
            if str(n).strip().lower() not in assets:
                note(n, "other (variant or effect)", s)
    with open(out / "asset_list.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["asset", "kind", "first_shot", "first_time", "uses", "hero_uses", "max_complexity"])
        w.writeheader()
        for a in sorted(assets.values(), key=lambda x: (x["kind"], x["first_time"])):
            w.writerow(a)

    # ---- audio_cues.csv ------------------------------------------------------------
    with open(out / "audio_cues.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["timecode", "shot", "source", "cue", "motif_id", "motif_event"])
        for s in shots:
            if s.get("ambient_audio"):
                w.writerow([timecode(s["_start"], fps), s["id"], "ambient_audio", s["ambient_audio"],
                            s.get("motif_id", ""), s.get("motif_event", "")])
            t = s.get("transition_out") or {}
            if t.get("audio_bridge"):
                w.writerow([timecode(s["_end"], fps), s["id"], "transition audio_bridge", t["audio_bridge"], "", ""])

    # ---- markers.csv ---------------------------------------------------------------
    with open(out / "markers.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["timecode", "name", "note"])
        for s in shots:
            tc = timecode(s["_start"], fps)
            if s.get("hero"):
                w.writerow([tc, f"{s['id']} HERO", s.get("literal", "")[:120]])
            if s.get("pattern_interrupt"):
                w.writerow([tc, f"{s['id']} INTERRUPT", s.get("pattern_interrupt_note", "")])
            if s.get("story_function") in ("hook", "rehook", "reveal"):
                w.writerow([tc, f"{s['id']} {s['story_function'].upper()}", s.get("narration", "")[:120]])
            for entry in s.get("loop_opened") or []:
                w.writerow([tc, f"{s['id']} LOOP OPEN", entry])
            for lid in s.get("loop_closed") or []:
                w.writerow([tc, f"{s['id']} LOOP CLOSE", lid])
            t = s.get("transition_out") or {}
            if t.get("type") not in (None, "hard_cut", "audio_lead"):
                w.writerow([timecode(s["_end"], fps), f"{s['id']} {t['type'].upper()}", t.get("bridge", "")])

    print(f"Wrote 5 files to {out}/ at {fps} fps: scene_map.csv, scene_map.md, asset_list.csv, audio_cues.csv, markers.csv")


if __name__ == "__main__":
    main()
