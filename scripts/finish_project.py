#!/usr/bin/env python3
"""END-OF-PROJECT SELF-IMPROVEMENT: the plugin learns from the project it just made. Run after EVERY project.

  python finish_project.py --project-name "Name" --work-dir WORK --lessons lessons.json --out OUT [--extra-dir DIR]

What it does (in order; stops with a clear message if a rule is broken):
 1. COLLECT every problem of this run automatically: FAIL / MANUAL-fail rows in gate*_report.md, the autofix report,
    failed commands in pipeline_log.json (written by run_toon.py), reviewer findings listed in qa_report.md ("OPEN" / "FIXED" lines).
 2. REQUIRE a lesson for each one. `lessons.json` is a list written by Claude (the author of the fix):
      {"id": "V8", "area": "idea|packaging|script|voiceover-script|scene-map|bridge|clauses|builder|qa|env|plugin", "symptom": "...", "cause": "...",
       "fix": "what was changed in the plugin (file + rule)", "files": ["scripts/x.py", ...], "still_manual": "...",
       "prevention": "check|autofix|rule|none", "covers": ["G1-15", "F2", ...]  # finding keys this lesson answers}
    Claude must have ALREADY patched the plugin files (scripts / skills / references) before running this; this script
    only records, verifies and ships. A problem with no lesson, or a lesson with prevention "none" and no still_manual
    text, is listed as UNRESOLVED in improvement_report.md and the run exits 2 (you may still ship with --allow-unresolved).
 3. SELF-TEST the patched plugin (selftest.py: every script compiles; bridge, gates, catalogue and the 3D engine files are checked). A patch that
    breaks the plugin aborts the shipment.
 4. APPEND the lessons to references/known-issues.md and references/lessons.json, bump the patch version in
    .claude-plugin/plugin.json, copy the run's outlier research
    (<work-dir>/research/outliers/<batch>/) into the plugin's research/outliers/ and delete only batches older than 1 year (keyword window 14 days, outlier window 60 days),
    and write OUT/<plugin name>.plugin (name read from .claude-plugin/plugin.json)
    plus OUT/improvement_report.md.
Install the returned .plugin: that is how the plugin keeps the fixes and the library.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--project-name", required=True)
ap.add_argument("--work-dir", required=True, help="folder holding gate1_report.md, gate2_report.md, qa_report.md, autofix_report.md, pipeline_log.json (searched recursively)")
ap.add_argument("--lessons", required=True)
ap.add_argument("--extra-dir", help="optional folder kept under library/extra_<project>/ (for example a custom 3D theme or character preset you made)")
ap.add_argument("--plugin-dir", default=os.path.abspath(os.path.join(HERE, "..")))
ap.add_argument("--out", required=True)
ap.add_argument("--allow-unresolved", action="store_true")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

# 1 collect
found = []
def rd(p):
    try: return open(p, encoding="utf-8").read()
    except Exception: return ""
for p in (glob.glob(os.path.join(a.work_dir, "**", "*.md"), recursive=True) + glob.glob(os.path.join(a.work_dir, "**", "pipeline_log.json"), recursive=True)
          + glob.glob(os.path.join(a.work_dir, "**", "master_problems.jsonl"), recursive=True)):
    n = os.path.basename(p); t = rd(p)
    if re.match(r"gate[12].*report\.md", n):
        runs = re.split(r"(?m)^## Run \d+", t)
        for i, r in enumerate(runs[1:], 1):          # every run, also the failed ones that were later fixed
            for m in re.finditer(r"(?m)^\|?\s*(G[12]-\d+)\s*\|[^|]*\|\s*\*{0,2}FAIL\*{0,2}\s*\|\s*(.{0,160})", r):
                found.append(f"{n} run {i}: {m.group(1)} FAIL - {m.group(2).strip()}")
    elif n == "qa_report.md":
        for l in t.splitlines():   # review findings are written "- F2 text ... FIXED|OPEN" (key first)
            if re.match(r"-\s*[A-Z]\d+\b", l.strip()) and re.search(r"\b(OPEN|FIXED|FAIL)\b", l): found.append(f"qa_report: {l.strip()[:200]}")
    elif n == "autofix_report.md":
        for l in t.split("## Needs the editor")[-1].splitlines():
            if l.startswith("- ") and "nothing" not in l: found.append(f"autofix todo: {l[2:][:200]}")
    elif n == "pipeline_log.json":
        try:   # run_toon writes a plain list of {"cmd","rc",...}; older logs used {"commands":[{"returncode"}]}
            data = json.load(open(p)); data = data.get("commands", []) if isinstance(data, dict) else data
            for e in data:
                if e.get("returncode", e.get("rc", 0)): found.append(f"command failed: {str(e.get('cmd'))[:160]}")
        except Exception: pass
    elif n == "master_problems.jsonl":       # every stage of the master run logs here (scripts/problem_log.py)
        for l in t.splitlines():
            try:
                r = json.loads(l); found.append(f"{r['id']} [{r.get('stage')}] {r.get('symptom', '')[:170]}")
            except Exception: pass
found = list(dict.fromkeys(found))

# 2 lessons
L = json.load(open(a.lessons, encoding="utf-8"))
need = ["id", "area", "symptom", "cause", "fix", "prevention"]
bad = [l.get("id", "?") for l in L if any(not l.get(k) for k in need)]
if bad: sys.exit(f"lessons missing fields {need}: {bad}")
unresolved = [l["id"] for l in L if l["prevention"] == "none" and not l.get("still_manual")]
files_missing = [(l["id"], f) for l in L for f in l.get("files", []) if not os.path.exists(os.path.join(a.plugin_dir, f))]
if files_missing: sys.exit(f"lesson lists files that do not exist in the plugin (patch first): {files_missing}")
def key(f):
    m = re.search(r"\b(G[12]-\d+)\b", f) or re.search(r"^qa_report: -\s*([A-Z]\d+)\b", f) or re.search(r"^(M-[a-z-]+-\d+)\b", f)
    return m.group(1) if m else None
cov = {k for l in L for k in [l["id"]] + list(l.get("covers", []))}
# every finding (gate FAIL row or review finding) needs a lesson whose id or "covers" list names its key
uncovered = [f for f in found if key(f) and key(f) not in cov]

# 3 selftest
st = subprocess.run([sys.executable, os.path.join(a.plugin_dir, "scripts", "selftest.py")], capture_output=True, text=True)
print(st.stdout.strip())
if st.returncode:
    sys.exit("SELFTEST FAILED - the patched plugin is broken, nothing shipped:\n" + st.stderr[-1500:])

# 4 ship
tmp = tempfile.mkdtemp()
pc = os.path.join(tmp, os.path.basename(os.path.abspath(a.plugin_dir)))
shutil.copytree(a.plugin_dir, pc, ignore=shutil.ignore_patterns("__pycache__", ".git", ".in_use", "node_modules", ".build-*", "*.mp4"))
ki = os.path.join(pc, "skills", "toon-video-studio", "references", "known-issues.md")
os.makedirs(os.path.dirname(ki), exist_ok=True)
with open(ki, "a", encoding="utf-8") as f:
    f.write(f"\n## Lessons from \"{a.project_name}\"\n| # | Area | Symptom | Cause | Plugin change | Prevention | Still manual |\n|---|---|---|---|---|---|---|\n")
    for l in L:
        f.write(f"| {l['id']} | {l['area']} | {l['symptom']} | {l['cause']} | {l['fix']} {', '.join(l.get('files', []))} | {l['prevention']} | {l.get('still_manual', 'none')} |\n")
lj = os.path.join(pc, "skills", "toon-video-studio", "references", "lessons.json")
hist = json.load(open(lj)) if os.path.exists(lj) else []
hist.append({"project": a.project_name, "lessons": L})
json.dump(hist, open(lj, "w"), indent=1)
mref = os.path.join(pc, "skills", "story-video-master", "references")
if os.path.isdir(os.path.join(pc, "skills", "story-video-master")):      # master plugin: lessons of ALL stages are kept where every stage reads them
    os.makedirs(mref, exist_ok=True)
    with open(os.path.join(mref, "known-issues-master.md"), "a", encoding="utf-8") as f:
        f.write(f"\n## Lessons from \"{a.project_name}\"\n| # | Area | Symptom | Cause | Plugin change | Prevention | Still manual |\n|---|---|---|---|---|---|---|\n")
        for l in L:
            f.write(f"| {l['id']} | {l['area']} | {l['symptom']} | {l['cause']} | {l['fix']} {', '.join(l.get('files', []))} | {l['prevention']} | {l.get('still_manual', 'none')} |\n")
    mlj = os.path.join(mref, "lessons-master.json")
    mh = json.load(open(mlj)) if os.path.exists(mlj) else []
    mh.append({"project": a.project_name, "lessons": L}); json.dump(mh, open(mlj, "w"), indent=1)
pj = os.path.join(pc, ".claude-plugin", "plugin.json")
meta = json.load(open(pj)); v = meta["version"].split("."); v[-1] = str(int(v[-1]) + 1); meta["version"] = ".".join(v)
json.dump(meta, open(pj, "w"), indent=2)
if a.extra_dir:
    shutil.copytree(a.extra_dir, os.path.join(pc, "library", "extra_" + re.sub(r"\W+", "_", a.project_name)), dirs_exist_ok=True)
# outlier research: the run's store (<work-dir>/research/outliers) is copied into the shipped plugin's research/outliers, then batches older than 1 year are deleted
run_store = os.path.join(a.work_dir, "research", "outliers")
plug_store = os.path.join(pc, "research", "outliers")
os.makedirs(plug_store, exist_ok=True)
if os.path.isdir(run_store):
    for b in sorted(os.listdir(run_store)):
        if os.path.exists(os.path.join(run_store, b, "meta.json")):
            shutil.copytree(os.path.join(run_store, b), os.path.join(plug_store, b), dirs_exist_ok=True)
            print("outlier research batch shipped into the plugin:", b)
_os = os.path.join(pc, "scripts", "outlier_store.py")
if os.path.exists(_os):
    subprocess.run([sys.executable, _os, "purge", "--store", plug_store], check=False)
dst = os.path.join(a.out, meta["name"] + ".plugin")
with zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED) as z:
    for dp, dn, fs in os.walk(pc):
        dn[:] = [d for d in dn if d not in ("__pycache__", "node_modules")]
        for fn in sorted(fs):
            full = os.path.join(dp, fn); z.write(full, os.path.relpath(full, pc))      # plugin root at the zip root (.claude-plugin/plugin.json first level)
rep = [f"# Improvement report - {a.project_name}", f"New plugin version: {meta['version']}", "",
       "## Problems found automatically in this run", *(f"- {x}" for x in found or ["none"]), "",
       "## Lessons applied to the plugin", *(f"- {l['id']} [{l['area']}] {l['symptom']} -> {l['fix']} (prevention: {l['prevention']})" for l in L), "",
       "## UNRESOLVED (needs a fix or a still_manual note)", *(f"- lesson {x}" for x in unresolved), *(f"- no lesson mentions: {x}" for x in uncovered), ""]
open(os.path.join(a.out, "improvement_report.md"), "w", encoding="utf-8").write("\n".join(rep))
shutil.rmtree(tmp, ignore_errors=True)
print("shipped ->", dst, "version", meta["version"], f"| lessons {len(L)} | unresolved {len(unresolved) + len(uncovered)}")
if (unresolved or uncovered) and not a.allow_unresolved:
    print("UNRESOLVED items listed in improvement_report.md - fix them, add lessons, re-run (or --allow-unresolved)"); sys.exit(2)
