---
name: master-autofix
description: Final stage of the story-video-master flow (Stage 8). Collects every problem met while making the output (all stages, both runs), changes the plugin so each one cannot repeat, self-tests it, and returns the new .plugin. Use at the end of every run, or when the user says "autofix the plugin", "fix the plugin from this run", "return the plugin".
---

# Plugin autofix (mandatory, after the 3D video and check report)

Goal: the problems of this run never happen again. The returned plugin is the plugin input of the next run.

## 1. Collect
List every problem of the whole run: `reports/master_problems.jsonl` (all stages), FAIL rows in every Gate 1 / Gate 2 run (not just the last), reviewer findings, failed commands, hand fixes, `[VERIFY]` that blocked, user complaints, anything not in the log yet (add it with `problem_log.py` now). Nothing is skipped because it was fixed by hand.

## 2. Fix in the plugin - in this order, the first that works
a. a **bridge / cleaner rule** (`scripts/scene_map_to_toon.py`, `scripts/clean_voiceover_script.py`, the mappings in `library/library.json`);
b. a **check** (`scripts/toon_qa.py`, `scripts/master_selftest.py`, or a stage check) so it is caught next time;
c. a fix in the **studio / clause scripts** (`toon-studio/`, `scripts/run_toon.py`, `scripts/split_clauses.py`);
d. a **rule** in the owning skill or agent file (idea, packaging, script, scene-mapping, voiceover-ready-script, 3D skills) and a row in `references/known-issues-master.md`;
e. only if none is possible: a `still_manual` note.

Rules: change the smallest thing; **never delete a skill, agent, command, script, reference or rule without asking the user first** (list the proposed removal and the reason, wait for yes); do not edit the user's rules (the script rulebook in `story-explainer-scripts`, retention/transition thresholds, editing rules) to make a check pass - fix the cause or ask.

## 3. Write `lessons.json`
List of `{"id","area","symptom","cause","fix","files":[...],"still_manual","prevention":"check|autofix|rule|none","covers":["M-script-1","G1-15",...]}`. `area`: idea | packaging | script | voiceover-script | scene-map | bridge | clauses | render | qa | env | plugin. Every problem id must appear in some lesson's `id` or `covers`. `files` must exist in the plugin (patch first).

## 4. Ship
`python scripts/finish_project.py --project-name "<video>" --work-dir <run folder> --lessons lessons.json --out <OUT>`
It collects the problems itself, requires a lesson for each, runs the self-test (a patch that breaks the plugin aborts the shipment), appends the lessons to the known-issues files, bumps the version, copies the run's outlier research (`<run folder>/research/outliers/<batch>/`, with its real thumbnails) into the plugin's `research/outliers/` and deletes only batches older than 1 year (keyword analysis valid 14 days, outlier analysis 60 days, then kept but not used as active), and writes `OUT/story-video-master.plugin` + `improvement_report.md`. Exit code 2 = unresolved items: fix and re-run.

## 5. Tell the user
New version, what was fixed (one line each), what stays manual, proposed removals (if any) waiting for their yes, and: install the returned `.plugin`; the installed copy may be read-only, so fixes only persist through the new file.
