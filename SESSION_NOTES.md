SESSION\_NOTES.md

HOW TO START A WORK SESSION (follow top to bottom, in order)

Open the folder C:\\Dev\\Stegano

Double-click stegano.bat (black window opens, stays blank 30-60 seconds - WAIT)

Wait until you see the line: diff>

Type: /add Stegano.py then press Enter

Type: /add SESSION\_NOTES.md then press Enter

Now type the task instruction. Read "WHAT TO DO NEXT" below and type it in.

HOW TO FINISH A WORK SESSION (follow top to bottom, in order)

In the Aider window (diff> prompt) type: /exit (whole window may close - that is fine)

In the black PowerShell window type: .\\save.bat then press Enter

Finished when you see a line ending in: main -> main

If anything in the save looks wrong: STOP, do nothing more, ask an AI in the browser

(paste exactly what the window says)

WHILE AIDER IS WORKING - THE GATES

Offer to add a .wav, .mp3 or .png file: answer N

"Allow edits to file that has not been added?": answer N

"Create new file?": answer Y only if the task says to create that exact file

If Aider seems stuck or repeats itself: press Ctrl+C - if unsure, STOP and ask a browser AI

AFTER THE TEST - THE VERDICT (one command, in PowerShell)

Type: git log --oneline

The TOP line is the verdict. It should mention the module just worked on.

Program works + new top line = SUCCESS. Go to "HOW TO FINISH".

Program broken = do not save. Ask a browser AI, paste the last error line.

WHAT TO DO NEXT

The dual-password feature is COMPLETE and verified: dual saves work, both layers decode,

Enter in Pass 2 reveals layer 2, deleting Pass 2 + Enter un-reveals to layer 1, and the

tab switching (clicking between Pass fields) swaps layers in DECODE mode.

The double-click password popup is implemented (double-click either Pass field opens the

saved-passwords dialog; the key icon button is hidden).

REMAINING BACKLOG: password bar redesign; requirements.txt; README; the executable

(PyInstaller); cleanup pass (test images in vault); state-matrix test session (optional).

Also: test files now belong in C:\\Dev\\SteganoTest (outside the repo) - see BACKLOG below.

ALSO SEE: PHASE2\_DESIGN.md (in this folder) - ratified Phase 2 design: Settings dialog,

graduated password reveal, error explanations. Its Part 6 defers password replacement.



BACKLOG - PASSWORD BAR REDESIGN (design session needed)

The password row is convoluted and accumulated rather than designed

Asymmetry: two dedicated show/hide toggles but one shared clear button

Icon clarity: the removed memory button's key icon was not recognised even by the

owner after months of use

The password strength indicator bar's placement and usefulness need review

Do this alongside the view-mode tab enhancement, as both reshape the same control row

(NOTE: view-mode tab switching was since implemented - see SAVED PASSWORDS section)

SAVED PASSWORDS - KNOWN BEHAVIOR

The saved-passwords list holds a maximum of 10 passwords, most-recent-first; the oldest

is dropped when the list overflows. This is intended behavior. Passwords are saved

automatically on successful decodes and encrypted at rest. If a password disappears from

the list, it was pushed out by newer entries. Double-clicking either Pass field opens the

saved-passwords dialog (the key icon button has been hidden).



WHERE THINGS STAND

All 6 refactoring steps COMPLETE. Dual-password feature FULLY WORKING and verified:

dual saves work, both layers decode, un-reveal works, tab switching works in decode mode.

Double-click password popup implemented and tested. View-mode tab switching implemented.

Test files belong in C:\\Dev\\SteganoTest (outside the repo). Program verified working

05/10/2026.



KNOWN DEFECT: Save blocked after failed decode (discovered 26/09/2026)

Reproduction: load encoded image, decode with Pass 1, type a NEW password into

Pass 1, press Enter (decode fails as designed), click message window (Encode mode),

type new password in Pass 1, press Enter (inert, as designed), click Save.

RESULT: Save does nothing. WORKAROUND: click Cancel first, then Save works.

Status: RESOLVED 29/09/2026 - root cause was the save REFUSING with a

near-invisible status message ("Message 2 has content..."), not state corruption.

Fixed by the error-visibility change (see Session 29/09/2026 entry below).

This section's original suspected cause is superseded by that entry.



Session 29/09/2026 - Error-status visibility fix

WHAT WAS DONE:



Diagnosed the documented "Save unresponsive after failed decode" defect. Root cause:

