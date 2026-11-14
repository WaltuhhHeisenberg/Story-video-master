---
name: packaging-cycle
description: "Runs the stress-test cycle on a video's packaging (title + thumbnail) between the master-packager (creates and fixes), the thumbnail-maker (draws the real thumbnail image) and the lazy-viewer (a viewer 3x worse than average who scrolls 3x faster). The lazy-viewer is shown a BLIND FEED of real images: the candidate thumbnail hidden among every saved outlier thumbnail (from research/outliers), with no idea which card is new, and he must click one. The packaging passes only when he clicks the candidate with a real pull, over at least 3 rounds. Use after a Video Brief exists, or whenever the user asks to test, stress-test, fix, loop on, iterate or \"run the packaging cycle\" on a title and thumbnail, or wants finished, tested packaging for a video. Also use when the user says the packaging \"isn't clicking\" and wants it recreated."
---

# Packaging Cycle

> **Agent names in this plugin:** the packaging judge is `story-video-master:packaging-lazy-viewer` (written "lazy-viewer" below); the script judge is a different agent, `story-video-master:script-lazy-viewer`. Do not mix them. The thumbnail drawer is `story-video-master:thumbnail-maker`.

The packaging is a title and a thumbnail. It passes only when the **lazy-viewer**, who gives a card half a second and scrolls 3x faster than normal, is shown a feed made of **every saved outlier thumbnail plus the candidate**, all as real images, is **never told which card is the candidate**, and **clicks the candidate with a real pull**. The **master-packager** creates and repairs the packaging, the **thumbnail-maker** turns his brief into the real image. This skill runs them against the viewer for **at least 3 rounds**.

Subagents cannot launch other subagents, so you (the main session) run the loop, spawn each agent, build the feed, and carry the cards between them.

## Where the outlier data is stored (exact)

The outlier data is the researched top-performing titles with their view counts and their **real thumbnail images**. It lives in `research/outliers/<batch>/` (batch = `<date>-<keyword-slug>`): `outliers.json`, `thumbs/<video_id>.jpg`, `keywords.json`, `analysis.md`, `meta.json` with the expiry. Full layout and rules: `research/README.md`. There are two stores with the same layout:

| Store | Path | Notes |
|---|---|---|
| **Run store** | `<run folder>/research/outliers/` | written by Stage 1 in this run. `<run folder>` is the calling workflow's folder: `story-video-run/<video-slug>/`; if the cycle runs alone, use `packaging-cycle/<video-slug>/` |
| **Plugin store** | `research/outliers/` in the plugin | shipped inside the `.plugin` by Stage 8 (`scripts/finish_project.py`); outlier data is used as active until its `outliers_expires_at` (60 days after saving; the keyword analysis is valid 14 days); the batch is kept for 1 year, then deleted |

## The psychology the cycle enforces

The viewer clicks the one card that is highest on six tests: C1 contrast, C2 a mystery with the least context, C3 title and thumbnail as two halves of a story without spoiling, C4 a familiar entity (optional), C5 easily understandable, and C6 the underdog test (the candidate is shown with a low view count). Full definitions, checks and the scorecard: `skills/extreme-thumbnails/references/viewer-psychology.md`. Every stage below applies it: the packager designs for it, the maker protects it, the reader and the pre-flight check it, the viewer judges it, and every defect is traced back to a test number.

## Inputs

- A Video Brief: keyword, story, internal story type. If none exists, run the `story-video-idea-system` skill first (or ask the user for the keyword and the story).
- **The full outlier data (compulsory), found in this order:**
  1. `python scripts/outlier_store.py status --store <run folder>/research/outliers --store research/outliers` shows every batch and whether it is active or EXPIRED, and how many outliers lack an image.
  2. Active batches in the run store, then in the plugin store: use them all (duplicates are merged).
  3. Outlier data the user pastes or attaches this session: save it first with `python scripts/outlier_store.py save --store <run folder>/research/outliers --keyword "<keyword>" --outliers <file>` (thumbnail images the user attached go in `--thumbs-dir`).
  4. If nothing is active (no batch, or the 2-month outlier window is over; older batches stay on disk for one year but are not used as active data): ask the user one short question whether to run fresh outlier research now. If yes, research it per `skills/extreme-thumbnails/SKILL.md` (thumbnails over 100k views in this niche and for this keyword, PLUS at least 4 videos of the niche under 50,000 views as decoys, flagged `"decoy": true`, each with its real thumbnail) and save it with `save`. **Never run the cycle on an empty or partial feed.**
