---
description: Run the Lazy Viewer on a script and get the predicted drop-off point, every hover point, and the smallest fix for each
argument-hint: "<path to script file, or paste the script> [title: <video title>]"
---

Run the Lazy Viewer on the script the user gave.

Input: $ARGUMENTS

Steps:
1. Work out what the input is. If it looks like a file path, confirm the file exists (Glob if needed). If it is pasted script text, use it as is. If it is empty, ask the user for the script (one short question) and stop.
2. If the user included a title or thumbnail text, pass it along as the video's promise.
3. Launch the `story-video-master:script-lazy-viewer` agent with only: the script (path or text) and the title/thumbnail text if known. Do not pass your own opinions, the user's explanations, or any hint about what the script is trying to do.
4. Return the agent's report to the user exactly as produced. Then add one line offering the next step: "Run /fix-script to have the Script-Writing Teacher fix these gaps, or /retention-loop to fix and re-test automatically."
