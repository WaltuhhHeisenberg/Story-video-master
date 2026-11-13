---
description: "Stage 6a-2: make the 3D assets (worlds, objects, character looks) the scene map names and the library lacks; validate, preview, save, re-run the bridge"
argument-hint: "<run folder> | <what to make, e.g. 'a harbour world'>"
---

Run the `make-3d-assets` skill.

Input: $ARGUMENTS (default: the open gaps in the most recent run's `work/asset_gaps.json`).

Make every open gap as a JSON asset (`asset_catalog.py add`), look at its preview PNG and fix it, then run the bridge again until Gate 1 G1-13 passes. If the user names something to make (a world, object or character), make that. Say plainly what primitives cannot show. Then offer: "Run /toon-build."
