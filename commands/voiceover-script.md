---
description: "Stage 3c only: resolve every [VERIFY] and produce the clean narration-only 04-voiceover-script.txt, then stop"
argument-hint: "<path to the final script, or run folder>"
---

Run Stage 3c of the `story-video-master` skill, using `voiceover-ready-script`.

Input: $ARGUMENTS (default: the latest `.revised.md` or `03-script.md` in the most recent run folder).

Resolve every `[VERIFY]` first, run `scripts/clean_voiceover_script.py`, show the clean script, word count, runtime and read-aloud risks, and tell the user what Run B needs (voiceover audio, word-level transcript, assets). Do not continue past this point.
