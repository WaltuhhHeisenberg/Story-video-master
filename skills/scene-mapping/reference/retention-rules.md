# Retention rules

Retention is mostly decided by open loops and pacing. The thresholds below are conventions from editing practice, stored in `scripts/config.json`. They are not measured laws. The only real evidence is the user's own retention graph.

## Open loops

An open loop is a question in the viewer's head that has not been answered yet.

1. Keep a ledger: `L1`, `L2`, ... with the question text. Record `loop_opened` on the shot where the question forms and `loop_closed` on the shot where the answer is spoken.
2. Show the puzzle's pieces before they are explained, so the viewer starts forming the question.
3. Show the answer's visual at the moment the answer is spoken, not earlier. Showing it early spends the payoff.
4. Never close a loop without opening the next one within about two shots. The validator warns on this.
5. A loop that never closes before the final stretch of the video is a broken promise. The validator warns.
6. Hold-the-question shots (`job: hold_question`) keep a loop alive. A hard cut to black on an open question is a strong ending for a scene.

## Hook

- A shot with `story_function: hook` must start inside the first 30 seconds. No logo or intro before it.
- Hero shot candidate.

## Re-hooks

- A shot with `story_function` of `hook` or `rehook`, or one that opens a loop, must appear in every 60-second window. This is the main guard against mid-video sag.

## Pacing curve

Shot density should vary on purpose: fast and short for setup or montage, slower and longer for a reveal, fast again afterward. A flat rhythm is the real danger because viewers stop registering it.

- Typical shots are 2 to 5 seconds. A few are under 1 second (fast sequences) and a few are 6 to 8 seconds (a key image or reveal).
- If every shot is nearly the same length, the validator flags it (coefficient of variation below 0.15).
- Maximum shot length default: 8 seconds.

## Pattern interrupts

A pattern interrupt restarts attention. Examples: a punch-in, a smash cut, a switch of scene type, a switch to black and white, a sudden silence, a glitch frame, a stopped motif.

- Place them where content is naturally slower, such as after a long explanation.
- Overuse makes them background noise.
- The validator warns when more than 30 seconds pass without one.

## Variety checks

- Scene type: no more than 3 in a row of the same type.
- Camera move: no more than 3 in a row of the same move.
- Ambient detail: no more than 4 identical in a row without a motif id.
- Complexity: no more than 2 complexity-3 shots in a row (animator burnout and visual overload), and a cap on complexity points per minute.

## Asset reuse

- Share of shots introducing a new asset should stay under 50 percent.
- Every entity must be introduced exactly once in `new_assets`, on its first shot.

## Fact anchors

Every new number, date, and name in the narration gets an `overlay_text` on the shot where it is spoken. The validator checks digits only (it cannot read spelled-out numbers), so also check these by hand.

## Dips

When the user supplies retention-dip timestamps, look at:

1. The shots at the dip and the ones about 10 seconds before.
2. Whether a loop was closed with nothing open.
3. Whether the same scene type or camera move repeated.
4. Whether a long shot had no change driver.
5. Whether the stretch was low complexity and low ambient intensity (flat).

These produce hypotheses. The map shows what was planned, not what was rendered or what viewers saw. Suggest one change per dip and record the outcome in `meta.notes`.
