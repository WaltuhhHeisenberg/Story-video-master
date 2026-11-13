#!/usr/bin/env python3
"""Step 1 - divide a word-level transcript into natural 3-4 s clauses (clauses.json).

Usage:
  python split_clauses.py --transcript audio_out/transcript_words.csv \
      --audio audio_out/voiceover.wav --out clauses.json [--sections sections.json]

Boundaries are chosen by dynamic programming over real speech boundaries (never a fixed grid):
  dramatic pause > sentence end > beat pause > phrase break > breath; never inside a tight phrase.
A clause ends where the NEXT word starts, so the pause after a clause belongs to that clause
(convention: skills/split-clauses/references/clauses-spec.md). Clauses are contiguous: first starts at
0, last ends at the audio end, every boundary equals a word edge.

--sections sections.json : [{"name":"THE_PROBLEM","role":"hook","start":0},
                            {"name":"THE_COUNT","role":"onboarding","start":10.6}, ...]
  (start in seconds, snapped to the nearest clause-able word start). Without it, sections are
  proposed automatically and flagged "auto": rename them in Step 1 review.
"""
import argparse
import json
import re
import sys

import numpy as np

import vo_common as C

TARGET, MIN_D, MAX_D, HARD = 3.5, 3.0, 4.0, 4.5

EN_CONNECT = {"but", "so", "because", "which", "however", "then", "and", "or", "yet", "while", "although",
              "since", "instead", "except", "if", "when"}
HI_CONNECT = {"लेकिन", "तो", "क्योंकि", "यानी", "मगर", "इसलिए", "जबकि", "परंतु"}
HI_POST = {"का", "की", "के", "में", "से", "को", "पर", "ने", "तक", "लिए"}
EN_TIGHT_PREV = {"the", "a", "an", "of", "to", "in", "on", "at", "for", "with", "by", "from", "into", "my",
                 "your", "his", "her", "its", "our", "their", "this", "that", "these", "those", "is", "are",
                 "was", "were", "be", "been", "has", "have", "had", "will", "would", "can", "could", "not",
                 "no", "than", "as", "about", "over", "under", "per", "behind", "between", "through",
                 "during", "after", "before", "within", "without", "across", "against", "toward",
                 "towards", "near", "like", "and", "or", "but", "so", "if", "when", "while", "because",
                 "that", "which", "who", "what", "how", "why", "every", "each", "some", "any", "all",
                 "very", "more", "most", "just", "also", "even", "only", "i", "we", "you", "they", "he", "she", "it"}
UNITS = {"hours", "hour", "minutes", "minute", "seconds", "days", "day", "years", "year", "months", "percent",
         "%", "dollars", "rupees", "km", "kg", "miles", "people", "times", "million", "billion", "thousand",
         "hundred", "crore", "lakh"}


def boundary_cost(words, k, G):
    """Cost of ending a clause after word k (boundary at next word start). Lower is better."""
    p, n = words[k]["word"], words[k + 1]["word"]
    pt, nt = C.clean_token(p).lower(), C.clean_token(n).lower()
    g = G[k]
    sent = C.ends_sentence(p)
    # tight phrases: effectively forbidden
    if pt in EN_TIGHT_PREV and not sent:
        return 8.0, "inside phrase"
    if nt in HI_POST and not sent:
        return 8.0, "inside phrase"
    if C.is_number(p) and nt in UNITS:
        return 8.0, "inside phrase"
    if (C.clean_token(p)[:1].isupper() and C.clean_token(n)[:1].isupper() and not sent
            and k > 0 and not C.ends_sentence(words[k - 1]["word"])):
        return 8.0, "inside name"
    if g >= 1.0:
        return 0.0, f"dramatic pause ({g:.1f} s)"
    if sent and g >= 0.6:
        return 0.0, f"sentence end + beat pause ({g:.1f} s)"
    if sent:
        return 0.3, "sentence end"
    if g >= 0.6:
        return 0.5, f"beat pause ({g:.1f} s)"
    comma = C.ends_comma(p)
    conn = nt in EN_CONNECT or nt in HI_CONNECT
    if comma and conn:
        return 0.8, "phrase break (comma + connector)"
    if comma:
        return 1.0, "phrase break (comma)"
    if conn and g >= 0.15:
        return 1.2, f"phrase break ('{nt}')"
    if conn:
        return 1.8, f"phrase break ('{nt}')"
    if g >= 0.30:
        return 1.6, f"breath ({g:.2f} s)"
    if pt in HI_POST:
        return 5.0, "mid phrase"
    return 5.0, "mid phrase"


