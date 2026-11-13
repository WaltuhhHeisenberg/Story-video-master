# Known issues (master flow) - lessons from runs

## Semmelweis run (2026-11)
- Intake report was written but Gate 1/2 could not find it: it now also looks in `<project>/reports/` and `<project>/work/` (qa_checks.py G1-25).
- Sections left auto-named failed G1-05: rule in skills/story-video-master (write work/sections.json with real names).
- Clause over 4.0 s with a callout at 0.3 s left a gap over 4.0 s (G1-12): the bridge now places the callout mid-clause for clauses over 4.0 s.
- problem_log.py did not accept stage `intake`: added.
- Outlier thumbnails could not be downloaded in the sandbox: ask the user early (idea-system).
- A title option claimed "refused for 20 years" the story did not support: verify every title claim against the ledger (idea-system).
- Research windows changed by the user: keyword analysis valid 14 days, outlier analysis 60 days, batches kept 1 year (outlier_store.py, research/README.md).
- Packaging viewer made view-biased by the user: skips cards under 50k views unless he has a strong reason; every feed card shows views, the candidate gets a random low count, at least 3 sub-50k decoys are required (build_feed.py, agents/packaging-lazy-viewer.md, skills/packaging-cycle).
