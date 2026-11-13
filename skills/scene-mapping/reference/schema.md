# Scene map JSON schema

One file per video. Top level:

```json
{
  "meta": {
    "title": "string",
    "fps": 24,
    "timing_source": "srt | estimated",
    "producer": "three_toon | own_software | animator | ai_video | unspecified",
    "is_excerpt": false,
    "notes": "string"
  },
  "assumptions": ["period or setting detail Claude chose that is not in the script"],
  "shots": [ { ...shot... } ]
}
```

`is_excerpt: true` tells the validator the map is a piece of a longer video, so whole-video checks (hook window, re-hook intervals, hero count, hard-cut share, unclosed loops, one-off motifs) are skipped.

## Shot fields

A "shot" is one continuous visual unit of roughly 2 to 5 seconds. Beats group shots through `beat_id`.

| Field | Type | Required | Rule |
|---|---|---|---|
| `id` | string | yes | Unique, e.g. `S001`. |
| `beat_id` | string | yes | e.g. `B01`. Shots of one idea share it. |
| `start`, `end` | seconds or `m:ss` | yes | `end` is greater than `start`. Each shot starts where the previous one ended. |
| `narration` | string | yes | The words spoken during the shot, exactly as given. |
| `story_function` | enum | yes | `hook`, `setup`, `escalation`, `reveal`, `explanation`, `bridge`, `rehook`, `resolution` |
| `job` | enum | yes | `show_event`, `show_place`, `show_time`, `show_mechanism`, `show_relationship`, `show_stakes`, `hold_question`, `introduce_character` |
| `scene_type` | enum | yes | `character_action`, `environment`, `object_closeup`, `mechanism`, `map`, `kinetic_text`, `metaphor`, `comparison_graphic` |
| `literal` | string | yes | What is physically drawn and what moves. Subject, action, setting, camera. |
| `camera_move` | string | yes | Short snake_case label: `push_in`, `pull_back`, `pan_left`, `tilt_down`, `static`, `track`, `whip_pan`. |
| `characters` | list | no | Names exactly as they appear in `new_assets` on first use. |
| `background` | string | no | Same naming rule. |
| `props` | list | no | Same naming rule. |
| `overlay_text` | string | no | Every new number, date, and name in the narration needs one. |
| `mood_target` | string | yes | The feeling for this scene, one to three words. |
| `ambient_visual` | string | one of the two | Physical animated detail. Not a mood word. |
| `ambient_audio` | string | one of the two | Physical sound. Not a mood word. |
| `ambient_intensity` | 1, 2, 3 | yes | 1 barely noticed, 3 obvious. Most shots are 1 or 2. |
| `motif_id` | string | no | e.g. `M1` for a repeating detail. |
| `motif_event` | `start`, `continue`, `end` | no | Where the motif is in its life. |
| `pattern_interrupt` | boolean | no | True if this shot restarts attention (punch-in, smash cut, switch of scene type, sudden silence). |
| `loop_opened` | list of strings | no | Format `"L1: the question in the viewer's head"`. |
| `loop_closed` | list of strings | no | Ids only: `["L1"]`. |
| `complexity` | 1, 2, 3 | yes | Estimated animation effort. Calibrate against real production time. |
| `hero` | boolean | no | True for the few shots that get the most effort. |
| `new_assets` | list | no | Assets first appearing here. |
| `reused_assets` | list | no | Assets reused from earlier shots. |
| `transition_out` | object | all but the last shot | See below. |

## transition_out

```json
{
  "type": "hard_cut",
  "out_frame": "what is on screen in the last half second, with key object position",
  "in_frame": "what is on screen in the first half second of the next shot",
  "bridge": "shared shape, continuing movement, sound, or none",
  "audio_bridge": "what is heard across the boundary, or silence",
  "duration_frames": 0
}
```

Types: `hard_cut`, `audio_lead`, `match_cut`, `motion_carry`, `in_world_wipe`, `zoom_through`, `dissolve`, `dip_to_black`, `smash_cut`, `text_card`.

`hard_cut` and `audio_lead` need only `type`. All other types need `out_frame`, `in_frame`, and `bridge` filled in with physical descriptions.

## Writing `literal` for each kind of producer

- **three_toon (the plugin's own 3D studio, the master flow's default)**: subject, action, setting, camera in the words the studio understands: a time and place that names a world (day, sunset, night, snow, desert: e.g. "night ward", "winter street"), one clear verb for the stickman actor (walk, run, wave, jump, dance, stand), and a `camera_move` from `push_in, pull_back, pan_left, pan_right, tilt_up, tilt_down, static, track, whip_pan`. The studio cannot draw faces, named buildings, charts or real maps: put numbers and names in `overlay_text` (burned-in caption) and keep the picture a world + actor + camera shot. Full table: `skills/toon-video-studio/references/scene-to-3d-rules.md`.

- **own_software (After Effects etc.)**: add layer structure and motion in plain terms: background, subject layer, what moves, ease direction, approximate duration. No made-up property names.
- **animator**: storyboard language. Framing, action, timing in seconds, what enters and exits.
- **ai_video**: one self-contained prompt per shot. Repeat the identical character and style description every time (consistency anchors), because the generator remembers nothing between clips. State the camera move in words. Do not promise character consistency; it is the main failure point.
- **unspecified**: storyboard language.