def dur_cost(d):
    if MIN_D <= d <= MAX_D:
        return 0.3 * ((d - TARGET) / 0.5) ** 2
    if d < MIN_D:
        return 3.0 + (MIN_D - d) * 6.0
    if d <= HARD:
        return 2.0 + (d - MAX_D) * 4.0
    return 10.0 + (d - HARD) * 10.0


def segment_dp(words, G, i0, i1, t0, t1):
    """Best clause partition of words[i0..i1] spanning time t0..t1.
    Returns list of (first, last, boundary_cost, boundary_desc)."""
    n = i1 - i0 + 1
    start_t = lambda i: t0 if i == i0 else words[i]["start"]  # clause starting at word i
    end_t = lambda j: t1 if j == i1 else words[j + 1]["start"]  # clause ending with word j
    INF = 1e18
    best = [INF] * (n + 1)
    prev = [-1] * (n + 1)
    best[0] = 0.0
    for a in range(n):
        if best[a] >= INF:
            continue
        i = i0 + a
        for j in range(i, i1 + 1):
            d = end_t(j) - start_t(i)
            if d > HARD + 2.5:
                break
            if j == i1:
                bc, _ = 0.0, "end"
            else:
                bc, _ = boundary_cost(words, j, G)
            cost = best[a] + dur_cost(d) + bc
            b = j - i0 + 1
            if cost < best[b]:
                best[b], prev[b] = cost, a
    if best[n] >= INF:  # could not satisfy: single clause
        return [(i0, i1, 0.0, "end")]
    out, b = [], n
    while b > 0:
        a = prev[b]
        j = i0 + b - 1
        bc, desc = (0.0, "end") if j == i1 else boundary_cost(words, j, G)
        out.append((i0 + a, j, bc, desc))
        b = a
    return out[::-1]


def auto_sections(words, G, dur):
    """Propose sections at strong boundaries. Returns list of dicts(name, role, start_word)."""
    n = len(words)
    cands = []  # (word index starting a new section, strength)
    for k in range(n - 1):
        if C.ends_sentence(words[k]["word"]) and G[k] >= 0.8:
            cands.append((k + 1, G[k]))

    def pick(target, lo, hi):
        pool = [(i, s) for i, s in cands if lo <= words[i]["start"] <= hi]
        if not pool:
            return None
        return min(pool, key=lambda c: abs(words[c[0]]["start"] - target) - 3.0 * c[1])[0]

    starts = [0]
    h = pick(30.0, 15.0, 45.0) if dur > 50 else None
    if h is not None:
        starts.append(h)
    t = words[starts[-1]]["start"] if len(starts) > 1 else 0.0
    cta_start = None
    if dur > 90:
        tail_from = dur * 0.85
        for i, w in enumerate(words):
            if w["start"] >= tail_from and re.search(r"subscrib|like|comment|link|channel|सब्सक्राइब|लाइक", w["word"], re.I):
                j = i
                while j > 0 and not C.ends_sentence(words[j - 1]["word"]):
                    j -= 1
                cta_start = j
                break
    last_limit = words[cta_start]["start"] if cta_start else dur
    while True:
        t = words[starts[-1]]["start"]
        if last_limit - t < 90:
            break
        nxt = pick(t + 45.0, t + 25.0, min(t + 70.0, last_limit - 15.0))
        if nxt is None or nxt <= starts[-1]:
            break
        starts.append(nxt)
    if cta_start and cta_start > starts[-1]:
        starts.append(cta_start)
    secs = []
    for si, w in enumerate(starts):
        if si == 0:
            name, role = "HOOK", "hook"
        elif si == 1 and h is not None:
            name, role = "ONBOARDING", "onboarding"
        elif cta_start is not None and w == cta_start:
            name, role = "CTA", "cta"
        else:
            name, role = f"BODY_{si}", "body"
        secs.append({"name": name, "role": role, "start_word": w, "auto": True})
    return secs


