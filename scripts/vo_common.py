#!/usr/bin/env python3
"""Shared helpers for the clause / transcript scripts.

Needs: Python 3.9+, numpy, scipy, and ffmpeg/ffprobe on PATH.
Nothing here modifies an input file.
"""
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys

import numpy as np

SR = 48000  # working sample rate everywhere


# ----------------------------------------------------------------- basics
def die(msg, code=2):
    print("ERROR: " + str(msg), file=sys.stderr)
    sys.exit(code)


def need_tools():
    for t in ("ffmpeg", "ffprobe"):
        if not shutil.which(t):
            die(f"{t} not found on PATH. Install ffmpeg (https://ffmpeg.org) and retry.")


def run(cmd, check=True):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        die("command failed: " + " ".join(str(c) for c in cmd) + "\n" + p.stderr[-1500:])
    return p


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def db(x, floor=1e-10):
    return 20.0 * math.log10(max(float(x), floor))


def rms(x):
    x = np.asarray(x, dtype=np.float64)
    return float(np.sqrt(np.mean(x * x))) if x.size else 0.0


def rms_db(x):
    return db(rms(x))


# ------------------------------------------------------------------ audio
def probe(path):
    p = run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
             "stream=codec_name,channels,sample_rate,duration,bits_per_sample:format=duration",
             "-of", "json", path])
    j = json.loads(p.stdout)
    if not j.get("streams"):
        die(f"no audio stream in {path}")
    s = j["streams"][0]
    dur = s.get("duration") or j.get("format", {}).get("duration")
    return {"codec": s.get("codec_name"), "channels": int(s["channels"]),
            "sample_rate": int(s["sample_rate"]), "duration": float(dur),
            "bits": s.get("bits_per_sample")}


def decode(path, channels=None, sr=SR, af=None):
    """Decode to float32 numpy array shaped (n, ch) at `sr`."""
    ch = channels or probe(path)["channels"]
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"]
    p = subprocess.run([str(c) for c in cmd], capture_output=True)
    if p.returncode != 0:
        die("decode failed: " + p.stderr.decode("utf-8", "replace")[-800:])
    return np.frombuffer(p.stdout, dtype=np.float32).reshape(-1, ch).copy()


def write_wav_f32(path, data, sr=SR):
    from scipy.io import wavfile
    wavfile.write(path, sr, np.asarray(data, dtype=np.float32))


def mono_mix(x):
    return x.mean(axis=1) if x.ndim == 2 else x


def ebur128(path, af_prefix=None):
    """Return dict(I, LRA, TP) using ffmpeg's ebur128 filter."""
    chain = (af_prefix + "," if af_prefix else "") + "ebur128=peak=true"
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", chain, "-f", "null", "-"])
    t = p.stderr
    tail = t[t.rfind("Summary:"):] if "Summary:" in t else t
    def g(pat):
        m = re.search(pat, tail)
        return float(m.group(1)) if m else float("nan")
    return {"I": g(r"I:\s+(-?[\d.]+)\s+LUFS"), "LRA": g(r"LRA:\s+(-?[\d.]+)\s+LU"),
            "TP": g(r"Peak:\s+(-?[\d.]+)\s+dBFS")}


