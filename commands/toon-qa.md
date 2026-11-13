---
description: "Stage 6c: Gate 2, the editor Pass 5, and the independent toon-qa-reviewer on the rendered 3D video"
argument-hint: "<run folder>"
---

Run Stage 6c of the `story-video-master` skill: `qa-toon-project` (Gate 2 all PASS, manual rows only with a recorded verdict), `perfect-editor` Pass 5, then a fresh `story-video-master:toon-qa-reviewer` given only the output folder and the QA checklist.

Input: $ARGUMENTS (default: the most recent run folder).

Report PASS, FAIL and NOT RUN exactly as computed; never mark a manual item PASS without looking. Log every finding with `problem_log.py`. Then offer: "Run /build-video to finish Stage 7 and Stage 8, or /plugin-autofix."
