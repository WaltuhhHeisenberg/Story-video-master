---
name: scene-map-to-toon
description: Stage 6a of the story-video-master flow. Converts the scene-mapping output (one shot per voiceover clause) into a three.js toon-studio project (toon_project.json + toon_plan.json) without guessing - sections become 3D worlds, clauses become camera shots, overlay_text becomes burned-in captions. Use when a scene map and clauses.json exist and the 3D video must be built from them.
---

# Scene map -> 3D project

The scene-mapping skill decides what each clause shows; this step only applies it. It is mechanical and deterministic: same inputs, same project.

1. Inputs: `05-scene-map.json` (one shot per clause), `work/clauses.json` (sections with real names), the voiceover file (optional: without it the render is silent and Gate 1 G1-08 is NOT RUN).
2. Run `python scripts/scene_map_to_toon.py --scene-map 05-scene-map.json --clauses work/clauses.json --out <run>/toon_project.json --plan <run>/work/toon_plan.json --audio <voiceover> --report <run>/reports/scene_map_bridge_report.md` (or `scripts/run_toon.py --stage bridge`).
   - Exit 2 = shots and clauses do not line up (counts or times): nothing is written. Fix by re-running scene-mapping on `clauses.json` with one shot per clause; never merge, split or reorder to make it fit. Log it (`problem_log.py`, stage `bridge`).
3. What the bridge writes (rules in `skills/toon-video-studio/references/scene-to-3d-rules.md`, data in `library/library.json`):
   - one world per section (a section over 40 s is cut at clause boundaries); theme by keyword score of the shots' `literal`, `mood_target`, `background`; same `background`/section name = same seed;
   - one camera shot per clause from `camera_move` (else `scene_type`), blend from the previous shot's `transition_out`;
   - hero action per clause from the `literal` verbs (else the scene_type default); `pause_after` >= 0.6 s = idle through the pause; a companion actor when 2+ characters or a group are named;
   - grown assets from `library/assets/` are used when the shots' words match their keywords (themes compete with the built-ins by keyword score; props are added to the world; character looks style the hero/companion) and are embedded in the project's `assets` block;
   - `overlay_text` as one caption (burned in + `.srt`).
4. Read `reports/scene_map_bridge_report.md`: the plan table (clause, world, action, camera, caption) and the rows **not produced** (ambient visual/audio, unknown camera moves or transitions). These are reported, never dropped silently. If a theme or action looks wrong for a clause, the cause is the `literal` wording: change the scene map (user's decision), do not hand-edit the project.
5. **Asset gaps.** The bridge also writes `work/asset_gaps.json` (table in the report): characters, props, `new_assets` and backgrounds the map names that the open library does not have. If any are open, run `make-3d-assets` (make them, preview them, save them), then run the bridge again. `run_toon.py` pauses on open gaps; `--accept-gaps` is the user's decision only.
6. Continue with `build-toon-project`.