def silence_rms(mono, thr_db, min_d=0.08, sr=SR):
    """RMS-based silence detector (20 ms window, 10 ms hop). Unlike ffmpeg's peak-based
    silencedetect it is consistent with how the noise floor is measured, so it also works on
    noisy files. Returns [(start, end)] in seconds."""
    win, hop = 960, 480
    if len(mono) < win:
        return []
    nfr = 1 + (len(mono) - win) // hop
    idx = np.arange(nfr)[:, None] * hop + np.arange(win)[None, :]
    lv = 20 * np.log10(np.sqrt((mono[idx].astype(np.float64) ** 2).mean(axis=1)) + 1e-10)
    quiet = lv < thr_db
    # bridge breaths: a short (<= 250 ms) run below -30 dBFS between two quiet runs is non-speech
    i = 0
    while i < nfr:
        if not quiet[i]:
            j = i
            while j < nfr and not quiet[j]:
                j += 1
            if 0 < i and j < nfr and (j - i) <= 25 and lv[i:j].max() < -30.0:
                quiet[i:j] = True
            i = j
        else:
            i += 1
    out, i = [], 0
    while i < nfr:
        if quiet[i]:
            j = i
            while j < nfr and quiet[j]:
                j += 1
            s, e = i * hop / sr, ((j - 1) * hop + win) / sr
            # a frame window overlaps its neighbours: shrink by half a window each side
            s, e = (s + 0.01 if i > 0 else 0.0), (e - 0.01 if j < nfr else len(mono) / sr)
            if e - s >= min_d:
                out.append((s, e))
            i = j
        else:
            i += 1
    return out


def silence_intervals(path, noise_db, d=0.08, af_prefix=None):
    chain = (af_prefix + "," if af_prefix else "") + f"silencedetect=noise={noise_db:.1f}dB:d={d}"
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", chain, "-f", "null", "-"])
    out, start = [], None
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
        m = re.search(r"silence_end:\s*(-?[\d.]+)", line)
        if m and start is not None:
            out.append((start, float(m.group(1))))
            start = None
    if start is not None:
        out.append((start, float("inf")))
    return out


# ------------------------------------------------------------- transcript
NUMBER_WORDS = set("""zero one two three four five six seven eight nine ten eleven twelve thirteen
fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty
ninety hundred thousand million billion trillion percent""".split())
REVEAL_WORDS = set("""but however actually surprisingly secret truth answer reveal revealed finally
turns twist except instead""".split())


def clean_token(w):
    return re.sub(r"^[\W_]+|[\W_]+$", "", w, flags=re.UNICODE)


def is_number(w):
    t = clean_token(w).lower()
    return bool(re.search(r"\d", t)) or t in NUMBER_WORDS


def ends_sentence(w):
    return bool(re.search(r"[.?!\u0964\u2026]+[\"'\u201d)\]]*$", w))


def ends_comma(w):
    return bool(re.search(r"[,;:\u2014\u2013-][\"'\u201d)\]]*$", w))


def _pick(d, keys):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _norm_words(items):
    out, ms_keys = [], False
    for it in items:
        w = _pick(it, ["word", "text", "w", "token", "punctuated_word"])
        s = _pick(it, ["start", "s", "start_time", "start_ms", "startTime", "begin"])
        e = _pick(it, ["end", "e", "end_time", "end_ms", "endTime", "finish"])
        if w is None or s is None or e is None:
            continue
        if any(k.endswith("_ms") for k in it):
            ms_keys = True
        out.append([str(w), float(s), float(e)])
    if out and (ms_keys or max(o[2] for o in out) > 20000):
        for o in out:
            o[1] /= 1000.0
            o[2] /= 1000.0
    return out


def _tc(s):
    s = s.strip().replace(",", ".")
    parts = s.split(":")
    v = 0.0
    for p in parts:
        v = v * 60 + float(p)
    return v


def _interpolate(cues):
    """cues: [(start, end, text)] -> approximate word list by character count."""
    out = []
    for s, e, text in cues:
        toks = text.split()
        if not toks:
            continue
        tot = sum(len(t) for t in toks)
        t0 = s
        for t in toks:
            dt = (e - s) * len(t) / tot
            out.append([t, t0, t0 + dt * 0.92])
            t0 += dt
    return out


