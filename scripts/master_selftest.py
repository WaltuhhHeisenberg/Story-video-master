#!/usr/bin/env python3
"""Master-plugin self-test (run by selftest.py, so finish_project.py blocks a shipment that breaks any of this).

1. plugin.json readable, name + version present.
2. Every skill folder has SKILL.md whose `name:` equals the folder; every agent file's `name:` equals the file name.
3. Every `story-video-master:<agent>` mention resolves to an agent file; every `skills/<skill>/SKILL.md` mention resolves.
4. Every backticked relative file reference (references/x.md, reference/x.md, scripts/x.py, examples/x.json, library/x.json ...) in a skill,
   agent or command resolves (relative to the skill folder, the plugin root, the toon-video-studio skill or toon-studio/). Files created at run time are whitelisted.
5. Scene-mapping validator passes on its bundled example; the 3D bridge, the 3D gates and the voiceover-script cleaner run on a tiny sample; the 3D asset library (built-ins vs engine, every grown asset valid) is checked, a missing prop becomes an open asset gap and making it closes the gap.
6. Packaging test smoke: outlier_store save/merge -> make_thumbnail -> build_feed (images required, candidate never in the first 3) -> verdict.
7. Wiring: every skill, agent and command appears in the wiring map of skills/story-video-master/SKILL.md (no idle piece).
8. No skill, agent or command refers to a piece that is not in this plugin (prepare-voiceover, story-video-pipeline, video-pipeline/).
"""
import json, os, re, subprocess, sys, tempfile

H = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(H, ".."))
bad = []
RUNTIME = {"lessons.json", "lessons-master.json", "known-issues-master.md", "toon_project.json", "toon_plan.json", "clauses.json", "intake_report.md", "manual2.json", "library.json"}


def front(p):
    t = open(p, encoding="utf-8-sig").read().replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    n = re.search(r"(?m)^name:\s*(.+)$", m.group(1)) if m else None
    return (n.group(1).strip() if n else None), t


try:
    meta = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8"))
    PN = meta["name"]; meta["version"]
except Exception as e:
    bad.append(f"plugin.json: {e}"); PN = "story-video-master"
skills = {}
sd = os.path.join(ROOT, "skills")
for d in sorted(os.listdir(sd)):
    p = os.path.join(sd, d, "SKILL.md")
    if not os.path.exists(p):
        bad.append(f"skills/{d} has no SKILL.md"); continue
    n, _ = front(p)
    if n != d:
        bad.append(f"skills/{d}/SKILL.md name is '{n}'")
    skills[d] = os.path.join(sd, d)
agents = {}
ad = os.path.join(ROOT, "agents")
for f in sorted(os.listdir(ad)):
    if f.endswith(".md"):
        n, _ = front(os.path.join(ad, f))
        if n != f[:-3]:
            bad.append(f"agents/{f} name is '{n}'")
        agents[f[:-3]] = 1
docs = [(os.path.join(sd, d, "SKILL.md"), skills[d]) for d in skills] + [(os.path.join(ad, f + ".md"), ROOT) for f in agents]
cd = os.path.join(ROOT, "commands")
if os.path.isdir(cd):
    docs += [(os.path.join(cd, f), ROOT) for f in sorted(os.listdir(cd)) if f.endswith(".md")]
REF = re.compile(r"`((?:references?|scripts|examples|library|toon-studio)/[A-Za-z0-9_./-]+\.(?:md|py|json|csv|txt|mjs))`")
for p, base in docs:
    t = open(p, encoding="utf-8-sig").read()
    rel = os.path.relpath(p, ROOT)
    for m in re.finditer(r"story-video-master:([a-z][a-z-]*)", t):
        if m.group(1) not in agents:
            bad.append(f"{rel}: agent `{PN}:{m.group(1)}` does not exist")
    for m in re.finditer(r"story-(?:video|script)-[a-z-]*:|script-retention:", t):
        if not m.group(0).startswith("story-video-master:") and not m.group(0).startswith("story-video-idea") and not m.group(0).startswith("story-video-pipeline"):
            bad.append(f"{rel}: stale plugin prefix '{m.group(0)}'")
    for m in re.finditer(r"skills/([a-z][a-z-]*)/SKILL\.md", t):
        if m.group(1) not in skills:
            bad.append(f"{rel}: skill '{m.group(1)}' does not exist")
    for m in REF.finditer(t):
        ref = m.group(1)
        if os.path.basename(ref) in RUNTIME:
            continue
        if not any(os.path.exists(os.path.join(b, ref)) for b in (base, ROOT, skills.get("toon-video-studio", ROOT), os.path.join(ROOT, "toon-studio"), os.path.dirname(p))):
            bad.append(f"{rel}: file `{ref}` does not exist")
