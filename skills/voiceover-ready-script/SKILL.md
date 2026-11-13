---
name: voiceover-ready-script
description: Stage 3c of the story-video-master flow. Turns the final retention-tested script into a clean, voiceover-ready text (plain narration only) and stops for the user to record. Use when the user wants the clean script to read aloud, "voiceover script", "script for recording", or after the retention loop.
---

# Voiceover-ready script (the STOP deliverable)

Input: the final script file (`03-script.md` or its latest `.revised.md`). Fresh-chat rule: start from that file only.

1. **Open facts first.** Every `[VERIFY]` must be resolved (search for the fact, or ask the user once, all items in one message). Nothing unverified goes to a voice actor.
2. **Run the cleaner:** `python scripts/clean_voiceover_script.py --script <file> --out 04-voiceover-script.txt --report reports/voiceover_script_report.md`. It strips headings, ledger/beat-map tables, notes, `[cues]`, markdown; it never rewrites a word. Exit 2 = not ready (open `[VERIFY]`, placeholders, no narration): fix the cause, run again.
3. **Read the risks list** and decide with the user only where it matters (digits and symbols a voice may misread, acronyms, very long sentences). Changes are made in the script file, never silently by the cleaner; then re-run.
4. **Read-through:** read the clean text once as speech. Anything that cannot be said in one breath or only makes sense on screen gets reworded in the script file (log it as a problem if the scriptwriting stage should have prevented it).
5. **Deliver** `04-voiceover-script.txt` + word count + runtime (150 wpm) and say what Run B needs (voiceover, word-level transcript, assets).

Never add cues, stage directions, timestamps, headings or notes to the delivered text: it is pure narration.
