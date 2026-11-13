# toon_project.json (the project file of the three.js toon studio)

Full reference: `toon-studio/README.md` (kept as delivered). Summary of what the bridge writes and what you may edit by hand:

```jsonc
{ "title": "...", "width": 1280, "height": 720, "fps": 30, "supersample": 1.5, "crf": 17,
  "fade": 0.4,                 // seconds of dip at every scene (section) boundary
  "burnCaptions": true,        // captions burned into the picture (always also written as .srt)
  "audio": "/abs/path/voiceover.mp3",
  "scenes": [ { "id": "s01_the_cold_evening", "duration": 9.0,
      "world": { "theme": "night", "seed": 123456, "houses": 6, "clearance": 9 },
      "actors": [ { "id": "hero", "start": 0.3, "character": { "scarf": 15087942, "hat": "tophat" },
                    "timeline": [ { "t": 0, "action": "walk" }, { "t": 3.0, "action": "idle" } ] },
                  { "id": "buddy", "follow": { "target": "hero", "side": 1.7, "back": 0.4 } } ],
      "shots": [ { "from": 0, "to": 3.0, "type": "crane", "target": "hero", "blend": 0.05, "camFrom": {...}, "camTo": {...} } ],
      "captions": [ { "from": 0.3, "to": 2.1, "text": "Oxford, 12 February 1941" } ] } ] }
```
Themes: day, sunset, night, snow, desert. Actions: idle, walk, run, wave, jump, dance. Shots: follow, side, orbit, closeup, crane, topdown, fixed, static. Same `seed` = same world, so a place can come back later in the video (the bridge derives the seed from the shot's `background` name or the section name).

## Limits (v1 of the studio, stated plainly)
Single character type (stickman), one world per scene, procedural animation only (no imported models), no lip-sync, picture + captions only (no music, SFX or ambient sound), software rendering (about 0.1-0.16 s per frame per core; `node toon-studio/cli.mjs estimate` gives the real number for this machine).