# the script agents take their rulebook from the story-explainer-scripts skill (the old separate rulebook skill was removed on purpose)
if "story-explainer-scripts" not in skills:
    bad.append("skill story-explainer-scripts missing (script-lazy-viewer and script-writing-teacher load it)")
for a in ("script-lazy-viewer", "script-writing-teacher"):
    ap_ = os.path.join(ad, a + ".md")
    if os.path.exists(ap_) and "skills/story-explainer-scripts/SKILL.md" not in open(ap_, encoding="utf-8-sig").read():
        bad.append(f"agents/{a}.md does not load skills/story-explainer-scripts/SKILL.md")
for ref in ("hooks.md", "sentence-shapes.md", "audit.md", "sentence-breakdowns.md"):
    if not os.path.exists(os.path.join(sd, "story-explainer-scripts", "references", ref)):
        bad.append(f"skills/story-explainer-scripts/references/{ref} missing")
_ids = os.path.join(sd, "story-video-idea-system", "SKILL.md")
if os.path.exists(_ids) and re.search(r"(?m)^\d+\.\s+\*\*Hook\*\*", open(_ids, encoding="utf-8-sig").read()):
    bad.append("skills/story-video-idea-system/SKILL.md lists a Hook in the Video Brief (hooks are written only in the script stage)")
STALE = ("lazy-viewer" + "-scripting", "R1" + "-R8")     # built in pieces so this file does not match itself
for dp, _dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith((".md", ".py", ".json", ".txt")):
            fp = os.path.join(dp, f)
            if os.path.relpath(fp, ROOT).replace(os.sep, "/").startswith(("toon-studio/node_modules", "research/")):
                continue
            try:
                tx = open(fp, encoding="utf-8-sig").read()
            except Exception:
                continue
            for s in STALE:
                if s in tx:
                    bad.append(f"{os.path.relpath(fp, ROOT)}: stale reference '{s}' (the script rulebook is story-explainer-scripts)")


def run(cmd, label, ok=(0,)):
    r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True)
    if r.returncode not in ok:
        bad.append(f"{label}: exit {r.returncode} " + (r.stdout + r.stderr)[-300:])
    return r


sm = os.path.join(sd, "scene-mapping")
if os.path.isdir(sm):
    run([os.path.join(sm, "scripts", "validate_map.py"), os.path.join(sm, "examples", "albert_alexander.json")], "scene-mapping validator on its example")
t = tempfile.mkdtemp()
cl = {"project": {"name": "t", "fps": 30, "width": 1920, "height": 1080}, "voiceover": {"file": "v.wav", "duration": 7.0}, "sections": [{"id": "S01", "name": "THE COLD STREET", "role": "hook", "start": 0, "end": 7.0}],
      "clauses": [{"id": "C001", "section": "S01", "start": 0.0, "end": 3.5, "dur": 3.5, "text": "a b c"}, {"id": "C002", "section": "S01", "start": 3.5, "end": 7.0, "dur": 3.5, "text": "d e f"}]}
sm_ = {"meta": {"title": "t", "fps": 24, "producer": "three_toon"}, "shots": [{"id": "S001", "start": 0, "end": 3.5, "scene_type": "character_action", "camera_move": "push_in", "literal": "A doctor walks through a winter street", "overlay_text": "Hi", "ambient_audio": "wind"},
                                                    {"id": "S002", "start": 3.5, "end": 7.0, "scene_type": "environment", "camera_move": "whip_pan", "literal": "The street at night", "transition_out": {"type": "match_cut", "out_frame": "a", "in_frame": "b", "bridge": "c"}}]}
