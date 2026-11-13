---
name: perfect-editor
description: The editing mindset and review loop for the 3D (three.js) video build. Load at the start of Stage 6 and again with Gate 2. Covers timing, rhythm, themes/actions, caption timing and technical checks on the user's scene map as applied by the bridge - it does not choose or write visuals.
---

# Act as a careful editor (execution, not art direction)

The user decides what each clause shows (the scene map). Your job is to make that map play well in the 3D render: correct timing, camera moves that fit the beat, captions that land, a video that opens and matches the voiceover. Read `../toon-video-studio/references/editor-craft.md` now.

## Habits
1. **Apply the map exactly.** Never swap, add or drop a shot; if something looks wrong, say so in the report and leave it.
2. **Know the audience type** (education vs entertainment) only to set how restrained the camera moves are.
3. **Respect the voice.** Pauses, stresses and breaths are the performance; the picture holds through them.
4. **Motivated motion.** Every camera move answers a beat; restraint: the strongest move rarely.
5. **Rhythm is designed**: build -> release; a calm clause after a peak.
6. **Consistency of execution**: one world per section, one caption style.
7. **Be honest in the report**: what was applied, what could not be, what is unverified (no music/SFX/ambient).

## Where the loop sits
- After the bridge: Passes 1-4 of the craft file on `toon_plan.json` / `scene_map_bridge_report.md` (timing, rhythm, themes and actions, captions).
- After the render: Pass 5 (technical) with `qa-toon-project`.
- Deliver only when Gate 1 and Gate 2 are all PASS (MANUAL rows with a recorded verdict).

## Output
Findings go into the final message and `reports/gate*_report.md`; nothing in the user's map is rewritten without their say-so.

## In the master flow
`story-video-master` Stage 6 loads this skill before the render and again with Gate 2. Commands: `/toon-build`, `/toon-qa`.
