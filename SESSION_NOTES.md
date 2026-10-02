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

## Session 29/09/2026 — Error-status visibility fix
WHAT WAS DONE:
- Diagnosed the documented "Save unresponsive after failed decode" defect. Root cause: the save was actually REFUSING with a status-bar message ("Message 2 has content - add a Pass 2 password before saving.") that was effectively invisible to the user. Not a logic defect.
- Fix: _status() in Stegano.py now treats error-type messages as alerts — one error sound (played centrally) plus a ~1.2s pulse of the status text (bold bright-white alternating with dim red, brightness-based for colour-blind accessibility), settling in dim red for ~4 seconds. Info/success messages unchanged.
- Removed five now-duplicate self.audio.play_sfx('error') calls that sat directly next to error-status messages (in _on_decode_result, _on_decode_error, the file-size validation block, _on_image_load_error, _on_encode_error) to prevent double-beeps.
- Stegano.bat now launches Aider with --no-auto-commits (backup at Stegano.bat.bak); Aider no longer self-commits.

TESTED (by user, live):
- Original failing scenario: the previously-silent Save refusal now flashes and beeps clearly.
- Clean-session and dirty-session (post failed-decode) saves of virgin images both behave correctly.
- Post-save resting state (message shown, passwords cleared, Save hidden) confirmed as designed behaviour.
- Syntax check passed; committed via save.bat as 5c7d996.

OPEN ITEMS:
1. UNREPRODUCED: one occurrence of "Message 2 has content" warning on a virgin JPEG (load -> type -> Pass 1 -> Save). Two controlled reproduction attempts (clean session; dirty session after failed decode) both FAILED to reproduce. Likely trigger: stray focus on Pass 2 (eventFilter silently switches message slots on password-field focus — see lines ~1224-1235). If it recurs, capture the exact click sequence before touching anything.
2. DESIGN DECISION PENDING (user request): saving should arguably NOT clear passwords/reset workflow state — user considers a normal save a non-event, not a security event. Current behaviour unchanged; needs design discussion (possibly a settings toggle).
3. FUTURE: password-replacement flow (decode with old password, enter NEW password, save to re-encrypt without a re-decode attempt). Currently a changed password triggers a doomed re-decode that wipes the decoded message.
4. FUTURE (accessibility): static colour-only success/error distinction may be hard for colour-blind users; consider icons or paired sounds.
5. Housekeeping: leftover patch script fix_enter.py in project folder is not part of the app and can be deleted.

