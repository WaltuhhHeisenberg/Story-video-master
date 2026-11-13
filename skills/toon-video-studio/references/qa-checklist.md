# QA checklist for the independent reviewer (`story-video-master:toon-qa-reviewer`)

You get only the output folder (video, `toon_project.json`, `toon_plan.json`, `clauses.json`, reports). Check, and report each failed check with location and evidence:

1. `toon_project.json` is valid JSON; scene durations are whole frames; scenes cover the voiceover; every scene has actors, shots and (where the map has overlay_text) captions inside the scene.
2. One shot per clause on its times; shot types, themes and actions exist in `library/library.json`.
3. `toon_plan.json` rows match the project (scene count, theme, action, camera, caption per clause).
4. The video opens with ffprobe; duration, size, fps match the project (preview renders are 640x360); audio present and as long as the video when the project names an audio file; `.srt` cue count equals the caption count.
5. Look at `reports/contact_sheet.png` and at 3 frames of your choice (one at a caption): blank or flat frames, actor off screen, camera inside a prop, unreadable caption.
6. Rhythm: longest shot, longest run of identical set-ups, number of scenes against the number of story sections.
7. Honesty: the delivery says picture + captions only (no music/SFX/ambient), says whether the render is full or preview, and does not claim anything the gates did not compute.
Do not judge the creative choices of the scene map. Do not fix anything; do not praise. Return: failed checks, then warnings, then what you could not verify.