json.dump(cl, open(os.path.join(t, "c.json"), "w")); json.dump(sm_, open(os.path.join(t, "m.json"), "w"))
r = run([os.path.join(H, "scene_map_to_toon.py"), "--scene-map", os.path.join(t, "m.json"), "--clauses", os.path.join(t, "c.json"), "--out", os.path.join(t, "w", "toon_project.json")], "3D bridge smoke run")
if r.returncode == 0:
    pj = json.load(open(os.path.join(t, "w", "toon_project.json")))
    sc = pj["scenes"]
    if len(sc) != 1 or len(sc[0]["shots"]) != 2 or sc[0]["shots"][0]["type"] != "crane" or sc[0]["shots"][1]["type"] != "orbit" or len(sc[0]["captions"]) != 1 or abs(sc[0]["duration"] - 7.0) > 1e-6:
        bad.append("3D bridge output not as specified (one scene, one shot per clause, push_in -> crane, whip_pan -> orbit, one caption, 7.0 s)")
    # a stem must not match inside another word: 'winter' is not 'win' -> dance
    if "dance" in json.dumps(pj["scenes"][0]["actors"][0]["timeline"]):
        bad.append("3D bridge matched an action keyword inside another word")
    qj = os.path.join(t, "w", "toon_plan.json")
    r2 = run([os.path.join(H, "toon_qa.py"), "gate1", "--project", os.path.join(t, "w", "toon_project.json"), "--plan", qj, "--clauses", os.path.join(t, "c.json"), "--scene-map", os.path.join(t, "m.json"), "--out", os.path.join(t, "g1.md")], "toon_qa gate1 runs", ok=(0, 1))
    g1 = open(os.path.join(t, "g1.md"), encoding="utf-8").read() if os.path.exists(os.path.join(t, "g1.md")) else ""
    for must in ("G1-01", "G1-02", "G1-07"):
        if not re.search(r"\|\s*" + must + r"\s*\|[^|]*\|\s*\*\*PASS\*\*", g1):
            bad.append(f"toon_qa gate1 {must} did not PASS on the aligned sample")
# open library: a missing prop is reported as a gap; making it (a JSON file in library/assets) closes the gap and embeds it; bad assets are refused
import shutil
tl = os.path.join(t, "lib"); shutil.copytree(os.path.join(ROOT, "library"), tl, ignore=shutil.ignore_patterns("previews"))
sm_gap = json.loads(json.dumps(sm_)); sm_gap["shots"][0]["props"] = ["zeppelin dock"]; json.dump(sm_gap, open(os.path.join(t, "mg.json"), "w"))
gp = os.path.join(t, "gaps.json")
run([os.path.join(H, "scene_map_to_toon.py"), "--scene-map", os.path.join(t, "mg.json"), "--clauses", os.path.join(t, "c.json"), "--out", os.path.join(t, "wg", "toon_project.json"), "--library", tl, "--gaps", gp], "bridge with a missing prop")
G = json.load(open(gp)) if os.path.exists(gp) else {"gaps": []}
if not any(g["kind"] == "prop" and "zeppelin" in g["name"] and g["status"] == "open" for g in G["gaps"]):
    bad.append("bridge did not report the missing prop 'zeppelin dock' as an open asset gap")
newp = {"id": "PRP_zeppelin_dock", "kind": "prop", "name": "zeppelin dock", "description": "mast and platform", "keywords": ["zeppelin dock", "airship mast"],
        "place": {"mode": "at", "at": {"u": 0.2, "side": 1, "d": 8}}, "parts": [{"shape": "cyl", "color": "#888888", "pos": [0, 3, 0], "scale": [0.2, 6, 0.2]}, {"shape": "box", "color": "#aa7744", "pos": [0, 0.2, 0], "scale": [2, 0.4, 2]}]}
os.makedirs(os.path.join(tl, "assets", "props"), exist_ok=True)
json.dump(newp, open(os.path.join(tl, "assets", "props", "zeppelin_dock.json"), "w"))
run([os.path.join(H, "scene_map_to_toon.py"), "--scene-map", os.path.join(t, "mg.json"), "--clauses", os.path.join(t, "c.json"), "--out", os.path.join(t, "wg", "toon_project.json"), "--library", tl, "--gaps", gp], "bridge with the prop made")
G = json.load(open(gp)); pj2 = json.load(open(os.path.join(t, "wg", "toon_project.json")))
if any(g["status"] == "open" for g in G["gaps"] if "zeppelin" in g["name"]) or "PRP_zeppelin_dock" not in pj2.get("assets", {}).get("props", {}):
    bad.append("a made prop did not close its gap / was not embedded in the project")
