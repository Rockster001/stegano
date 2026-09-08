# SESSION_NOTES.md
State: Steps 1, 2 and half of 3 done (audio, password, encryption modules extracted & tested).
Next: Step 3 second half — image functions (encode_image, decode_image, encode_dual_image,
decode_dual_image) into steganography_utils.py. Then Steps 4 (ui_components), 5 (workers), 6 (tidy).
Gotchas: model hits token limits if asked for too much — one small instruction per session.
Workflow: fresh Aider → /add Stegano.py → /add REFACTOR_PLAN.md → one instruction → test → save.bat.
Scoring: after any session, "git log --oneline" in PowerShell — top line is the verdict.