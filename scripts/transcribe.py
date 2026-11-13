#!/usr/bin/env python3
"""Make the word-level transcript (word,start,end CSV) from a voiceover - no manual transcript needed.

Usage:
  python transcribe.py --audio voiceover.mp3 --out transcript_words.csv [--language en|hi|auto] [--model small]
  python transcribe.py --from-json whisper_output.json --out transcript_words.csv     # convert an existing result

Backends (first one installed is used; pip install one of them):
  faster-whisper   (recommended, fast, CPU ok)   pip install faster-whisper
  openai-whisper                                  pip install openai-whisper
The model is downloaded on first use (internet needed once). Word timestamps are used as-is; split_clauses.py
then cross-checks them against the audio (silences) before anything is cut, and warns if they are unreliable.
Models: tiny/base/small/medium/large-v3 - use 'small' or 'medium' for English, 'medium' or 'large-v3' for Hindi.
The result is plain text: read it once, fix mis-heard words in the CSV (do not change start/end).
"""
import argparse
import csv
import json
import sys

import vo_common as C


def words_from_whisperlike(j):
    """Accept faster-whisper-style segment list or openai-whisper dict."""
    out = []
    segs = j["segments"] if isinstance(j, dict) and "segments" in j else j
    for s in segs:
        ws = s.get("words") if isinstance(s, dict) else getattr(s, "words", None)
        for w in ws or []:
            if isinstance(w, dict):
                word, st, en = w.get("word") or w.get("text"), w.get("start"), w.get("end")
            else:
                word, st, en = w.word, w.start, w.end
            if word is None or st is None or en is None:
                continue
            out.append((word.strip(), float(st), float(en)))
    return out


def run_faster_whisper(audio, model, language, device):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device=device, compute_type="int8" if device == "cpu" else "float16")
    segs, info = m.transcribe(audio, language=None if language == "auto" else language, word_timestamps=True,
                              vad_filter=False, beam_size=5)
    segs = list(segs)
    print(f"faster-whisper: language={info.language} p={info.language_probability:.2f}, {len(segs)} segments")
    return words_from_whisperlike(segs), info.language


def run_openai_whisper(audio, model, language):
    import whisper
    m = whisper.load_model(model)
    r = m.transcribe(audio, language=None if language == "auto" else language, word_timestamps=True)
    print(f"openai-whisper: language={r.get('language')}")
    return words_from_whisperlike(r), r.get("language")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio")
    ap.add_argument("--from-json")
    ap.add_argument("--out", default="transcript_words.csv")
    ap.add_argument("--language", default="auto")
    ap.add_argument("--model", default="small")
    ap.add_argument("--device", default="cpu")
    a = ap.parse_args()
    if a.from_json:
        words, lang = words_from_whisperlike(json.load(open(a.from_json, encoding="utf-8"))), None
    else:
        if not a.audio:
            C.die("give --audio or --from-json")
        C.need_tools()
        try:
            words, lang = run_faster_whisper(a.audio, a.model, a.language, a.device)
        except ImportError:
            try:
                words, lang = run_openai_whisper(a.audio, a.model, a.language)
            except ImportError:
                C.die("no speech-to-text backend installed. Run: pip install faster-whisper   "
                      "(or provide your own word-level transcript with --from-json / a CSV)")
    words = [w for w in words if w[0]]
    if not words:
        C.die("no words recognised")
    # sanity: monotonic, non-negative durations
    fixed = 0
    prev_end = 0.0
    out = []
    for w, s, e in words:
        if s < prev_end - 1e-3:
            s = prev_end
            fixed += 1
        if e <= s:
            e = s + 0.02
            fixed += 1
        out.append((w, s, e))
        prev_end = e
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["word", "start", "end"])
        for w, s, e in out:
            wr.writerow([w, f"{s:.3f}", f"{e:.3f}"])
    print(f"{len(out)} words, {out[-1][2]:.1f} s -> {a.out}" + (f" ({fixed} timestamps nudged to stay monotonic)" if fixed else ""))
    if lang:
        print(f"detected language: {lang}")
    print("NEXT: read the CSV once and fix mis-heard words (keep start/end). Then split_clauses.py cuts the clauses from it (the voiceover itself is never modified).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
