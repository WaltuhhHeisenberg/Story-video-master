# Known issues - 3D (three.js) video flow

Format: symptom -> cause -> what the plugin now does -> what is still manual. Lessons from runs are appended below by `finish_project.py`.
History of the retired CapCut flow: `skills/story-video-master/references/known-issues-master.md` (rows marked "CapCut era").

| # | Area | Symptom | Cause | Plugin does now | Still manual |
|---|---|---|---|---|---|
| T1 | env | render cannot start on a headless Linux box | headless-gl needs an X display | `toon-studio/cli.mjs` starts Xvfb itself; Gate 1 G1-10 checks node, ffmpeg, Xvfb, node_modules | install `xvfb ffmpeg` and run `npm install` in `toon-studio/` |
| T2 | render | a long video does not finish inside one tool call | tool calls time out (about 5 min) | `run_toon.py --stage render` is resumable (finished chunks are skipped); run it detached with `nohup` and poll `reports/render_log.txt` | none |
| T3 | bridge | wrong action from a word inside another word ("winter" -> win -> dance) | prefix keyword match | keywords match whole words plus s/es/ed/d/ing/ly only | none |
| T4 | scope | no music, SFX or ambient sound in the output | the studio makes picture and captions only | ambient rows are listed in `scene_map_bridge_report.md` and in the README_FIRST of the delivery; nothing is dropped silently | add sound in an audio editor |
| T5 | look | the library had only 5 worlds and one look | v1 of the studio was rigid | the library is OPEN: worlds, objects and character looks are JSON files in `library/assets/` that Claude makes (`make-3d-assets`); the bridge reports gaps and Gate 1 G1-13 blocks the render while one is open | new actions, new shapes and a second rig need engine code |
| T7 | assets | a grown asset is not used | its keywords do not occur in the shot text | the bridge matches `name` + `keywords` as whole words (plural/ed/ing endings allowed): copy the gap's own wording into `keywords` | none |
| T6 | gates | MANUAL rows could be mistaken for PASS | judgement items | MANUAL stays MANUAL until a verdict + evidence is recorded with `--manual` | the human look at the contact sheet |
