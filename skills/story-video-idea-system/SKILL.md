---
name: story-video-idea-system
description: Turn a keyword into a complete story-driven YouTube video brief (keyword, hidden story type, off-context titles, thumbnail text, story spine) for a channel about history, science and invention told as human drama. Use whenever the user wants video ideas, topics, titles, thumbnails, a video plan or a story outline for this channel, mentions keyword research, discovery/rivalry/stolen-genius/dangerous-idea stories, or asks "what should my next video be", even if they don't name the system. Keyword research always runs; outlier research is optional and must be asked about first.
---

# Story Video Idea System

This channel wins on **stories about people**, not on explaining concepts. Viewers come for human drama (mistakes, hatred, injustice, persecution) and stay for the story. The topic is chosen by **search demand**, and one keyword then frames the entire video.

## The workflow

Run these steps in order. Do not skip step 2.

### 1. Ask about outlier research (ask the user)

Before doing anything else, ask the user one short question: should this run also include outlier research (finding videos that massively outperformed their channel's average, as extra inspiration)?

- This channel relies on keyword research, not outlier data, so the default suggestion is **no**. Ask anyway; it is the user's call every time.
- If yes, do it as a supporting step after keyword research, never instead of it. Outliers can suggest angles or story framing for a keyword already chosen; they never pick the topic.
- If the user already said yes or no in their request, don't ask again.
- If the outlier data is already in the plugin then it is compulsory. Check where it lives: `python scripts/outlier_store.py status --store story-video-run/<video-slug>/research/outliers --store research/outliers`. Any batch listed as active (inside its window: keywords 14 days, outliers 60 days) must be used in this run. The plugin's own store is `research/outliers/<batch>/` (layout and rules: `research/README.md`).
- The packaging stage tests the thumbnail inside a blind feed made of this data, so it needs every outlier's title, view count and REAL thumbnail image. If there is no active batch, say that in your question and suggest yes.

### 2. Keyword research (compulsory)

Every video starts here. Without a keyword the video has no demand behind it, and everything downstream (title, thumbnail, story) is built around the keyword.

1. Build a pool of 8-15 candidate keywords in the user's area (their topic, era, invention, or a story type they want). Mine web search, YouTube/Google autocomplete, "people also ask", related searches, and Google Trends where reachable.
2. Get search-rate evidence for each candidate. Best source is data the user supplies (vidIQ, TubeBuddy, Keyword Planner, Ahrefs, etc.). If they have none, use the best available proxies (autocomplete position, trend interest, result volume) and **say plainly that these are proxies, not true volumes**. Never invent search volume numbers.
3. Rank candidates and pick **the one keyword with the highest search rate**. That is the video's keyword. Show the ranked table so the user can see why it won, and ask the user to confirm if the top two are close or the evidence is only proxies.

The keyword must have low competition but high demand. It can be a topic too

If the user already has a keyword, still sanity-check it against a few alternatives, then proceed.

If you can't find the keyword/topic, then find the a video in the niche which is 3-15 years old and got more than 100x then there average (breakout), pivot the topic a bit to a different angle and get a new topic or replace the main entity and keep the same angle. If you still can't find the topic, repeat this process again and again.

Then save(at the time after autofix, the end) that exact data(keyword analysis, outlier analysis in whole, full thumbnails with their view count,etc and keywords with their analysis) in the plugin with two validity windows: the keyword analysis is valid for 2 weeks (14 days), the outlier analysis for 2 months (60 days). Use each part inside its window and do not research it again; after a window is over, ask the user before researching that part again. Never delete older batches when a window ends; they are deleted only after 1 year. Alongside the outliers, save at least 4 videos of the niche under 50,000 views as decoys (`"decoy": true`, real thumbnail, real view count): the packaging viewer skips cards under 50k views, so the feed needs low-view cards other than the candidate.

**Where the outlier data is stored (exact).** In `research/outliers/<batch>/` (batch = `<date>-<keyword-slug>`; full layout and rules in `research/README.md`):
- `outliers.json`: every outlier with title, view count, channel, url, video id and published date;
- `thumbs/<video_id>.jpg`: the real thumbnail image of every outlier, none skipped;
- `keywords.json`: the keyword analysis; `analysis.md`: the outlier analysis in whole;
- `meta.json`: saved date, `keywords_expires_at` (+14 days), `outliers_expires_at` (+60 days) and `purge_after` (+365 days).
During the run the batch is written to the run store `story-video-run/<video-slug>/research/outliers/` (the installed plugin may be read-only): `python scripts/outlier_store.py save --store story-video-run/<video-slug>/research/outliers --keyword "<keyword>" --outliers <found.json> --keywords <keywords.json> --analysis <analysis.md>`, then `python scripts/outlier_store.py fetch-thumbs --batch-dir <the batch folder>` to download every thumbnail. If a thumbnail cannot be downloaded, ask the user to supply it (put it in `thumbs/` as `<video_id>.jpg`); never drop an outlier and never invent a view count. Stage 8 (`scripts/finish_project.py`) copies the batch into the plugin's `research/outliers/` and deletes expired batches. Save the images now: Stage 2 needs them.

**Check every claim in a title option before it goes anywhere.** A title or hook may not state a span, count or outcome the story does not support (a run once promised "refused to follow for 20 years" when the facts were: adopted in the first clinic, 18 years between the rule and his death). Verify it in the fact ledger or change the title.

**Thumbnails of outliers.** The sandbox shell cannot reach i.ytimg.com. Right after saving the outlier batch, run `fetch-thumbs`; if any image is missing, ask the user to upload the missing thumbnails (list their numbers, titles and video ids) in the SAME message as the keyword result, and keep working on other stages meanwhile. Never skip an outlier.

### 3. Match the keyword to a story

Find the true story behind the keyword and sort it into one of four story types. The type is an internal tool for shaping the story. It is never shown to the viewer.

| Type | What drives it | Shape |
|---|---|---|
| Accidental / stupid discovery | Brilliant people make a massive mistake that accidentally changes the world | Setup, the blunder, the "wait, what?" moment, the consequence for millions |
| Intellectual rivalry | Two geniuses who hate each other | Origin of the feud, escalation, who actually deserved credit, the aftermath |
| Forgotten / stolen genius | Someone erased from textbooks or robbed of credit; injustice drives engagement | The work, the theft or erasure, who got the glory, the late justice or lack of it |
| Dangerous idea | A scientist faces execution, exile or backlash before being proven right | The idea, the backlash, the cost to the person, the vindication |

A keyword can fit more than one type. Pick the one with the strongest emotional engine and name it in the brief. If the keyword's true story fits none of the four, say so and suggest the nearest keyword that does rather than forcing it.

### 4. Frame the whole video around the keyword

The keyword is the spine, not a tag. Check that it shows up in the title or promise, as the through-line of the story, and in the description. Every story beat should answer the question the keyword implies.

### 5. Package: title and thumbnail text

Both stay **off-context**: they provoke curiosity about the story without giving away which story it is.

**Title rules**
- Never name the person or people in the story.
- Never name the story type ("rivalry", "stolen genius", etc.) or use the type's own label.
- Keep the keyword in the title (it is the demand signal), but leave the identity of the story unrevealed.
- Make a bold, broad, human claim about the keyword. Offer 5 options.
- Never repeat same words from the title.

Style references (illustrating the register, not templates to copy word for word):
- the invention that started the industrial revolution
- the lost science we aren't supposed to know
- the fraud that built the modern world
- how the steam engine changed everything

**Thumbnails: go to the extreme, not the surface.** Thumbnails decide the click, so they get the most rigorous work in this skill. Before producing any thumbnail concept, read the `extreme-thumbnails` skill in full. The standard in short:
- Mine the actual story for true, specific physical details (objects, tools, materials, numbers) and build the thumbnail from one of them, rather than reaching for a portrait, an archival photo, the finished machine or a generic prop.
- Generate at least 15 concepts across the channel's three thumbnail styles, then kill most of them with a one-line reason each, using the kill tests in the reference.
- Deliver 1 primary and 2 variants (ideally from different styles), each with a designer-ready brief precise enough that two designers would produce nearly the same image.

The three styles (full mechanics, execution notes and fail cases are in the reference):
1. **Impossible Object Hook:** one mundane, everyday object zoomed in next to a massive historical consequence, so the viewer can only resolve the riddle by clicking.
2. **Unsolved Mystery / Censored Detail:** an unmistakable blueprint, map or part with one vital piece removed, circled or blacked out, so the missing 1% itches.
3. **Counter-Intuitive Truth:** the raw, gritty, low-tech reality that subverts the romanticized story. It must be true and paid off in the video.

**Thumbnail text rules**
- One or two words, usually a question that plants doubt about who is the hero or villain, or a clipped claim ("The missing 1%").
- Also off-context: no names, no type labels, no explanation of the story. The text adds a second question to the image; it never repeats the image or the title.
- Offer 3-5 text options. Style references: "victim?", "genius?".

### 6. Story spine

Write the beat-by-beat outline for the video. Two rules shape it:

- **Concepts stay shallow.** Explain the science or invention only as much as the viewer needs to feel the stakes. If a paragraph reads like a textbook (deep quantum mechanics, chemistry mechanisms, math derivations), cut it down to one plain-language sentence. The audience is here for the people.
- **Storytelling goes deepest.** Spend the detail on motives, emotions, specific scenes, turning points, cost to the people involved, and the moment of irony or injustice. Use concrete scenes (who was in the room, what they said or did) rather than summary.

Give: 6-10 story beats with one line each on what the viewer should feel, the turning point, and an ending that lands the human takeaway and ties back to the keyword.

**Do not write a hook or any opening lines here.** The idea stage does not write hooks. The script stage writes the hook, using the hook rules of the `story-explainer-scripts` skill.

## Output format

Deliver one **Video Brief**:

1. **Keyword** (winner) + ranked candidate table + evidence quality (real volumes or proxies)
2. **Story type** (internal) + one line on why it fits
3. **Title options** (5, off-context)
4. **Thumbnail package:** concept log (15+ concepts with the kill reasons), 1 primary + 2 variants with full designer briefs per the `extreme-thumbnails` skill, and 3-5 off-context text options
5. **Story spine** (beats, no hook)
6. **Outlier notes**, only if the user opted in or an active batch exists: the batch folder (`research/outliers/<batch>/`) and the few takeaways

If the user asks for several video ideas at once, run steps 2-6 per idea, with a distinct keyword for each, and offer them as separate briefs.

## Pitfalls to avoid

- Picking the topic first and hunting a keyword to justify it. The order is keyword, then story.
- Showing story-type names or figure names in titles or thumbnails.
- Letting concept explanation eat the runtime.
- Quoting search volumes that were not actually retrieved.
- Surface-level thumbnails: first-idea concepts, portraits, finished machines, generic props, or text that explains the image. Follow the `extreme-thumbnails` skill.
- A "counter-intuitive" thumbnail that is not actually true or not paid off in the video.

## Next step: stress-test the packaging

Once the Video Brief exists, do not treat the title and thumbnail as final. Run the `packaging-cycle` skill, which puts the packaging through at least 3 rounds before it is delivered: the `master-packager` creates the card, the `thumbnail-maker` draws the real image, and the `lazy-viewer` picks one card from a blind feed made of the saved outlier data (`research/outliers/`) with the candidate hidden in it. Offer this at the end of the brief, or run it directly if the user asked for a finished, tested package.
