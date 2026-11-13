#!/usr/bin/env python3
"""Assemble the final deliverable folder of a 3D video run.

  python package_output.py --project DIR --out OUT_DIR [--note "text"] [--zip]

OUT_DIR gets:
  video.mp4 (+ video.srt)            the rendered 3D video (the --preview render is copied as video_preview.mp4 when it is all there is)
  toon_project.json                  the editable project: change a scene, theme, action or camera and re-render (toon-studio/README.md)
  toon_plan.json                     clause -> world / action / camera / caption plan
  reports/                           gate1/gate2 reports, bridge report, clause sheet, contact sheet, stills, render log, problems log
  check_report.md                    the single check report (if present in the project)
  README_FIRST.md                    what is verified, what is not, how to re-render
Nothing here is edited by hand; files that do not exist are listed as missing instead of being invented.
"""
import argparse, glob, os, shutil, sys, zipfile


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--note", default="")
    ap.add_argument("--zip", action="store_true", help="also write OUT_DIR.zip")
    a = ap.parse_args()
    P, O = os.path.abspath(a.project), os.path.abspath(a.out)
    os.makedirs(O, exist_ok=True)
    items, missing = [], []

    def cp(src, dst, label):
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, dst, **({"dirs_exist_ok": True} if os.path.isdir(src) else {}))
            items.append(label)
        else:
            missing.append(label)

    full, prev = os.path.join(P, "render", "video.mp4"), os.path.join(P, "render", "video_preview.mp4")
    if os.path.exists(full):
        cp(full, os.path.join(O, "video.mp4"), "video.mp4")
        cp(full[:-4] + ".srt", os.path.join(O, "video.srt"), "video.srt")
    elif os.path.exists(prev):
        cp(prev, os.path.join(O, "video_preview.mp4"), "video_preview.mp4 (PREVIEW 640x360 only - the full render is not done)")
        cp(prev[:-4] + ".srt", os.path.join(O, "video_preview.srt"), "video_preview.srt")
    else:
        missing.append("video.mp4 (no render found in render/)")
    cp(os.path.join(P, "toon_project.json"), os.path.join(O, "toon_project.json"), "toon_project.json")
    cp(os.path.join(P, "work", "toon_plan.json"), os.path.join(O, "toon_plan.json"), "toon_plan.json")
    cp(os.path.join(P, "reports"), os.path.join(O, "reports"), "reports/")
    cp(os.path.join(P, "check_report.md"), os.path.join(O, "check_report.md"), "check_report.md")
    for f in glob.glob(os.path.join(P, "intake_report.md")):
        cp(f, os.path.join(O, "reports", "intake_report.md"), "intake_report.md")
    full_ok = os.path.exists(full)
    readme = f"""# README FIRST

{a.note}

## What this is
A 3D animated video made with the three.js toon studio (toon-shaded worlds, stickman actors, camera shots) from your voiceover and scene map: one camera shot per clause, one world per story section.

## Verified (computed, see reports/)
- Gate 1 (project before the render) and Gate 2 (video: duration, size, audio, captions, no blank frames, a visible change at every cut) - read `check_report.md` for PASS / FAIL / NOT RUN exactly as computed.
- Rows marked MANUAL need your look: open `reports/contact_sheet.png` (one frame per clause).

## Not verified / not produced
- Judgement items (story reads from the pictures, captions legible on a phone, no camera clipping) are yours.
- The studio makes picture and captions only: music, sound effects and ambient sound are not produced (listed in `reports/scene_map_bridge_report.md`). The voiceover is muxed exactly as delivered.
- {'This is the FULL render.' if full_ok else 'Only the PREVIEW render (640x360) exists. Run: python scripts/run_toon.py --project <run> --audio <voiceover> --stage render  (then --stage gate2).'}

## Change something and re-render
Edit `toon_project.json` (scene theme/seed, actor timeline actions, shots, captions; schema in toon-studio/README.md), then:
`node toon-studio/cli.mjs render toon_project.json --out video.mp4` (resumable; `--preview` for a quick draft; `still ... --t SEC` for one frame).
To change what the story shows, change the scene map and run the bridge again (scripts/scene_map_to_toon.py).

## Included
""" + "\n".join(f"- {i}" for i in items) + ("\n\n## Missing\n" + "\n".join(f"- {m}" for m in missing) if missing else "") + "\n"
    open(os.path.join(O, "README_FIRST.md"), "w", encoding="utf-8").write(readme)
    if a.zip:
        z = O.rstrip("/\\") + ".zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for dp, _dn, fs in os.walk(O):
                for fn in fs:
                    full_p = os.path.join(dp, fn)
                    zf.write(full_p, os.path.relpath(full_p, O))
        print("zip ->", z)
    print(f"package ok -> {O}: {len(items)} item(s)" + (f"; MISSING: {', '.join(missing)}" if missing else ""))
    return 1 if any(m.startswith("video") for m in missing) else 0


if __name__ == "__main__":
    sys.exit(main())
