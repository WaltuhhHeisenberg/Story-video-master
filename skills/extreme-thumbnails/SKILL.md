---
name: extreme-thumbnails
description: Extreme-level thumbnail system for a story-driven history and science YouTube channel, built on three styles (Impossible Object hook, Unsolved Mystery / Censored Detail, Counter-Intuitive Truth). Use whenever the user wants thumbnail ideas, concepts, text, a designer brief, an AI image prompt, or a fix for a weak thumbnail, even if they only say "make the thumbnail better". Defines surface-level versus extreme-level work and requires 15+ concepts, kill tests and designer-ready briefs.
---

# Thumbnail Playbook (extreme-level standard)

This is the full standard. Apply all of it before producing any thumbnail concept. The thumbnail is the single biggest lever on whether the video gets clicked, so it gets the most rigorous process in the whole workflow.

## What "extreme level" means (and what surface level looks like)

**Surface level (this is a fail):** a first-idea concept; a portrait, an archival photo, the finished machine, a generic prop (atom, light bulb); text that explains the image; fewer than 15 concepts; concepts made without studying the outliers.

**Extreme level (this is the bar):** YouTube shows 30-40 thumbnails in the feed, search or homepage, and the chances of a click are low. An extreme thumbnail is built against that crowd: it studies the saved outlier thumbnails first (the active batches in `research/outliers/`, the run's `<run folder>/research/outliers/` first, then the plugin's; layout in `research/README.md`; real images in `thumbs/`; research new ones with `python scripts/outlier_store.py save` when none is active), interrupts the pattern as hard as possible and opens a stronger curiosity gap than any of them, so the viewer does not scroll away.

## The judge: how the click is decided (read before making anything)

The packaging is judged by the `packaging-lazy-viewer`, who clicks exactly one card in the whole feed: the card that is **highest** on these six tests. Being acceptable is a loss. Full explanation, checks and the scorecard: `skills/extreme-thumbnails/references/viewer-psychology.md`. In short:

- **C1 Contrast:** one element is the loudest thing on the card AND stands out against the crowd of outliers.
- **C2 Mystery with the least context:** the smallest amount of information that still forms a question. One subject, one gap. Nothing that answers it.
- **C3 Two halves of a story:** the picture is half, the title is the other half, neither complete alone, nothing spoiled.
- **C4 Familiar entity (optional):** something known at a glance (never a named person), only if it adds no context.
- **C5 Easily understandable:** one glance on a phone, no decoding. Clear beats clever.
- **C6 Underdog:** the card is shown with a low view count, so it must be stronger than the biggest cards, not just good.

Every concept is written as Half A (picture) / Half B (title) / the join (what the video pays off) before anything else, and scored on the scorecard in that file.

## A few style discussed below(not rigid, they establish a strong curiosity gap, you can even create a style yourself like these but they must establish a strong curiosity gap):

### 1. The "Impossible Object" Hook
Zoom in on one everyday, recognizable object that seems wildly out of place beside a serious, massive historical consequence. Do not show the whole finished machine or a standard archival photo. This object is always off video.
- Mechanism: a mundane object (thermos, chocolate, sewing needle, bicycle lock) placed next to a huge consequence. The brain tries to solve "what does this household item have to do with that?" and can only resolve it by clicking.
- Execution notes: the object is hero-sized and sharply lit. The consequence is implied or half-visible (a shadow, a silhouette, a scorched edge, a headline-scale number), not explained. One surprising pairing only; two competing riddles cancel each other.
- Fail: the object is only loosely related, or the connection can be guessed from the image alone.

### 2. The Unsolved Mystery / Censored Detail
Show an unmistakable blueprint, map or mechanical part where one vital piece is visibly removed, circled or blacked out, paired with a short prompt.
- Mechanism: people hate incomplete patterns. 99% complete with one missing link makes the open gap feel unbearable.
- Execution notes: the whole object must be instantly recognizable so the gap is obvious. The missing or marked piece is the only thing that pops (a red circle, a clean black bar, a hole where the part should be). Prompt text is tiny in word count, e.g. "The missing 1%" or "The fatal mistake".
- Fail: the object is obscure (no one notices what is missing), several things are missing, or the censored area is so big the pattern stops feeling incomplete.

### 3. The Counter-Intuitive Truth (Subverting Expectations)
Challenge what casual viewers assume they already know by showing the raw, gritty, low-tech reality in place of the romanticized version (chalkboards and genius physicists versus a plumbing issue, a machinist's hand tool, manual labor).
- Mechanism: it shatters the story people think they know. The reaction is "Wait, that can't be right... how did that happen?"
- Execution notes: show the unglamorous reality as the hero, with the expected image (formulas, lab coats, the famous finished product) deliberately absent or pushed to the background.

## Rules that apply to every style
- **Off-context.** No named people, no story-type labels, no text that explains the story. The image and text provoke; the video answers.
- **Text:** one or two words, usually a question or a clipped claim ("victim?", "genius?", "The missing 1%"). The text adds a second question to the image, never repeats it.
- **Image + title are complements.** The title makes the broad human promise containing the keyword; the thumbnail adds the unexplained twist. They must not say the same thing.
- **One focal point, one idea.** If you can't describe the thumbnail in one sentence, it is too busy.
- **Familiar entity (C4) vs off-context.** A familiar entity is a thing, not a person: an everyday object, a generic cartoon figure, an animal, a place type. Never a named person, a real likeness or a logo.
- **Least context (C2).** After the concept works, remove one more element. If the question survives, keep it removed.
- **Keyword connection.** The keyword should still be legible in spirit (the object or subject belongs to the keyword's world) so the click matches the search demand.
- **Truth, in one place.** The picture is not limited to literal scenes from the video: a symbol, an exaggerated object or a visual metaphor is allowed when it raises the question (video truths do not limit the thumbnail). Two lines still hold: the title and the on-image text never state a falsehood, and the question the card raises is one the video answers. A card whose question the video cannot answer is a bait-and-switch and fails.
- CHANNEL STYLE: detailed, realistic-looking lit illustration (shaded objects from the icon library, soft shadows, glow, real type), never flat MS Paint fills. Every object must be recognisable to a stranger in half a second (see skill thumbnail-making).

## The kill tests (run on every concept)
0. **Scorecard.** Score the concept on C1-C6 (`skills/extreme-thumbnails/references/viewer-psychology.md`). Any FAIL on C1, C2, C3 or C5 kills it, and a WEAK on C6 kills it.
1. **Crowd test (strict C6).** Explain why the viewer clicks this thumbnail while 40 others compete for the click. Use the saved outliers in `research/outliers/`, place the concept among them, be strict and use plain common sense without pretending. No honest answer: kill it.
2. **Question test (C2).** Does it raise a question that can only be resolved by clicking, between 40 other thumbnails? If not, kill it.
3. **Glance test (C1, C5).** At phone-feed size, in one second, is there a single clear focal point? If not, kill it.
4. **Cliché test.** Have a hundred other videos used this exact image (generic atom, light bulb, portrait with arrows)? If so, kill it or push it further.

Deliver 1 primary thumbnail and 2 variants (ideally from different styles), each with a drawable designer brief.
