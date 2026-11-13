# Gates (computed by `scripts/toon_qa.py`; PASS / FAIL / NOT RUN / MANUAL, never invented)

## Gate 1 - before any render (`python scripts/toon_qa.py gate1 ...`)
| id | check |
|---|---|
| G1-01 | scene timeline covers the voiceover exactly (frames, +-1) |
| G1-02 | exactly one camera shot per clause, on the clause's times |
| G1-03 | every theme, action and shot type exists (built-in or grown) |
| G1-04 | a visible change at least every 4.5 s |
| G1-05 | sections have real names (not S01, S02 ...) |
| G1-06 | no more than 4 identical camera set-ups in a row |
| G1-07 | every `overlay_text` of the map is a caption, inside its scene |
| G1-08 | voiceover file opens and matches the timeline (+-1.0 s); NOT RUN without a voiceover (silent render, stated) |
| G1-09 | frame settings sane; world `clearance` >= 9 |
| G1-10 | render tools present: node, ffmpeg, ffprobe, Xvfb (Linux), `toon-studio/node_modules` |
| G1-11 | `intake_report.md` exists |
| G1-12 | no scene (world) longer than the cap (default 40 s) |
| G1-13 | no open asset gap: every character, prop and world the map names exists in the library (built-in or grown), or the user accepted the gap |
| G1-14 | embedded grown assets are valid and every prop a scene uses is embedded |

## Gate 2 - after the render (`python scripts/toon_qa.py gate2 ...`, add `--preview` for a 640x360 draft)
| id | check |
|---|---|
| G2-01 | video file opens (video and audio streams counted) |
| G2-02 | video duration equals the project (+-0.15 s) |
| G2-03 | size and frame rate equal the project |
| G2-04 | audio stream present, as long as the video (+-0.5 s) |
| G2-05 | `.srt` has one cue per caption |
| G2-06 | no blank or flat frames (sampled mid-clause) |
| G2-07 | the picture changes visibly across every clause cut (sampled 0.25 s either side) |
| G2-08 | contact sheet written (one frame per clause) |
| G2-09 | `intake_report.md` exists |
| G2-10 | plan matches project |
| M-1..M-3 | MANUAL: the contact sheet reads as the story; captions legible at phone size; no camera clipping through props or actor off screen. Recorded with a verdict + evidence via `--manual manual.json` (`{"M-1": {"status": "PASS", "evidence": "looked at reports/contact_sheet.png: ..."}}`) |

Every run is kept in the report as `## Run N`; `finish_project.py` learns from the failed ones too. Exit code 0 only when nothing is FAIL.
