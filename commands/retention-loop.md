---
description: Run Lazy Viewer, then the Script-Writing Teacher, then Lazy Viewer again, up to 3 rounds, until the viewer stays to the end or progress stalls
argument-hint: "<path to script file, or paste the script> [title: <video title>]"
---

Run the full test-and-fix loop on the script the user gave.

Input: $ARGUMENTS

Setup: work out whether the input is a file path (confirm it exists) or pasted text. If it is pasted text, save it to `script.md` in the working directory first. If empty, ask for the script in one short question and stop. Note the title/thumbnail text if given.

Loop (maximum 3 rounds):
1. **Listen.** Launch `story-video-master:script-lazy-viewer` with only the current script and the title/thumbnail text. Record the drop-off time (or "reaches the end"), the lowest meter value, and the leak list.
2. **Check stop conditions.** Stop the loop if any is true:
   - The viewer reaches the end with a lowest meter value of 25 or more and no leak that ends the viewing. This is a pass.
   - This is round 3.
   - The drop-off is no later than in the previous round (stalled). Stop and report it as stalled; do not keep rewriting blindly.
3. **Teach and fix.** Launch `story-video-master:script-writing-teacher` with the current script, the title/thumbnail text, and the Lazy Viewer report from this round. It saves a `.revised.md` file. Make that revised file the current script.
4. Go back to step 1 with the revised script. Give the Lazy Viewer only the revised script, never the Teacher's reasoning, so the test stays independent.

When done, report to the user in a short summary:
- A small table: round, drop-off time (or "end"), lowest meter value.
- The final script path.
- Any [VERIFY] items the Teacher flagged.
- If it did not pass, the top remaining leak and what the user should decide.
- One line reminding them this is a simulation: compare the predicted leak points with the real retention graph after upload.
