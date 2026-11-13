---
description: Run A of the master workflow - idea, packaging, script, then STOP with a clean voiceover-ready script
argument-hint:
- keyword or topic - or nothing
---

Run the story-video-master workflow, Run A, using the `story-video-master` skill.

Input: $ARGUMENTS (empty is valid: the idea stage then researches the keyword itself).

Do Stage 0 (read the plugin's lessons, make the run folder, one intake message), then Stages 1, 2 and 3 in order, each as if in its own fresh chat, starting only from the previous stage's saved file. Stop after `04-voiceover-script.txt` and tell the user what Run B needs.
