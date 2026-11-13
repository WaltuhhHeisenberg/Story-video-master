# three-toon-studio

A headless **three.js** toolkit that renders cartoon 3D animated videos from a JSON project file.
No browser, no GPU required: three.js runs on a software WebGL context (`headless-gl`), frames are piped into **ffmpeg**, and long videos are split into chunks that render in parallel and can be resumed.

```
project.json ──► scenes (world + actors + camera shots) ──► frame range chunks ──► N workers ──► ffmpeg ──► video.mp4 (+ .srt)
```

## Install

Requirements: Node 18+, ffmpeg, and on Linux `Xvfb` (`apt install xvfb ffmpeg`). The CLI starts Xvfb for you.

```bash
npm install
node cli.mjs render examples/showreel.json --out showreel.mp4
```

## CLI

| Command | What it does |
|---|---|
| `generate --minutes 20 --seed 3 --out project.json` | Auto-builds a complete multi-scene project (themes, actions, camera shots) of any length. Options: `--width --height --fps --ss --title`. |
| `render project.json --out video.mp4` | Renders the video. `--workers N` (default: all cores), `--chunk 300` frames per job, `--preview` (640x360, fast), `--from SEC --to SEC` to render a slice. **Resumable**: re-run the same command and finished chunks are skipped. |
| `still project.json --t 12.5 --out frame.png` | Renders a single frame, great for checking a look in seconds. Add `--preview` for speed. |
| `estimate project.json` | Benchmarks your machine on sample frames from several scenes and prints projected render time for 1–32 workers. |

If the project has `captions`, an `.srt` file is written next to the video. If it has `audio`, the track is muxed in (AAC).

## Project file

```jsonc
{
  "title": "My video",
  "width": 1280, "height": 720, "fps": 30,
  "supersample": 1.5,          // render at 1.5x then downscale = anti-aliasing (1 = fastest)
  "crf": 17,                   // x264 quality (lower = better/larger)
  "fade": 0.4,                 // seconds of fade-in/out at each scene boundary (0 = hard cuts)
  "audio": "music.mp3",        // optional
  "scenes": [ /* see below */ ]
}
```

### Scene

```jsonc
{
  "id": "intro", "duration": 20,                  // seconds
  "world":  { "theme": "day", "seed": 7, "houses": 7, "density": 1, "hills": 1, "clearance": 9,
              "path": { "rx": 42, "rz": 28, "wobble": 0.25 }, "features": { "windmill": false } },
  "actors": [ /* see below */ ],
  "shots":  [ /* see below */ ],
  "captions": [ { "from": 1, "to": 4, "text": "Hello!" } ]    // scene-local seconds
}
```

**World themes:** `day`, `sunset`, `night` (stars, moon, lamps, glowing windows), `snow` (snow pines, snowmen, snowfall), `desert` (cacti, mesas).
Same `seed` = same world. Use `override` to tweak a theme (e.g. `"override": {"grass": [16711680, 255]}`) and `features` to toggle `trees, pines, houses, windmill, flowers, rocks, cacti, mesas, snowmen`.

### Actors