the save was actually REFUSING with a status-bar message ("Message 2 has content -

add a Pass 2 password before saving.") that was effectively invisible to the user.

Not a logic defect.

Fix: \_status() in Stegano.py now treats error-type messages as alerts - one error

sound (played centrally) plus a \~1.2s pulse of the status text (bold bright-white

alternating with dim red, brightness-based for colour-blind accessibility),

settling in dim red for \~4 seconds. Info/success messages unchanged.

Removed five now-duplicate self.audio.play\_sfx('error') calls that sat directly next

to error-status messages (in \_on\_decode\_result, \_on\_decode\_error, the file-size

validation block, \_on\_image\_load\_error, \_on\_encode\_error) to prevent double-beeps.

Stegano.bat now launches Aider with --no-auto-commits (backup at Stegano.bat.bak);

Aider no longer self-commits.

TESTED (by user, live):

Original failing scenario: the previously-silent Save refusal now flashes and beeps

clearly.

Clean-session and dirty-session (post failed-decode) saves of virgin images both

behave correctly.

Post-save resting state (message shown, passwords cleared, Save hidden) confirmed as

designed behaviour.

Syntax check passed; committed via save.bat as 5c7d996.

OPEN ITEMS:

UNREPRODUCED: one occurrence of "Message 2 has content" warning on a virgin JPEG

(load -> type -> Pass 1 -> Save). Two controlled reproduction attempts (clean

session; dirty session after failed decode) both FAILED to reproduce. Likely

trigger: stray focus on Pass 2 (eventFilter silently switches message slots on

password-field focus). If it recurs, capture the exact click sequence before

touching anything.

DESIGN DECISION PENDING (user request): saving should arguably NOT clear

passwords/reset workflow state - user considers a normal save a non-event, not a

security event. Current behaviour unchanged; needs design discussion (possibly a

settings toggle). NOW RATIFIED IN PHASE2\_DESIGN.md (setting S2, default ON).

FUTURE: password-replacement flow (decode with old password, enter NEW password,

save to re-encrypt without a re-decode attempt). Currently a changed password

triggers a doomed re-decode that wipes the decoded message. NOW DEFERRED to

PHASE2\_DESIGN.md Part 6 (future phase).

FUTURE (accessibility): static colour-only success/error distinction may be hard

for colour-blind users; consider icons or paired sounds. NOW PARTIALLY ADDRESSED

in PHASE2\_DESIGN.md (S3/S4 alert escalation; highlight-bar fallback).

Housekeeping: DONE - fix\_enter.py was deleted on 24/09.

PARKED CONCEPT - MULTI-MESSAGE, SINGLE FIELD (explored 27/09, not committed)

THE CONCEPT: One Pass field. An image holds N independent, standalone messages,

each encrypted with its OWN password. Entering any correct password reveals that

message. NO layer structure, NO order, NO hierarchy, NO recorded relationships

between messages. Password-as-identity, not password-as-position.



MOTIVATING SCENARIOS (owner's):



Targeted distribution: one image, multiple recipients, each with their own

password, each reading only their message. No recipient can discover that

other messages exist.

The quiz/answers pattern, generalized beyond two states.

The DECOY pattern: deliberately crackable passwords protect decoy messages that

are complete, plausible, and self-terminating - an interceptor who cracks one

(or several) is SATISFIED and stops, because each decoy reads as genuine with

its own natural ending. Decoy effectiveness is SOCIAL (the adversary stops when

satisfied), reducing the need for the payload count to be technically

undetectable.

STRENGTHS DISCUSSED: the payload-delimiter format extends to N payloads naturally;

the two-layer state machinery (the bug-densest code) would dissolve into simpler

list handling; single field does not advertise structure to observers.



WEAKNESSES DISCUSSED: campaign-sized rebuild touching every decode/encode path;

positional certainty lost; security model needs full re-validation; existing dual

images need conversion or become legacy; the Links mechanism answers most

game-scenario needs on the CURRENT system.



RE-EVALUATION TRIGGERS (any one justifies revisiting):



An actual use case hits the two-message ceiling with no workaround.

The toolchain becomes reliable for large rebuilds.

External users report the two-message limit as a practical barrier.

RELATED: a HYBRID variant (dual Pass fields, each holding multiple messages) was

explored and set aside - its necessity argument did not survive scrutiny. May

warrant revisiting only if the concept above advances to design. See also

PHASE2\_DESIGN.md Part 6 (password replacement).



DESIGN PRINCIPLE (owner's ruling 27/09) - STRUCTURAL IGNORANCE

The program must NEVER know, record, or display the relationships between encoded

messages. No sequence numbers, no timestamps, no tier tags, no importance flags, no

payload ordering, no "this is the real one" metadata. The payload structure must

remain an unordered, unannotated list of independent encrypted blobs.



RATIONALE (owner's words): "The program NEVER needs to know or record the

relationships between the encoded messages. In fact, that ability would be

demonstrably detrimental to the purpose of the program!" The program's ignorance

is a security feature - even full program access must reveal nothing about which

message matters, which is a decoy, or how messages relate. This principle OUTLIVES

the parked concept: it applies to the current dual system, any future

multi-payload format, and every feature that touches message storage.



PRACTICAL CONSEQUENCES:



Decode display must be structurally neutral: show the message, never reveal

position, collection size, or decode history

The saved-passwords feature must not imply message relationships

Any future format change that adds structure or metadata violates this principle

unless the owner explicitly re-rules it

RELEASE CHECKLIST (for the executable/release stage)

Ship starter pack of virgin images (curated, variety of sizes)

First-run: seed C:\\Users<name>\\Documents\\Stegano\\Images with the starters

Select Image dialog: first-run default = that folder (lastDir memory unchanged

after first selection)

Ensure NO dev/test files ship in the release package

Include requirements.txt and README (the shareability kit)

