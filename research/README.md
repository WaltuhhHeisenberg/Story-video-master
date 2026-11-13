# research/ - where researched data lives

`research/outliers/` is the **one place** the plugin keeps outlier research: the top-performing titles and their REAL thumbnail images (with view counts), the keyword analysis, and the outlier analysis in whole. It is empty until the first run that does outlier research.

```
research/outliers/<batch>/          batch = <date>-<keyword-slug>, one folder per research run
    meta.json        batch_id, keyword, saved_at, keywords_expires_at (saved_at + 14 days), outliers_expires_at / expires_at (saved_at + 60 days), purge_after (saved_at + 365 days), count
    outliers.json    every outlier: title, views, channel, url, video_id, published, text, image
    keywords.json    the keyword analysis (candidates, evidence, ranking)
    analysis.md      the outlier analysis in whole
    thumbs/          the real thumbnail images, 1280x720 JPEG, named <video_id>.jpg
```

## The two stores (same layout)

| Store | Path | Written by | Read by |
|---|---|---|---|
| Run store | `<run folder>/research/outliers/` (the run folder is `story-video-run/<video-slug>/`) | Stage 1 (idea), because the installed plugin may be read-only | Stage 2 (packaging), same run |
| Plugin store | `<plugin>/research/outliers/` (this folder) | `scripts/finish_project.py` at Stage 8, which copies the run store in and deletes batches older than 1 year | every later run, Stage 1 and Stage 2 |

Install the `.plugin` file the autofix returns: that is how the saved research persists.

## Rules

- **Two windows, one year of storage.** The keyword analysis (`keywords.json`) is valid for 14 days after `saved_at`; the outlier analysis (`outliers.json`, `thumbs/`, `analysis.md`) is valid for 60 days (2 months). Inside its window the data is used and not researched again. After a window is over the idea stage asks the user whether to research that part again. **Previous batches are never deleted when a window ends**; `purge` removes a batch only when it is older than 1 year (`purge_after`).
- **View bias and decoys.** The packaging viewer skips a card under 50,000 views unless it gives him a strong reason. Every feed card shows its view count, the candidate is shown with a random low count, so each batch should also hold at least 4 sub-50k videos of the niche flagged `"decoy": true` (real thumbnails, real counts); `build_feed.py` refuses a feed with fewer than 3.
- **Active data is compulsory.** If a batch inside its window exists (14 days keywords, 60 days outliers), every run uses it (the idea stage, and the packaging cycle as the blind feed).
- **Real images only.** The packaging cycle's blind feed uses real thumbnail images. Every outlier must have one in `thumbs/`. Download them with `fetch-thumbs`; if that cannot work (no network, video removed), ask the user to put the thumbnails in `thumbs/` as `<video_id>.jpg`. Never drop an outlier to make the feed pass.
- **Nothing is invented.** No made-up view counts, titles or images.

## Commands (`scripts/outlier_store.py`)

```
python scripts/outlier_store.py status                                   # lists batches, expiry, missing images (plugin store by default)
python scripts/outlier_store.py status --store <run>/research/outliers --store research/outliers
python scripts/outlier_store.py save --store <run>/research/outliers --keyword "<kw>" --outliers found.json [--keywords kw.json] [--analysis analysis.md] [--thumbs-dir DIR]
python scripts/outlier_store.py fetch-thumbs --batch-dir <run>/research/outliers/<batch>
python scripts/outlier_store.py merge --store <run>/research/outliers --store research/outliers --out <cycle>/outliers.json --require-images
python scripts/outlier_store.py purge --store research/outliers                # only batches older than 1 year
```