import importlib.util
spec = importlib.util.spec_from_file_location("asset_catalog", os.path.join(H, "asset_catalog.py")); AC_ = importlib.util.module_from_spec(spec); spec.loader.exec_module(AC_)
if not AC_.validate_asset({"id": "PRP_bad", "kind": "prop", "name": "bad", "description": "x", "keywords": ["x"], "parts": [{"shape": "teapot", "color": "red"}]}, AC_.load()):
    bad.append("asset validator accepted an unknown shape and a colour that is not #rrggbb")
if AC_.validate_asset(newp, AC_.load()):
    bad.append("asset validator rejected a valid prop: " + str(AC_.validate_asset(newp, AC_.load())))
run([os.path.join(H, "asset_catalog.py"), "validate"], "all grown assets in library/assets are valid")
sm_["shots"].pop(); json.dump(sm_, open(os.path.join(t, "m2.json"), "w"))
run([os.path.join(H, "scene_map_to_toon.py"), "--scene-map", os.path.join(t, "m2.json"), "--clauses", os.path.join(t, "c.json"), "--out", os.path.join(t, "s2.json")], "3D bridge must refuse a misaligned map", ok=(2,))
run([os.path.join(H, "thumbnail_icons.py"), "validate"], "thumbnail icon library is valid")
for need in ("assets/fonts/Inter-Black.otf", "library/thumbnail-icons/bolt.json", "library/thumbnail-icons/skull.json", "agents/thumbnail-reader.md"):
    if not os.path.exists(os.path.join(ROOT, need)):
        bad.append(f"{need} is missing (thumbnail renderer needs it)")
run([os.path.join(H, "asset_catalog.py"), "check"], "3D asset catalogue vs toon-studio engine")
for need in ("cli.mjs", "package.json", "src/engine.mjs", "src/world.mjs", "src/characters.mjs", "src/scene.mjs", "src/render-chunk.mjs", "src/project.mjs", "src/autogen.mjs", "examples/showreel.json"):
    if not os.path.exists(os.path.join(ROOT, "toon-studio", need)):
        bad.append(f"toon-studio/{need} is missing (the 3D engine)")
if os.path.exists(os.path.join(ROOT, "toon-studio", "node_modules")):
    pass                                                 # installed copy of the engine is fine locally; finish_project never ships it
open(os.path.join(t, "s.md"), "w").write("## Script\n" + ("The story begins in a small town where nothing ever happened. " * 3) + "[ARCHIVE CLIP: x]\n")
run([os.path.join(H, "clean_voiceover_script.py"), "--script", os.path.join(t, "s.md"), "--out", os.path.join(t, "o.txt")], "voiceover script cleaner")
run([os.path.join(H, "problem_log.py"), "add", "--log", os.path.join(t, "p.jsonl"), "--stage", "env", "--symptom", "x"], "problem_log")
# packaging test: outlier store -> thumbnail renderer -> blind feed -> verdict (all with real images, in a temp folder)
if not os.path.isdir(os.path.join(ROOT, "research", "outliers")):
    bad.append("research/outliers/ (the saved outlier research store) is missing")
