---
description: Collect every problem of the run, fix the plugin so it cannot repeat, and return the new .plugin
argument-hint:
- run folder
---

Run the `master-autofix` skill for the run in: $ARGUMENTS (default: the most recent folder under `story-video-run/`).

Collect, patch the plugin in the skill's order, write `lessons.json`, run `scripts/finish_project.py`, and return the new `story-video-master.plugin`. Never delete anything from the plugin without asking first.
