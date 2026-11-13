---
name: qa-toon-project
description: Stage 6c of the story-video-master flow. Runs Gate 2 on the rendered 3D video (duration, size, audio, captions, blank frames, visible change at every clause cut, contact sheet), records the manual verdicts, and runs the editor Pass 5. Use after build-toon-project, or to check any rendered toon video against its project.
---

# QA of the rendered 3D video

1. `python scripts/run_toon.py --project <run> --stage gate2` (add `--preview` when the video is the 640x360 draft) -> `reports/gate2_report.md` and `reports/contact_sheet.png`. All computed rows must be PASS. Fix the cause and re-render (the render is resumable: delete only the chunks that are wrong).
2. **Manual rows (M-1..M-3):** open `reports/contact_sheet.png` and 3 frames (one with a caption). Record each verdict with evidence in `manual2.json` and re-run `toon_qa.py gate2 ... --manual manual2.json`. Never mark a manual row PASS without looking.
3. Apply `perfect-editor` Pass 5 (technical) with this gate.
4. The independent review is done by `story-video-master:toon-qa-reviewer` (Stage 6, after Gate 2 is all PASS) with only the output folder and `skills/toon-video-studio/references/qa-checklist.md`.
5. Log every finding with `problem_log.py` (stage `qa`) and fix or report it. Then offer: "Run /build-video to finish Stage 7 and Stage 8, or /plugin-autofix."
