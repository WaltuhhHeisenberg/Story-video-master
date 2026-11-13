# script-retention

Two agents that make YouTube scripts hold a lazy viewer, plus the method they share.

## The agents

**Lazy Viewer** (`story-video-master:script-lazy-viewer`)
An impatient listener set to 3x worse than the average viewer. He hears your script in spoken order at real speaking speed, runs a visible interest meter, and tells you the exact timestamp where he leaves, every earlier moment his thumb hovered, and the smallest fix for each leak. Read-only. He never rewrites your script and never accepts "it gets good later."

**Script-Writing Teacher** (`story-video-master:script-writing-teacher`)
Diagnoses the gaps in your hook, pacing, payoffs and ending, teaches the principle behind each fix using a before/after on your own lines, and saves a revised script next to the original. Never invents facts: anything uncertain is marked [VERIFY]. Can also build a script from a title and raw notes, or answer how-do-I-write-this questions.

## The method

Both agents use the `story-explainer-scripts` skill as their rulebook: state the outcome first, every sentence pays off one thing and opens one thing, expectation then violation, numbers instead of adjectives, plain voice and strong order. The Lazy Viewer scores a script on eight named checks drawn from it (Hook, Pays and opens, Expectation break, Numbers, Hook payoffs, Voice and rhythm, Structure, Ending and promise) and names leaks with the skill's audit flags. The Teacher follows the skill's workflow (fact ledger, story engine, beat map, draft, audit) and fixes by the same flags, so both judge and fix by one standard.

## Commands

| Command | What it does |
|---|---|
| `/lazy-test <script>` | Lazy Viewer report: drop-off time, timeline, leaks, scorecard |
| `/fix-script <script>` | Teacher diagnoses, teaches, and saves `<name>.revised.md` |
| `/retention-loop <script>` | Viewer, Teacher, Viewer again, up to 3 rounds, stops on pass or stall |

`<script>` can be a file path or pasted text. Add the video title after it for a sharper test, for example `title: the accident that saved millions of lives`.

## Try it now

A deliberately weak sample script is in `examples/sample-script.md`:

```
/lazy-test examples/sample-script.md
/retention-loop examples/sample-script.md
```

## Install

- Local test with Claude Code: `claude --plugin-dir ./script-retention`
- To share or install elsewhere, upload the zipped folder (`script-retention.zip`) wherever your Claude app accepts plugins.

## Honest limits

The Lazy Viewer is a simulation from text, not YouTube analytics. It cannot see visuals, music, editing or your voice, and its patience numbers are working assumptions. Use it to find and fix likely leaks before filming, then check the real retention graph after upload and trust the graph.
