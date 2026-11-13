# story-video-master (v2.2.0)

One plugin for the whole story-channel video workflow. Since v2.0.0 the video is a **3D animation rendered with three.js** (the toon studio in `toon-studio/`); CapCut is gone.

| Part | Lives in |
|---|---|
| Idea system, thumbnails, packaging cycle, packaging + script agents | `skills/story-video-idea-system`, `extreme-thumbnails`, `thumbnail-making`, `packaging-cycle`; `agents/`; `commands/` |
| Script writing and retention | `skills/story-explainer-scripts`, `voiceover-ready-script` |
| Clauses, scene mapping | `skills/split-clauses`, `skills/scene-mapping` (logic unchanged; only its input/output format knows the producer `three_toon`) |
| **3D video (new)** | `toon-studio/` (engine), `skills/toon-video-studio`, `scene-map-to-toon`, `build-toon-project`, `qa-toon-project`, `perfect-editor`; `agents/toon-qa-reviewer.md`; `scripts/run_toon.py`, `scene_map_to_toon.py`, `toon_qa.py`, `asset_catalog.py` |
| **3D asset library (open, growing; replaces the 2D PNG library)** | `library/library.json` (built-ins + mapping rules) and `library/assets/` (worlds, objects, character looks that Claude makes as JSON; `skills/make-3d-assets`) |
| Orchestrator and self-improvement | `skills/story-video-master`, `skills/master-autofix` |

## Flow
**Run A** (input: nothing or a keyword): 1 Idea -> 2 Packaging -> 3 Script (write, retention loop, clean) -> **STOP**: `04-voiceover-script.txt`.
**Run B** (input: voiceover + word-level transcript + this plugin): 4 Clauses -> 5 Scene map (one shot per clause, producer `three_toon`) -> 6 Bridge to the 3D project, make the missing assets, Gate 1, stills, render, Gate 2 -> 7 Check report + video -> 8 Plugin autofix -> new `story-video-master.plugin`.
Every stage starts only from the previous stage's saved file, as if it were a new chat.

## The asset library grows
The bridge lists everything the scene map names (characters, objects, backgrounds) that the library lacks (`work/asset_gaps.json`). Claude makes those assets (worlds, objects built from primitives, character looks) as JSON files in `library/assets/`, previews them with the real engine, and re-runs the bridge; the render is blocked (Gate 1 G1-13) while a gap is open. Every asset stays for the next video and travels inside the returned `.plugin`.

## How the 3D video is made
Each story **section** becomes one 3D world (theme day / sunset / night / snow / desert chosen from the shots' words), each **clause** becomes exactly one **camera shot** on its times, the hero stickman's action comes from the shot's verbs, `overlay_text` becomes a burned-in caption (+ `.srt`), the voiceover is muxed as delivered. Output: `video.mp4`, `video.srt`, an editable `toon_project.json`, gate reports, a contact sheet.
Requirements: Node 18+, ffmpeg, Xvfb (Linux); `npm install` runs automatically in `toon-studio/` on the first render. Render speed is about 0.1-0.16 s per frame per core (`node toon-studio/cli.mjs estimate`); renders are parallel and resumable.

## Thumbnails (detailed, not flat)
`scripts/make_thumbnail.py` renders a 1280x720 anti-aliased, lit illustration: gradients, bevel, soft shadows, glow, spotlights, real fonts (`assets/fonts`, Inter Black, SIL OFL), vignette/bloom/grain, from a growing library of shaded icons (`library/thumbnail-icons/`, `scripts/thumbnail_icons.py`; sheet: `_sheet.png`). The agent `thumbnail-reader` is a blind recognition test: it sees only the PNG and must name every object and the story; misses go back to the maker (max 3 loops) before any viewer sees the card. A cheap 3D-rendered background from the studio is optional (mood only, dimmed/blurred).

## Packaging test and saved research
Unchanged: `research/outliers/<batch>/` stores outlier titles, view counts and real thumbnails (`research/README.md`, `scripts/outlier_store.py`); Stage 2 hides the candidate thumbnail in a blind feed (`scripts/build_feed.py`).

## Self-check
`python scripts/selftest.py` compiles every script, checks every agent/skill/file reference and the wiring map, runs the scene-map validator on its example, the 3D bridge, the 3D gates, the asset catalogue against the engine files, the cleaner and the packaging test. `finish_project.py` refuses to ship a plugin that fails it.

## Honest limits
The studio makes picture and captions only (no music, SFX, ambient sound; they are listed in the bridge report). One rig (stickman) with grown looks and accessories, worlds and objects made of primitives only, five built-in actions, no imported models, no lip-sync. Gate rows needing judgement stay MANUAL until a human verdict is recorded. The lazy viewers are simulations. The thumbnail is the only image the plugin draws itself (`thumbnail-maker`). Earlier READMEs are kept as `README.script-retention.md` and `README.story-video-studio.md` (older plugin names). Retired CapCut history: `skills/story-video-master/references/known-issues-master.md`.