try:
    from PIL import Image
    pk = os.path.join(t, "pk"); os.makedirs(os.path.join(pk, "th"))
    outs = []
    for i in range(1, 6):
        outs.append({"title": f"Outlier title {i}", "views": ["12K", "30K", "45K", "250K", "1.2M"][i - 1], "url": f"https://youtu.be/abcdefghi{i:02d}"})
        Image.new("RGB", (640, 360), (i * 40, 60, 90)).save(os.path.join(pk, "th", f"abcdefghi{i:02d}.png"))
    json.dump(outs, open(os.path.join(pk, "o.json"), "w"))
    OS = os.path.join(H, "outlier_store.py"); BF = os.path.join(H, "build_feed.py")
    run([OS, "save", "--store", os.path.join(pk, "rs"), "--keyword", "kw", "--outliers", os.path.join(pk, "o.json"), "--thumbs-dir", os.path.join(pk, "th")], "outlier_store save")
    run([OS, "merge", "--store", os.path.join(pk, "rs"), "--out", os.path.join(pk, "m.json"), "--require-images"], "outlier_store merge with images")
    run([OS, "merge", "--store", os.path.join(pk, "none"), "--out", os.path.join(pk, "m0.json")], "outlier_store merge must refuse when nothing is active", ok=(2,))
    shot = os.path.join(pk, "thumb.png")
    run([os.path.join(H, "make_thumbnail.py"), "--scene", os.path.join(sd, "thumbnail-making", "examples", "example_scene.json"), "--out", shot], "make_thumbnail on the example scene")
    json.dump({"title": "Candidate title", "text": "ONE BOLT?", "image": shot}, open(os.path.join(pk, "c.json"), "w"))
    json.dump({"title": "Candidate title", "text": "ONE BOLT?"}, open(os.path.join(pk, "c_noimg.json"), "w"))
    run([BF, "build", "--outliers", os.path.join(pk, "m.json"), "--card", os.path.join(pk, "c_noimg.json"), "--feeds-root", os.path.join(pk, "f"), "--key", os.path.join(pk, "k0.json")], "build_feed must refuse a card without an image", ok=(2,))
    run([BF, "build", "--outliers", os.path.join(pk, "m.json"), "--card", os.path.join(pk, "c.json"), "--feeds-root", os.path.join(pk, "f"), "--key", os.path.join(pk, "k1.json"), "--min-decoys", "4"], "build_feed must refuse without enough sub-50k decoys (view bias)", ok=(2,))
    r = run([BF, "build", "--outliers", os.path.join(pk, "m.json"), "--card", os.path.join(pk, "c.json"), "--feeds-root", os.path.join(pk, "f"), "--key", os.path.join(pk, "k.json")], "build_feed with real images")
    if r.returncode == 0:
        k = json.load(open(os.path.join(pk, "k.json")))
        if k["mode"] != "images" or k["candidate_position"] < 4 or k["n_cards"] != 6:
            bad.append("build_feed key not as specified (images mode, candidate never in the first 3, all outliers + candidate)")
        feed = open(os.path.join(k["feed_folder"], "feed.md"), encoding="utf-8").read()
        if re.search(r"(?i)youtu|abcdefghi|\\.png|thumb\\.", feed) or len(re.findall(r"\*\*Views:\*\*", feed)) != 6:
            bad.append("feed.md leaks metadata, source file names or the candidate's file name")
        open(os.path.join(pk, "v.md"), "w").write(f"**VERDICT: CLICK card {k['candidate_position']:02d}**\n**PULL: REAL**\n**Thumb-stoppers:** card {k['candidate_position']:02d}\n")
        run([BF, "verdict", "--key", os.path.join(pk, "k.json"), "--verdict", os.path.join(pk, "v.md")], "build_feed verdict parses a pass")
except ImportError:
    bad.append("Pillow is not installed (thumbnail renderer, feed builder and outlier store need it)")
# psychology wiring: the viewer-psychology rules must be reachable from every piece that makes or judges a thumbnail, and the gate must work
PSY = "skills/extreme-thumbnails/references/viewer-psychology.md"
if not os.path.exists(os.path.join(ROOT, PSY)):
    bad.append(PSY + " is missing")
