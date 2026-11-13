# The non-literal (ambient) layer

Every shot has two components.

- **Literal layer**: what the narration is about. It carries information. Delete it and the story is lost.
- **Non-literal layer**: small secondary details that carry no information but set the mood: air blowing, a clock ticking, dust in a lamp beam. Delete it and the story still makes sense, but the shot feels flat.

Map them in separate fields so the mood details are not forgotten or written as vague adjectives.

## Rules

1. **It must be a physical thing that happens.** "Eerie" is not a detail. "A curtain moves in a draft" is. The validator rejects short descriptions built around mood words.
2. **It must not compete with the literal layer.** Keep it in the background or at the edges, slow, low contrast. If the viewer reads it before the subject, it is too strong.
3. **It must have a job.** Choose the `mood_target` first, then the details that produce it.
4. **It is a cheap way to keep a locked shot alive.** A 5-second static shot feels alive if a lamp flickers and dust drifts. This helps the "something changes every 2 to 5 seconds" rule at far lower cost than a new scene.
5. **It can be a deliberate contrast.** Birdsong in a grim scene produces unease. Use rarely.
6. **It can carry across shots as a motif.** A clock ticking through several shots builds waiting. Stopping it is a strong pattern interrupt.

## Two sub-types

- **Visual ambient (`ambient_visual`)**: animated. Curtain, dust, flicker, breath fog, drip, shifting shadow, a fly, steam.
- **Audio ambient (`ambient_audio`)**: sound design notes, not animation. Clock, wind, distant footsteps, a low hum, a creaking bed. Claude only writes these as notes; mixing is done elsewhere.

A detail can be both (a visible clock face plus its ticking). Put each half in its own field.

## Mood to detail starting points

These are starting points, not rules. Pick specifics that fit the scene and period.

| Mood target | Visual details | Audio details |
|---|---|---|
| waiting | pendulum, dripping tap, slow blinking light, a hand tapping | clock ticking, slow drip |
| cold | breath fog, frost on glass, smoke that rises slowly, hunched shoulders | low wind, a distant bell |
| fragile | uneven breathing moves a sheet, flickering lamp, a thin thread swaying | shallow breathing, a single creak |
| claustrophobic | walls slightly closing in during a slow push, dust, low ceiling shadow | muffled room tone, close footsteps |
| urgent | papers fluttering, rushing feet, fast shadow movement | footsteps, quickened pulse-like beat |
| dread | stillness, a single small movement in an otherwise static frame | near silence, a low hum |
| neglect | a fly, peeling paint, dust on surfaces | a distant drip, silence |
| wonder | drifting particles, soft light shifts, warm glow growing | sustained tone, gentle air |

## Intensity

- `1`: barely noticeable. Most shots.
- `2`: noticeable if you look.
- `3`: the viewer is meant to notice. Use for few shots, usually the last beat of a scene or a deliberate contrast. The validator caps the share at 20 percent by default.

## Motifs

Give a repeating detail a `motif_id` (`M1`) and mark `motif_event` as `start`, `continue`, or `end`. A motif should be introduced quietly, continue for a while, and then either keep going or be deliberately stopped. A motif that appears once is flagged, because it is probably just wallpaper.

## Do not repeat the identical detail in every shot

Using the same ambient detail in many consecutive shots with no motif id makes it background wallpaper. The validator flags more than four identical consecutive ambient descriptions that are not tagged as a motif.

## Carrying the layer across a boundary

The ambient audio is the cheapest transition tool. See `transitions.md` for pre-laps, stopping a motif at a cut, and continuing a motif through a hard cut.
