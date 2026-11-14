# Viewer psychology: how the click is decided, and so how the thumbnail is made

Single source of truth for the psychology of packaging. It is taken from the "How you judge" section of `agents/packaging-lazy-viewer.md`, which is the judge every card must beat. If that section changes, change this file to match, then re-check the places that point here (`master-packager`, `extreme-thumbnails`, `thumbnail-making`, `thumbnail-maker`, `thumbnail-reader`, `packaging-cycle`).

This file is about the mind of the viewer, not about drawing. How a picture is rendered is in `skills/thumbnail-making/SKILL.md`.

## The judge in one paragraph

A tired viewer, 3x worse than average, gives each card half a second. He clicks **exactly one** card in the whole feed: the one that is **highest** on the criteria below. Being good is not enough, a card must be the **highest in the feed**. This rule overrides every other rule. He is cruelest on cards under 50,000 views, and the card under test always arrives with a low view count, so it is always the underdog.

## The six tests (C1-C6)

Each test says what the viewer's mind does, how to make for it, how to check it, and what fails.

### C1. Contrast: the loudest card in the feed
- **The viewer's mind:** in half a second the eye goes to the strongest difference. Weak contrast is not seen, so it is not judged.
- **Make:** choose ONE element that is the highest-contrast thing on the card (light against dark, one accent colour against one dominant colour, one isolated object). Everything else supports it or is quiet. Study the outliers first: if most of them are dark and warm, a card that is dark and warm disappears. Contrast is relative to the crowd, not only inside the card.
- **Check:** the grayscale squint at phone size: does the focal element still stand out? Does it still win next to the 3 loudest outliers?
- **Fail:** two competing bright things; low contrast text; the same palette as the crowd; contrast only from detail the thumb cannot see.

### C2. A mystery with the least context
- **The viewer's mind:** a question forms when he has a piece but not the rest. Too much shown and the question is answered (no click needed). Too little shown and there is no question at all (nothing to want).
- **Make:** show the smallest amount that still forms a question. List everything on the card that explains. Keep only the question's subject and its gap. Target: one subject, one gap, at most 2 words of text. Each element that is not the subject or the gap is context: remove it.
- **Check:** the guess test: can a stranger guess the answer from the card alone? If yes, it is over-explained. The itch test: after the second look, is the question still alive? If no, it is dead.
- **Fail:** the answer can be guessed; the question needs technical knowledge to be asked; several questions at once (they cancel); a caption that explains the picture.

### C3. Two halves of a story, nothing spoiled
- **The viewer's mind:** a story opens when he is handed two pieces that clearly belong together but do not connect yet (cause and missing effect, before and missing after, an expectation and its contradiction). He clicks to join them.
- **Make:** write the card as three lines before drawing or titling anything:
  - **Half A (the picture):** what the image alone says.
  - **Half B (the title):** what the title alone says.
  - **The join (what the video pays off):** the one thing that connects A and B. It appears on neither.
  The picture and the title must each be incomplete alone, each pointing at the other. They complement and never repeat.
- **Check:** cover the title: the picture should feel like half of something. Cover the picture: the title should feel like half of something. Look at both: a story is implied, but the ending is not given.
- **Fail:** A and B say the same thing (one half is wasted); A and B are unrelated (no story forms); together they state the outcome (spoiled).

### C4. A familiar entity (optional, a tie-breaker)
- **The viewer's mind:** something he already knows is understood with no effort, and the brain stays on it a moment longer.
- **Make:** if it adds no context and no second focal point, use something universally familiar: an everyday object, a generic cartoon person (`ICO_person`, `ICO_person_tophat`), an animal, a recognisable place type, a famous thing known by its look. **Familiar never means a named person.** The channel's off-context rules still win: no names, no likeness of a real person, no logos.
- **Check:** can a stranger name it in a tenth of a second without help?
- **Fail:** a familiar entity added only to look familiar; it explains the story (context); it becomes a second focal point; it is a real person's likeness.

### C5. Easily understandable
- **The viewer's mind:** if he has to decode a card he has already moved on. A mystery he cannot read is not a mystery, it is confusion. This test beats cleverness: when clever and clear disagree, clear wins.
- **Make:** the card is describable in one sentence. Every object shows its recognition cues. The thumbnail text is one or two words. Nothing is small, thin or low contrast.
- **Check:** the blind `thumbnail-reader` names every object, names the focal element first, reads the text exactly, and says what question it raises, all at phone size.
- **Fail:** any object read as something else; the focal element not named first; the reader needed more than a glance; the question the reader reports differs from the one intended.

