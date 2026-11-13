---
name: story-video-master
description: Run the whole story-channel video workflow with one plugin - idea (keyword) -> packaging (title + thumbnail) -> script (written, retention-tested, cleaned) -> STOP with a clean voiceover-ready script -> then, with the user's voiceover and word-level transcript, clauses -> scene mapping -> 3D video rendered with three.js (toon studio) + check report -> plugin autofix that returns the improved plugin. Use for "make a whole video", "idea to 3D video", "run the master plugin", "start a new video", "I have the voiceover and transcript, build the project", or when the user hands over a keyword (or nothing) and wants the pipeline.
---

# Story Video Master

Two runs with one stop between them. Every stage works **as if it were run in its own fresh chat**.

```
RUN A (input: nothing | a keyword)                          RUN B (input: voiceover + transcript + this plugin)
 1 Idea -> 2 Packaging -> 3 Script (3a write, 3b retention,   4 Clauses -> 5 Scene map -> 6 Bridge + 3D render + Gates
 3c clean) ==> STOP: 04-voiceover-script.txt                    -> 7 Check report + 3D video -> 8 Plugin autofix -> new .plugin
```

Outputs: the **3D video** (`video.mp4` + `.srt` + editable `toon_project.json` + reports) and **`check_report.md`**. Final: the **autofixed plugin** (`story-video-master.plugin`) - install it, and it is the plugin input of the next run.

## Rules for every stage (the "separate chats" rule)
1. **Start from the handoff file only.** A stage reads the file(s) the previous stage saved, plus this plugin's rules. It does not use the previous stage's reasoning, drafts, rejected options, tone or chat history. In one session, say "Stage N starts from <file>" and re-read that file instead of relying on memory. For hard isolation the user can run each stage in a new chat with the same files (stage skills are self-contained).
2. **Run the real process.** Follow the stage skill in full (minimums, rounds, kill tests, gates). Never fabricate search data, agent verdicts, rounds, gate results or "I ran it". If something cannot run (no search, no ffmpeg, no network), say so in that stage's output and log it.
3. **One clean deliverable per stage**, saved to a file. Working notes stay out of it.
4. **Finish a stage before the next.** No stage starts until the previous deliverable exists and its own checks pass.
5. **Log every problem** the moment it happens (`python scripts/problem_log.py add --log <run>/reports/master_problems.jsonl --stage <stage> --symptom "..."`): failed check, non-zero exit, missing file / agent / path, hand workaround, reviewer finding, user complaint. Fixed-by-hand problems are logged too. This log is what the autofix learns from.
6. **Nothing is removed from the plugin** by a run except through the autofix rules (`master-autofix` skill), and removals there need the user's yes.

