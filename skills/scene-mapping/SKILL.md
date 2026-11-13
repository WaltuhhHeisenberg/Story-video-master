---
name: scene-mapping
description: Turn timed narration into a complete scene map for a fully animated, high-retention storytelling documentary. Use whenever the user wants to map, plan, storyboard, audit, or fix the visuals of an animated documentary, including breaking narration into beats and shots, writing what is literally drawn, adding mood details (ambient visuals and sound), planning transitions between scenes, tracking open loops, budgeting animation work, or checking pacing against a retention graph. Triggers on "scene map", "map these scenes", "storyboard this narration", "shot list for my video", "transitions between scenes", "why does this drop off at 2:10". Does NOT write scripts or voiceover, and does NOT source stock footage or photos (all visuals are assumed animated).
---

# Scene Mapping

This skill converts narration that already exists into a structured scene map. Every shot has two layers, **literal** (what the narration is about) and **non-literal** (mood details such as air moving or a clock ticking), and every boundary between shots has a mapped **transition**.

## Hard facts about what this skill is

- Claude outputs text and files. It does not see, animate, or render anything. The map is only useful to whoever or whatever produces the animation.
- Claude is reliable at deciding what should be drawn for a line. Claude is unreliable at counting seconds and spotting rhythm problems across 150 rows. So the pacing checks are done by `scripts/validate_map.py`, not by Claude's judgment. Always run the validator.
- All numeric thresholds (shot lengths, interrupt gaps, ratios) are conventions from editing practice, stored in `scripts/config.json`. They are starting defaults, not measured laws. The user's retention graph is the only real evidence of what works for their audience.
- Period details (clothing, rooms, instruments, weather) that Claude chooses are plausible inventions, not facts from the script. They must be listed in `assumptions` so the user can check them against references.

## Scope

In scope: beats, shots, literal descriptions, ambient layer, transitions, open loops, asset registry, complexity budget, validation, exports, retention-dip diagnosis.

Out of scope: writing or editing the script, voiceover, finding stock or archival media, actual animation, sound mixing.

## Inputs

1. **Narration with timing** (best): SRT, or a transcript with timestamps.
2. **Narration without timing**: allowed, but timing must be estimated at about 150 words per minute (slightly slower for dramatic lines). Set `meta.timing_source` to `"estimated"` and tell the user the timecodes are approximate.
3. Optional: the user's retention-graph dip timestamps, an existing asset registry, a style note.

Ask at most one question before starting, and only if it changes the output format: **who or what produces the animation** (the 3D toon studio `three_toon`, own software, a hired animator, AI video tools). Default if unanswered: storyboard-style descriptions an animator could draw without asking anything. See `reference/schema.md` for how `literal` changes per producer.

## Modes

- **Full map**: narration in, complete map out.
- **Single scene**: map one passage, same format.
- **Transitions only**: given an existing map, fill or fix `transition_out`.
- **Audit**: given an existing map, run the validator and fix what it flags.
- **Dip diagnosis**: given dip timestamps, run the validator with `--dips` and explain which shots sat there.

## Workflow (full map)

Work in these passes. Do not skip ahead; each pass depends on the one before.

### Pass 1: Beats
Split the narration into beats. A new beat starts when the **subject**, **place**, **time**, or **question in the viewer's head** changes. A beat is usually 5 to 15 seconds. See `reference/beats-and-jobs.md`.

### Pass 2: Beat job and story function
For each beat decide the picture's **job** (show_event, show_place, show_time, show_mechanism, show_relationship, show_stakes, hold_question, introduce_character) and the **story function** (hook, setup, escalation, reveal, explanation, bridge, rehook, resolution). The job picks the scene type. Never pick the scene type because it looks impressive.

### Pass 3: Open-loop ledger
Before drawing anything, list the questions the viewer is holding after each beat (`L1`, `L2`, ...). Decide where each opens and where its answer lands. The visual for the answer appears when the answer is spoken, not earlier. Never close a loop without opening another within about two shots. See `reference/retention-rules.md`.

