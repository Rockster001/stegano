# SESSION_NOTES.md

## HOW TO START A WORK SESSION (follow top to bottom, in order)

1. Open the folder C:\Dev\Stegano
2. Double-click  stegano.bat   (black window opens, stays blank 30-60 seconds - WAIT)
3. Wait until you see the line:  diff>
4. Type:  /add Stegano.py     then press Enter
5. Type:  /add SESSION_NOTES.md   then press Enter
6. Now type the task instruction. Read "WHAT TO DO NEXT" below and type it in.

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
- If Aider seems stuck or repeats itself:  press Ctrl+C  - if unsure, STOP and ask a browser AI

## AFTER THE TEST - THE VERDICT (one command, in PowerShell)
- Type:  git log --oneline
- The TOP line is the verdict. It should mention the module just worked on.
- Program works + new top line = SUCCESS. Go to "HOW TO FINISH".
- Program broken = do not save. Ask a browser AI, paste the last error line.

## WHAT TO DO NEXT
The dual-password feature is COMPLETE and verified: dual saves work, both layers decode,
Enter in Pass 2 reveals layer 2, deleting Pass 2 + Enter un-reveals to layer 1, and the
tab switching (clicking between Pass fields) swaps layers in DECODE mode.
REMAINING BACKLOG: password bar redesign; requirements.txt; README; the executable
(PyInstaller); cleanup pass (test images in vault); state-matrix test session (optional).
Also: test files now belong in C:\Dev\SteganoTest (outside the repo) - see BACKLOG below.

## BACKLOG - PASSWORD BAR REDESIGN (design session needed)
- The password row is convoluted and accumulated rather than designed
- Asymmetry: two dedicated show/hide toggles but one shared clear button
- Icon clarity: the removed memory button's key icon was not recognised even by the
  owner after months of use
- The password strength indicator bar's placement and usefulness need review
- Do this alongside the view-mode tab enhancement, as both reshape the same control row
  (NOTE: view-mode tab switching was since implemented - see SAVED PASSWORDS section)

## SAVED PASSWORDS - KNOWN BEHAVIOR
The saved-passwords list holds a maximum of 10 passwords, most-recent-first; the oldest
is dropped when the list overflows. This is intended behavior. Passwords are saved
automatically on successful decodes and encrypted at rest. If a password disappears from
the list, it was pushed out by newer entries. Double-clicking either Pass field opens the
saved-passwords dialog (the key icon button has been hidden).

## WHERE THINGS STAND
All 6 refactoring steps COMPLETE. Dual-password feature FULLY WORKING and verified:
dual saves work, both layers decode, un-reveal works, tab switching works in decode mode.
Test files belong in C:\Dev\SteganoTest. Program verified working 24/09/2026.

## KNOWN DEFECT: Save blocked after failed decode (discovered 26/09/2026)
Reproduction: load encoded image, decode with Pass 1, type a NEW password into
Pass 1, press Enter (decode fails as designed), click message window (Encode mode),
type new password in Pass 1, press Enter (inert, as designed), click Save.
RESULT: Save does nothing. WORKAROUND: click Cancel first, then Save works.
Suspected cause: failed decode corrupts editing state (_editing_layer or buffers);
Cancel repairs it. Likely affects Pass 2 identically (untested).
Status: DIAGNOSED IN PRINCIPLE - fix pending next session.