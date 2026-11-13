#!/usr/bin/env python3
"""Validate a scene map JSON against mechanical pacing, continuity and schema rules.

Usage:
    python validate_map.py map.json
    python validate_map.py map.json --config my_config.json
    python validate_map.py map.json --dips 2:10,3:45
    python validate_map.py map.json --json report.json

Exit code 1 if any error is found, otherwise 0. Warnings never fail the run.
All thresholds come from config.json and are conventions, not measured laws.
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

STORY_FUNCTIONS = {"hook", "setup", "escalation", "reveal", "explanation", "bridge", "rehook", "resolution"}
JOBS = {"show_event", "show_place", "show_time", "show_mechanism", "show_relationship",
        "show_stakes", "hold_question", "introduce_character"}
SCENE_TYPES = {"character_action", "environment", "object_closeup", "mechanism", "map",
               "kinetic_text", "metaphor", "comparison_graphic"}
TRANSITIONS = {"hard_cut", "audio_lead", "match_cut", "motion_carry", "in_world_wipe",
               "zoom_through", "dissolve", "dip_to_black", "smash_cut", "text_card"}
PLAIN_TRANSITIONS = {"hard_cut", "audio_lead"}
REQUIRED = ["id", "beat_id", "start", "end", "narration", "story_function", "job",
            "scene_type", "literal", "camera_move", "mood_target", "ambient_intensity", "complexity"]


def parse_time(value):
    """Seconds as number, or 'm:ss(.f)' / 'h:mm:ss' string. Returns float or None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            total = 0.0
            for part in value.strip().split(":"):
                total = total * 60 + float(part)
            return total
        except ValueError:
            return None
    return None


