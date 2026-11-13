# Animation scene types and writing `literal`

All visuals are animated, so the bottleneck is animation labor and visual consistency, not sourcing. Every shot must be drawn from scratch or reused from earlier work.

## Writing `literal`

State four things: **subject, action, setting, camera**. Use physical terms.

Test: could an animator draw it without asking a question?

- Fails: "Tension builds in the ward."
- Passes: "Wide shot of a hospital ward, six beds, a doctor walks between them, camera pushes to an empty bed being stripped."

Never put mood in `literal`. Mood goes in the ambient layer.

## Something changes every 2 to 5 seconds

Each stretch must have a change driver. Allowed drivers:

- camera move or new framing
- a new object entering or leaving
- a state change on screen (a number ticks, a light goes out, a patch appears)
- a text callout
- a cut to another scene

If 8 seconds pass with no new information on screen, the shot is dead even if it looks good. The validator flags shots over the maximum length, but it cannot see whether something changes inside a shot, so check this yourself.

## Readable space

Viewers lose track in animation unless geography is consistent.

- Introduce a location wide, then medium, then detail.
- Keep screen direction consistent for travel (heading east stays left to right) unless the point is a reversal.
- Return to the same room or setup from a different angle instead of drawing a new one.
- Delay showing a face or key object when its first appearance should land as a hit; show belongings, place, or hands first.

## Hero shots

Mark 5 to 8 hero shots in a full-length video: the hook, the major reveal, the climax. These get the most animation effort. Everything else should reuse a small set:

- 3 to 5 recurring environments
- a small cast
- reusable props

## Complexity scale

- **1**: reused background and character, simple motion or text.
- **2**: some new asset or a camera move with layers.
- **3**: new character, new complex background, or detailed motion.

These are estimates. Ask the user how long a 1, 2, and 3 actually take them and record it in `meta.notes`.
