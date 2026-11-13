#!/usr/bin/env python3
"""Outlier store: where the researched top-performing titles and REAL thumbnail images live.

Two stores exist, with the same layout (one folder per research batch):
  <plugin>/research/outliers/<batch>/            shipped inside the .plugin; read by every later run until the batch expires
  <run>/research/outliers/<batch>/               where a run writes its own research (the installed plugin may be read-only);
                                                 scripts/finish_project.py (Stage 8) copies it into the plugin and purges expired batches
A batch folder holds:
  meta.json       {batch_id, keyword, saved_at, keywords_expires_at, outliers_expires_at, expires_at, purge_after, count}
                  keyword analysis is valid 14 days after saved_at; outlier analysis is valid 60 days (2 months); expires_at = outliers_expires_at;
                  the batch itself is KEPT (never deleted) until purge_after = saved_at + 365 days. Old meta files without these fields get the
                  same windows computed from saved_at.
  outliers.json   list of outliers: title, views, channel, url, video_id, published, text, image ("thumbs/<id>.jpg"), + optional
                  medium/subject/framing/colors/composition and any extra keys
  keywords.json   the keyword analysis (candidates, evidence, ranking)  [optional]
  analysis.md     the outlier analysis in whole                          [optional]
  thumbs/         the real thumbnail images, 1280x720 JPEG

Commands
  save          write a batch into a store
  fetch-thumbs  download missing thumbnails of a batch from YouTube (i.ytimg.com), needs network
  status        list batches, expiry and missing images
  merge         union of every non-expired batch of the given stores -> one outliers.json for the packaging cycle (image paths absolute)
  purge         delete batches older than 1 year (purge_after); a batch past its 14-day / 60-day window is kept, only no longer used as active data
Exit codes: 0 ok, 2 refused/none found, 3 merge found outliers without a real image file (with --require-images)
"""
import argparse, datetime as dt, json, os, re, shutil, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_STORE = os.path.abspath(os.path.join(HERE, "..", "research", "outliers"))
TODAY = dt.date.today()
KEYWORD_DAYS = 14      # keyword analysis validity (2 weeks)
OUTLIER_DAYS = 60      # outlier analysis validity (2 months)
KEEP_DAYS = 365        # previous batches are kept; deleted only after 1 year


def die(m, code=2):
    sys.stderr.write(m + "\n"); sys.exit(code)


def jload(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def jdump(o, p):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=1, ensure_ascii=False)


def vid(o):
    if o.get("video_id"):
        return str(o["video_id"]).strip()
    m = re.search(r"(?:youtu\.be/|[?&]v=|/shorts/|/embed/)([A-Za-z0-9_-]{11})", str(o.get("url", "")))
    return m.group(1) if m else ""


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")[:60] or "batch"


def norm_image(src, dst):
    """Copy a thumbnail as a 1280x720 JPEG (bounded size, one format). Falls back to a plain copy without Pillow."""
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    try:
        from PIL import Image
        Image.open(src).convert("RGB").resize((1280, 720), Image.LANCZOS).save(dst, "JPEG", quality=88)
    except ImportError:
        shutil.copyfile(src, dst)


def batches(store):
    out = []
    if not os.path.isdir(store):
        return out
    for d in sorted(os.listdir(store)):
        bd = os.path.join(store, d)
        mp = os.path.join(bd, "meta.json")
        if os.path.isdir(bd) and os.path.exists(mp):
            try:
                m = jload(mp)
                saved = dt.date.fromisoformat(m["saved_at"])
            except Exception:
                continue
            if "purge_after" not in m:      # old meta (21-day expires_at): compute the current windows from saved_at
                m["keywords_expires_at"] = (saved + dt.timedelta(days=KEYWORD_DAYS)).isoformat()
                m["outliers_expires_at"] = (saved + dt.timedelta(days=OUTLIER_DAYS)).isoformat()
                m["purge_after"] = (saved + dt.timedelta(days=KEEP_DAYS)).isoformat()
            exp = dt.date.fromisoformat(m["outliers_expires_at"])
            out.append((bd, m, exp, exp < TODAY))
    return out