- **Every outlier needs a real thumbnail image.** If `status` shows missing images, run `python scripts/outlier_store.py fetch-thumbs --batch-dir <batch folder>`. If it still cannot get some (no network, video removed), ask the user to put those thumbnails in the batch's `thumbs/` as `<video_id>.jpg`. Do not drop an outlier to make the feed pass.
- Use **all** of it. Do not pick the "relevant" ones, drop the strong ones, or cap the count. Fewer than 15 outliers still runs, but say so in the delivery: the feed is thinner than a real 30-40 card feed.

## Setup

Create a working folder `packaging-cycle/<video-slug>/` and a task list with one task per round plus a final delivery task. Add tasks as rounds are added.

Merge the stored data into one file, once, before round 1:
`python scripts/outlier_store.py merge --store <run folder>/research/outliers --store research/outliers --out packaging-cycle/<video-slug>/outliers.json --require-images`
(exit 3 = some outlier has no image: fix as above and re-run). The merged file has absolute image paths and all the extras (views, channel, url).

Inside the working folder:

| File | Who may read it |
|---|---|
| `outliers.json` (full outlier data: views, channels, links, image paths) | master-packager only |
| `round-N-packaging.md` (his concept log, designer brief, card) | you, master-packager, thumbnail-maker |
| `round-N-card.json`, `round-N-thumbnail.png`, `round-N-thumbnail_phone.png`, `round-N-scene.json` | you, master-packager, thumbnail-maker |
| `round-N-feed-key.json` (which card position is the candidate, which outlier is where) | **you only. Never shown to the viewer, never pasted in a prompt.** |
| `round-N-verdict.md`, `round-N-debrief.md` | you, master-packager |

The feed the viewer sees is built into a **separate neutral folder** (`_feeds/<random>/`) that holds nothing but the feed and its neutrally named images.

## The rules of the cycle

- **Minimum 3 rounds, always.** A round is one master-packager pass, one thumbnail drawn, one blind feed, one lazy-viewer verdict.
- **A round PASSES only if** the viewer clicked the candidate **and** his pull was `REAL` (not `FORCED`). Clicking an outlier, or clicking the candidate as a forced least-bad pick, is a FAIL.
- **Stop when:** at least 3 rounds are complete AND the **latest 2 rounds both passed**. One lucky pass is not the finish. After a first pass the next round is a **hardening round**: the master-packager builds a stronger version from the weakest point and the closest rival the viewer named, the thumbnail-maker draws it, and it goes through a new blind feed.
- **Maximum 8 rounds.** If round 8 has not produced two consecutive passes, stop and report honestly (see Delivery).
- **A fresh lazy-viewer every round and a fresh shuffle every round.** Never continue a previous round's viewer. He judges every feed with no memory.
- **The master-packager sees everything except the key:** the brief, the full outlier data and the outlier images (he can open them with Read), his previous card and image, the last blind verdict and the debrief. He is told which outlier won a failed round.
- **Do not edit the cards yourself.** You may only pass the packager's brief and card to the thumbnail-maker, pass the finished card to the script, and flag problems back. Do not rewrite his title or thumbnail text, and do not redraw the image.
- **Never re-run an unchanged card to get a different result.** Every round needs a materially different card (a fix, a replacement or a hardening). The only exception: a round **voided for a leak** (see below) is re-run once, with the same card and image, a fresh feed and a fresh viewer.

## The blind: the viewer must never learn which card is the candidate

This is the heart of the cycle. Before every feed, check each of these.

