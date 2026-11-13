---
description: Have the Script-Writing Teacher diagnose a script, teach each fix, and save a revised version
argument-hint: "<path to script file, or paste the script> [title: <video title>]"
---

Have the Script-Writing Teacher fix the script the user gave.

Input: $ARGUMENTS

Steps:
1. Work out what the input is: a file path (confirm it exists), pasted script text, or empty. If empty, ask for the script in one short question and stop.
2. If a Lazy Viewer report for this script already exists earlier in this conversation, include it verbatim in what you pass along.
3. Launch the `story-video-master:script-writing-teacher` agent with the script (path or text), the title/thumbnail text if known, and the Lazy Viewer report if there is one.
4. Show the user the Teacher's lesson and tell them where the revised script was saved. Then offer: "Run /lazy-test on the revised script to see whether the drop-off moved later."
