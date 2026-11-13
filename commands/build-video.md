---
description: Run B of the master workflow - voiceover + transcript -> clauses -> scene map -> 3D video (three.js) + check report -> plugin autofix
argument-hint: <voiceover file> <transcript file> [assets folder]
---

Run the story-video-master workflow, Run B, using the `story-video-master` skill.

Input: $ARGUMENTS

If the voiceover or the word-level transcript is missing, ask for both in one short message and stop. Then Stage 4 (clauses), Stage 5 (scene map on the clauses, one shot per clause), Stage 6 (bridge to the 3D project, Gate 1, render, Gate 2), Stage 7 (check report and delivery) and Stage 8 (plugin autofix, return the new .plugin). Each stage starts only from the previous stage's saved file.
