---
name: build-toon-project
description: Stage 6b of the story-video-master flow. Runs Gate 1 on the bridged 3D project, renders preview stills of every world, then renders the video with three.js (voiceover muxed, captions burned in) - resumable and parallel. Use after scene-map-to-toon when the 3D video must be rendered.
---

# Build the 3D video

Read `skills/toon-video-studio/SKILL.md` and `references/gate-checklists.md` first.

1. **Environment.** `python scripts/run_toon.py --project <run> --stage gate1` checks node, ffmpeg, Xvfb and the npm packages (G1-10); the first render runs `npm install` in `toon-studio/` when `node_modules` is missing. If a tool is missing, say so, log it (`problem_log.py`, stage `env`) and stop: no fake render.
2. **No open asset gap** (G1-13): if the bridge left gaps, run `make-3d-assets` first.
3. **Gate 1 must be all PASS before anything is rendered** (NOT RUN rows are reported as NOT RUN). Fix causes in the scene map / clauses (G1-01..G1-07), not in the project file by hand.
4. **Stills.** `--stage stills` writes one preview frame per world into `reports/stills/`. View at least the first, a night/snow scene if present, and one caption frame; fix clipping or empty frames at the source (theme, seed via `background`, camera_move) and run the bridge again.
5. **Quote the time.** `node toon-studio/cli.mjs estimate <run>/toon_project.json` and tell the user the projected render time for their core count.
6. **Render.** `python scripts/run_toon.py --project <run> --audio <voiceover> --stage render` (add `--preview` for a 640x360 draft first on anything over a few minutes). Tool calls time out after about 5 minutes: for a long render run it detached (`nohup python scripts/run_toon.py ... --stage render > reports/render_nohup.txt 2>&1 &`) and poll `reports/render_log.txt`; it is **resumable** (re-run the same command).
7. Then `qa-toon-project`. Editing habits for the passes: `perfect-editor`. Commands: `/toon-build`.

The build is editing only: it applies the map exactly and never adds, swaps or "improves" a scene. Music, SFX and ambient sound are not produced (listed in the bridge report); say so in the delivery.
