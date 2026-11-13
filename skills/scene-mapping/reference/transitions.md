# Transitions

A transition is the boundary between two shots. Three things happen at it: something **leaves**, something **arrives**, and something **connects** the two or deliberately does not. Mapping a transition means writing down all three in physical terms, for picture and for sound.

Because everything is animated, designed transitions are not free. Match cuts and in-world wipes need both scenes to be drawn with the connection in mind. Adding them after the scenes are finished usually means redrawing one side. So transitions are mapped at the same time as the scenes.

## Types

| `type` | What literally happens | Use for |
|---|---|---|
| `hard_cut` | Frame A ends, frame B starts. | Default. Continuous action, same place, any beat needing no bridge. |
| `audio_lead` | Hard cut, with the next shot's sound starting before its picture, or the previous sound continuing under the new picture (J/L cut). | The least visible link; no animation cost. |
| `match_cut` | Last frame of A and first frame of B share a shape, position, or motion. | Linking two ideas (a clock face becomes a petri dish). |
| `motion_carry` | A camera move or object movement continues across the cut in the same direction and speed. | Momentum in travel, chases, escalation. |
| `in_world_wipe` | Something inside the scene sweeps across the frame (a person passing the lens, a door, a curtain, smoke) and reveals the next scene. | Changing place or time without a flat graphic wipe. |
| `zoom_through` | Camera pushes into an object or dark opening until it fills the frame, and the next scene emerges from it. | Outside to inside, big picture to detail. |
| `dissolve` | A fades out as B fades in. | Time passing. Overuse makes the video feel slow. |
| `dip_to_black` | A fades to black, a beat of black, then B. | Major section breaks, or the moment before a reveal. |
| `smash_cut` | Abrupt cut between opposite energy levels. | Shock, irony, resetting attention. |
| `text_card` | A date, number, or title animates in as the connector ("Three weeks later"). | Time jumps and chapter titles. |

## Pick by job

- Same moment, new angle: `hard_cut`.
- New place: `in_world_wipe`, `zoom_through`, or a `hard_cut` plus an establishing wide.
- Time jump: `dissolve`, `text_card`, or a changed ambient detail such as daylight to lamp light.
- Cause and effect: `match_cut`.
- Reveal or payoff: a beat of black or silence, then a hard cut.
- Section break: `dip_to_black` plus a tonal reset (new ambient motif or music).
- Energy change: `smash_cut`.

A transition earns its place only when it tells the viewer something about the relationship between the two scenes. Never choose one because it looks good.

## The three-part note

For every boundary except the last shot's:

1. **`out_frame`**: what is on screen in the last half second of A, including where the key object sits in the frame.
2. **`in_frame`**: what is on screen in the first half second of B, including where its key object sits.
3. **`bridge`**: what connects them. A shared shape, a continuing movement, a sound, or "none" for a clean cut.

Writing both frames down shows whether a match cut is even possible, since matching depends on object position and scale.

For `hard_cut` and `audio_lead` only the type is required. Fill the others when something about the boundary is worth recording, such as a sound carrying over.

## Audio does half the work

- A **motif** (a ticking clock) can continue through a hard cut and make the boundary almost invisible.
- **Stopping a motif** at a cut is itself a strong transition.
- **Pre-lap**: start the next shot's ambient sound 0.5 to 1 second early so the cut feels already coming.
- **Contrast**: quiet after loud, or loud after quiet, resets attention.
- **Silence before a reveal**: record it in `audio_bridge` as "silence". The validator looks for this on reveal shots.

## Rules of thumb (defaults, tune per video)

1. Hard cuts by default. If more than about a third of boundaries are designed transitions, they stop standing out. The validator checks the share of plain cuts stays between 60 and 90 percent.
2. Designed transitions are short: 0.5 to 1 second for wipes and zoom-throughs. A longer one reads as a delay.
3. Do not stack effects (zoom-through plus flash plus sound hit plus text card).
4. Keep screen direction consistent across the boundary unless the point is a reversal.
5. Reserve match cuts and zoom-throughs for one or two moments per video where the link matters.
6. Dips to black: no more than about one per 90 seconds.
7. Dissolves only for time jumps. The validator warns if neither neighboring shot has the job `show_time`.

## Worked boundary

Scene A ends on a hard cut to black with a ticking clock cut out entirely. Scene B (assumed) is a lab flask dripping.

```json
"transition_out": {
  "type": "dip_to_black",
  "out_frame": "Black. Last visible image: a bed chart with a fly on its rail.",
  "in_frame": "Close-up of a glass flask on a bench, pale liquid dripping slowly from a funnel.",
  "bridge": "No visual link. A drip sound starts during the black at the same tempo as the cut-out clock.",
  "audio_bridge": "About 1 second of silence after the clock stops, then a single drip, then drips at the clock's rhythm; picture cuts in on the second drip.",
  "duration_frames": 24
}
```

The viewer hears the waiting rhythm return before seeing anything. It costs one sound effect and no extra animation.