1. **Real images only, same treatment for every card.** All cards, outliers and candidate, are images. `scripts/build_feed.py` re-encodes every one to the same size and format (1280 x 720 JPEG, no metadata) and gives it a neutral name (`card-07.jpg`). It refuses to build if any card has no image. (A text-description feed exists only behind `--allow-descriptions`, is a weaker test, and needs the user's agreement.)
2. **Channels, dates and links stripped; views shown on every card (view bias).** The viewer skips a card under 50,000 views unless it gives him a strong reason, so every card prints one line "Views: ..." and nothing else of the metadata (no channel, date, link, "ago"). Outliers show their real count. The candidate shows a believable low count (random 0 to 10). Since a lone low count would single the candidate out, the feed needs at least 3 outliers under 50,000 views as decoys (`"decoy": true`, with real thumbnails); `build_feed.py` refuses without them. Never show the candidate with a high count to make it pass, and never drop an outlier to make the feed easier.
3. **Neutral labels and a random position.** Cards are numbered by on-screen position only. The candidate's slot is random each round and never in the first 3 positions (worst case: the best real estate goes to the outliers). The script writes the position only to the private key file.
4. **The candidate image carries no mark.** Open the candidate's image with Read before building: no label, version number, watermark, "test" or anything that is not part of the thumbnail itself.
5. **Psychology and rules are checked before the feed, not by the viewer.** First the psychology: read the packager's scorecard for the card and check it against the image you just opened. The loudest element in the image is the planned one (C1); nothing on the image is outside the brief's context list (C2); the title and the image each feel incomplete alone, do not repeat each other and do not give the ending away (C3); the thumbnail-reader's glance sentence matches the brief's (C5). If a test fails, send it back once (concept and title to the packager, drawing to the thumbnail-maker) before spending a viewer. Then the rules: the viewer does not police the channel's rules in the blind pass (a name or a story label would single the candidate out). **You** check the candidate (title and the image you just opened) against the packager's rules 1-3 (no named person, no story-type label, keyword present, nothing the video cannot pay off) and check that the image's text equals the card's `text`. If it breaks one, send it back once (to the packager for the concept, to the thumbnail-maker for the drawing) before spending a viewer.
6. **A neutral prompt.** Give the viewer the feed and nothing else. Never say test, candidate, ours, new, packaging, channel, round, brief or keyword, and never put the video's slug in a path he can see. Paste the content of the built `feed.md` into the prompt (it lists the image paths). The prompt is exactly:
   > Here is your feed of N cards. Open each card's image with Read, in order, scan fast, and click one. Follow your output format.

   followed by the text of `feed.md`.
7. **The viewer can only Read.** Do not give him the key, the packaging files, the outlier file or any other path.
8. **Different-looking is allowed, and left honest.** The channel's illustrated look can differ from photographic outliers (that is real, and a pattern interrupt only helps if it also gives a question). Do not disguise it and do not make the drawing worse to blend in.

## Round procedure

**Before round 1:** run the Inputs and Setup steps above so `outliers.json` exists with a real image for every outlier. Note the outlier count.

**Round 1**
1. Spawn `story-video-master:master-packager` with the Video Brief and the full `outliers.json`. Ask for a Packaging Card as the JSON object in his hand-off format, concept log, a **buildable designer brief** (format in `skills/thumbnail-making/SKILL.md`: elements with recognition cues, what the viewer must conclude) for the primary and for each of the 2 variants, and the 2 variants' cards. Tell him to read `skills/extreme-thumbnails/references/viewer-psychology.md` first. Save as `round-1-packaging.md`; save the primary card as `round-1-card.json` (variants as `variant-A-card.json`, `variant-B-card.json`).
   **Psychology gate (mandatory, before anything is drawn):** `python scripts/check_scorecard.py scorecard --file packaging-cycle/<video-slug>/round-1-packaging.md --expect 3`. Exit 1 = send the printed PROBLEM lines back to the master-packager once and re-run; do not draw, build a feed or spend a viewer on a card that has not passed.
2. Spawn `story-video-master:thumbnail-maker` with the primary card, its designer brief (including its psychological spec) and the output folder, and tell it to read `skills/extreme-thumbnails/references/viewer-psychology.md`. It returns `round-1-thumbnail.png`, the phone preview, `round-1-scene.json` and the card with `image` filled in (overwrite `round-1-card.json`).
   **Recognition test (before any viewer):** spawn a fresh `story-video-master:thumbnail-reader` with ONLY the two PNG paths. Compare its reading with the brief's elements and "what the viewer must conclude" (rules in the thumbnail-making skill). On any miss, send the miss list to `thumbnail-maker`, re-render and test with a **fresh** reader; at most 3 loops, then continue with the best image and record the remaining weakness. Save the last reading as `round-1-reader.md`.
3. Pre-flight (blind rules 4 and 5): open the image with Read, check it. Then build the feed:
   `python scripts/build_feed.py build --outliers packaging-cycle/<video-slug>/outliers.json --card packaging-cycle/<video-slug>/round-1-card.json --feeds-root _feeds --key packaging-cycle/<video-slug>/round-1-feed-key.json`
4. Spawn a fresh `story-video-master:packaging-lazy-viewer` with the neutral prompt only. Save his reply as `round-1-verdict.md` before anything else happens.
5. Read the result: `python scripts/build_feed.py verdict --key packaging-cycle/<video-slug>/round-1-feed-key.json --verdict packaging-cycle/<video-slug>/round-1-verdict.md` (exit 0 = PASS, 1 = FAIL, 2 = unreadable: ask him to restate his verdict in the format).
6. **Debrief the same viewer instance** (the verdict is already saved and locked) with a `SendMessage`: "Your choice is locked. Card NN was the card under test; you did not know. Give the debrief." Use the candidate's position from the key. Save it as `round-1-debrief.md`. His defects are labelled C1-C6. **Debrief gate:** `python scripts/check_scorecard.py debrief --file packaging-cycle/<video-slug>/round-1-debrief.md`; exit 1 = ask the same viewer to restate the debrief with a C label on every defect. Pass the labels to the packager unchanged. If the instance cannot be continued, spawn a fresh viewer with the same feed, his saved verdict and the reveal, labelled a post-mortem, not a judgment.
7. If the debrief names a tell, the round is **voided for a leak**: fix the tell, rebuild the feed, spawn a new viewer, and run the round once more with the same card and image.

**Round N (2 and later)**
1. Spawn `master-packager` (told to read `skills/extreme-thumbnails/references/viewer-psychology.md` first) with: the Video Brief, the full `outliers.json`, the previous round's packaging file and image, the previous verdict and the debrief. Tell him which outlier took the click if one did (use the key).
   - After a FAIL: find root causes **per test label (C1-C6)** and fix, recreate or switch style; learn which test the winning outlier beat the candidate on and the mechanism it used, never copy its image.
   - After a first PASS: run a hardening round (strengthen the weakest point, move away from the closest rival).
2. Run the **psychology gate** on `round-N-packaging.md` (`python scripts/check_scorecard.py scorecard --file ... --expect 1`; same handling as round 1) and the **debrief gate** on the previous debrief before the packager starts. Then spawn `thumbnail-maker` (told to read `skills/extreme-thumbnails/references/viewer-psychology.md`) with the new card, the new designer brief, the previous image and the debrief, then run the same **recognition test** (fresh `thumbnail-reader`, only the PNG paths, up to 3 fix loops) and save `round-N-reader.md`.
3. Pre-flight, build a fresh feed (a new random shuffle and a new random folder), spawn a fresh viewer, save the verdict, read the result, debrief, save.
4. Record the round in a running log: round number, who got the click (candidate or which outlier), pull strength, candidate position, the most serious defect, what the packager changed, what the maker changed.

**Between rounds,** check that the master-packager's changes answer the viewer's defects and the winner's mechanism, and that the new image really shows the new brief. If he resubmitted the same card with cosmetic edits, send it back once with that instruction before spending a viewer.

## Final pass

When the stop condition is met, spawn `thumbnail-maker` once for each of the 2 variants (each also passes the blind `thumbnail-reader` test), then run each through its own blind feed (full outliers + that variant, fresh shuffle, fresh viewer, with debrief), so the user knows how each alternative performs against the same crowd. Do not count these toward the rounds.

## Delivery

Give the user, in the reply:

1. **The winning package:** title, the thumbnail image (present the PNG file `round-N-thumbnail.png`, with its `round-N-scene.json`), the on-image text, and the primary designer brief (full brief in the file).
2. **The 2 variants** with their images and their blind-feed results (clicked or not, pull strength, which outlier beat them).
3. **A round log table:** round, who got the click (the candidate or which outlier title), pull (REAL/FORCED), candidate position in the feed, most serious defect with its test label (C1-C6), what changed.
4. **The feed:** how many outliers the candidate was tested against, which batch(es) of `research/outliers/` they came from, and their saved dates.
5. **The remaining weakness:** the one thing the viewer says would lose the click on a worse day, and the closest rival outlier.
6. **Honest status:** state clearly that this is a simulated worst-case viewer picking from real images, not measured data, and that the real test is the first impressions on YouTube. The candidate image is the plugin's own lit illustration, which a human designer can redo from the brief. If round 8 ended without two consecutive passes, say so plainly, deliver the best attempt, name what is blocking it, and suggest whether the problem looks like the concept, the drawing, the keyword framing or the story angle. **Never reveal the candidate to the viewer, shrink or soften the feed, or loosen the pass rule to get a click.** A click earned that way would say nothing about the real feed.

Send the working files (`round-N-packaging.md`, `round-N-verdict.md`, `round-N-debrief.md`) only if the user wants them. Never send the key files to the viewer.
