# clauses.json (output of Stage 4, input of the scene map and of the bridge)
```json
{
  "project": {"name":"My Video","fps":30,"language":"en"},
  "voiceover": {"file":"voiceover.mp3","duration":812.4},
  "sections": [{"id":"S01","name":"THE COLD EVENING","role":"hook","start":0.0,"end":18.3}],
  "clauses": [
    {"id":"C001","section":"S01","start":0.0,"end":3.6,"dur":3.6,
     "text":"Every big city has the same problem.","words":[0,6],
     "boundary":"pause (beat) after 'problem.'","pause_after":0.5,"emphasis":["same"],"flags":[]}
  ]
}
```
Clauses are contiguous (first starts at 0, last ends at the voiceover end), 3.0-4.0 s (<= 4.5 only with a flag), sections align to clause boundaries and have real names (not S01, S02).

What the 3D bridge does with it: each **section** becomes one world (scene) of the video, each **clause** becomes exactly one camera shot (`from`/`to` = clause start/end on the frame grid), `pause_after` >= 0.6 s makes the actor stand idle through the pause. See `skills/scene-map-to-toon/SKILL.md`.
