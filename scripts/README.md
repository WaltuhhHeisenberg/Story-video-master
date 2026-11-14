# scripts/

Python 3.9+, `numpy`, `pillow`, ffmpeg/ffprobe on PATH; Node 18+ for the 3D render (`toon-studio/`).

## Run B (voiceover -> 3D video)
| Script | Use |
|---|---|
| `run_toon.py --project DIR --audio vo.mp3 [--transcript t.csv] --stage prepare|bridge|gate1|stills|render|gate2|all [--preview]` | one command for the mechanical stages; logs every command in `reports/pipeline_log.json`; the render is resumable |
| `transcribe.py` | Whisper word timestamps (`faster-whisper` or `openai-whisper`), or `--from-json` |
| `split_clauses.py` | speech-driven 3-4 s clauses -> `clauses.json` (dramatic pause > sentence end > beat > phrase > breath) |
| `mapping_tools.py sheet` | clause sheet to write the scene map against |
| `scene_map_to_toon.py` | scene map + clauses -> `toon_project.json` + `toon_plan.json` (sections -> worlds, clauses -> camera shots, overlay_text -> captions); refuses a misaligned map (exit 2) |
| `toon_qa.py gate1 / gate2` | computed gates with evidence (see `skills/toon-video-studio/references/gate-checklists.md`); every run kept as `## Run N` |
| `asset_catalog.py info / schema / validate / add / preview / reindex / check` | the OPEN 3D asset library: built-ins + grown assets in `library/assets/`; add validates and saves, preview renders one frame with the engine |
| `make_check_report.py` | the single check report (PASS / FAIL / NOT RUN) |
| `package_output.py --project DIR --out OUT` | delivery folder: video, srt, project, plan, reports, README_FIRST |

## Run A and shared
`clean_voiceover_script.py`, `outlier_store.py`, `build_feed.py`, `check_scorecard.py` (psychology gate: scorecard + debrief labels, run by packaging-cycle every round), `make_thumbnail.py` (realistic thumbnail renderer, packaging test), `thumbnail_icons.py` (the open icon library: info/find/validate/add/sheet/preview), `problem_log.py`, `vo_common.py`.

## Plugin self-improvement
`finish_project.py` (collect problems, require lessons, self-test, bump version, ship `.plugin`), `selftest.py`, `master_selftest.py`.

## Direct engine use
`node toon-studio/cli.mjs generate|render|still|estimate` (see `toon-studio/README.md`; `render` also takes `--burn` / `--no-burn` for captions).