```jsonc
{ "id": "hero", "start": 0.02,                     // position on the path loop, 0..1
  "reverse": false,                                 // walk the loop backwards
  "character": { "color": 1315871, "scarf": 15086150, "hat": "none|cap|tophat", "hatColor": 2781147, "scale": 1 },
  "timeline": [ { "t": 0, "action": "walk" }, { "t": 8, "action": "wave" }, { "t": 11, "action": "run", "speed": 6 } ] }
```
Actions: `idle, walk, run, wave, jump, dance`. `walk`/`run` move along the path; others stand still. Actions cross-blend over 0.3 s.
Other placement modes: `{ "at": {"x":10,"z":5,"yaw":1.2}, "faceTo": "hero" }` (stationary actor that turns to watch another) and `{ "follow": {"target":"hero","side":1.7,"back":0.3} }` (companion that mirrors the target's movement).

### Camera shots

`shots` is a list of `{from, to, type, target, ...}` in scene seconds; consecutive shots cross-blend over `blend` seconds (default 0.8).

| type | Description | Options (defaults) |
|---|---|---|
| `follow` | behind & slightly to the side | `back 6.5, side 2.6, up 2.8, lookAhead 2` |
| `side` | tracking from the side, ahead of the actor | `side -6, ahead 4.5, up 1.1, fov 44` |
| `orbit` | circles the actor | `radius 15, height 8.5, speed 0.32, angle 0.6` |
| `closeup` | tight shot of upper body | `side 1.2, ahead 2.2, up 1.4, fov 40` |
| `crane` | moves from one offset to another | `camFrom {back,side,up}`, `camTo {back,side,up}` |
| `topdown` | high overhead | `height 22` |
| `fixed` | tripod placed ahead; actor walks past | `ahead 10, side 4, up 1.6` |
| `static` | absolute position | `pos [x,y,z]`, `look [x,y,z]` (optional) |

## How long does a 20-minute video take?

Run `node cli.mjs estimate project.json` on your own machine for exact numbers. Reference measurements (software rendering, 1 CPU core, 1280x720 output with 1.5x supersampling):

* ~0.11–0.16 s per frame (7–9 fps), including per-scene world builds and encoding
* 20 min @ 30 fps = 36,000 frames ≈ **70–95 CPU-minutes**

| Workers (cores) | Wall-clock for 20 min |
|---|---|
| 1 | ~1h 10m – 1h 35m |
| 4 | ~20 – 27 min |
| 8 | ~10 – 14 min |
| 16 | ~5 – 7 min |

Speed levers: `"supersample": 1` in the project or `generate --ss 1` (about 2x faster, slightly jaggier edges), `--preview` for drafts, 24 fps (-20%), fewer trees (`density`), a GPU machine, or more cores.

## Architecture / extending

* `src/engine.mjs` headless GL stage, toon + outline materials, `Batch` (merges thousands of props into one draw call)
* `src/world.mjs` terrain, path, props, sky, weather, themes (`THEMES` is a plain object: add your own)
* `src/characters.mjs` stickman rig and animation clips (`sample()` is a pure function: add a clip with a new `case`)
* `src/scene.mjs` actors, locomotion, camera director
* `src/render-chunk.mjs` worker; `src/autogen.mjs` project generator; `cli.mjs` render farm

Every frame is a pure function of time (no state carried between frames), which is why chunks can render anywhere, in any order, on any number of machines. To scale beyond one machine, run `render --from/--to` slices on different machines and concatenate the outputs with ffmpeg.

## Limits (v1)

Single character type (stickman), one world per scene, procedural animation only (no imported glTF models), no dialogue lip-sync. Captions are always written as `.srt`; with `"burnCaptions": true` in the project (or `render --burn`) they are also burned into the picture (`--no-burn` overrides).

## Open assets (added in the story-video-master plugin v2.1)
Worlds, objects and character accessories are data, not code. A project may carry an `assets` block:
```jsonc
"assets": { "themes": { "harbour": { "extends": "day", "sky": ["#6f8fb5", "#dfe8f0"], "props": ["PRP_crate"] } },
            "props":  { "PRP_crate": { "radius": 1, "place": { "mode": "scatter", "count": 6 }, "parts": [ { "shape": "box", "color": "#8b5a2b", "pos": [0, 0.5, 0], "scale": [1, 1, 1] } ] } } }
```
A scene uses them with `"world": { "theme": "harbour", "props": ["PRP_crate"] }` (or `{ "id": "PRP_crate", "count": 3, "place": {...} }`), an actor with `"character": { "parts": [ { "attach": "head", "shape": "sph", ... } ] }`. Shapes: box, cyl, sph, cone, dodec, oct, tor, pyr. Each prop has its own seeded generator, so adding one never moves anything else. Format: `skills/make-3d-assets/references/asset-schema.md` in the plugin.