### C6. The underdog test (under 50,000 views)
- **The viewer's mind:** he does not trust small videos. A low view count alone is never a reason to click, so the card must win on C1-C5 harder than the big cards, by being the question that is still alive after the second look and stronger than anything on the big cards.
- **Make:** design against the strongest outlier, not the average one. Name the three outliers most likely to take the click (by views and by mechanism) and beat each of them on a named test.
- **Check:** the strict feed test: place the concept among the real outliers and say, in plain common sense, why a tired thumb picks it over those three. If the honest answer is "it would not", kill it.
- **Fail:** relying on the channel, the polish, or the effort; winning only against weak outliers.

## The scorecard (used in every concept log)

For every concept that survives the first cut, write this block. One line per test, with a verdict (STRONG / OK / WEAK / FAIL) and the reason in plain words.

```
Concept: <one sentence>
Half A: <picture says>   Half B: <title says>   The join: <what the video pays off>
C1 contrast: <STRONG|OK|WEAK|FAIL> - <the one loudest element and why it beats the loudest outliers>
C2 least context: <STRONG|OK|WEAK|FAIL> - <the subject, the gap, what was removed, can the answer be guessed?>
C3 two halves: <STRONG|OK|WEAK|FAIL> - <A and B each incomplete alone? spoiled?>
C4 familiar entity: <what it is, or "none, not needed">
C5 understandable: <STRONG|OK|WEAK|FAIL> - <one-sentence description; what could be misread>
C6 underdog: <STRONG|OK|WEAK|FAIL> - <the 3 outliers it must beat, and the named reason it beats each>
Verdict: KEEP | KILL because ...
```

**This is enforced, not advisory.** `python scripts/check_scorecard.py scorecard --file round-N-packaging.md --expect N` must pass before the thumbnail is drawn (N = 3 in round 1 for the primary and 2 variants, 1 in later rounds). It rejects a KEEP block with a missing half, a missing verdict or reason, a FAIL on C1, C2, C3 or C5, or a WEAK/FAIL on C6, and a designer brief without the psychological spec. `python scripts/check_scorecard.py debrief --file round-N-debrief.md` must pass before the packager repairs anything (every defect carries a C label).

Rules for the verdict:
- Any **FAIL** on C1, C2, C3 or C5 kills the concept. C4 is optional and never kills. A **WEAK** on C6 kills it (the card must be the strongest, not an acceptable one).
- Between two surviving concepts, the one that is higher on C2 wins, then C1, then C3.
- A card is not scored in isolation. Each line names the outlier it is compared with.

## The stages of the thumbnail-making process (psychology only)

| # | Stage | Who | The psychology applied |
|---|---|---|---|
| 1 | Read the crowd | master-packager | For every outlier: its loudest element (C1), its question (C2), its two halves (C3), its familiar entity (C4). Write a crowd map: what is over-used, what is spent, which palette dominates, which outliers are strongest. |
| 2 | Mine the story | master-packager | True physical details become raw material for the subject and the gap (C2). |
| 3 | Concepts | master-packager | 15+ concepts, each written as Half A / Half B / the join (C3) before any other detail. |
| 4 | Kill by scorecard | master-packager | The scorecard above, plus the kill tests in `extreme-thumbnails`. C6 is the last and hardest cut. |
| 5 | Title as Half B | master-packager | The title is written after the picture is chosen, as the other half (C3) and with the keyword. |
| 6 | The psychological brief | master-packager | The brief states the contrast plan, the context list, the two halves, the familiar entity and the glance sentence (see `thumbnail-making`). |
| 7 | Protect it in the drawing | thumbnail-maker | The maker may not trade any of C1-C5 for detail or beauty. |
| 8 | Blind recognition | thumbnail-reader | Tests C5 and checks C1, C2 and C4 as a stranger would. |
| 9 | Pre-flight | orchestrator | Checks the card against C1-C5 before a viewer is spent. |
| 10 | The feed | packaging-lazy-viewer | Judges C1-C6 together in the blind feed, then in the debrief names the defects by test number. |
| 11 | Repair | master-packager | Finds the root cause by test number (C1-C6), then fixes, replaces or switches style. |

## Debrief language

The viewer's debrief labels every defect with the test it failed (C1-C6). The master-packager's revision log answers each label, so a failure is always traced to one test and one cause, never to "it did not feel right".