def img_ok(bd, o):
    p = o.get("image")
    return bool(p) and os.path.exists(p if os.path.isabs(p) else os.path.join(bd, p))


def cmd_save(a):
    outs = jload(a.outliers)
    outs = outs.get("outliers", []) if isinstance(outs, dict) else outs
    if not outs:
        die("no outliers to save")
    bid = a.batch or f"{TODAY.isoformat()}-{slug(a.keyword or 'research')}"
    bd = os.path.join(a.store, bid)
    if os.path.exists(bd):
        if not a.replace:
            die(f"batch {bid} already exists in {a.store} (use --replace)")
        shutil.rmtree(bd)
    os.makedirs(os.path.join(bd, "thumbs"))
    saved = []
    for i, o in enumerate(outs, 1):
        if not str(o.get("title", "")).strip():
            die(f"outlier #{i} has no title")
        o = dict(o)
        o["video_id"] = vid(o)
        key = o["video_id"] or f"o{i:03d}"
        src = o.get("image")
        if (not src or not os.path.exists(src)) and a.thumbs_dir:
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                c = os.path.join(a.thumbs_dir, key + ext)
                if os.path.exists(c):
                    src = c; break
        if src and os.path.exists(src):
            norm_image(src, os.path.join(bd, "thumbs", key + ".jpg"))
            o["image"] = f"thumbs/{key}.jpg"
        else:
            o["image"] = ""
        saved.append(o)
    jdump(saved, os.path.join(bd, "outliers.json"))
    if a.keywords:
        shutil.copyfile(a.keywords, os.path.join(bd, "keywords.json"))
    if a.analysis:
        shutil.copyfile(a.analysis, os.path.join(bd, "analysis.md"))
    jdump({"batch_id": bid, "keyword": a.keyword or "", "saved_at": TODAY.isoformat(),
           "keywords_expires_at": (TODAY + dt.timedelta(days=a.keyword_days)).isoformat(),
           "outliers_expires_at": (TODAY + dt.timedelta(days=a.days)).isoformat(),
           "expires_at": (TODAY + dt.timedelta(days=a.days)).isoformat(),
           "purge_after": (TODAY + dt.timedelta(days=a.keep_days)).isoformat(),
           "days": a.days, "keyword_days": a.keyword_days, "keep_days": a.keep_days, "count": len(saved)},
          os.path.join(bd, "meta.json"))
    miss = [o["title"] for o in saved if not o["image"]]
    print(f"saved batch {bid}: {len(saved)} outliers, {len(saved) - len(miss)} images -> {bd}")
    if miss:
        print(f"{len(miss)} outliers have no image yet. Run: python scripts/outlier_store.py fetch-thumbs --batch-dir {bd}")


def cmd_fetch(a):
    bd = a.batch_dir
    outs = jload(os.path.join(bd, "outliers.json"))
    got = fail = 0
    for o in outs:
        if img_ok(bd, o):
            continue
        v = vid(o)
        if not v:
            print(f"SKIP (no video id/url): {o.get('title')}"); fail += 1; continue
        ok = False
        for name in ("maxresdefault", "mqdefault"):
            url = f"https://i.ytimg.com/vi/{v}/{name}.jpg"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                data = urllib.request.urlopen(req, timeout=15).read()
            except Exception as e:
                last = str(e); continue
            if len(data) < 2500:
                continue
            tmp = os.path.join(bd, "thumbs", v + ".dl")
            os.makedirs(os.path.dirname(tmp), exist_ok=True)
            open(tmp, "wb").write(data)
            norm_image(tmp, os.path.join(bd, "thumbs", v + ".jpg")); os.remove(tmp)
            o["image"] = f"thumbs/{v}.jpg"; ok = True; got += 1
            break
        if not ok:
            fail += 1
            print(f"FAILED: {o.get('title')} ({v})")
    jdump(outs, os.path.join(bd, "outliers.json"))
    print(f"downloaded {got}; still missing {fail}")
    if fail:
        print("Missing images: ask the user to put the thumbnails in "
              f"{os.path.join(bd, 'thumbs')} as <video_id>.jpg, then re-run save/status. Never drop an outlier from the feed.")
        sys.exit(3)


