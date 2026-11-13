---
description: "Stage 5 only: build the scene map on the clauses, one shot per clause, and validate it -> 05-scene-map.json"
argument-hint: "<run folder or path to clauses.json>"
---

Run Stage 5 of the `story-video-master` skill, using `scene-mapping` in full map mode.

Input: $ARGUMENTS (default: the most recent run folder).

Start only from `clauses.json`: exactly one shot per clause, shot start and end equal to the clause start and end. Validate with `validate_map.py`, fix every error, and fix or explain every warning. Save `05-scene-map.json`, set `meta.producer` to `three_toon` (the 3D studio draws the video; write `literal` as in `skills/toon-video-studio/references/scene-to-3d-rules.md`), then offer: "Run /toon-build."