else:
    for f_ in ("agents/master-packager.md", "agents/thumbnail-maker.md", "skills/extreme-thumbnails/SKILL.md", "skills/thumbnail-making/SKILL.md", "skills/packaging-cycle/SKILL.md"):
        if "viewer-psychology" not in open(os.path.join(ROOT, f_), encoding="utf-8-sig").read():
            bad.append(f_ + " does not point to viewer-psychology.md (the psychology would sit unused)")
    pc_ = open(os.path.join(ROOT, "skills", "packaging-cycle", "SKILL.md"), encoding="utf-8-sig").read()
    if pc_.count("check_scorecard.py") < 3:
        bad.append("packaging-cycle must run check_scorecard.py (scorecard gate in round 1 and round N, and the debrief gate)")
    lv_ = open(os.path.join(ROOT, "agents", "packaging-lazy-viewer.md"), encoding="utf-8-sig").read()
    for k_ in ("C1", "C2", "C3", "C4", "C5", "C6", "VERDICT: CLICK", "PULL:"):
        if k_ not in lv_:
            bad.append(f"agents/packaging-lazy-viewer.md lacks '{k_}' (the debrief must label defects C1-C6 and the verdict must parse)")
    ref_ = open(os.path.join(ROOT, PSY), encoding="utf-8-sig").read()
    for k_ in ("C1.", "C2.", "C3.", "C4.", "C5.", "C6."):
        if k_ not in ref_:
            bad.append(f"viewer-psychology.md lacks the {k_[:-1]} section")
    good_ = ("Concept: a bolt beside a cracked clock face\nHalf A: a hex bolt and a cracked clock   Half B: a broad claim about one small thing   The join: which bolt and why it failed\n"
             "C1 contrast: STRONG - the bolt is the only bright warm object on a dark cold field unlike the outliers\n"
             "C2 least context: OK - only the bolt and the crack remain so the answer cannot be guessed from the picture\n"
             "C3 two halves: STRONG - the picture shows a part and the title the claim and neither is complete alone\n"
             "C4 familiar entity: none, not needed\n"
             "C5 understandable: OK - one bolt and one clock named correctly by a stranger at phone size in a glance\n"
             "C6 underdog: STRONG - beats the biggest outlier on contrast and the second outlier on question strength\n"
             "Verdict: KEEP\nContrast plan: bolt. Context list: bolt, crack. Glance sentence: a bolt by a clock. Underdog: outlier 4.\n")
    open(os.path.join(t, "sc_good.md"), "w").write(good_)
    open(os.path.join(t, "sc_bad.md"), "w").write(good_.replace("C2 least context: OK", "C2 least context: FAIL"))
    open(os.path.join(t, "sc_nospec.md"), "w").write(good_.split("Contrast plan")[0])
    open(os.path.join(t, "db_good.md"), "w").write("Defects: C2 the answer can be guessed\n")
    open(os.path.join(t, "db_bad.md"), "w").write("Defects: it felt weak\n")
    CS = os.path.join(H, "check_scorecard.py")
    run([CS, "scorecard", "--file", os.path.join(t, "sc_good.md")], "psychology gate passes a complete scorecard")
    run([CS, "scorecard", "--file", os.path.join(t, "sc_bad.md")], "psychology gate must refuse a KEEP with a FAIL on C2", ok=(1,))
    run([CS, "scorecard", "--file", os.path.join(t, "sc_nospec.md")], "psychology gate must refuse a brief without the psychological spec", ok=(1,))
    run([CS, "scorecard", "--file", os.path.join(t, "sc_good.md"), "--expect", "3"], "psychology gate must refuse fewer KEEP blocks than expected", ok=(1,))
    run([CS, "debrief", "--file", os.path.join(t, "db_good.md")], "debrief gate passes a labelled debrief")
    run([CS, "debrief", "--file", os.path.join(t, "db_bad.md")], "debrief gate must refuse an unlabelled debrief", ok=(1,))
# 7. wiring: every skill, agent and command must have a job in the master's wiring map
mt = open(os.path.join(sd, "story-video-master", "SKILL.md"), encoding="utf-8-sig").read()
parts = mt.split("## Wiring map", 1)
if len(parts) < 2:
    bad.append("story-video-master/SKILL.md has no '## Wiring map' section")
else:
    wm = parts[1].split("\n## ", 1)[0]
    for s_ in skills:
        if f"`{s_}`" not in wm:
            bad.append(f"skill '{s_}' is not in the wiring map of story-video-master (every skill needs a job)")
    for a_ in agents:
        if f"`{PN}:{a_}`" not in wm:
            bad.append(f"agent '{a_}' is not in the wiring map of story-video-master")
    if os.path.isdir(cd):
        for f_ in sorted(os.listdir(cd)):
            if f_.endswith(".md") and f"/{f_[:-3]}`" not in wm:
                bad.append(f"command '/{f_[:-3]}' is not in the wiring map of story-video-master")
# 8. removed or never-installed pieces must not be referenced by a skill, agent or command
for p_, base_ in docs:
    t_ = open(p_, encoding="utf-8-sig").read()
    for stale_ in ("prepare-voiceover", "story-video-pipeline", "video-pipeline/"):
        if stale_ in t_:
            bad.append(f"{os.path.relpath(p_, ROOT)}: refers to '{stale_}', which is not part of this plugin")
if bad:
    print("MASTER SELFTEST FAIL"); sys.stderr.write("\n".join(bad) + "\n"); sys.exit(1)
print("master selftest ok")
