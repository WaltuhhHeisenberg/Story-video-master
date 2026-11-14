---
name: thumbnail-making
description: Makes the real thumbnail IMAGE (1280x720 PNG) for a packaging card from the master-packager's designer brief - a detailed, realistic-looking illustration (anti-aliased, lit, shaded, with shadows, glow and real type) built from a growing library of recognisable icons, optionally on a cheap 3D-rendered background - and proves it is understandable with a blind recognition test before it goes to the viewer. Use in every packaging-cycle round after the master-packager hands over a card (and for each variant in the final pass), and whenever the user wants a thumbnail actually drawn, not just briefed. The blind feed needs a real image for every card, so no card reaches the lazy-viewer without one.
---

# Thumbnail Making

The lazy-viewer picks from a feed of **real images**: the researched outlier thumbnails and the candidate. So the candidate must be a real image too, and it must be **understood in half a second by someone who has not seen the brief**. A thumbnail nobody can read is worth nothing, however pretty. This skill turns the master-packager's brief into that image with the plugin's renderer `scripts/make_thumbnail.py`, and checks it with a blind reader.

> The plugin draws images in two places only: thumbnails (this skill) and the 3D video (three.js studio). It never sources or traces other people's images.

## Who does it
`story-video-master:thumbnail-maker` (agent) builds and renders. The **main session** (packaging-cycle) then runs `story-video-master:thumbnail-reader` (blind recognition) and sends misses back to the maker, at most 3 loops. The maker gets: the card JSON, the buildable brief, and (round 2+) the last image and the viewer's debrief. It returns the PNG, its scene file, the phone preview, and the card with `image` filled in.

## The buildable designer brief (what the master-packager must write)
Everything in the brief must be something the renderer can show **recognisably**:
1. **The idea in one sentence** and the **one thing that must pop** (focal element, at least 35% of the height).
2. **Elements, each with its recognition cues.** For every object: its name, its library icon id if one exists (`python scripts/thumbnail_icons.py find "<words>"`), or else the 3 features that make a stranger name it ("bolt = hex head + visible diagonal threads + washer"). An element without cues will come out as a blob.
3. **Layout on a 3 x 3 grid:** where each element sits and how big (share of the height).
4. **Palette:** one dominant hue, one accent that pops, a dark and a light; mood in plain words (cold, warm, sick, triumphant).
5. **Text:** the exact words (one or two), where.
6. **Deliberately absent:** what must NOT show (the expected romantic image, a formula).
7. **What the viewer must conclude** in one line (the question or tension). The blind reader is checked against this.
8. **The psychological spec** (from `skills/extreme-thumbnails/references/viewer-psychology.md`); it is what the drawing must protect:
   - **Contrast plan (C1):** the single loudest element, what it contrasts with, and the palette choice that separates the card from the outlier crowd.
   - **Context list (C2):** the subject, the gap, and nothing else that explains. Anything on the card that is neither is listed as "removed".
   - **The two halves (C3):** Half A (what the picture says), Half B (the title), and the join (what the video pays off, shown in neither).
   - **Familiar entity (C4):** what it is and where it sits, or "none".
   - **Glance sentence (C5):** the picture in one plain sentence a stranger would say at a glance.
   - **Underdog line (C6):** the outlier this card must beat and the named reason it does.

## The look (always): detailed and real, never flat
- Anti-aliased, lit and shaded: gradients, bevel, soft shadows, glow, highlights, a lit background (use `spotlight`, never a hard-edged circle for light), vignette, bloom and slight grain from `post`. **No flat fills, no thick black cartoon outlines, no MS Paint look.**
- Objects come from the **icon library** (`library/thumbnail-icons/`, shaded, recognisable) or are drawn with the shape vocabulary (`rrect, ellipse, polygon, path, arc, pie, star, ngon, capsule, line`, gradients, `bevel`). Simple shapes are fine; **recognition is the requirement**: every object must show its defining features (threads on the bolt, teeth on the gear, scale marks on the syringe).
- **People:** a generic cartoon figure (`ICO_person`, `ICO_person_tophat`, recoloured) is allowed and encouraged: it tells the viewer who the story is about. No likeness of a real person, no named people, no logos or trademarked marks, no copyrighted characters.
- One focal point, one idea. Text: one or two words, `Inter Black`, 130 px or larger, dark stroke + shadow, contrast of at least 4.5:1; it adds a second question and never repeats the picture.
- Keep 40 px clear of every edge; keep the **bottom-right corner (about 220 x 70 px) free**, YouTube puts the duration badge there.
- A small palette still pops best: one dominant hue plus one accent.
- Never trace, copy or recolor an outlier. Use the outliers only to understand the crowd.

