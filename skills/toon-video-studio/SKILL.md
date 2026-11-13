---
name: toon-video-studio
description: The 3D video engine of the story-video-master plugin (Stages 5-7) - cartoon 3D worlds, stickman actors and camera shots made with three.js (toon-studio/), rendered headlessly to MP4 with the voiceover and burned-in captions. Use to render, preview, change or explain the 3D video, to check the render machine, or to read the project schema, gate checklists and known issues. Also use when the user asks for a 3D animated video, a three.js render, a stickman animation or a cartoon world outside the full flow.
---

# toon-video-studio

Engine: `toon-studio/` (package `three-toon-studio`, three.js 0.160 on software WebGL `headless-gl`, frames piped to ffmpeg, parallel chunked and **resumable** render). Its own README is kept at `toon-studio/README.md`. The 3D asset library is **open and growing**: built-ins in `library/library.json` plus every grown asset in `library/assets/` (worlds, objects, character looks as JSON; `python scripts/asset_catalog.py info`). Claude makes missing ones with `skills/make-3d-assets`.

## In the master flow
Stage 6 runs `scene-map-to-toon` (bridge) -> `build-toon-project` (Gate 1, stills, render) -> `qa-toon-project` (Gate 2). This skill is the reference library they read:
- `skills/make-3d-assets/SKILL.md` - how to make a world, object or character look
- `references/project-schema.md` - the project file and the limits of the studio
- `references/scene-to-3d-rules.md` - how the scene map is turned into worlds, actions and cameras
- `references/gate-checklists.md`, `references/qa-checklist.md` - Gate 1 / Gate 2 and the reviewer's list
- `references/editor-craft.md` - the five review passes (`perfect-editor` applies them)
- `references/known-issues.md`, `references/lessons.json` - what went wrong before

## Outside the flow (a project file by hand or generated)
1. **Environment**: `node -v`, `ffmpeg -version`, `which Xvfb`; `npm install` once in `toon-studio/` (`run_toon.py` does it when `node_modules` is missing). Linux needs Xvfb (the CLI starts it).
2. **Project**: write `toon_project.json` (start from `toon-studio/examples/showreel.json`) or `node toon-studio/cli.mjs generate --minutes N --seed S --out project.json` for an automatic multi-scene project of any length.
3. **Look before you render**: `node toon-studio/cli.mjs still project.json --t SEC --preview --out f.png`, view the PNG; fix camera clipping or empty frames in the JSON. Check one still per theme.
4. **Quote the time**: `node toon-studio/cli.mjs estimate project.json` (about 0.1-0.16 s per frame per core at 1280x720 with 1.5x supersampling; a 20 min video is 70-95 CPU-minutes).
5. **Render**: `node toon-studio/cli.mjs render project.json --out video.mp4 [--workers N] [--preview] [--burn|--no-burn]`. For more than about 3 minutes of render, run it detached `(nohup node cli.mjs render ... > log.txt 2>&1 &)` and poll the log; re-running the same command resumes.
6. **Deliver**: copy the mp4 (and .srt) to `/mnt/user-data/outputs/` and present it.

## Rules of thumb
- Keep `clearance` >= 9 so trees never sit where the camera passes.
- Speed levers: `"supersample": 1`, `--preview` for drafts, 24 fps, fewer trees (`density`), more cores.
- Voice-over and music are not generated: the voiceover is muxed as delivered (`"audio"` in the project); nothing else is added.
- Anything beyond the stickman + procedural world (imported models, lip-sync, a second character type) is out of scope for the studio; say so plainly.
