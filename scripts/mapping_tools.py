#!/usr/bin/env python3
"""Scene-mapping helpers. The plugin does NOT choose or write visuals: the user supplies a scene-mapping description, and these
tools only turn it into the exact build input `scene_mapping.json`.

  python mapping_tools.py sheet   --clauses clauses.json --out clause_sheet.md [--skeleton scene_mapping.json]
      clause_sheet.md = id | section | start-end | spoken text, for the user to write the mapping against (no suggestions, no candidates).
      --skeleton also writes scene_mapping.json with only id/section/start/end/spoken and `object: null` for Claude to fill from the description.
  python mapping_tools.py resolve --script scene_mapping.json --transcript transcript_words.csv [--out same_file]
      any overlay/text/sfx/host entry may carry "at_word": "same" or {"word":"same","nth":1} instead of `at`; replaced by `at`
      (= word start - clause start) from the transcript. Unknown / ambiguous words are reported, never guessed.
"""
import argparse
import json
import re
import sys

import vo_common as C


def sheet(a):
    cl = json.load(open(a.clauses, encoding="utf-8-sig"))
    rows = ["# Clause sheet - write your scene mapping against these ids", "", "| id | section | time | spoken |", "|---|---|---|---|"]
    for c in cl["clauses"]:
        rows.append(f"| {c['id']} | {c['section']} | {C.fmt_t(c['start'])}-{C.fmt_t(c['end'])} | {c['text'].replace('|', '/')} |")
    open(a.out, "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print(f"{len(cl['clauses'])} clauses -> {a.out}")
    if a.skeleton:
        out = {k: cl[k] for k in ("project", "voiceover", "sections") if k in cl}
        out.update({"style": {"default_motion": {"name": "kenburns_in", "z": 1.035}}, "music": [], "clauses": [
            {"id": c["id"], "section": c["section"], "start": c["start"], "end": c["end"], "spoken": c["text"], "text": None,
             "object": None, "placeholder": False, "motion": None, "overlays": [], "host": None, "sfx": [], "silence": None}
            for c in cl["clauses"]]})
        C.write_json(a.skeleton, out)
        print("skeleton ->", a.skeleton, "(every `object` is null until the mapping description is applied)")
    return 0


def resolve(a):
    S = json.load(open(a.script, encoding="utf-8-sig"))
    words, _approx = C.load_transcript(a.transcript)
    probs, n = [], 0

    def find(c, spec):
        word = spec["word"] if isinstance(spec, dict) else spec
        nth = (spec.get("nth", 1) if isinstance(spec, dict) else 1)
        hits = [w for w in words if c["start"] - 1e-3 <= w["start"] < c["end"] and re.sub(r"\W", "", w["word"].lower()) ==
                re.sub(r"\W", "", word.lower())]
        if len(hits) < nth:
            return None, f"{c['id']}: word '{word}' not found in the clause"
        if len(hits) > 1 and not isinstance(spec, dict):
            return None, f"{c['id']}: word '{word}' occurs {len(hits)}x - give {{\"word\":..,\"nth\":..}}"
        return hits[nth - 1]["start"] - c["start"], None

    for c in S["clauses"]:
        items = [("overlay", x) for x in c.get("overlays") or []] + [("sfx", x) for x in c.get("sfx") or []]
        if c.get("text"):
            items.append(("text", c["text"]))
        if c.get("host"):
            items.append(("host", c["host"]))
        for kind, x in items:
            if isinstance(x, dict) and "at_word" in x:
                t, err = find(c, x["at_word"])
                if err:
                    probs.append(err)
                else:
                    x["at"] = round(max(0.0, t + x.get("at_offset", 0.0)), 3)
                    n += 1
    C.write_json(a.out or a.script, S)
    print(f"{n} anchors resolved" + (f"; {len(probs)} problems:\n  " + "\n  ".join(probs) if probs else ""))
    return 1 if probs else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("sheet")
    s.add_argument("--clauses", required=True)
    s.add_argument("--out", default="clause_sheet.md")
    s.add_argument("--skeleton")
    r = sp.add_parser("resolve")
    r.add_argument("--script", required=True)
    r.add_argument("--transcript", required=True)
    r.add_argument("--out")
    a = ap.parse_args()
    return resolve(a) if a.cmd == "resolve" else sheet(a)


if __name__ == "__main__":
    sys.exit(main())
