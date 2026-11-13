#!/usr/bin/env python3
"""Blind-feed builder for the packaging cycle.

build    Mix the candidate card into the FULL outlier set, give every card the same template, strip metadata, shuffle
         with a fresh random seed, and write (a) the viewer-facing feed and (b) a private key the viewer never sees.
verdict  Read the viewer's blind verdict + the key and print who got the click (candidate or which outlier), the pull
         strength, and whether this round PASSED.

Exit codes: build 0 ok / 2 refused (card or data problem). verdict 0 = candidate clicked with a REAL pull (PASS),
1 = not a pass, 2 = verdict unreadable.

Real images are required: the feed is built from thumbnail images only, and the build refuses if any card (outliers or candidate)
has no image file. A text-description feed needs the explicit --allow-descriptions flag and is a weaker test.

Outlier file (outliers.json, produced by scripts/outlier_store.py merge): a list, or {"outliers": [...]}. Each outlier is a dict. Only the whitelisted fields below ever
reach the viewer; every other key (views, channel, url, date, video_id, notes ...) is kept in the file for the packager but
is never copied into the feed.
    title            exact title                                     (required)
    text             exact on-image text, "" if none                 (optional)
    medium subject framing colors composition                         (observational description fields)
    visual           one free-text description (used only if no structured fields are common to ALL cards)
    image            absolute path to the card's thumbnail image (required for every card, candidate included)
Candidate file (card.json): the same fields for the card under test.

VIEW BIAS (the viewer skips a card under 50k views unless he has a strong reason): every card shows ONE line "Views: 512K views".
Outliers show their real `views` (number or text such as "501K", "1.2M"); an outlier without parsable views is refused. The candidate shows a
believable LOW count: --candidate-views N, or a random number between 5,000 and 45,000 chosen from the seed (a new video has no history,
and the test is whether the packaging gives a strong enough reason to click a small video). Because a lone low count would single the
candidate out, the build REFUSES unless at least --min-decoys (default 3) outliers have under 50,000 views (store them with "decoy": true in
outliers.json and real thumbnails); --allow-no-decoys overrides it for testing only. Nothing else (channel, date, link) is ever shown.

A description field is shown only if EVERY card (all outliers and the candidate) has it, so the candidate can never be
told apart by having more, or different, information than the rest.
"""
import argparse, json, os, re, secrets, shutil, statistics, sys, random

FIELDS = ["medium", "subject", "framing", "colors", "composition"]
INTENT_WORDS = ["curiosity", "hook", "riddle", "itch", "gap", "click", "off-context", "keyword", "mystery", "mysterious",
                "intriguing", "striking", "haunting", "viral", "outlier", "candidate", "variant", "test", "round"]
META_PAT = re.compile(r"(\b\d[\d.,]*\s?[kKmMbB]?\s*(views?|subscribers?|subs)\b|\bviews?\s*[:=]|\bsubscribers?\b|https?://|www\.|@\w|"
                      r"\b\d+\s*(hours?|days?|weeks?|months?|years?)\s+ago\b|\bchannel\s*[:=])", re.I)


def die(msg):
    sys.stderr.write("REFUSED: " + msg + "\n")
    sys.exit(2)


def load(p):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        die(f"cannot read {p}: {e}")


