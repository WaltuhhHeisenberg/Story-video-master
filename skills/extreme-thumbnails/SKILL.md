---
name: extreme-thumbnails
description: Extreme-level thumbnail system for a story-driven history and science YouTube channel, built on three styles (Impossible Object hook, Unsolved Mystery / Censored Detail, Counter-Intuitive Truth). Use whenever the user wants thumbnail ideas, concepts, text, a designer brief, an AI image prompt, or a fix for a weak thumbnail, even if they only say "make the thumbnail better". Defines surface-level versus extreme-level work and requires 15+ concepts, kill tests and designer-ready briefs.
---

# Thumbnail Playbook (extreme-level standard)

This is the full standard. Apply all of it before producing any thumbnail concept. The thumbnail is the single biggest lever on whether the video gets clicked, so it gets the most rigorous process in the whole workflow.

## What "extreme level" means (and what surface level looks like)

**Surface level (this is a fail):**
Look into latest outlier analysis(saved/new) with thumbnails over 100k views. Saved = the active batches in `research/outliers/` (the run's `<run folder>/research/outliers/` first, then the plugin's; layout in `research/README.md`), with their real thumbnail images in `thumbs/`. New = research it fresh and save it there with `python scripts/outlier_store.py save`.

**Extreme level (this is the bar):**
Youtube shows 30-40 thumbnails in the feed/search/homepage. An extreme thumbnail stands out in those 30-40 thumbnails. The chances are really low to get a click so you have to interrupt the pattern hardest possible to grab the attention immediately and establish a strong curiosity gap than others so viewer does not click away.

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
- **Keyword connection.** The keyword should still be legible in spirit (the object or subject belongs to the keyword's world) so the click matches the search demand.
- **Honest payoff.** Every promise in the thumbnail is paid off in the video.
- CHANNEL STYLE: detailed, realistic-looking lit illustration (shaded objects from the icon library, soft shadows, glow, real type), never flat MS Paint fills. Every object must be recognisable to a stranger in half a second (see skill thumbnail-making).

## The kill tests (run on every concept)
1. **Explain why the viewer will click the thumbnail while he has other 40 thumbnails competing for the click(use the saved outlier data in `research/outliers/` to test the thumbnail between the others). Do it in the most strict way possible and use literal common sense without pretending anything. If you have no answer, kill it.
2. **does it raise a question the viewer can only resolve by clicking between 40 other thumbnails? If no, kill.
3. **at phone-feed size, in one second, is there a single clear focal point? If no, kill.
4. **does it have a hundred other videos used this exact image (generic atom, light bulb, portrait with arrows)? If yes, kill or push further.

**MOST IMPORTANTLY, VIDEO TRUTHS DO NOT LIMIT THE THUMBNAILS**.
Give 1 primary thumbnail at the end.