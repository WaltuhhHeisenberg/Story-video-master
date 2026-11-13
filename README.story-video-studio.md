# Story Video Studio

A plugin for a story-driven YouTube channel (history and science told as human drama). It takes a video from keyword to a stress-tested title and thumbnail.

## What's inside

**Skills**
- `story-video-idea-system`: keyword-led idea workflow. Outlier research is optional (it asks); keyword research is compulsory. One highest-search-rate keyword frames the whole video. Four hidden story types. Off-context titles. Outputs a Video Brief.
- `extreme-thumbnails`: the extreme-level thumbnail standard. Three styles (Impossible Object, Unsolved Mystery / Censored Detail, Counter-Intuitive Truth), 15+ concepts, kill tests, designer-ready briefs.
- `thumbnail-making`: turns the master-packager's drawable designer brief into the real thumbnail image (1280x720, detailed lit illustration; older MS Paint flat style retired in v2.2) with the design skill's method and `scripts/make_thumbnail.py`; no card reaches the viewer without a real image.
- `packaging-cycle`: runs the agents against each other for at least 3 rounds (maximum 8). The candidate card is hidden inside a blind feed of real images made of every saved outlier thumbnail (stored in `research/outliers/`, see `research/README.md`); the viewer is never told which card is the candidate and must click one. Built by `scripts/build_feed.py`.

**Agents**
- `lazy-viewer`: a viewer 3x worse than average who scrolls 3x faster and gives each card about half a second. He gets a feed of 30-40 cards, does not know which one is new, and clicks exactly one, stating whether the pull was REAL or FORCED. If he does not click the candidate with a real pull, the packaging has failed. After his verdict is locked he is told which card was the candidate and debriefs the defects; he never writes the fix.
- `thumbnail-maker`: draws the real thumbnail image from the designer brief, renders a phone-size preview, checks it, and writes the card's description fields to match the picture. He draws the brief; he never redesigns it.
- `master-packager`: studies the full outlier data (and the outlier images), creates the packaging, diagnoses the blind verdict and debrief (including which outlier beat him), fixes or fully recreates the weak parts, and hands the new card back as JSON.

## How the cycle works

1. Build a Video Brief with `story-video-idea-system`.
2. `packaging-cycle` runs round 1: the master-packager creates, the thumbnail-maker draws the real image, the card is mixed into the full outlier feed (real images, same size and format, no metadata, shuffled, never in the first 3 slots), a fresh lazy-viewer clicks one card.
3. Every round where he clicks an outlier, or clicks the candidate only as a forced pick, triggers a root-cause fix or recreation, then a new feed and another fresh viewer.
4. A first pass does not end the cycle. The next round is a hardening round that builds a stronger version.
5. The cycle ends when at least 3 rounds are done and the latest 2 rounds both ended with the viewer clicking the candidate with a real pull (maximum 8 rounds).

## Note

The lazy viewer is a simulated worst-case audience. It stress-tests packaging against the real outlier crowd; it does not predict real click-through rates. The candidate is never revealed to the viewer before his choice is locked.
