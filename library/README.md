# 3D asset library (open and growing)

This is **not a fixed list.** It has two layers:

| layer | where | who changes it |
|---|---|---|
| built-in | `library.json`: 5 themes (day, sunset, night, snow, desert), 6 actions, 8 camera shots, the stickman rig, world features, and the `mappings` rules the bridge reads | engine code (`toon-studio/src`) |
| **grown** | `assets/themes/*.json` (worlds), `assets/props/*.json` (objects built from primitives), `assets/characters/*.json` (looks and accessories), previews in `assets/previews/` | **Claude makes them** whenever a scene map names something the library lacks; you can also ask ("make a harbour world") |

How it grows: the bridge compares what the scene map names (`characters`, `props`, `new_assets`, `background`) with the library and writes `work/asset_gaps.json`; Gate 1 G1-13 blocks the render while a gap is open; the skill `make-3d-assets` makes the asset (JSON, validated by `scripts/asset_catalog.py add`, previewed with the real engine, saved here); the next bridge run finds it by its keywords and embeds it in the project. Every asset stays in the library for the next video, and `finish_project.py` ships the grown library inside the returned `.plugin`.

Commands: `python scripts/asset_catalog.py info | schema | validate | add FILE | preview ID | reindex | check`. Format and examples: `skills/make-3d-assets/references/asset-schema.md`. List with previews: `INDEX.md`.
Seed assets (also templates to copy): props hospital_bed, park_bench, market_stall, street_lantern; themes autumn_town, hospital_dusk; character doctor_tophat.
Limits: only primitives (box, cylinder, sphere, cone, pyramid, torus, dodecahedron, octahedron), one stickman rig, procedural actions; new actions or shapes need engine code.