## The process
1. **Plan (short):** the icons per element, the layout (two ASCII wireframes), palette, light direction (where the light comes from and what it makes glow).
2. **Find or make the icons.** `python scripts/thumbnail_icons.py find "<words>"` and `info`. **If an object has no icon, draw one** (below) instead of improvising it as loose shapes in the scene.
3. **Scene file** (`round-N-scene.json`; format at the top of `scripts/make_thumbnail.py`). Icons are placed by `box` (the icon fits inside, aspect kept: give the box the real height you want) and can be `rotate`d, `flip`ped, recoloured via `colors`, given `shadow` and `glow`.
4. **Render:** `python scripts/make_thumbnail.py --scene <scene.json> --out <round-N-thumbnail.png>`; read the printed checks and WARN lines.
5. **Look at both PNGs with Read** (full and phone): one focal point in a second? text readable? the bottom-right clear? any object that does not look like what it is? Fix and re-render.
6. **Blind recognition test** (the main session runs it, see Recognition below). Fix every miss.
7. **Deliver** after the reader passes or after 3 loops with the remaining weakness listed.

## Recognition (the part that was missing)
Spawn `story-video-master:thumbnail-reader` with **only the two PNG paths** (never the brief, the card or the title). It describes what it sees, names every object, says what is happening and what question it raises. Compare with the brief's elements and "what the viewer must conclude":
- **PASS:** every key element named correctly (a synonym is fine), the focal element named first, the text read exactly, and the tension or question stated close to the brief's. Also: the reader's **glance sentence** matches the brief's (C5), the **loudest element** he names is the contrast plan's element (C1), and the picture told him **the question but not the answer** (C2). Anything the reader names that is not in the brief's context list is unplanned context: remove it.
- **MISS:** an element called something else, not noticed, or the story misunderstood; the wrong thing was loudest; the reader could not say what it is at a glance; the picture explained the answer, or asked no question. Fix the cause: bigger, add the defining feature, use another icon, remove clutter, fix contrast. Re-render and test with a **fresh** reader. At most 3 loops.

## Growing the icon library (when an object is missing)
Icons are JSON in `library/thumbnail-icons/<name>.json`: a 100 x 100 unit drawing of one object made from the shape vocabulary with the palette keys `$main $light $dark $accent`, gradients and bevel, 5-40 shapes. Copy the structure of an existing icon (`bolt.json`, `flask.json`). Then:
1. `python scripts/thumbnail_icons.py validate <file>` and `add <file>` (saves it and rebuilds `library/thumbnail-icons/_sheet.png`).
2. `python scripts/thumbnail_icons.py preview ICO_<name>` and look at it: could a stranger name it? Fix until yes (shape silhouette first, then the 2 or 3 defining details, then shading).
3. Have a fresh `thumbnail-reader` name it from the preview alone (no hint). Only keep icons that are recognised.
Never delete or rename an existing icon; improve it in place.

## Optional: a 3D background (only when it is cheap)
If the story's setting is already in the 3D library (a built-in or grown world: `python scripts/asset_catalog.py info`), a lit 3D render can be the background: `"background_3d": {"world": {"theme": "night", "seed": 5}, "actors": [...], "shot": {...}, "assets": {...}}` (one still, a few seconds). Use it for mood only: `"post": {"bg_dim": 0.45, "blur_bg": 3}` so the icons pop, the character facing the camera, and nothing cluttered. **Do not make new 3D assets just for a thumbnail**, and do not use 3D when a lit 2D background says the same thing (it usually does); a busy 3D background hurts recognition.

## Fidelity rules
- **Build the brief; do not redesign it.** Concept, objects, text and palette come from the master-packager. If something cannot be shown recognisably, make the smallest honest simplification and report it.
- **The text is exact**: the on-image text equals the card's `text` character for character.
- **No decorative extras.** Before finishing, remove one element.
- **The image is the truth.** Rewrite the card's description fields (`medium`, `subject`, `framing`, `colors`, `composition`) so they describe what is actually in the image, in plain observational words with no effect or intent words. Set `image` to the PNG's absolute path.

## Output
In the folder the orchestrator names: `round-N-thumbnail.png` (1280 x 720), `round-N-thumbnail_phone.png`, `round-N-scene.json`, the updated `round-N-card.json`, and a short note (passes, simplifications, remaining weakness, the reader's last result). Keep the note out of the card. A worked example scene: `examples/example_scene.json`.
