# SESSION_NOTES.md

## HOW TO START A WORK SESSION (follow top to bottom, in order)

1. Open the folder C:\Dev\Stegano
2. Double-click  stegano.bat   (black window opens, stays blank 30-60 seconds - WAIT)
3. Wait until you see the line:  diff>
4. Type:  /add Stegano.py     then press Enter
5. Type:  /add REFACTOR_PLAN.md   then press Enter
6. Type:  /add SESSION_NOTES.md   then press Enter
7. Now type the task instruction. Read "WHAT TO DO NEXT" below and type it in.

## HOW TO FINISH A WORK SESSION (follow top to bottom, in order)

1. In the Aider window (diff> prompt) type:  /exit   (whole window may close - that is fine)
2. In the black PowerShell window type:  .\save.bat   then press Enter
3. Finished when you see a line ending in:  main -> main
4. If anything in the save looks wrong: STOP, do nothing more, ask an AI in the browser
   (paste exactly what the window says)

## WHILE AIDER IS WORKING - THE GATES
- Offer to add a .wav, .mp3 or .png file:  answer  N
- "Allow edits to file that has not been added?":  answer  N
- "Create new file?":  answer Y only if the task says to create that exact file
- If Aider seems stuck or repeats itself:  type  /undo  - if unsure, STOP and ask a browser AI

## AFTER THE TEST - THE VERDICT (one command, in PowerShell)
- Type:  git log --oneline
- The TOP line is the verdict. It should mention the module just worked on.
- Program works + new top line = SUCCESS. Go to "HOW TO FINISH".
- Program broken = do not save. Ask a browser AI, paste the last error line.

## WHAT TO DO NEXT
Fix the dual-password bug: when decoding a dual-layer message, pressing Enter after typing Password 2 reverts to status 'Password Required' instead of proceeding (same failure when encoding to a virgin image with Pass 2). Bug predates the refactor — verified by testing the pre-refactor version. Territory: Enter-key handling and decode-trigger flow in Stegano.py's SteganographyApp class. Approach: investigate first, change nothing until diagnosis is confirmed.

## WHERE THINGS STAND
All 6 refactoring steps COMPLETE and vaulted as of today. Program runs clean. Known issue: the Pass 2 dual-password bug above — the only remaining defect. Next: investigate and fix it.
