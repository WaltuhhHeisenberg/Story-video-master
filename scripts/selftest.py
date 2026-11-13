#!/usr/bin/env python3
"""Smoke test of the plugin after a self-patch: every script compiles, the 3D gates and the asset catalogue run, then the master self-test."""
import json, os, py_compile, subprocess, sys, tempfile
H = os.path.dirname(os.path.abspath(__file__))
bad = []
for f in sorted(os.listdir(H)):
    if f.endswith(".py"):
        try: py_compile.compile(os.path.join(H, f), doraise=True, cfile=os.path.join(tempfile.gettempdir(), "selftest.pyc"))
        except Exception as e: bad.append(f"{f}: {e}")
for cmd, label in (([sys.executable, os.path.join(H, "toon_qa.py"), "--help"], "toon_qa.py --help"),
                   ([sys.executable, os.path.join(H, "run_toon.py"), "--help"], "run_toon.py --help"),
                   ([sys.executable, os.path.join(H, "scene_map_to_toon.py"), "--help"], "scene_map_to_toon.py --help"),
                   ([sys.executable, os.path.join(H, "asset_catalog.py"), "check"], "asset_catalog.py check")):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        bad.append(f"{label}: " + (r.stdout + r.stderr)[-400:])
mst = os.path.join(H, "master_selftest.py")          # manifest / reference / bridge / gate / cleaner / packaging checks
if os.path.exists(mst):
    r = subprocess.run([sys.executable, mst], capture_output=True, text=True)
    if r.returncode:
        bad.append("master_selftest.py: " + (r.stdout + r.stderr)[-1500:])
if bad:
    print("SELFTEST FAIL"); sys.stderr.write("\n".join(bad)); sys.exit(1)
print("selftest ok")