def clean(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()


def words(s):
    return len(re.findall(r"\w+", s))


def card_view(c, fields, use_visual):
    d = {"title": clean(c.get("title")), "text": clean(c.get("text"))}
    if use_visual:
        d["visual"] = clean(c.get("visual"))
    else:
        for f in fields:
            d[f] = clean(c.get(f))
    return d


def parse_views(v):
    """Number of views from 512000, "512,000", "512K", "1.2M", "1.2 million views"; None if unreadable."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    m = re.search(r"([\d][\d.,]*)\s*([kKmMbB]|thousand|million|billion)?", str(v))
    if not m:
        return None
    num = m.group(1).replace(",", "")
    try:
        x = float(num)
    except ValueError:
        return None
    mult = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "b": 1e9, "billion": 1e9}.get((m.group(2) or "").lower(), 1)
    return int(round(x * mult))


def fmt_views(n):
    if n >= 1_000_000:
        x = n / 1e6
        return f"{x:.1f}M views".replace(".0M", "M")
    if n >= 10_000:
        return f"{round(n / 1000)}K views"
    if n >= 1000:
        return f"{n / 1000:.1f}K views".replace(".0K", "K")
    return f"{n} views"


def render(pos, v, image=None, views=None):
    out = [f"## Card {pos:02d}", f"**Title:** {v['title']}"]
    if views:
        out.append(f"**Views:** {views}")
    if image:
        out.append(f"**Thumbnail:** image file `{image}` (open it with Read)")
    else:
        out.append("**Thumbnail:**")
        if "visual" in v:
            out.append(f"- Picture: {v['visual']}")
        else:
            for f in FIELDS:
                if f in v:
                    out.append(f"- {f.capitalize()}: {v[f]}")
        out.append(f"- Text on image: {v['text'] if v['text'] else '(none)'}")
    return "\n".join(out) + "\n"


def reencode(src, dst):
    """Same size/format for every image, no metadata. Needs Pillow; returns False if it cannot."""
    try:
        from PIL import Image
    except Exception:
        return False
    im = Image.open(src).convert("RGB").resize((1280, 720), Image.LANCZOS)   # identical size for every card
    im.save(dst, "JPEG", quality=90)               # Pillow writes no EXIF / ICC / text metadata unless asked to
    return True


def build(a):
    raw = load(a.outliers)
    outs = raw.get("outliers", []) if isinstance(raw, dict) else raw
    if not isinstance(outs, list) or not outs:
        die("outliers file holds no outliers. The test must run against the full outlier data, never an empty feed.")
    cand = load(a.card)
    if isinstance(cand, dict) and "card" in cand:
        cand = cand["card"]
    if not clean(cand.get("title")):
        die("candidate card has no title")
    for i, o in enumerate(outs):
        if not clean(o.get("title")):
            die(f"outlier #{i + 1} has no title (every outlier needs a title; none may be dropped)")
    if clean(cand["title"]).lower() in {clean(o["title"]).lower() for o in outs}:
        die("candidate title is identical to an outlier title")

    cards = outs + [cand]
    warn = []
    ov = []
    for i, o in enumerate(outs):
        n_ = parse_views(o.get("views"))
        if n_ is None:
            die(f"outlier #{i + 1} ({clean(o.get('title'))[:50]}) has no readable `views`; every card must show a view count (the viewer is view-biased)")
        ov.append(n_)
    low = [n_ for n_ in ov if n_ < 50000]
    if len(low) < a.min_decoys and not a.allow_no_decoys:
        die(f"only {len(low)} outlier(s) have under 50,000 views; at least {a.min_decoys} are needed as decoys, otherwise a low view count "
            "singles out the candidate. Research and save sub-50k videos of the niche (with real thumbnails, \"decoy\": true) or, for a test only, use --allow-no-decoys.")
    common = [f for f in FIELDS if all(clean(c.get(f)) for c in cards)]
    dropped = [f for f in FIELDS if f not in common and any(clean(c.get(f)) for c in cards)]
    use_visual = False
    use_images = all(c.get("image") and os.path.exists(str(c.get("image"))) for c in cards)
    if not use_images and not a.allow_descriptions:
        lack = [("CANDIDATE" if c is cand else f"outlier #{i + 1} ({clean(c.get('title'))[:50]})")
                for i, c in enumerate(cards) if not (c.get("image") and os.path.exists(str(c.get("image"))))]
        die("real thumbnail images are required for every card, and these have none: " + "; ".join(lack[:12])
            + (" ..." if len(lack) > 12 else "")
            + ". Outliers: run `scripts/outlier_store.py fetch-thumbs`, or ask the user to supply them. Candidate: have the "
              "thumbnail-maker render it. (Text-only feeds need the explicit flag --allow-descriptions.)")
    if not use_images:
        if not common:
            if all(clean(c.get("visual")) for c in cards):
                use_visual = True
            else:
                die("no description field is present on ALL cards (outliers and candidate). Fill the same fields "
                    f"({', '.join(FIELDS)}) or `visual` for every card, or supply an image for every card.")
        if dropped:
            warn.append("description fields dropped because not every card has them: " + ", ".join(dropped)
                        + (" (the test is blind to these)" if dropped else ""))
        if "medium" not in common and not use_visual:
            warn.append("`medium` (style/look of the thumbnail) is not on every card, so the viewer will not see it. "
                        "Fill it for every outlier or the channel's visual style is untested.")

    views = [card_view(c, common, use_visual) for c in cards]
    for i, v in enumerate(views):
        for k, val in v.items():
            if META_PAT.search(val):
                warn.append(f"card {'CANDIDATE' if i == len(cards) - 1 else 'outlier #' + str(i + 1)} field '{k}' looks like it holds metadata "
                            f"({META_PAT.search(val).group(0)!r}); remove it from the text")
            if i == len(cards) - 1 and k not in ("title", "text"):      # a packager's voice in the description is the tell
                for w in INTENT_WORDS:
                    if re.search(r"\b" + re.escape(w) + r"\b", val.lower()):
                        warn.append(f"CANDIDATE description field '{k}' contains the intent/hype word '{w}'; describe only what is visible")
    if not use_images:
        def size(v): return sum(words(x) for k, x in v.items() if k not in ("title", "text"))
        osz = [size(v) for v in views[:-1]]
        med = statistics.median(osz)
        if med and not (0.6 * med <= size(views[-1]) <= 1.6 * med):
            warn.append(f"candidate description is {size(views[-1])} words vs outlier median {med:.0f}; make it the same level of detail")
    if len(outs) < 15:
        warn.append(f"only {len(outs)} outliers: the feed is thinner than a real 30-40 card feed, so the test is weaker")

    n = len(cards)
    min_pos = min(a.min_pos, n)
    seed = a.seed if a.seed is not None else secrets.randbits(64)
    rng = random.Random(seed)
    cand_views = a.candidate_views if a.candidate_views is not None else rng.randint(5000, 45000)
    if cand_views >= 50000:
        warn.append(f"candidate views {cand_views} are not under 50,000; the view-bias test is skipped for it")
    vlabel = [fmt_views(n_) for n_ in ov] + [fmt_views(cand_views)]
    order = list(range(len(outs)))
    rng.shuffle(order)                               # outlier order
    cand_pos = rng.randint(min_pos, n)               # candidate never in the first (min_pos-1) slots
    seq = order[:cand_pos - 1] + ["C"] + order[cand_pos - 1:]

    folder = os.path.join(a.feeds_root, secrets.token_hex(4))
    os.makedirs(folder, exist_ok=True)
    blocks = []
    for pos, ref in enumerate(seq, 1):
        c, v = (cand, views[-1]) if ref == "C" else (outs[ref], views[ref])
        img = None
        if use_images:
            img = os.path.join(folder, f"card-{pos:02d}.jpg")
            if not reencode(c["image"], img):
                shutil.copyfile(c["image"], img)
                warn.append("Pillow missing: images copied as-is (metadata and sizes not normalized)")
        blocks.append(render(pos, v, img, vlabel[-1] if ref == "C" else vlabel[ref]))
    head = f"# Your feed ({n} cards)\n\nCards are listed in the order they appear on screen.\n\n"
    with open(os.path.join(folder, "feed.md"), "w", encoding="utf-8") as f:
        f.write(head + "\n".join(blocks))

    key = {"seed": seed, "n_cards": n, "candidate_position": cand_pos, "mode": "images" if use_images else "descriptions",
           "candidate_views_shown": cand_views, "feed_folder": folder, "positions": [{"pos": p, "who": "CANDIDATE" if r == "C" else "outlier",
                                               "title": clean((cand if r == "C" else outs[r]).get("title")),
                                               "outlier_index": None if r == "C" else r + 1}
                                              for p, r in enumerate(seq, 1)]}
    os.makedirs(os.path.dirname(os.path.abspath(a.key)), exist_ok=True)
    with open(a.key, "w", encoding="utf-8") as f:
        json.dump(key, f, indent=1)
    print(f"feed: {os.path.join(folder, 'feed.md')}   cards: {n} ({len(outs)} outliers + 1)   mode: {key['mode']}")
    print(f"candidate position: {cand_pos}, shown with {fmt_views(cand_views)}; sub-50k decoys in feed: {len(low)} (private: written only to {a.key})")
    for w in warn:
        print("WARN:", w)
    if warn and a.strict:
        sys.exit(2)


def verdict(a):
    key = load(a.key)
    try:
        t = open(a.verdict, encoding="utf-8-sig").read()
    except Exception as e:
        die(f"cannot read verdict: {e}")
    m = re.search(r"VERDICT\s*:?\**\s*CLICK\**\s*[:\-\u2013\u2014]?\s*\**\s*(?:card[\s\-_#]*)?0*(\d+)", t, re.I)
    if not m:
        sys.stderr.write("verdict unreadable: expected 'VERDICT: CLICK card NN'\n"); sys.exit(2)
    pos = int(m.group(1))
    p = re.search(r"PULL\s*:?\**\s*(REAL|FORCED)", t, re.I)
    pull = p.group(1).upper() if p else "UNSTATED"
    stop = []
    sm = re.search(r"thumb[\s\-]*stoppers?[^\n]*\n?([^\n]*(?:\n(?!\*\*)[^\n]*)*)", t, re.I)
    if sm:
        stop = sorted({int(x) for x in re.findall(r"card[\s\-_#]*0*(\d+)", sm.group(0), re.I)})
    who = {x["pos"]: x for x in key["positions"]}
    if pos not in who:
        sys.stderr.write(f"viewer clicked card {pos}, which is not in the feed\n"); sys.exit(2)
    cand = key["candidate_position"]
    clicked = who[pos]
    ok = (pos == cand and pull == "REAL")
    print(f"clicked: card {pos:02d} = {'THE CANDIDATE' if pos == cand else 'outlier #' + str(clicked['outlier_index']) + ': ' + clicked['title']}")
    print(f"pull: {pull}")
    if key.get("candidate_views_shown") is not None:
        print(f"candidate was shown with {key['candidate_views_shown']:,} views; clicked card was shown at "
              + ("the candidate's count" if pos == cand else "an outlier's real count") + (" (view-biased test)" if key["candidate_views_shown"] < 50000 else ""))
    print(f"candidate was card {cand:02d}; candidate among thumb-stoppers: {'yes' if cand in stop else 'no'} ({', '.join(f'{s:02d}' for s in stop) or 'none listed'})")
    if pos == cand and pull != "REAL":
        print("note: candidate was clicked but only as a forced pick (pull not REAL), so this round is NOT a pass")
    print("ROUND RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = ap.add_subparsers(dest="cmd", required=True)
b = sub.add_parser("build")
b.add_argument("--outliers", required=True)
b.add_argument("--card", required=True)
b.add_argument("--feeds-root", required=True, help="neutral folder; a random sub-folder is created per feed")
b.add_argument("--key", required=True, help="private key file; must NOT be inside the feeds root")
b.add_argument("--seed", type=int, default=None, help="testing only; normally a fresh random seed")
b.add_argument("--min-pos", type=int, default=4, help="earliest slot the candidate may take (default 4: never in the top 3)")
b.add_argument("--candidate-views", type=int, default=None, help="view count printed on the candidate (default: random 5,000-45,000)")
b.add_argument("--min-decoys", type=int, default=3, help="refuse unless this many outliers have under 50,000 views (default 3)")
b.add_argument("--allow-no-decoys", action="store_true", help="testing only: allow a feed without sub-50k decoys")
b.add_argument("--strict", action="store_true", help="exit 2 on any warning")
b.add_argument("--allow-descriptions", action="store_true",
               help="allow a text-description feed when some card has no image (weaker test; default is to refuse)")
v = sub.add_parser("verdict")
v.add_argument("--key", required=True)
v.add_argument("--verdict", required=True)
a = ap.parse_args()
if a.cmd == "build":
    if os.path.commonpath([os.path.abspath(a.key), os.path.abspath(a.feeds_root)]) == os.path.abspath(a.feeds_root):
        die("the key file must not be inside the feeds root (the viewer can read that folder)")
    build(a)
else:
    verdict(a)