def load_transcript(path):
    """Return (words, approx). words = [{'i','word','start','end'}] in seconds.

    Accepts: CSV/TSV (word,start,end), JSON list, Whisper/AssemblyAI/Deepgram-style JSON,
    SRT/VTT and 'm:ss text' lines (cue-level -> approx=True).
    """
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = f.read()
    approx = False
    ext = os.path.splitext(path)[1].lower()
    items = None
    if ext == ".json" or raw.lstrip()[:1] in "[{":
        j = json.loads(raw)
        if isinstance(j, dict):
            if "words" in j:
                j = j["words"]
            elif "segments" in j:
                j = [w for s in j["segments"] for w in s.get("words", [])]
            elif "results" in j:
                try:
                    j = j["results"]["channels"][0]["alternatives"][0]["words"]
                except Exception:
                    die("unrecognised JSON transcript layout")
            else:
                die("unrecognised JSON transcript layout")
        items = _norm_words(j)
    elif ext in (".srt", ".vtt") or "-->" in raw:
        cues = []
        for block in re.split(r"\n\s*\n", raw.replace("\r", "")):
            m = re.search(r"([\d:.,]+)\s*-->\s*([\d:.,]+)", block)
            if m:
                text = block[m.end():].strip().replace("\n", " ")
                cues.append((_tc(m.group(1)), _tc(m.group(2)), text))
        items, approx = _interpolate(cues), True
    else:
        first = raw.splitlines()[0].lower() if raw.strip() else ""
        if "word" in first and "start" in first:
            delim = "\t" if "\t" in first and "," not in first else ","
            rows = list(csv.DictReader(raw.splitlines(), delimiter=delim))
            rows = [{k.strip().lower(): v for k, v in r.items()} for r in rows]
            items = _norm_words([{k: (float(v) if k in ("start", "end") else v)
                                  for k, v in r.items() if v not in (None, "")} for r in rows])
        else:
            lines = [l for l in raw.splitlines() if l.strip()]
            stamped = []
            for l in lines:
                m = re.match(r"^\s*\[?(\d+(?::\d+)+(?:[.,]\d+)?)\]?\s+(.*)$", l)
                if m:
                    stamped.append((_tc(m.group(1)), m.group(2)))
            if stamped:
                cues = []
                for k, (t, txt) in enumerate(stamped):
                    nxt = stamped[k + 1][0] if k + 1 < len(stamped) else t + 4.0
                    cues.append((t, nxt, txt))
                items, approx = _interpolate(cues), True
            else:
                die("cannot recognise transcript format; give word,start,end CSV/JSON")
    words = []
    for w, s, e in items:
        if re.fullmatch(r"\s*[\[\(].*[\]\)]\s*", w):  # [music], [laughter], [संगीत]
            continue
        if not w.strip():
            continue
        words.append({"i": len(words), "word": w.strip(), "start": float(s), "end": float(e)})
    if not words:
        die("transcript contains no words")
    return words, approx


def gaps_of(words):
    """gap k lies between word k and word k+1."""
    return [words[k + 1]["start"] - words[k]["end"] for k in range(len(words) - 1)]


def check_gaps(words, intervals, tol, n=20, min_gap=0.3, min_cover=0.5):
    """Silence cross-check. A sampled gap passes if a detected silence overlaps at least
    `min_cover` of it and does not leak into neighbouring words by more than `tol`."""
    idx = [k for k in range(len(words) - 1)
           if words[k + 1]["start"] - words[k]["end"] >= min_gap]
    if not idx:
        return 0, 0, []
    if len(idx) > n:
        idx = [idx[int(round(i * (len(idx) - 1) / (n - 1)))] for i in range(n)]
    res, ok = [], 0
    for k in idx:
        a, b = words[k]["end"], words[k + 1]["start"]
        # all silent pieces touching the gap (a kept breath splits the silence in two): their
        # summed overlap must cover >= min_cover of the gap and none may leak into the words
        pieces = [(s, e) for s, e in intervals if e > a and s < b]
        cover = sum(min(b, e) - max(a, s) for s, e in pieces)
        good = bool(pieces) and cover >= min_cover * (b - a) and \
            all(s >= a - tol and e <= b + tol + 1e-9 for s, e in pieces)
        ok += good
        res.append({"gap": k, "start": round(a, 3), "end": round(b, 3), "pass": good})
    return len(idx), ok, res


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def fmt_t(t):
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:05.2f}"
