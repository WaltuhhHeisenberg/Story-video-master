#!/usr/bin/env python3
"""Make the clean, voiceover-ready script (the hand-off at the STOP between scriptwriting and the voiceover).

  python clean_voiceover_script.py --script 03-script.md --out 04-voiceover-script.txt [--report 04-voiceover-script-report.md] [--wpm 150]

Takes the final script file (which may contain headings, a fact ledger, a beat map, bracketed cues, notes) and writes ONLY what is read aloud:
plain paragraphs, no markdown, no [cues], no notes. It removes formatting and non-spoken material; it never rewrites, reorders or "improves" a word.
Exit 2 (nothing written as final) if: no narration found, or [VERIFY] / TODO / TBD markers remain (resolve them first), or a bracket cue is unbalanced.
Read-aloud risks (digits, symbols, abbreviations, very long sentences, URLs) are LISTED in the report for the writer to decide; they are not changed.
"""
import argparse, os, re, sys

SKIP_HEAD = re.compile(r"^(notes?|production notes?|alternative|alternate|hooks?( options)?|short|shorts?|cutdown|audit|changes|word count|fact ledger|beat map|"
                       r"promise|sources?|verify|open items|round log|retention|appendix)\b", re.I)
START_HEAD = re.compile(r"^(the\s+)?(final\s+)?(script|narration|voice-?over( script)?)\b", re.I)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report")
    ap.add_argument("--wpm", type=int, default=150)
    a = ap.parse_args()
    raw = open(a.script, encoding="utf-8-sig").read().replace("\r\n", "\n")
    removed, errors = [], []
    lines = raw.split("\n")
    if lines and lines[0].strip() == "---":                       # front matter
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
            removed.append("front matter"); lines = lines[end + 1:]
        except StopIteration:
            pass
    heads = [(i, len(m.group(1)), m.group(2).strip()) for i, l in enumerate(lines) if (m := re.match(r"^(#{1,6})\s+(.*)$", l))]
    start = next(((i, lv) for i, lv, t in heads if START_HEAD.match(re.sub(r"[*_`:]", "", t))), None)
    if start:
        i0, lv0 = start
        body = []
        for j in range(i0 + 1, len(lines)):
            m = re.match(r"^(#{1,6})\s+(.*)$", lines[j])
            if m and (len(m.group(1)) <= lv0 or SKIP_HEAD.match(re.sub(r"[*_`:]", "", m.group(2)).strip())):
                removed.append("everything from heading '" + m.group(2).strip()[:40] + "' on"); break
            body.append(lines[j])
        removed.append("everything before the script heading")
        lines = body
    text = "\n".join(lines)
    text = re.sub(r"<!--.*?-->", lambda m: removed.append("html comment") or "", text, flags=re.S)
    keep = []
    in_table = False
    for l in text.split("\n"):
        s = l.strip()
        if re.match(r"^#{1,6}\s", s):
            removed.append("heading: " + s[:40]); continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            continue
        if s.startswith("|") or re.match(r"^\|?\s*:?-{3,}", s):
            if not in_table:
                removed.append("table")
            in_table = True; continue
        in_table = False
        if s.startswith(">") or re.match(r"^(note|production note|word count|estimated runtime|runtime|source|sources|dramatized)\s*[:\-]", s, re.I):
            removed.append("note line: " + s[:40]); continue
        s = re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", s)                # list markers
        keep.append(s)
    text = "\n".join(keep)
    # bracketed cues [ARCHIVE CLIP: ..], [ON-SCREEN TEXT: ..], [pause 2s], [VERIFY ..]
    if text.count("[") != text.count("]"):
        errors.append("unbalanced [ ] in the script")
    verify = re.findall(r"\[[^\]]*VERIFY[^\]]*\]", text, re.I)
    if verify:
        errors.append(f"{len(verify)} [VERIFY] flag(s) still open: " + "; ".join(v[:50] for v in verify[:5]) + " - resolve each fact before the voiceover")
    for m in re.findall(r"\[[^\]]*\]", text):
        removed.append("cue " + m[:40])
    text = re.sub(r"\[[^\]]*\]", "", text)
    todo = re.findall(r"\b(TODO|TBD|XXX|\?\?\?)\b", text)
    if todo:
        errors.append("placeholder markers left in the narration: " + ", ".join(sorted(set(todo))))
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(?<![\w*])[*_](?!\s)(.+?)(?<!\s)[*_](?![\w*])", r"\1", text)
    text = text.replace("`", "")
    text = re.sub(r"[ \t]+", " ", text)
    paras = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paras = [p for p in paras if p]
    narration = "\n\n".join(paras)
    words = len(re.findall(r"\b[\w'’-]+\b", narration))
    risks = []
    for m in re.finditer(r"https?://\S+|www\.\S+", narration):
        risks.append("URL read aloud: " + m.group(0)[:50])
    for pat, label in ((r"\d[\d,.]*\s?%|%", "percent sign"), (r"[$€£₹]\s?\d[\d,.]*", "currency symbol"), (r"\b[A-Z]{2,}\b", "abbreviation/acronym"),
                       (r"\d{5,}", "long number"), (r"[&@#/=+<>]", "symbol"), (r"\b\d+(?:st|nd|rd|th)\b", "ordinal digits")):
        hits = sorted(set(m.group(0) for m in re.finditer(pat, narration)))
        if hits:
            risks.append(f"{label}: " + ", ".join(hits[:12]) + (" ..." if len(hits) > 12 else ""))
    for p in paras:
        for sent in re.split(r"(?<=[.!?])\s+", p):
            n = len(sent.split())
            if n > 38:
                risks.append(f"very long sentence ({n} words): {sent[:60]}...")
    if not narration or words < 20:
        errors.append("no narration found (empty or under 20 words after cleaning)")
    rem_l = [f"- {x}" for x in sorted(set(removed))[:60]] or ["- nothing"]
    risk_l = [f"- {x}" for x in risks[:60]] or ["- none found"]
    err_l = [f"- {x}" for x in errors] or ["- none"]
    rep = ["# Voiceover-ready script - report", "", f"- narration words: {words}", f"- runtime at {a.wpm} wpm: {words / a.wpm:.1f} min",
           f"- paragraphs: {len(paras)}", "", "## Removed (non-spoken)", *rem_l, "",
           "## Read-aloud risks (decide before recording; nothing was changed)", *risk_l, "", "## Blocking", *err_l, ""]
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)) or ".", exist_ok=True)
        open(a.report, "w", encoding="utf-8").write("\n".join(rep))
    if errors:
        sys.stderr.write("NOT READY:\n  " + "\n  ".join(errors) + "\n"); return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(narration + "\n")
    print(f"voiceover-ready script -> {a.out} ({words} words, {words / a.wpm:.1f} min at {a.wpm} wpm; {len(risks)} read-aloud risk(s) listed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
