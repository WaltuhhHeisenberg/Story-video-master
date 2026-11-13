# Intake checklist (Gate 0) - run before Stage 4

Write `intake_report.md` into the run folder (Gate 1 row G1-11 and Gate 2 row G2-09 look in the run, `reports/`, `work/` and `toon/`). One line per row: `# | status | evidence`. Status: `RECEIVED` | `DERIVED` | `MISSING-BLOCKING` | `MISSING-OPTIONAL (fallback: ...)`. All blocking rows must be RECEIVED before Stage 4; ask for every missing blocking item in ONE short message.

| # | Input | What must be true | Evidence to write | If missing |
|---|---|---|---|---|
| I1 | **Transcript** | word-level (word, start, end); covers the whole voiceover; language known; format in `input-formats.md` | word count; first and last timestamp; max gap; last word end within 1 s of the voiceover duration | BLOCKING (cue-level only -> clauses approximate; say so) |
| I2 | **Voiceover audio** | opens; duration, channels, sample rate recorded (muxed as delivered, never processed) | ffprobe numbers | MISSING-OPTIONAL: build on silence of the transcript's length and say so; the render is then silent |
| I3 | **Scene map** | `05-scene-map.json`, one shot per clause | DERIVED from the scene-mapping stage; counts equal | produced by Stage 5 |
| I4 | **Visual look** | nothing to supply: worlds, actors and cameras come from `library/library.json` | DERIVED | - |
| I5 | **Render machine** | node 18+, ffmpeg + ffprobe, Xvfb (Linux), `npm install` done in `toon-studio/` | the tool versions; core count | BLOCKING for the render (Gate 1 G1-10) |
| I6 | **Target** | resolution and fps (default 1280x720 @ 30), burned-in captions yes/no | state it | DERIVED from `library/library.json` defaults |
| I7 | **Audience type** | education or entertainment (sets nothing but how restrained the camera moves are) | state it | DERIVED from the tone |

End with **Blocking items open: N** (must be 0 to continue) and the fallbacks chosen.