def cmd_status(a):
    stores = a.store or [PLUGIN_STORE]
    n_act = n_img = 0
    for s in stores:
        bs = batches(s)
        print(f"store {s}: {len(bs)} batch(es)")
        for bd, m, exp, expired in bs:
            outs = jload(os.path.join(bd, "outliers.json"))
            have = sum(1 for o in outs if img_ok(bd, o))
            left = (exp - TODAY).days
            kexp = dt.date.fromisoformat(m["keywords_expires_at"])
            kst = f"keyword analysis valid {(kexp - TODAY).days} more day(s)" if kexp >= TODAY else "keyword analysis STALE (ask the user, then research keywords again)"
            print(f"  {m['batch_id']}  keyword={m.get('keyword', '')!r}  outliers={len(outs)}  images={have}/{len(outs)}  "
                  + (f"outlier window OVER (kept until {m['purge_after']}; ask the user before new outlier research)" if expired else f"outliers active, {left} day(s) left")
                  + f"  | {kst}")
            if not expired:
                n_act += len(outs); n_img += have
    print(f"ACTIVE outliers: {n_act}  with images: {n_img}  missing images: {n_act - n_img}")


def cmd_merge(a):
    seen, merged, miss, used = set(), [], 0, []
    for s in a.store:
        for bd, m, exp, expired in batches(s):
            if expired:
                continue
            used.append(m["batch_id"])
            for o in jload(os.path.join(bd, "outliers.json")):
                k = vid(o) or str(o.get("title", "")).strip().lower()
                if k in seen:
                    continue
                seen.add(k)
                o = dict(o)
                if img_ok(bd, o):
                    p = o["image"]
                    o["image"] = os.path.abspath(p if os.path.isabs(p) else os.path.join(bd, p))
                else:
                    o["image"] = ""; miss += 1
                o["source_batch"] = m["batch_id"]
                merged.append(o)
    if not merged:
        die("no active (non-expired) outlier data in: " + ", ".join(a.store) +
            "\nRun outlier research (ask the user first if the window is over) and save it with `outlier_store.py save`.")
    jdump(merged, a.out)
    print(f"merged {len(merged)} outliers from batches {used} -> {a.out}; without a real image: {miss}")
    if miss and a.require_images:
        for o in merged:
            if not o["image"]:
                print("  NO IMAGE:", o.get("title"))
        die("every outlier needs a real thumbnail image. Run fetch-thumbs, or ask the user to supply the missing thumbnails.", 3)


def cmd_purge(a):
    gone = 0
    for bd, m, exp, expired in batches(a.store):
        pa = dt.date.fromisoformat(m["purge_after"])
        if pa < TODAY:
            print(("would delete " if a.dry_run else "deleted ") + m["batch_id"] + f" (older than 1 year, purge_after {pa})")
            if not a.dry_run:
                shutil.rmtree(bd)
            gone += 1
    print(f"{gone} batch(es) older than 1 year")


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--today", help="YYYY-MM-DD (testing only)")
sub = ap.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("save")
s.add_argument("--store", required=True); s.add_argument("--outliers", required=True)
s.add_argument("--batch"); s.add_argument("--keyword"); s.add_argument("--keywords"); s.add_argument("--analysis")
s.add_argument("--thumbs-dir"); s.add_argument("--days", type=int, default=OUTLIER_DAYS, help="outlier validity, default 60"); s.add_argument("--keyword-days", type=int, default=KEYWORD_DAYS); s.add_argument("--keep-days", type=int, default=KEEP_DAYS); s.add_argument("--replace", action="store_true")
f = sub.add_parser("fetch-thumbs"); f.add_argument("--batch-dir", required=True)
t = sub.add_parser("status"); t.add_argument("--store", action="append")
m = sub.add_parser("merge"); m.add_argument("--store", action="append", required=True); m.add_argument("--out", required=True)
m.add_argument("--require-images", action="store_true")
p = sub.add_parser("purge"); p.add_argument("--store", required=True); p.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
if a.today:
    TODAY = dt.date.fromisoformat(a.today)
{"save": cmd_save, "fetch-thumbs": cmd_fetch, "status": cmd_status, "merge": cmd_merge, "purge": cmd_purge}[a.cmd](a)