### Pass 4: Shots and the literal layer
Split each beat into shots of about 2 to 5 seconds, with a few deliberately shorter and a few longer. For each shot write `literal`: the subject, the action, the setting, and the camera, in physical terms. Apply the animator test: could someone draw it without asking a question? Something on screen must change at least every 2 to 5 seconds (camera move, new object, state change, text, or cut). See `reference/scene-types.md`.

### Pass 5: Ambient layer (non-literal)
Pick a `mood_target` for the scene (cold, waiting, claustrophobic, fragile, urgent). Then choose physical details that produce it, split into `ambient_visual` (animated) and `ambient_audio` (sound design notes). Rules: it must be a physical thing that happens, it must not compete with the literal layer, it must have a job, and it should carry across shots as a motif when useful. Give each ambient detail an intensity of 1 to 3. See `reference/ambient-layer.md`.

### Pass 6: Transitions
For every boundary except after the last shot, fill `transition_out`: `type`, `out_frame`, `in_frame`, `bridge`, `audio_bridge`, `duration_frames`. Default is a hard cut. Designed transitions (match cut, in-world wipe, zoom-through, dissolve, dip to black, smash cut, text card) must be earned by what the boundary tells the viewer, and need all three of out frame, in frame, and bridge. Use ambient motifs and audio to carry boundaries before using animation. See `reference/transitions.md`.

### Pass 7: Registry and budget
Every character, prop, and background must be listed in `new_assets` on the shot where it first appears and only there. Prefer reuse: same room from another angle, same character in another pose. Mark 5 to 8 hero shots per full-length video (hook, major reveal, climax) and put the animation effort there. Complexity is 1 (simple, reused assets), 2 (some new work), 3 (new character or complex motion).

### Pass 8: Validate and fix
Save the map as JSON and run:

```
python scripts/validate_map.py map.json
```

Read the output. Fix every `error`. Review every `warn` and either fix it or state in the summary why it stays. Re-run until there are no errors. Never claim the map passed without having run it. If the script cannot run, say so and do the checks by hand, labeled as unverified.

### Pass 9: Export and summarize
Run:

```
python scripts/export_csv.py map.json --out exports/ --fps 24
```

This writes the readable map, the asset list, the audio cue list, and a generic marker list. Then give the user a short summary: runtime, shot count, hero shots, asset count and the most expensive shots, loops opened and where they close, the validator result, and the `assumptions` list.

## Output rules

- The source of truth is the JSON map (schema in `reference/schema.md`). Show the user a readable table, not raw JSON, unless they ask.
- Times in the JSON are seconds or `m:ss`. Readable output uses `m:ss`.
- Never use mood words alone as descriptions ("tense", "eerie", "ominous"). The validator rejects them.
- Do not invent historical facts. If a detail is not in the narration, it is an assumption.
- When the user supplies real timestamps later, replace estimated ones and re-validate.

## Dip diagnosis

When the user gives retention-dip timestamps, run `validate_map.py map.json --dips 2:10,3:45`. The script lists the shots at each dip and the shots just before. Explain what those shots literally contain (long shot, no change, repeated scene type, loop closed with nothing open, low-complexity stretch). State that this is a hypothesis: the map shows what was planned, not what was actually rendered or what viewers actually saw. Suggest one change per dip and record the result in `meta.notes` so thresholds can be tuned over time.

## Reference files

- `reference/schema.md`: JSON schema and field rules
- `reference/beats-and-jobs.md`: segmentation and picking the visual's job
- `reference/scene-types.md`: animation scene types, writing `literal`, readable space
- `reference/ambient-layer.md`: non-literal layer rules and mood-to-detail table
- `reference/transitions.md`: transition types, selection by job, the three-part note
- `reference/retention-rules.md`: open loops, pacing curve, pattern interrupts, thresholds
- `examples/albert_alexander.json`: a complete mapped passage that passes the validator
