# Input formats

## 1. Voiceover
Any audio file (mp3, wav, m4a). Record its exact duration (ffprobe or the transcript end). It is muxed into the video exactly as delivered (never processed).

## 2. Word-level transcript - accepted dialects
Normalise everything to: `[{"i":0,"w":"Every","start":0.00,"end":0.40}, ...]` (seconds).

| Source | How to recognise | Notes |
|---|---|---|
| Plain list | `[{"word":..,"start":..,"end":..}]` (keys may be `text`, `w`, `token`; `s`/`e`, `start_time`/`end_time`) | |
| Whisper-style | `{"segments":[{"words":[...]}]}` or `{"words":[...]}` | |
| Milliseconds | max `end` > 20000, or keys ending `_ms` | divide by 1000 |
| AssemblyAI / Deepgram style | `words` with `text`, `start`, `end` (ms) | |
| CSV / TSV | header with `word,start,end`; or three columns | |
| SRT / VTT | `00:00:01,200 --> 00:00:04,100` cues | **cue-level only** - interpolate words by character count and tell the user timing is approximate |
| Timestamped lines | `0:11 text...` or `[01:07] text` (YouTube-style copy/paste) | cue-level only; same caveat; strip noise tags like `[music]`, `[संगीत]`, "1 second" |

Strip non-speech tags (`[music]`, `[laughter]`, `[संगीत]`, `[खांसने की आवाज़]`) from the word list but remember their times as hints (music present, a pause, a reaction). Keep Hindi/Devanagari as-is (UTF-8). Language is detected from the script; record it.

## 3. Visuals
The 3D studio draws every picture itself from the scene map (see `toon-video-studio`); the user does not supply image assets. An optional custom 3D look (theme colours, character scarf/hat) is an edit of `toon_project.json`.

## 4. Optional extras (ask only if useful)
Title + thumbnail concept (hook brief), audience type (education vs entertainment), channel vibe (horror, finance, explainer), CTA offer, language, brand colours.
