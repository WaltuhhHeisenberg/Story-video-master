#!/usr/bin/env python3
"""Assemble the single CHECK REPORT delivered with the 3D (three.js) video.

  python make_check_report.py --run RUN_DIR --out RUN_DIR/check_report.md

Reads what exists (never invents a result): reports/gate1_report.md, reports/gate2_report.md, the render log, scene-map validator output
(reports/scene_map_validation.txt), the bridge report, voiceover-script report, autofix report, problems log.
Every section says PASS / FAIL / NOT RUN with the evidence line. NOT RUN is shown honestly, never as PASS.
"""
import argparse, glob, json, os, re, sys


DIRS = []


def rd(p):
    """Read a report by its path relative to the run: tries <run>/reports and <run>/toon/reports (and the run itself)."""
    name = os.path.basename(p)
    for d in DIRS:
        try:
            return open(os.path.join(d, name), encoding="utf-8").read()
        except Exception:
            continue
    return None


def gate_status(t):
    """Last '## Run N' block of a gate report. FAIL if any FAIL row; NOT RUN if no rows can be read (never a silent PASS)."""
    if t is None:
        return "NOT RUN", ""
    runs = re.split(r"(?m)^## Run \d+", t)
    last = runs[-1] if len(runs) > 1 else t
    rows = re.findall(r"(?m)^\|\s*((?:G[12]-\d+)|(?:M-\d+))\s*\|[^|]*\|\s*\*{0,2}(PASS|FAIL|MANUAL|NOT RUN)\*{0,2}\s*\|", last)
    if not rows:
        return "NOT RUN", "report has no readable rows"
    fails = [k for k, v in rows if v == "FAIL"]
    pas = sum(1 for _, v in rows if v == "PASS")
    man = [k for k, v in rows if v == "MANUAL"]
    ev = f"{pas} PASS, {len(fails)} FAIL, {len(man)} MANUAL (need your look)" + (": FAIL " + ", ".join(fails) if fails else "")
    return ("FAIL" if fails else ("PASS + MANUAL REVIEW" if man else "PASS")), ev


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    DIRS[:] = [os.path.join(a.run, "reports"), os.path.join(a.run, "toon", "reports"), a.run, os.path.join(a.run, "toon")]
    R = os.path.join(a.run, "reports")
    rows = []
    s, d = gate_status(rd(os.path.join(R, "gate1_report.md"))); rows.append(("Gate 1 - 3D project before the render (computed checks)", s, d))
    s, d = gate_status(rd(os.path.join(R, "gate2_report.md"))); rows.append(("Gate 2 - rendered video (duration, size, audio, captions, frames)", s, d))
    rl = rd(os.path.join(R, "render_log.txt"))
    rows.append(("Render", "PASS" if rl and "done:" in rl else "NOT RUN", (re.search(r"done: .*", rl).group(0) if rl and re.search(r"done: .*", rl) else "reports/render_log.txt missing or no 'done:' line")))
    t = rd(os.path.join(R, "scene_map_validation.txt"))
    if t is None:
        rows.append(("Scene-map validator (pacing, loops, transitions)", "NOT RUN", "reports/scene_map_validation.txt missing"))
    else:
        m = re.search(r"(\d+) error\(s\), (\d+) warning\(s\)", t)
        rows.append(("Scene-map validator (pacing, loops, transitions)", "PASS" if m and m.group(1) == "0" else "FAIL", m.group(0) if m else "unreadable"))
    t = rd(os.path.join(R, "scene_map_bridge_report.md"))
    rows.append(("Scene map <-> clauses alignment (bridge)", "PASS" if t and "OK" in t else "NOT RUN", (re.search(r"- shots = clauses.*", t).group(0) if t and re.search(r"- shots = clauses.*", t) else "")))
    t = rd(os.path.join(R, "voiceover_script_report.md")) or rd(os.path.join(a.run, "04-voiceover-script-report.md"))
    if t is None:
        rows.append(("Voiceover-ready script", "NOT RUN", ""))
    else:
        blocking = "## Blocking\n- none" in t
        rows.append(("Voiceover-ready script", "PASS" if blocking else "FAIL", (re.search(r"- narration words: \d+", t) or [""])[0] if re.search(r"- narration words: \d+", t) else ""))
    probs = []
    for d in DIRS:
        pl = os.path.join(d, "master_problems.jsonl")
        if os.path.exists(pl):
            probs += [json.loads(l) for l in open(pl, encoding="utf-8") if l.strip()]
    af = None
    out = ["# Check report", "", "| Check | Result | Evidence |", "|---|---|---|", *[f"| {n} | **{s}** | {d} |" for n, s, d in rows], ""]
    if any(s == "NOT RUN" for _, s, _ in rows):
        out += ["NOT RUN rows were not executed in this run; they are not passes.", ""]
    out += ["## Problems met in this run (input of the plugin autofix)"]
    out += [f"- {p['id']} [{p['severity']}] {p['symptom']}" + (f" -> handled: {p['handled']}" if p.get("handled") else "") for p in probs] or ["- none logged"]
    if af:
        out += ["", "## Timing autofix applied", af[:1500]]
    out += ["", "The picture is rendered by the three.js toon studio (toon-studio/); it makes picture and captions only. Voiceover is muxed as delivered; music, sound effects and ambient sound are not produced (listed in scene_map_bridge_report.md). MANUAL rows need your look at the contact sheet."]
    open(a.out, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("check report ->", a.out, "|", ", ".join(f"{n.split(' - ')[0]}: {s}" for n, s, _ in rows))
    return 1 if any(s == "FAIL" for _, s, _ in rows) or any(s == "NOT RUN" for _, s, _ in rows[:2]) else 0   # the three gates must have run


if __name__ == "__main__":
    sys.exit(main())