def sections_from_file(path, words):
    with open(path, encoding="utf-8-sig") as f:
        j = json.load(f)
    secs = []
    for s in j:
        t = float(s.get("start", 0))
        i = min(range(len(words)), key=lambda q: abs(words[q]["start"] - t))
        secs.append({"name": s["name"], "role": s.get("role", "body"), "start_word": i, "auto": False,
                     "micro_expectations": s.get("micro_expectations", [])})
    secs.sort(key=lambda s: s["start_word"])
    if secs[0]["start_word"] != 0:
        secs[0]["start_word"] = 0
    return secs


def emphasis_of(words, i0, i1, G):
    per_char = [(w["end"] - w["start"]) / max(1, len(C.clean_token(w["word"]))) for w in words]
    med = float(np.median(per_char)) if per_char else 0.1
    scored = []
    for i in range(i0, i1 + 1):
        t = C.clean_token(words[i]["word"])
        if len(t) < 2:
            continue
        s = 0
        if C.is_number(t):
            s = 5
        elif len(t) >= 4 and per_char[i] > 1.6 * med:
            s = 4
        elif t.isupper() and len(t) > 1:
            s = 3
        elif i < len(G) and G[i] >= 0.6 and not C.ends_sentence(words[i]["word"]):
            s = 2
        elif words[i]["word"][0] in "\"'“" or words[i]["word"][-1] in "\"'”":
            s = 2
        if s:
            scored.append((s, i, t.lower()))
    scored.sort(key=lambda x: (-x[0], x[1]))
    keep = sorted(scored[:3], key=lambda x: x[1])
    return [t for _, _, t in keep]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--audio", help="clean voiceover (duration is read from it)")
    ap.add_argument("--duration", type=float)
    ap.add_argument("--out", default="clauses.json")
    ap.add_argument("--sections")
    ap.add_argument("--name", default="My Video")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--audience", default="education", choices=["education", "entertainment"])
    ap.add_argument("--language", help="en / hi ... (auto-detected from script if omitted)")
    a = ap.parse_args()

    words, approx = C.load_transcript(a.transcript)
    if approx:
        print("WARNING: cue-level transcript -> word times are interpolated; clause timing is approximate.")
    if a.duration:
        dur, vfile = a.duration, a.audio or "voiceover.wav"
    elif a.audio:
        C.need_tools()
        dur, vfile = C.probe(a.audio)["duration"], a.audio
    else:
        dur, vfile = words[-1]["end"], "voiceover.wav"
    dur = round(max(dur, words[-1]["end"]), 3)
    G = C.gaps_of(words)
    lang = a.language or ("hi" if sum(1 for w in words if re.search(r"[ऀ-ॿ]", w["word"])) >
                          len(words) * 0.3 else "en")

    secs = sections_from_file(a.sections, words) if a.sections else auto_sections(words, G, dur)
    clauses, sections = [], []
    for si, s in enumerate(secs):
        i0 = s["start_word"]
        i1 = (secs[si + 1]["start_word"] - 1) if si + 1 < len(secs) else len(words) - 1
        t0 = 0.0 if si == 0 else words[i0]["start"]
        t1 = dur if si + 1 == len(secs) else words[i1 + 1]["start"]
        sid = f"S{si + 1:02d}"
        sections.append({"id": sid, "name": s["name"], "role": s["role"], "start": round(t0, 3),
                         "end": round(t1, 3), "micro_expectations": s.get("micro_expectations", []),
                         **({"auto": True} if s.get("auto") else {})})
        for (f, l, bc, desc) in segment_dp(words, G, i0, i1, t0, t1):
            st = t0 if f == i0 else words[f]["start"]
            en = t1 if l == i1 else words[l + 1]["start"]
            pause_after = (t1 if l == i1 else words[l + 1]["start"]) - words[l]["end"]
            d = en - st
            flags = []
            if d > MAX_D + 1e-9:
                flags.append("over-4s" if d <= HARD else "over-4.5s-hard-ceiling")
            if d < MIN_D - 1e-9:
                flags.append("short")
            inner_dramatic = any(G[k] >= 1.0 for k in range(f, l)) or pause_after >= 1.0
            if inner_dramatic:
                flags.append("dramatic pause inside: plan silence")
            if bc >= 3.0:
                flags.append("boundary mid-phrase: review")
            clauses.append({
                "id": "", "section": sid, "start": round(st, 3), "end": round(en, 3), "dur": round(d, 3),
                "text": " ".join(w["word"] for w in words[f:l + 1]), "words": [f, l],
                "boundary": desc if l != i1 else ("section end; " + desc if si + 1 < len(secs) else "end of voiceover"),
                "pause_after": round(pause_after, 3), "emphasis": emphasis_of(words, f, l, G), "flags": flags})
    for n, c in enumerate(clauses, 1):
        c["id"] = f"C{n:03d}"

    # verification (Gate 1 items G1-01..G1-05 that can be computed)
    gaps_ov = [round(clauses[i + 1]["start"] - clauses[i]["end"], 6) for i in range(len(clauses) - 1)]
    in_range = sum(1 for c in clauses if MIN_D - 1e-9 <= c["dur"] <= MAX_D + 1e-9)
    total = round(sum(c["dur"] for c in clauses), 3)
    problems = []
    if clauses[0]["start"] != 0 or clauses[-1]["end"] != dur or any(abs(g) > 1e-6 for g in gaps_ov):
        problems.append("clauses are not contiguous 0..end")
    if abs(total - dur) > 1e-3:
        problems.append(f"sum of durations {total} != {dur}")
    covered = sum(c["words"][1] - c["words"][0] + 1 for c in clauses)
    if covered != len(words):
        problems.append("not every word is in exactly one clause")
    secs_ok = all(any(abs(c["start"] - s["start"]) < 1e-6 for c in clauses) for s in sections)
    if not secs_ok:
        problems.append("a section boundary is not a clause boundary")

    data = {"project": {"name": a.name, "fps": a.fps, "width": a.width, "height": a.height, "language": lang},
            "voiceover": {"file": vfile, "duration": dur}, "audience": a.audience,
            "sections": sections, "clauses": clauses}
    C.write_json(a.out, data)

    print(f"{'id':5} {'start':>7} {'end':>7} {'dur':>5}  text / flags")
    for c in clauses:
        print(f"{c['id']:5} {c['start']:7.2f} {c['end']:7.2f} {c['dur']:5.2f}  {c['text'][:60]}"
              + (f"  [{', '.join(c['flags'])}]" if c["flags"] else ""))
    ds = np.array([c["dur"] for c in clauses])
    print(f"\n{len(clauses)} clauses in {len(sections)} sections, mean {ds.mean():.2f} s, "
          f"{in_range} inside 3.0-4.0 s, {len(clauses) - in_range} flagged/outside")
    print(f"contiguity: sum {total} s of {dur} s, gaps/overlaps: {max([abs(g) for g in gaps_ov] or [0]):.6f} s")
    if any(s.get("auto") for s in sections):
        print("NOTE: sections were proposed automatically - rename/adjust them (or pass --sections).")
    if problems:
        print("PROBLEMS: " + "; ".join(problems))
        return 1
    print(f"written: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