def fmt(sec):
    sec = max(0.0, sec)
    m = int(sec // 60)
    s = sec - 60 * m
    return f"{m}:{s:04.1f}"


def norm(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def text(value):
    return value.strip() if isinstance(value, str) else ""


def loop_id(entry):
    return str(entry).split(":", 1)[0].strip()


def run(data, cfg):
    issues = []
    stats = {}

    def add(sev, rule, shot, msg):
        issues.append({"severity": sev, "rule": rule, "shot": shot, "message": msg})

    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
    excerpt = bool(meta.get("is_excerpt"))
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        add("error", "structure", None, "Map has no 'shots' list.")
        return issues, stats

    # ---- structure and times -------------------------------------------------
    bad_structure = False
    ids = set()
    for i, s in enumerate(shots):
        if not isinstance(s, dict):
            add("error", "structure", f"#{i + 1}", "Shot is not an object.")
            bad_structure = True
            continue
        s["_i"] = i
        sid = s.get("id", f"#{i + 1}")
        s["_id"] = sid
        if sid in ids:
            add("error", "structure", sid, "Duplicate shot id.")
        ids.add(sid)
        for field in REQUIRED:
            if field not in s or s[field] in (None, ""):
                add("error", "missing_field", sid, f"Missing required field '{field}'.")
        if not (text(s.get("ambient_visual")) or text(s.get("ambient_audio"))):
            add("error", "ambient_missing", sid, "Needs ambient_visual or ambient_audio (no sterile shots).")
        s["_start"] = parse_time(s.get("start"))
        s["_end"] = parse_time(s.get("end"))
        if s["_start"] is None or s["_end"] is None:
            add("error", "time", sid, "start/end are not valid times.")
            bad_structure = True
        elif s["_end"] <= s["_start"]:
            add("error", "time", sid, "end must be greater than start.")
            bad_structure = True
        if s.get("story_function") not in STORY_FUNCTIONS:
            add("error", "enum", sid, f"story_function '{s.get('story_function')}' not in {sorted(STORY_FUNCTIONS)}.")
        if s.get("job") not in JOBS:
            add("error", "enum", sid, f"job '{s.get('job')}' not in {sorted(JOBS)}.")
        if s.get("scene_type") not in SCENE_TYPES:
            add("error", "enum", sid, f"scene_type '{s.get('scene_type')}' not in {sorted(SCENE_TYPES)}.")
        if s.get("ambient_intensity") not in (1, 2, 3):
            add("error", "enum", sid, "ambient_intensity must be 1, 2 or 3.")
        if s.get("complexity") not in (1, 2, 3):
            add("error", "enum", sid, "complexity must be 1, 2 or 3.")
        if s.get("motif_id") and s.get("motif_event") not in (None, "start", "continue", "end"):
            add("error", "enum", sid, "motif_event must be start, continue or end.")
    if bad_structure:
        add("error", "structure", None, "Fix structural/time errors first; timing checks skipped.")
        return issues, stats

    n = len(shots)
    runtime = shots[-1]["_end"] - shots[0]["_start"]
    tol = cfg["time_tolerance_seconds"]
    stats["runtime_seconds"] = round(runtime, 2)
    stats["shot_count"] = n

    # ---- contiguity and shot length -----------------------------------------
    for prev, cur in zip(shots, shots[1:]):
        delta = cur["_start"] - prev["_end"]
        if delta > tol:
            add("warn", "gap", cur["_id"], f"Gap of {delta:.2f}s after {prev['_id']}.")
        elif delta < -tol:
            add("error", "overlap", cur["_id"], f"Overlaps {prev['_id']} by {-delta:.2f}s.")
    lengths = [s["_end"] - s["_start"] for s in shots]
    for s, ln in zip(shots, lengths):
        if ln > cfg["max_shot_seconds"]:
            add("warn", "long_shot", s["_id"],
                f"Shot is {ln:.1f}s (max {cfg['max_shot_seconds']}s). Split it or justify it as a hero/reveal hold.")
        if ln < cfg["min_shot_seconds"]:
            add("warn", "short_shot", s["_id"], f"Shot is {ln:.2f}s (min {cfg['min_shot_seconds']}s).")
    stats["average_shot_seconds"] = round(statistics.mean(lengths), 2)
    if n >= cfg["shot_length_check_min_shots"]:
        cv = statistics.pstdev(lengths) / statistics.mean(lengths)
        stats["shot_length_cv"] = round(cv, 3)
        if cv < cfg["shot_length_cv_min"]:
            add("warn", "flat_rhythm", None,
                f"Shot lengths are nearly uniform (cv={cv:.2f}). Vary them on purpose.")
    if runtime >= 60:
        spm = n / (runtime / 60)
        stats["shots_per_minute"] = round(spm, 1)
        lo, hi = cfg["shots_per_minute_range"]
        if not lo <= spm <= hi:
            add("warn", "shots_per_minute", None, f"{spm:.1f} shots/min is outside {lo}-{hi}.")

    # ---- variety runs ---------------------------------------------------------
    def check_run(key, limit, rule, label):
        run_len, prev_val = 0, None
        for s in shots:
            val = s.get(key)
            run_len = run_len + 1 if val == prev_val else 1
            prev_val = val
            if run_len == limit + 1:
                add("warn", rule, s["_id"], f"More than {limit} {label} in a row ('{val}').")

    check_run("scene_type", cfg["max_consecutive_same_scene_type"], "scene_type_run", "shots of the same scene_type")
    check_run("camera_move", cfg["max_consecutive_same_camera_move"], "camera_run", "shots with the same camera_move")

    run_len = 0
    for s in shots:
        run_len = run_len + 1 if s.get("complexity") == 3 else 0
        if run_len == cfg["max_consecutive_complexity_3"] + 1:
            add("warn", "complexity_run", s["_id"],
                f"More than {cfg['max_consecutive_complexity_3']} complexity-3 shots in a row.")
    if runtime >= cfg["hero_check_min_runtime_seconds"] or runtime >= 60:
        cpm = sum(s["complexity"] for s in shots) / (runtime / 60)
        stats["complexity_points_per_minute"] = round(cpm, 1)
        if cpm > cfg["complexity_points_per_minute_max"]:
            add("warn", "complexity_budget", None,
                f"{cpm:.0f} complexity points/min exceeds {cfg['complexity_points_per_minute_max']}.")

    # ---- pattern interrupts, hook, re-hooks -----------------------------------
    last_interrupt, flagged = shots[0]["_start"], False
    for s in shots:
        if s.get("pattern_interrupt"):
            last_interrupt, flagged = s["_start"], False
        elif s["_start"] - last_interrupt > cfg["max_seconds_between_interrupts"] and not flagged:
            add("warn", "interrupt_gap", s["_id"],
                f"{s['_start'] - last_interrupt:.0f}s since the last pattern interrupt "
                f"(limit {cfg['max_seconds_between_interrupts']}s).")
            flagged = True

    if not excerpt:
        t0 = shots[0]["_start"]
        hooks = [s for s in shots if s.get("story_function") == "hook"
                 and s["_start"] - t0 < cfg["hook_window_seconds"]]
        if not hooks:
            add("error", "hook", None, f"No shot with story_function 'hook' in the first {cfg['hook_window_seconds']}s.")
        win = cfg["rehook_interval_seconds"]
        w = t0
        while w < shots[-1]["_end"]:
            w_end = min(w + win, shots[-1]["_end"])
            if w_end - w >= win / 2:
                ok = any(w <= s["_start"] < w_end and
                         (s.get("story_function") in ("hook", "rehook") or s.get("loop_opened"))
                         for s in shots)
                if not ok:
                    add("warn", "rehook", None,
                        f"No hook, rehook or newly opened loop between {fmt(w)} and {fmt(w_end)}.")
            w += win

    # ---- continuity of assets -------------------------------------------------
    seen = set()
    new_shot_count = 0
    for s in shots:
        new = {norm(x) for x in (s.get("new_assets") or [])}
        if new:
            new_shot_count += 1
        entities = list(s.get("characters") or []) + list(s.get("props") or [])
        if text(s.get("background")):
            entities.append(s["background"])
        for e in entities:
            ne = norm(e)
            if ne not in seen and ne not in new:
                add("error", "continuity", s["_id"],
                    f"'{e}' appears before being introduced. List it in new_assets on its first shot.")
        for ne in new:
            if ne in seen:
                add("warn", "not_new", s["_id"], f"'{ne}' is listed as new but was already introduced.")
        seen |= new | {norm(e) for e in entities}
    stats["new_asset_shot_ratio"] = round(new_shot_count / n, 2)
    if n >= 8 and new_shot_count / n > cfg["max_new_asset_shot_ratio"]:
        add("warn", "new_asset_ratio", None,
            f"{new_shot_count}/{n} shots introduce new assets (limit {cfg['max_new_asset_shot_ratio']:.0%}). Reuse more.")

    # ---- fact anchors -----------------------------------------------------------
    seen_numbers = set()
    for s in shots:
        nums = set(re.findall(r"\d[\d,.]*", s.get("narration", "")))
        fresh = nums - seen_numbers
        if fresh and not text(s.get("overlay_text")):
            add("warn", "overlay_missing", s["_id"],
                f"Narration contains {sorted(fresh)} but there is no overlay_text. (Digits only; check spelled-out numbers by hand.)")
        seen_numbers |= nums

    # ---- ambient layer ----------------------------------------------------------
    mood = set(cfg["mood_words"])
    for s in shots:
        for key in ("ambient_visual", "ambient_audio"):
            val = text(s.get(key))
            if not val:
                continue
            tokens = re.findall(r"[a-z']+", val.lower())
            if any(t in mood for t in tokens) and len(tokens) < 4:
                add("error", "ambient_mood_word", s["_id"],
                    f"{key} '{val}' is a mood word, not a physical thing that happens. Describe what moves or sounds.")
    run_len, prev_key = 0, None
    for s in shots:
        key = (norm(s.get("ambient_visual", "")), norm(s.get("ambient_audio", "")))
        if s.get("motif_id"):
            run_len, prev_key = 0, None
            continue
        run_len = run_len + 1 if key == prev_key else 1
        prev_key = key
        if run_len == cfg["max_consecutive_identical_ambient"] + 1:
            add("warn", "ambient_wallpaper", s["_id"],
                f"Identical ambient detail in more than {cfg['max_consecutive_identical_ambient']} shots with no motif_id.")
    high = sum(1 for s in shots if s.get("ambient_intensity") == 3)
    stats["ambient_intensity_3_ratio"] = round(high / n, 2)
    if n >= 8 and high / n > cfg["max_ambient_intensity_3_ratio"]:
        add("warn", "ambient_intensity", None,
            f"{high}/{n} shots at ambient intensity 3 (limit {cfg['max_ambient_intensity_3_ratio']:.0%}).")
    motifs = {}
    for s in shots:
        m = s.get("motif_id")
        if m:
            motifs.setdefault(m, []).append(s)
    for m, uses in motifs.items():
        if uses[0].get("motif_event") not in (None, "start") and len(uses) >= 1:
            add("warn", "motif_start", uses[0]["_id"], f"Motif {m} first appears without motif_event 'start'.")
        if len(uses) == 1 and not excerpt and uses[0].get("motif_event") != "end":
            add("warn", "motif_once", uses[0]["_id"], f"Motif {m} appears only once; it is probably wallpaper, not a motif.")

    # ---- transitions -------------------------------------------------------------
    designed_run = 0
    designed_count = 0
    boundaries = 0
    last_dip = None
    for i, s in enumerate(shots[:-1]):
        t = s.get("transition_out")
        if not isinstance(t, dict):
            add("error", "transition", s["_id"], "Missing transition_out object.")
            continue
        boundaries += 1
        ttype = t.get("type")
        if ttype not in TRANSITIONS:
            add("error", "transition", s["_id"], f"transition type '{ttype}' not in {sorted(TRANSITIONS)}.")
            continue
        if ttype not in PLAIN_TRANSITIONS:
            designed_count += 1
            designed_run += 1
            for f in ("out_frame", "in_frame", "bridge"):
                if not text(t.get(f)):
                    add("error", "transition", s["_id"], f"{ttype} needs '{f}' filled in with a physical description.")
            if designed_run == cfg["max_consecutive_designed_transitions"] + 1:
                add("warn", "transition_run", s["_id"],
                    f"More than {cfg['max_consecutive_designed_transitions']} designed transitions in a row.")
        else:
            designed_run = 0
        if ttype == "dissolve":
            nxt = shots[i + 1]
            if s.get("job") != "show_time" and nxt.get("job") != "show_time":
                add("warn", "dissolve_use", s["_id"], "Dissolve used where neither neighbouring shot has job 'show_time'.")
        if ttype == "dip_to_black":
            when = s["_end"]
            if last_dip is not None and when - last_dip < cfg["dip_to_black_min_seconds_apart"]:
                add("warn", "dip_frequency", s["_id"],
                    f"Dip to black only {when - last_dip:.0f}s after the previous one "
                    f"(limit {cfg['dip_to_black_min_seconds_apart']}s apart).")
            last_dip = when
    stats["boundaries"] = boundaries
    if boundaries:
        plain = boundaries - designed_count
        stats["plain_cut_ratio"] = round(plain / boundaries, 2)
        if not excerpt and boundaries >= cfg["hard_cut_check_min_boundaries"]:
            lo, hi = cfg["hard_cut_ratio_range"]
            if not lo <= plain / boundaries <= hi:
                add("warn", "plain_cut_ratio", None,
                    f"Plain cuts are {plain / boundaries:.0%} of boundaries (target {lo:.0%}-{hi:.0%}).")
    for i, s in enumerate(shots):
        if s.get("story_function") == "reveal" and i > 0:
            pt = shots[i - 1].get("transition_out") or {}
            ok = pt.get("type") == "dip_to_black" or "silence" in str(pt.get("audio_bridge", "")).lower()
            if not ok:
                add("warn", "reveal_setup", s["_id"],
                    "Reveal has no beat of black or silence before it (previous transition_out).")

    # ---- open loops ----------------------------------------------------------------
    opened = {}
    for s in shots:
        for entry in s.get("loop_opened") or []:
            lid = loop_id(entry)
            if lid in opened:
                add("warn", "loop", s["_id"], f"Loop {lid} opened twice.")
            opened[lid] = s
    closed = set()
    for i, s in enumerate(shots):
        for lid in s.get("loop_closed") or []:
            lid = str(lid).strip()
            if lid not in opened or opened[lid]["_i"] > i:
                add("error", "loop", s["_id"], f"Loop {lid} closed before (or without) being opened.")
                continue
            closed.add(lid)
            if not excerpt and shots[-1]["_end"] - s["_end"] > runtime * cfg["loop_unclosed_ignore_final_fraction"]:
                window = shots[i:i + cfg["loop_close_open_within_shots"] + 1]
                if not any(w.get("loop_opened") for w in window):
                    add("warn", "loop_close_without_open", s["_id"],
                        f"Loop {lid} closes with no new loop opened within {cfg['loop_close_open_within_shots']} shots.")
    if not excerpt:
        cutoff = shots[-1]["_end"] - runtime * cfg["loop_unclosed_ignore_final_fraction"]
        for lid, s in opened.items():
            if lid not in closed and s["_start"] < cutoff:
                add("warn", "loop_unclosed", s["_id"], f"Loop {lid} is never closed.")
        heroes = [s for s in shots if s.get("hero")]
        stats["hero_shots"] = len(heroes)
        if runtime >= cfg["hero_check_min_runtime_seconds"]:
            lo, hi = cfg["hero_per_minute_range"]
            per_min = len(heroes) / (runtime / 60)
            if not lo <= per_min <= hi:
                add("warn", "hero_count", None,
                    f"{len(heroes)} hero shots = {per_min:.2f}/min (target {lo}-{hi}).")

    return issues, stats


def locate_dips(data, dips, lookback=10.0):
    shots = data.get("shots", [])
    out = []
    for raw in dips:
        t = parse_time(raw)
        if t is None:
            out.append({"dip": raw, "error": "not a valid time"})
            continue
        at, before = None, []
        for s in shots:
            st, en = parse_time(s.get("start")), parse_time(s.get("end"))
            if st is None or en is None:
                continue
            if st <= t < en:
                at = s
            elif t - lookback <= st < t:
                before.append(s)
        out.append({"dip": raw, "at": at, "before": before})
    return out


def print_report(issues, stats, shots_total):
    errors = [i for i in issues if i["severity"] == "error"]
    warns = [i for i in issues if i["severity"] == "warn"]
    print(f"Scene map check: {shots_total} shots, {len(errors)} error(s), {len(warns)} warning(s)")
    if stats:
        print("Stats: " + ", ".join(f"{k}={v}" for k, v in stats.items()))
    for label, group in (("ERRORS", errors), ("WARNINGS", warns)):
        if group:
            print(f"\n{label}")
            for i in group:
                where = i["shot"] if i["shot"] is not None else "whole map"
                print(f"  [{i['rule']}] {where}: {i['message']}")
    if not issues:
        print("\nNo issues found by the mechanical checks. This does not prove the map works; only the retention graph can.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map")
    ap.add_argument("--config")
    ap.add_argument("--dips", help="Comma-separated retention dip timestamps, e.g. 2:10,3:45")
    ap.add_argument("--json", help="Write the report as JSON to this path")
    args = ap.parse_args()

    cfg_path = Path(args.config) if args.config else Path(__file__).with_name("config.json")
    cfg = json.loads(cfg_path.read_text())
    data = json.loads(Path(args.map).read_text())

    issues, stats = run(data, cfg)
    print_report(issues, stats, len(data.get("shots", [])) if isinstance(data.get("shots"), list) else 0)

    if args.dips:
        print("\nRETENTION DIPS (hypotheses only: the map shows what was planned, not what viewers saw)")
        for d in locate_dips(data, [x.strip() for x in args.dips.split(",") if x.strip()]):
            if "error" in d:
                print(f"  {d['dip']}: {d['error']}")
                continue
            at = d["at"]
            if at is None:
                print(f"  {d['dip']}: no shot at this time")
                continue
            print(f"  {d['dip']}: shot {at['id']} [{at.get('scene_type')}, {at.get('camera_move')}, "
                  f"cx{at.get('complexity')}, ambient {at.get('ambient_intensity')}] {at.get('literal', '')[:90]}")
            if at.get("loop_closed"):
                print(f"      closes loops {at['loop_closed']}; check something else stays open")
            print("      previous 10s: " + ", ".join(f"{b['id']}({b.get('scene_type')})" for b in d["before"]))

    if args.json:
        Path(args.json).write_text(json.dumps({"stats": stats, "issues": issues}, indent=2))
    sys.exit(1 if any(i["severity"] == "error" for i in issues) else 0)


if __name__ == "__main__":
    main()
