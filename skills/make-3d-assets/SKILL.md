---
name: make-3d-assets
description: Stage 6a-2 of the story-video-master flow, and any time the 3D library lacks something. The asset library is OPEN and grows: when the bridge reports asset gaps (a character, object or world the scene map names that the library does not have), Claude MAKES the missing assets as JSON files (themes/worlds, props/objects built from primitives, character looks), validates them, previews them with the 3D engine, saves them into library/assets/, and runs the bridge again. Use after scene-map-to-toon when asset_gaps.json has open gaps, when the user asks for a new world, object or character, or to improve an existing asset.
---

# Make 3D assets (the library grows; nothing is rigid)

The library is `library/library.json` (built-ins) **plus every file in `library/assets/{themes,props,characters}/`**. You do not need engine code to add to it: an asset is a small JSON file. Format and examples: `references/asset-schema.md` (also `python scripts/asset_catalog.py schema`). Seed examples to copy from: `library/assets/props/hospital_bed.json`, `park_bench.json`, `market_stall.json`, `street_lantern.json`, `themes/autumn_town.json`, `hospital_dusk.json`, `characters/doctor_tophat.json` (previews in `library/assets/previews/`).

## When
- After the bridge: `work/asset_gaps.json` / the "Asset gaps" table in `reports/scene_map_bridge_report.md` lists everything the scene map names (characters, `props`, `new_assets`, `background`) that the library does not match. **Gate 1 G1-13 fails while a gap is open.** Making the assets is your job, not the user's.
- On request: "make a lab world", "add a crowd character", "better lantern".
- Also proactively when a world or object you would reuse is poor: improve the asset file (keep the id), re-preview.

## How (one asset at a time, in this order: worlds, props, characters)
1. **Read the gap's context** (clauses, the shot's `literal`). Decide the kind:
   - a *place or atmosphere* (lab, harbour, ruined castle, ice cave) -> **theme** (`extends` a built-in or grown theme and overrides colours, features, lamps, weather, and lists the props that belong there);
   - an *object* (operating table, clock, flask, cannon, boat) -> **prop**: 3 to 25 primitives (`box, cyl, sph, cone, dodec, oct, tor, pyr`) with a position, size and colour, units in metres (a house is about 3 wide, the stickman is 2.4 tall). Give it a `place` rule (where the engine puts it: `scatter`, `path_edge`, `at`);
   - a *person or creature* (a named historical person, a policeman, a child) -> **character** look: colour, scarf, hat (`none|cap|tophat`), `scale`, and `parts` (accessories: a bag, a helmet, a beard, glasses made of primitives attached to the head/body).
2. **Write the JSON** into a scratch file, with `id` (`PRP_/THM_/CHR_` + lower_case_name), `name`, `description`, and **`keywords`**: the words and phrases a shot's text would use for it ("operating table", "surgery table", "autopsy table"). The bridge finds the asset by these, so list the plural/synonym forms the map actually used (copy the gap's name first).
3. **Validate and save:** `python scripts/asset_catalog.py add <file>` (it validates, refuses duplicates unless `--force`, copies it into `library/assets/<kind>s/`, rewrites `library/INDEX.md`). Fix every error it prints.
4. **Look at it:** `python scripts/asset_catalog.py preview <ID>` writes `library/assets/previews/<ID>.png` (one frame from the real engine). View the PNG. Fix proportions, colours, floating or buried parts; add/replace and preview again. A prop that reads as a blob at phone size is not done: bigger, simpler, higher contrast.
5. **Close the gap:** run the bridge again (`python scripts/run_toon.py --project <run> --stage bridge`). The gap must disappear (the keywords matched) and the project embeds the asset. If the user prefers the default look for something, record it with `--accept-gaps` (their decision, not yours).
6. Continue with `build-toon-project` (Gate 1 must pass G1-13 and G1-14).

## Rules
- **Make what the map names, nothing else.** No decorative extras; do not change the scene map to avoid making an asset.
- **Keep assets reusable**, not tied to one video: `keywords` general, no video-specific names unless it is a named character; `made_for` records the first video.
- **Light:** at most 80 parts per asset, no thousands of tiny pieces (the engine merges them but frames are software-rendered).
- **Never delete or rename a grown asset** without the user's yes (renaming breaks projects that embed or name it); improving in place is fine.
- **Honest limits:** only primitives, one stickman rig, procedural actions (idle, walk, run, wave, jump, dance). A realistic building, a face, a map of a real country or a new animation is not possible with a JSON asset: approximate it with primitives and put the exact name or number in `overlay_text`; say so in the delivery. New engine abilities (a new action, a new shape) are code changes in `toon-studio/src` - log them with `problem_log.py` and propose them to the user.
- Log what you made in the run (`problem_log.py`, stage `assets`, symptom "gap: <name>" -> handled "made PRP_..."): the autofix learns which kinds of assets the channel needs.
