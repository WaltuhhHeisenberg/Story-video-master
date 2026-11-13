#!/usr/bin/env python3
"""Run-wide problem log: EVERY stage appends each problem it meets, so the final plugin autofix can collect them all.

  python problem_log.py add --log RUN/reports/master_problems.jsonl --stage idea|packaging|script|voiceover-script|scene-map|bridge|clauses|intake|build|qa|plugin|env \
        --symptom "what went wrong" [--where "file or step"] [--cause "if known"] [--severity blocker|major|minor] [--handled "what was done by hand"]
  python problem_log.py list --log RUN/reports/master_problems.jsonl

Log a problem when: a check FAILS, a command exits non-zero, an agent/skill/reference/path cannot be found, a rule had to be worked around by hand,
a reviewer reports a finding, or the user complains. A problem that was fixed by hand is still logged (that is what the autofix learns from).
Ids look like M-<stage>-<n> (e.g. M-script-2); a lesson in lessons.json must name each id in `id` or `covers`.
"""
import argparse, json, os, sys, time

STAGES = ("idea", "packaging", "script", "voiceover-script", "scene-map", "bridge", "clauses", "intake", "build", "qa", "plugin", "env")


def load(p):
    out = []
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except Exception:
                    pass
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a_ = sp.add_parser("add")
    a_.add_argument("--log", required=True); a_.add_argument("--stage", required=True, choices=STAGES)
    a_.add_argument("--symptom", required=True); a_.add_argument("--where", default=""); a_.add_argument("--cause", default="")
    a_.add_argument("--severity", default="major", choices=("blocker", "major", "minor")); a_.add_argument("--handled", default="")
    l_ = sp.add_parser("list"); l_.add_argument("--log", required=True)
    a = ap.parse_args()
    rows = load(a.log)
    if a.cmd == "list":
        for r in rows:
            print(f"{r['id']} [{r['severity']}] {r['symptom']} ({r.get('where', '')})")
        print(f"{len(rows)} problem(s)")
        return 0
    n = sum(1 for r in rows if r["stage"] == a.stage) + 1
    row = {"id": f"M-{a.stage}-{n}", "stage": a.stage, "severity": a.severity, "symptom": a.symptom, "where": a.where, "cause": a.cause,
           "handled": a.handled, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    os.makedirs(os.path.dirname(os.path.abspath(a.log)), exist_ok=True)
    with open(a.log, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("logged", row["id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
