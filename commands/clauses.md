---
description: "Stage 4 only: divide the voiceover transcript into natural 3-4 second clauses -> clauses.json and the clause sheet"
argument-hint: "<voiceover file> <word-level transcript>"
---

Run Stage 4 of the `story-video-master` skill, using `split-clauses`.

Input: $ARGUMENTS. If the voiceover or the word-level transcript is missing, ask for both in one short message and stop.

Write `intake_report.md` first (Gate 0, `skills/split-clauses/references/intake-checklist.md`), use the voiceover and transcript exactly as delivered, and output `work/clauses.json` and `reports/clause_sheet.md`. Then offer: "Run /scene-map."
