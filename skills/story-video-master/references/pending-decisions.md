# Decisions (all resolved; nothing is pending)

## D1 - `voiceover-to-capcut` parent skill: KEPT
User rule: delete only if it has no work or does not affect the workflow. Check result: 13 of its reference files are read by `build-capcut-project`, `qa-capcut-project`, `split-clauses`, `perfect-editor`, `story-video-master:capcut-qa-reviewer` and by `scripts/build_capcut_draft.py`, `package_output.py` and others, so deleting it would break Stages 4-7. Its own procedure is not run from the master; it stays as the reference library. Nothing changed.

## D2 - `story-video-pipeline` skill: DELETED
User rule: delete if it does not affect the workflow. Check result: no stage, skill, agent, command or script depended on it; only documentation mentioned it. Its three stages are Stages 1-3 of `story-video-master`, which also add the clean voiceover script. Removed together with its map row. Its saved text exists in the original uploaded plugin.

## D3 - skills from older plugins: NOT BROUGHT BACK
User decision: none. `prepare-voiceover`, `write-visuals` and the old script-rulebook skill stay out (the voiceover is used as delivered; `scene-mapping` chooses pictures; `story-explainer-scripts` is the script rulebook, see J14).


## D4 - CapCut flow: REPLACED (v2.0.0)
User decision: remove CapCut everywhere and use the three.js 3D animation instead; old 2D assets replaced by the 3D asset library. D1 (`voiceover-to-capcut` kept as reference library) is superseded: its role is now `toon-video-studio`. Scene mapping: only its input/output format was edited.
