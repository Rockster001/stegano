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
## RELEASE CHECKLIST (for the executable/release stage)
- Ship starter pack of virgin images (curated, variety of sizes)
- First-run: seed C:\Users<name>\Documents\Stegano\Images with the starters
- Select Image dialog: first-run default = that folder (lastDir memory unchanged after first selection)
- Ensure NO dev/test files ship in the release package
- Include requirements.txt and README (the shareability kit)

## WHERE THINGS STAND
All 6 refactoring steps COMPLETE and vaulted as of today. Program runs clean. The dual-password feature is FIXED and verified end-to-end (quiz scenario passed). Remaining known work: this release checklist, plus a cleanup pass (vault contents, test images).
