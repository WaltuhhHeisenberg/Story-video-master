---
name: split-clauses
description: Stage 4 of the story-video-master flow. Use to divide a word-level transcript into natural 3-4 second clauses at real speech boundaries, grouped into story sections. Triggers - "split into clauses", "divide the transcript", "break the voiceover into beats".
---

# Stage 4 - Natural 3-4 second clauses

## Goal
Cut the whole voiceover into consecutive clauses of **3.0-4.0 seconds** (hard ceiling 4.5 s, only when no natural break exists - flag it). Each clause becomes exactly one camera shot of the 3D video (the shot the scene map gives it), so the picture changes every ~4 s by construction.

## Procedure
**Run `python scripts/split_clauses.py --transcript transcript_words.csv --audio voiceover.wav --out clauses.json`** (add `--sections` once the story map is decided). It applies the rules below and prints the verification. Then review every flagged clause and every auto-proposed section name by reading the text - the script cannot judge story. Edit `clauses.json` by hand only for those; keep contiguity.

The manual steps below describe the same method.

0. **Use the transcript and voiceover exactly as delivered** (`--transcript`, `--audio`); nothing is retimed or cleaned. Pauses in the voice are real pauses.
1. **Normalise the transcript** to a list of words with `start` and `end` in seconds. Accept any dialect (see `references/input-formats.md`). If the source is cue-level only (SRT / `0:12 text` lines) interpolate word times by character count and tell the user timing is approximate.
2. **Map the speech** (read the whole transcript first):
   - Sentence ends (. ? ! ।).
   - Pauses between words: breath 0.30-0.59 s, beat 0.60-0.99 s, dramatic >= 1.0 s. Note exact times - dramatic pauses become intentional silences later.
   - Phrase breaks (commas, "but", "so", "and then", "because", "which means", Hindi "लेकिन / तो / क्योंकि / यानी").
   - Emphasis words: numbers, stretched words, words followed by a pause, quoted lines, names.
3. **Group into sections** (story map): HOOK (promise, proof, plan, persona), ONBOARDING / first aha (time-to-value), then body sections (one idea each), CTA/close. Each section = one 3D world later (named for what the part is about, e.g. THE SCALPEL CLUE; never S01, S02). Section boundaries must coincide with clause boundaries.
4. **Place clause boundaries** within each section:
   - Prefer, in order: dramatic pause > sentence end > beat pause > phrase break > breath. Never cut inside a word or inside a tight phrase (article+noun, verb+object, number+unit, name).
   - Aim for 3.5 s; accept 3.0-4.0 s. A boundary placed in the middle of a pause is best - the pause belongs to the clause it follows (the visual holds through it).
   - Do not leave a tail shorter than 3.0 s: rebalance the previous 2-3 clauses instead.
   - A dramatic pause (>= 1.0 s) is never split from its sentence; it extends that clause even if that makes it 4.0-4.5 s (flag `over-4s` and plan an interrupt inside it).
   - Very short punchy sentences ("No.") join the neighbouring clause rather than becoming a 1 s scene.
5. **Write `clauses.json`** (fields in `references/clauses-spec.md`): id `C001...`, section, start, end, dur, text, first/last word index, boundary type, flags, `pause_after`, `emphasis` list.
6. **Verify**: (Gate 1 items G1-01 to G1-05 apply) clauses are contiguous (end of one = start of next, first starts at 0, last ends at the voiceover end), count how many fall in 3-4 s, list flagged ones. Show the user a compact table (id, time, text, flags) - do not stop for approval unless a flagged clause needs a decision.

## Output
`clauses.json` and a short summary: number of clauses, mean length, how many outside 3-4 s and why.

## Pitfalls
- Splitting by fixed time (every 3.5 s) - forbidden; boundaries must be speech-driven.
- Splitting by punctuation only - a long sentence needs internal phrase breaks.
- Ignoring Hindi/Hinglish connectors; treat them as phrase breaks like their English equivalents.
