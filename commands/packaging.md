---
description: "Stage 2 only: stress-test the title and thumbnail in the blind feed (3 to 8 rounds) -> 02-packaging.md"
argument-hint: "<run folder or path to 01-video-brief.md>"
---

Run Stage 2 of the `story-video-master` skill, using `packaging-cycle` completely.

Input: $ARGUMENTS (default: the most recent folder under `story-video-run/`).

Start only from `01-video-brief.md` and the saved outlier data. Use `story-video-master:master-packager`, `story-video-master:thumbnail-maker` (real image per `thumbnail-making`) and a fresh `story-video-master:packaging-lazy-viewer` every round. If the brief or the outlier thumbnails are missing, say so and stop. Output `02-packaging.md`, then offer: "Run /write-script."