## Step 0 - Start of every run
- Read `references/known-issues-master.md` and `references/lessons-master.json` if present (this plugin's own lessons, written by earlier autofixes), and `skills/toon-video-studio/references/known-issues.md` (the 3D engine's own). Apply them before starting; do not repeat a known problem.
- Create the run folder `story-video-run/<video-slug>/` (Run B: reuse Run A's folder if it exists) with `reports/` and `research/outliers/` inside. `research/outliers/` is the **run store** for outlier research (batch layout, the plugin store and the 14-day keyword window, the 60-day outlier window and 1-year retention: `research/README.md`).
- Run A asks **one** short message of intake: keyword/topic or nothing, and whether to include outlier research (default no). Run B asks one message for everything missing: voiceover file and word-level transcript (nothing else: the 3D studio draws every picture itself from the scene map). If the user answered, do not ask again.

---
# RUN A
## Stage 1 - Idea  (fresh chat; input: nothing | keyword)
Follow `skills/story-video-idea-system` completely (compulsory keyword research, story-type match, off-context titles, thumbnail concepts per `skills/extreme-thumbnails`, story spine; no hook is written at this stage).
- **Nothing given:** do not ask for a topic. Build the candidate pool from the channel's area (history, science, invention told as human drama), research real demand, rank, and pick by the skill's rule; show the ranked table and say plainly when evidence is only proxies.
- If the stage does outlier research, save it as a batch in the run store (`story-video-run/<video-slug>/research/outliers/<batch>/`: titles, view counts, REAL thumbnail images, keyword and outlier analysis) with `scripts/outlier_store.py`; any active batch already in the plugin's `research/outliers/` is compulsory.
- Output `01-video-brief.md`. Handoff: that file, plus the outlier batch in the run store.

## Stage 2 - Packaging  (fresh chat; input: `01-video-brief.md` + the saved outlier data: the run store `story-video-run/<video-slug>/research/outliers/` and the plugin's `research/outliers/`)
Follow `skills/packaging-cycle` completely (candidate hidden in a blind feed with the full outlier data, viewer never told which card is the candidate and must click one; min 3, max 8 rounds, pass = two consecutive real-pull clicks on the candidate, a fresh viewer and fresh shuffle every round, final pass on the 2 variants) with agents `story-video-master:master-packager`, `story-video-master:thumbnail-maker` (builds the real thumbnail image of every card per `skills/thumbnail-making/SKILL.md`), `story-video-master:thumbnail-reader` (blind recognition test of every thumbnail before any viewer sees it) and `story-video-master:packaging-lazy-viewer`. The blind feed is real images only: every outlier needs its thumbnail in `thumbs/`.
- Output `02-packaging.md`. Handoff: keyword + story from the brief, the winning title and thumbnail text. Nothing from the rounds.

## Stage 3 - Script  (fresh chat; input: handoff above + the brief's story spine)
**3a Write.** Follow `skills/story-explainer-scripts` (intake -> fact ledger -> story engine -> beat map -> sentence-by-sentence draft -> audit). The promise is the winning title. The hook is written here and only here, exactly by the hook rules of that skill (its hooks reference: three options, pick one); the brief contains no hook. Never invent dialogue, numbers or motives; every number traces to the ledger. Save `03-script.md` (with its ledger, beat map, notes).
**3b Retention loop** (logic of `commands/retention-loop.md`, max 3 rounds, stop on pass or stall): `story-video-master:script-lazy-viewer` listens (gets only the current script + winning title/thumbnail text); `story-video-master:script-writing-teacher` fixes and saves `.revised.md`. Both follow `skills/story-explainer-scripts/SKILL.md` (its hook rules, sentence shapes and audit flags); the viewer scores the script against its eight named checks and the teacher fixes by its audit flags. Facts that the teacher cannot verify stay marked `[VERIFY]`. The fixes must not break the fact ledger: re-check every changed number against it.
**3c Voiceover-ready script.** Follow `skills/voiceover-ready-script`: resolve every `[VERIFY]` (search, or ask the user), then run `python scripts/clean_voiceover_script.py --script <final script> --out 04-voiceover-script.txt --report reports/voiceover_script_report.md`. Show the user the clean script, word count, runtime and the read-aloud risks.

## ===> STOP (end of Run A)
Deliver: `04-voiceover-script.txt` (plain narration only, ready to record), the winning title/thumbnail, the retention result, open items. Tell the user exactly what Run B needs: **the voiceover audio, its word-level transcript, and (if changed) this plugin** - nothing else, the 3D studio draws every picture. Do not continue until the user returns with them.

---
# RUN B
## Stage 4 - Clauses  (fresh chat; input: voiceover + transcript)
Write `intake_report.md` first, saved in the run folder (Gate 1 row G1-11 and Gate 2 row G2-09 look in the run, `reports/`, `work/` and `toon/`) (Gate 0, `skills/split-clauses/references/intake-checklist.md`). Use the voiceover and transcript **exactly as delivered** (no cleaning, no retiming). `python scripts/run_toon.py --project <run> --audio <voiceover> --transcript <words> --name "<title>" --stage prepare` (skill `split-clauses`). Output `work/clauses.json`, `reports/clause_sheet.md`.

**Sections (G1-05).** Auto-named sections (S01, S02 ...) fail Gate 1. After `--stage prepare`, write `work/sections.json` with real names (what each part is about, e.g. "THE SCALPEL CLUE") and `auto` false, and run prepare again with `--sections work/sections.json`. Each section becomes one 3D world.
**No voiceover yet.** If the voiceover is not delivered yet, build without `--audio` for the render (the video is silent; Gate 1 G1-08 is NOT RUN) and say so in the intake report (I2 MISSING-OPTIONAL) and in the delivery; the clauses still come from the transcript.
**Clauses over 4.0 s.** The bridge places the caption of a clause over 4.0 s mid-clause so the gap between visible changes stays short; the camera changes at every clause anyway.

## Stage 5 - Scene map  (fresh chat; input: `clauses.json` only)
Follow `skills/scene-mapping` (full map mode) **on the clauses**: narration with timing = clause text and times; **exactly one shot per clause, shot start/end = clause start/end** (this is what lets the bridge apply the map without guessing). **Producer = `three_toon`** (do not ask): write every `literal` and `camera_move` in the words the 3D studio understands (`skills/toon-video-studio/references/scene-to-3d-rules.md`: world by time and place, one verb for the stickman actor, `camera_move` from the studio's list, numbers and names in `overlay_text`). Validate with `validate_map.py` and save its output to `reports/scene_map_validation.txt`; fix every error; for each warning fix it or state why it stays (the fixed 3-4 s clause lengths make the "shot lengths too even" warning expected). Save `05-scene-map.json` and the exports.

## Stage 6 - Bridge, 3D render, gates  (fresh chat; input: `05-scene-map.json`, `clauses.json`, voiceover)
Follow `skills/scene-map-to-toon`, then `skills/build-toon-project` (**Gate 1 must be all PASS before any render**; stills first), then `skills/qa-toon-project` (**Gate 2 all PASS**, manual rows only with a recorded verdict). The 3D part stays editing-only: it applies the map exactly and never adds, swaps or "improves" a shot. The studio makes picture and captions only; the voiceover is muxed as delivered; music, SFX and ambient sound are not produced (the bridge report lists them) - say so in the delivery.
- **Assets (`skills/make-3d-assets`).** The library is open and grows. After the bridge, every character, object (`props`, `new_assets`) and world (`background`) the scene map names that the library lacks is listed in `work/asset_gaps.json`; **you make them** (JSON assets, validated, previewed, saved into `library/assets/`) and run the bridge again. Gate 1 G1-13 fails while a gap is open; only the user may accept a gap (default look).
- **Editor habits (`skills/perfect-editor`).** Load it at the start of Stage 6 and apply its Passes 1-4 (timing, rhythm, themes and actions, captions) to the bridge report and plan before the render; apply its Pass 5 (technical) together with Gate 2. It checks and reports; it never swaps, adds or drops a shot.
- **Render time.** Quote `node toon-studio/cli.mjs estimate` before a full render; render a `--preview` draft first for anything long; run long renders detached (they are resumable).
- **Independent review (`story-video-master:toon-qa-reviewer`).** After Gate 2 is all PASS, launch a fresh reviewer with only the output folder and `skills/toon-video-studio/references/qa-checklist.md` (never your reasoning). Log every finding with `problem_log.py` (stage `qa`) and fix or report it before Stage 7.

## Stage 7 - Check report and delivery
`python scripts/make_check_report.py --run <run> --out <run>/check_report.md`, then `python scripts/package_output.py --project <run> --out <run>/delivery`. Deliver `video.mp4` + `video.srt` + `toon_project.json` + `check_report.md` + `reports/contact_sheet.png`. State plainly what is verified (computed gates) and what is not (manual rows, story reading, no music/SFX). Every check row must show PASS; NOT RUN is reported as NOT RUN; a preview-only render is called a preview.

## Stage 8 - Plugin autofix (mandatory, last)
Follow `skills/master-autofix`: collect every problem of the whole run (Run A + Run B), patch the plugin so it cannot repeat, self-test, bump the version, and return the new `story-video-master.plugin`. The shipment also copies the run's outlier research (`research/outliers/<batch>/`, with its thumbnails) into the plugin's `research/outliers/` and deletes only batches older than 1 year.

## Wiring map - every skill, agent and command has a job
`scripts/master_selftest.py` fails if a skill, agent or command is missing from this map. Add new pieces here when you add them.

| Skill | Job | Stage | Command |
|---|---|---|---|
| `story-video-master` | orchestrator, the two runs and the separate-chats rule | all | `/make-video`, `/build-video` |
| `story-video-idea-system` | keyword research, story type, titles, thumbnail concepts, story spine | 1 | `/idea` |
| `extreme-thumbnails` | thumbnail standard used by the idea stage and by `story-video-master:master-packager` | 1, 2 | via `/idea`, `/packaging` |
| `packaging-cycle` | blind-feed packaging test, 3-8 rounds | 2 | `/packaging` |
| `thumbnail-making` | draws the real thumbnail image | 2 | via `/packaging` |
| `story-explainer-scripts` | script rulebook: write, audit, hook rules | 3a, 3b | `/write-script`, `/lazy-test`, `/fix-script`, `/retention-loop` |
| `voiceover-ready-script` | clean narration-only text, then STOP | 3c | `/voiceover-script` |
| `split-clauses` | 3-4 s speech-driven clauses, intake checklist | 4 | `/clauses` |
| `scene-mapping` | one shot per clause, validated; producer `three_toon` | 5 | `/scene-map` |
| `make-3d-assets` | makes the missing worlds, objects and character looks as JSON assets (the open, growing 3D library) | 6a-2 | `/make-assets` |
| `scene-map-to-toon` | bridge from scene map to the three.js project (sections -> worlds, clauses -> camera shots) | 6a | `/toon-build` |
| `build-toon-project` | Gate 1, stills, then the three.js render | 6b | `/toon-build` |
| `perfect-editor` | editing habits and review passes 1-5 | 6 | via `/toon-build`, `/toon-qa` |
| `qa-toon-project` | Gate 2 and the QA report | 6c | `/toon-qa` |
| `master-autofix` | collect problems, patch the plugin, ship it | 8 | `/plugin-autofix` |
| `toon-video-studio` | the 3D engine (`toon-studio/`) and reference library for Stages 5-7 (project schema, scene-to-3D rules, gates, QA checklist, editor craft, known issues); outside the flow it renders hand-made projects | 5-7 | none (library) |

| Agent | Job | Stage |
|---|---|---|
| `story-video-master:master-packager` | creates and fixes title + thumbnail | 2 |
| `story-video-master:thumbnail-maker` | builds the thumbnail PNG (detailed lit illustration from the icon library) | 2 |
| `story-video-master:thumbnail-reader` | blind recognition test: names what a stranger sees in the PNG | 2 |
| `story-video-master:packaging-lazy-viewer` | blind-feed viewer | 2 |
| `story-video-master:script-writing-teacher` | teaches and fixes the script | 3b |
| `story-video-master:script-lazy-viewer` | predicts the drop-off | 3b |
| `story-video-master:toon-qa-reviewer` | independent review of the rendered 3D video | 6c |

## Where things live
`skills/` (one folder per stage skill plus `toon-video-studio`), `agents/` (packaging + script agents, 3D QA reviewer), `commands/`, `scripts/` (run_toon, bridge, gates, asset catalogue, cleaner, problem log, check report, finish), `toon-studio/` (the three.js engine), `library/` (the OPEN 3D asset library: built-ins + `library/assets/` grown by Claude), `research/` (saved outlier research: titles, view counts, real thumbnails; `research/README.md`). File map and flow: `README.md`.
