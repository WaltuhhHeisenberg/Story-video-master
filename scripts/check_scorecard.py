#!/usr/bin/env python3
"""Psychology gate for the packaging cycle: proves the viewer-psychology rules (skills/extreme-thumbnails/references/viewer-psychology.md)
were actually applied, so the wiring cannot sit unused.

  check_scorecard.py scorecard --file round-N-packaging.md [--expect N] [--brief-expect N]
      The packager's file must hold at least N scorecard blocks marked KEEP (default 1; use 3 in round 1: primary + 2 variants) and at least
      --brief-expect designer-brief psychological specs (default = --expect). A scorecard block looks like:
          Concept: <one sentence>
          Half A: ...   Half B: ...   The join: ...
          C1 contrast: STRONG - reason
          C2 least context: OK - reason
          C3 two halves: STRONG - reason
          C4 familiar entity: none, not needed        (optional, never kills)
          C5 understandable: OK - reason
          C6 underdog: STRONG - the outliers it beats and why
          Verdict: KEEP | KILL because ...
      A KEEP block fails the gate if: Half A / Half B / the join is missing or empty; C1, C2, C3, C5 or C6 has no verdict word
      (STRONG, OK, WEAK, FAIL) or no reason; C1, C2, C3 or C5 is FAIL; C6 is WEAK or FAIL.
      The brief spec needs these labels (case-insensitive): Contrast plan, Context list, Glance sentence, Underdog.
  check_scorecard.py debrief --file round-N-debrief.md
      The viewer's debrief must label at least one defect C1-C6 (so every failure is traced to a test).

Exit 0 = gate passed, 1 = problems (printed; send them back to the master-packager once), 2 = file unreadable.
"""
import argparse, re, sys

VERDICTS = ("STRONG", "OK", "WEAK", "FAIL")
NEED = {"C1": "contrast", "C2": "least context", "C3": "two halves", "C5": "understandable", "C6": "underdog"}
SPEC = ("Contrast plan", "Context list", "Glance sentence", "Underdog")


def read(p):
    try:
        return open(p, encoding="utf-8-sig").read().replace("\r\n", "\n")
    except Exception as e:
        sys.stderr.write(f"cannot read {p}: {e}\n"); sys.exit(2)


def words(s):
    return len(re.findall(r"\w+", s))


def blocks(t):
    starts = [m.start() for m in re.finditer(r"(?im)^[\s>*\-#]*\**Concept\**\s*:", t)]
    return [t[s:(starts[i + 1] if i + 1 < len(starts) else len(t))] for i, s in enumerate(starts)]


def field(b, key, others):
    m = re.search(key + r"\s*:\**\s*", b, re.I)
    if not m:
        return ""
    rest = b[m.end():]
    cut = len(rest)
    for o in others:
        mo = re.search(o + r"\s*:", rest, re.I)
        if mo:
            cut = min(cut, mo.start())
    mo = re.search(r"\n\s*[*\-]*\s*\**C[1-6]\b", rest)
    if mo:
        cut = min(cut, mo.start())
    return rest[:cut].strip(" *\n")


def check_block(b, n):
    why = []
    first = re.sub(r"(?i)^[\s>*\-#]*\**Concept\**\s*:\**", "", b.split("\n", 1)[0]).strip()
    tag = f"block {n} ({first[:50]})"
    v = re.search(r"(?im)^[\s>*\-#]*\**Verdict\**\s*:\**\s*(KEEP|KILL)", b)
    if not v:
        return tag, None, [f"{tag}: no 'Verdict: KEEP|KILL' line"]
    if v.group(1).upper() == "KILL":
        return tag, "KILL", []
    ha = field(b, r"Half A", [r"Half B", r"The join", r"Join"])
    hb = field(b, r"Half B", [r"Half A", r"The join", r"Join"])
    jn = field(b, r"(?:The )?join", [r"Half A", r"Half B"])
    for name, val in (("Half A", ha), ("Half B", hb), ("The join", jn)):
        if words(val) < 3:
            why.append(f"{tag}: '{name}' is missing or too short (write what the picture says / what the title says / what the video pays off)")
    for code, label in list(NEED.items()) + [("C4", "familiar entity")]:
        m = re.search(r"(?im)^[\s>*\-#]*\**" + code + r"\b[^:\n]*:\**\s*(.*)$", b)
        if not m:
            if code != "C4":
                why.append(f"{tag}: {code} ({label}) line is missing")
            continue
        text = m.group(1)
        verdict = next((x for x in VERDICTS if re.search(r"\b" + x + r"\b", text)), None)
        reason = re.sub(r"\b(" + "|".join(VERDICTS) + r")\b", "", text).strip(" -:\u2013\u2014*")
        if code == "C4":
            continue
        if not verdict:
            why.append(f"{tag}: {code} ({label}) has no verdict word (STRONG, OK, WEAK or FAIL)")
            continue
        if words(reason) < 6:
            why.append(f"{tag}: {code} ({label}) gives no real reason ({words(reason)} words); compare with a named outlier")
        if code in ("C1", "C2", "C3", "C5") and verdict == "FAIL":
            why.append(f"{tag}: {code} ({label}) is FAIL on a KEEP concept; a FAIL on C1, C2, C3 or C5 kills the concept")
        if code == "C6" and verdict in ("WEAK", "FAIL"):
            why.append(f"{tag}: C6 (underdog) is {verdict} on a KEEP concept; the card must be stronger than the biggest cards")
    return tag, "KEEP", why


def scorecard(a):
    t = read(a.file)
    bs = blocks(t)
    problems, keeps = [], 0
    if not bs:
        problems.append("no scorecard blocks found (each concept needs 'Concept: ...' ... 'Verdict: KEEP|KILL'; format in skills/extreme-thumbnails/references/viewer-psychology.md)")
    for i, b in enumerate(bs, 1):
        tag, v, why = check_block(b, i)
        problems += why
        if v == "KEEP" and not why:
            keeps += 1
    if keeps < a.expect:
        problems.append(f"{keeps} valid KEEP scorecard block(s), {a.expect} expected (primary{' + 2 variants' if a.expect >= 3 else ''})")
    be = a.brief_expect if a.brief_expect is not None else a.expect
    for label in SPEC:
        n = len(re.findall(re.escape(label), t, re.I))
        if n < be:
            problems.append(f"psychological spec '{label}' appears {n} time(s) in the designer briefs, {be} expected (one per brief; format in skills/thumbnail-making/SKILL.md item 8)")
    print(f"scorecard blocks: {len(bs)}, valid KEEP: {keeps}")
    for p in problems:
        print("PROBLEM:", p)
    print("PSYCHOLOGY GATE:", "PASS" if not problems else "FAIL")
    sys.exit(0 if not problems else 1)


def debrief(a):
    t = read(a.file)
    labels = sorted(set(re.findall(r"\bC([1-6])\b", t)))
    print("test labels found:", ", ".join("C" + x for x in labels) or "none")
    if not labels:
        print("PROBLEM: the debrief does not label any defect C1-C6; ask the viewer to restate it with the test label on every defect")
        print("DEBRIEF GATE: FAIL"); sys.exit(1)
    print("DEBRIEF GATE: PASS")


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = ap.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("scorecard"); s.add_argument("--file", required=True); s.add_argument("--expect", type=int, default=1); s.add_argument("--brief-expect", type=int, default=None)
d = sub.add_parser("debrief"); d.add_argument("--file", required=True)
a = ap.parse_args()
scorecard(a) if a.cmd == "scorecard" else debrief(a)
