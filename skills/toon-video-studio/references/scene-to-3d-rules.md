# Writing the scene map so the 3D studio can show it (producer = `three_toon`)

The studio can only show what is in `library/library.json`. Write each shot's `literal` as **subject, action, setting, camera** with words the studio understands, and keep to the map schema (`skills/scene-mapping/reference/schema.md`).

| Field | How the bridge uses it | Write it like this |
|---|---|---|
| `literal` + `mood_target` + `background` (per section) | picks the world THEME by keyword score (`library.json` -> theme `keywords`) | name the time and place: "night ward", "winter street", "village at dusk", "desert camp" |
| `literal` | picks the actor ACTION per clause (`idle, walk, run, wave, jump, dance` keywords) | one clear verb: "walks to the gate", "waves a warning", "stands and stares" |
| `scene_type` | default action and default camera when no `camera_move` | `character_action` -> follow, `environment` -> orbit, `map` -> topdown, `object_closeup` -> closeup |
| `camera_move` | `push_in`, `pull_back`, `pan_left`, `pan_right`, `tilt_up`, `tilt_down`, `static`, `track`, `whip_pan` -> camera shot type | always set it |
| `characters` | two or more names (or "two", "crowd", "group" in the literal) add a companion actor | name them as in `new_assets` |
| `overlay_text` | one burned-in caption | every new number, date and name |
| `transition_out.type` | blend between this shot and the next (`hard_cut` 0.05 s ... `dissolve` 0.9 s) | as the map rules require |
| `ambient_visual`, `ambient_audio` | NOT produced; listed in the bridge report | keep writing them (retention rules) - they tell the user what to add later |

Things the studio cannot draw (a specific face, a named building, a chart with real numbers, a map of a real country): do not promise them in `literal`; put the number or name in `overlay_text` so the caption carries it, and keep the picture a world + actor + camera shot.
