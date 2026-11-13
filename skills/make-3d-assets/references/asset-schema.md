# Asset files (library/assets/{themes,props,characters}/<name>.json)

Colours are `"#rrggbb"`. Units are metres. Primitive sizes are the `scale` values: `box` = width, height, depth; `cyl` = radius X, height, radius Z; `sph` = radii; `cone`/`pyr` = radius, height, radius; `tor` = ring radius (tube is 0.3 of it); `dodec`/`oct` = radii. `pos` is the centre of the primitive relative to the asset origin (y up, origin on the ground); `rot` is radians [x, y, z].
Every asset also has `id`, `kind`, `name`, `description`, `keywords` (non-empty), and optionally `created`, `made_for`.

## prop (an object)
```json
{ "id": "PRP_operating_table", "kind": "prop", "name": "operating table",
  "description": "Steel table with a white sheet and a lamp arm.",
  "keywords": ["operating table", "surgery table", "autopsy table", "table"],
  "radius": 1.6, "shadow": true, "auto": true,
  "place": { "mode": "scatter", "area": "near_path", "count": 3, "d": [4, 10], "scale": [0.9, 1.1], "yaw": 0.5 },
  "parts": [ { "shape": "box", "color": "#8a8f98", "pos": [0, 0.8, 0], "scale": [0.9, 0.1, 2.0] },
             { "shape": "cyl", "color": "#8a8f98", "pos": [0, 0.4, 0], "rot": [0, 0, 0], "scale": [0.12, 0.8, 0.12] },
             { "shape": "sph", "color": "#fff0a0", "glow": true, "pos": [0, 2.2, 0], "scale": [0.25, 0.25, 0.25] } ] }
```
- `parts[].color` may be a palette reference of the theme: `"$walls"`, `"$roofs"`, `"$leaves"`, `"$pine"`, `"$trunk"`, `"$rock"` (instance i takes the i-th colour). `glow: true` = unlit emissive part (windows, lamps, fire).
- `place.mode`: `scatter` (random spots, `area`: `near_path` 4..14 m from the path, `field` away from the path, `far` on the horizon ring; `d` = [min, max] distance from the path; `count`), `path_edge` (evenly along the path, `d` = distance from the path, alternating sides), `at` (one fixed spot: `at: {"u": 0.2, "side": 1, "d": 6}` along the path, or `{"x": 0, "z": 0, "yaw": 0}`). `radius` keeps other props away. `auto: false` = only used when a theme or scene lists it.
- A scene can also request it with `world.props: ["PRP_operating_table"]` or `{"id": "...", "count": 2, "place": {...}}`; the bridge does this when the shot text matches the keywords.

## theme (a world)
```json
{ "id": "THM_harbour", "kind": "theme", "name": "harbour", "extends": "day",
  "description": "Grey-blue harbour morning with stone-coloured buildings.",
  "keywords": ["harbour", "harbor", "port", "docks", "quay", "ship yard"],
  "sky": ["#6f8fb5", "#dfe8f0"], "fog": "#dfe8f0", "grass": ["#7d8f6a", "#6a7d5a"], "dirt": "#b9a98c",
  "walls": ["#cfc6b8", "#b8b0a4"], "roofs": ["#4a5a6a", "#6a4a3a"], "leaves": ["#5f7f4f"],
  "features": { "windmill": false, "flowers": false, "pines": false },
  "lamps": true, "glowWindows": false, "stars": false, "snowfall": false,
  "props": ["PRP_crate_stack", { "id": "PRP_rowing_boat", "count": 3 }] }
```
Fields that may be overridden (everything else comes from `extends`): `sky [top, horizon]`, `fog`, `fogN`, `fogF`, `grass [a, b]`, `dirt`, `hemi [skyLight, groundLight, intensity]`, `sun {color, dir [x,y,z], int, moon}`, `leaves`, `pine`, `trunk`, `walls`, `roofs`, `rock`, `cloud {color, emissive, count}`, `features` (trees, pines, houses, windmill, flowers, rocks, cacti, mesas, snowmen), `glowWindows`, `stars`, `lamps`, `snowfall`, `snowCap`, and `props` (prop ids that belong to this world). `extends` may name a built-in theme (`day sunset night snow desert`) or another grown theme.

## character (a look)
```json
{ "id": "CHR_policeman", "kind": "character", "name": "policeman",
  "description": "Stickman constable: dark coat, helmet, whistle.",
  "keywords": ["policeman", "police officer", "constable", "bobby"],
  "character": { "color": "#14141f", "scarf": "#1d3557", "hat": "none", "scale": 1.0,
                 "parts": [ { "attach": "head", "shape": "sph", "color": "#1d3557", "pos": [0, 0.22, 0], "scale": [0.34, 0.2, 0.34] },
                            { "attach": "body", "shape": "box", "color": "#c0c0c0", "pos": [0.2, 1.55, 0.14], "scale": [0.06, 0.06, 0.06] } ] } }
```
`character`: `color` (body ink), `scarf`, `hat` (`none|cap|tophat`), `hatColor`, `scale` (0.3-3), `parts` (accessories attached to `head` (origin at the head centre, head radius 0.3), `body` (origin at the hips, shoulders at y 1.82) or `root`). The bridge uses the first matching look for the hero and the second for a companion.

## Checks
`python scripts/asset_catalog.py validate` (all) / `validate FILE`; `add FILE`; `preview ID`; `info`; `check` (built-ins vs engine + every grown asset valid). Gate 1 G1-13 (no open gap) and G1-14 (embedded assets valid) run before any render.
