# STEGANO PROJECT — HANDOFF DOCUMENT

Read this fully before touching any code. It was written for you, the incoming AI assistant.

Companion file: `STEGANO_WORKLOG.md` — the complete task-by-task history of this project (Tasks 1–122), including every design decision, ruling, and reversal. When in doubt about WHY something is the way it is, look there first, then ask the user.

## 1. What the project is

A PyQt desktop application for dual-message LSB steganography, located at `C:\Dev\Stegano`.
Files that matter:
- `Stegano.py` (~1620 lines) — the GUI and all application logic.
- `steganography_utils.py` — the embedding/encryption engine.
- `workers.py` — background decode worker; emits `decoding_finished(str, bool, int, str, str)`.
- `Stegano.bat` — the launcher the user runs (starts Aider + app workflow).
- `Save.bat` — the git COMMIT script (running it commits everything uncommitted — do not confuse the two; a previous AI did, causing a stray commit `7f5361d`).
- Backup files on disk: `Stegano_broken_backup.py`, `Stegano_prerepair_backup.py`, `steganography_utils_broken_backup.py`, `workers_broken_backup.py`.

## 2. CRITICAL: how the app works (UI flow)

- **Encoding**: the user types messages/passwords into the UI, then SAVES the image. Saving performs the embedding. There is NO separate "Encode" button.
- **Decoding**: loading an encoded image automatically decodes it. There is NO separate "Decode" button. Passwords are supplied via the password fields / prompts at load time.
- NEVER invent UI elements, button names, or flows. The user is the spec-of-record; ask them, or verify in bytes, before describing the UI.

## 3. Steganographic format (byte-level)

LSB embedding of a byte payload:
- Dual-message: `DUAL_HEADER` (sha256 of b"STEGO_DUAL_MAGIC") + payload1 + delimiter (`\x00\x00\x03`) + payload2 + delimiter. Headers and delimiters are deliberately plaintext.
- Payloads are AES-encrypted when a password is given; empty password = plaintext ("open mode").
- Single-message formats use `STEALTH_HEADER` / `LEGACY_HEADER`.
- Engine functions (verified current): `encode_dual_image(img_path, msg1, msg2, save_path, dual_header_bytes, delim, out_format="PNG", pass1="", pass2="")`, `decode_dual_image(img_path, delim, pass1="", pass2="")`, `extract_dual_layer2_blob`, `encode_dual_image_from_blobs` (8 params — preserves layer-2 ciphertext verbatim when only message 1 is edited).

### One-password design (verified, DO NOT regress):
- Encode: msg2 present + pass2 empty → pass2 = pass1. Both messages + both passwords empty → both layers plaintext.
- Decode: layer 2 tries pass2 → falls back to pass1 (if pass1 and pass1 != pass2) → raw attempt when no pass2 (open mode) → raises ValueError("Incorrect password.") ONLY when pass2 was supplied; otherwise returns layer 1 gracefully.

### UI state model (dictates decode behavior):
- `_loaded_image_format`, `_decoded_layer2_blob`, `_message1/2_buffer`, `_decoded_layer1/2_message`, `_currently_shown_layer`, `_editing_layer`, `_layer2_active`.
- RULING: after decoding a dual image, the display ALWAYS lands on Layer 1, even if layer 2 was what decoded.
- `is_dual = (format=="dual") or bool(m2) or bool(pass2)`.

## 4. Git state

- HEAD = `15903c3` (04/11/2026): the verified, recovered, fully working state.
- `git status --short` was EMPTY (clean tree) at handoff.
- History: `7f5361d` (03/11) = accidental Save.bat commit of test images/backups (harmless); `1198c4c` (18/10) = earlier baseline.

## 5. Working protocols (MANDATORY — the user requires these)

1. **ONE instruction per message.** Written as complete literal steps. No shorthand like "(q)", no guessed button names, no assumed file names.
2. **Fresh bytes before any edit.** Never edit from memory; have the user run a read command and paste output first.
3. The user is NOT a programmer. Every instruction must be executable by a non-programmer, one step at a time, with an explicit report-back request.
4. **Arg-count checks** on every function dispatch/signature change.
5. **save.bat commit after every verified test pass.** Never leave the tree uncommitted across session boundaries.
6. The user's words are the spec-of-record. If you don't know something about the app, ASK — do not guess.

## 6. Status: what is verified vs. pending

Verified by history (restored in `15903c3`) but **NOT yet re-verified live** — this is your first job:
- Two-password encode/decode round-trip.
- One-password mode (Pass 2 empty → notification "Pass 2 empty - message 2 will be protected by Pass 1." → Pass 1 opens both layers).
- Open mode (no passwords → notification "No passwords - message 2 will be stored unencrypted." → both layers plaintext; `bool(m2)` dispatch).
- Wrong Pass 2 → exactly "Incorrect password."
- Decode always lands on Layer 1.
- Post-save layer retention (`_on_encode_success` logic).
- Cancel reverts to prior state.
- Compose-from-blobs edit path (msg1-only edit preserves layer-2 ciphertext).

## 7. Known open anomalies (undiagnosed)

(a) The "No passwords - message 2 will be stored unencrypted." notification never appeared in one run — status stayed "Ready to encode".
(b) Blank-panel click anomaly: clicking Pass 1 once showed an empty panel before re-decode in one Test-B run.

## 8. Backlog (discussed, NOT authorised — do not implement without explicit permission)

- C-O: open-mode layer-2 activation design.
- Engine hygiene: duplicate STEALTH/LEGACY header definitions (~line 246 of steganography_utils.py); duplicate decode chain in decode_image.
- Dead code cleanup: `self.state` and `self.ui_state` dicts in Stegano.py `__init__` (harmless, never read); leftover `stegano_repair.py` script.
- UX audit: Pass-2 click semantics; Edit icon redundancy.
- P3b; GCM mode deferred (decision D3=A).

## 9. Concepts logged, explicitly NOT authorised

- Carrier-replacement LSB sanitisation ("image hospital"): decision 1 approved in principle only (original file untouched, strip into working copy); fill pattern undecided (zeros vs random — random recommended). NOT authorised for implementation.
- Message-first compose flow (build messages/passwords before selecting an image). NOT authorised.
- Wipe-image utility: explicitly DECLINED ("not now or in the future").

## 10. History you must not repeat

- A rogue external edit session restructured Stegano.py (Config class, dead dicts, stolen help_tooltip, phantom _setup_* calls, deleted layout lines). Recovery by wound-by-wound patching took a full evening and failed; the fix that worked was: graft known-good `_init_ui` from git HEAD into the fix-rich backup, then rebuild. LESSON: after 2 structural crashes, diff against the last known-good version and restore — never trickle-repair.
- Aider (model glm-4.5-flash) loops on SEARCH/REPLACE edits and hallucinates. Preferred edit vehicle: deterministic assert-guarded PowerShell/Python scripts, run by the user, that verify anchors before patching.
- `diff>` is Aider's NORMAL prompt, not a special state. At "Add tokens of command output" prompts, press N.
- The previous AI lost the user's trust by guessing UI details (invented an "Encode" button), giving wrong launcher instructions (Save.bat vs Stegano.bat), and issuing shorthand instructions. The user explicitly ended the collaboration over this. Accuracy and literalism are the price of admission.

## 11. Environment & runbook

- Location: `C:\Dev\Stegano` on the user's Windows machine. Python + PyQt + Aider are installed and working (verified: `import Stegano; import steganography_utils; import workers` → OK on 04/11/2026).
- Exact dependency versions were never pinned. FIRST ACTION on your side: have the user run `pip list` and record PyQt version, cryptography version, Pillow version, and Python version in this document. Do not assume.
- To launch the app for testing: open PowerShell → `cd C:\Dev\Stegano` → `python Stegano.py`. The console window stays open and silent; that is normal.
- To launch the development workflow: the user runs `Stegano.bat` (Aider with both main files added). `Save.bat` = git commit, run only after a verified test pass.
- Test images live in `C:\Dev\Stegano\Images\` with virgin carriers in `Images\Virgin Images\`. The user has a limited stock of virgin images — reuse encoded ones only when valid, and note that an image's unused LSB capacity can be re-encoded but a saturated one cannot.

## 12. Concrete test scripts for the pending re-verification

Each test below is ONE user instruction. Record results, then run `Save.bat` only if all passed.

- **T1 two-password round-trip**: type Msg1=`Alpha-One`, Pass1=`KeyOne`, Msg2=`Bravo-Two`, Pass2=`KeyTwo`; save as `T1_dual.png`; reload it entering both passwords. Expect: display lands on Layer 1 showing exactly `Alpha-One`; Layer 2 viewable showing exactly `Bravo-Two`.
- **T2 one-password**: Msg1+Msg2 set, Pass1=`KeyOne`, Pass2 EMPTY. Expect notification "Pass 2 empty - message 2 will be protected by Pass 1."; save; reload with only Pass1 → both layers open.
- **T3 open mode**: both messages set, BOTH passwords empty. Expect notification "No passwords - message 2 will be stored unencrypted."; save; reload with no passwords → both layers plaintext.
- **T4 wrong Pass 2**: reload T1_dual.png with Pass1=`KeyOne`, Pass2=`WrongKey`. Expect exactly "Incorrect password." (not a crash, not a silent L1 return).
- **T5 decode lands on Layer 1**: in T1's reload, even if layer 2 is what decrypts first, the panel must show Layer 1.
- **T6 retention**: after saving an encoded image, message/password fields must keep their contents (check `_on_encode_success` behavior).
- **T7 cancel revert**: start an edit/cancel action → UI returns to prior state, no half-applied changes.
- **T8 compose-from-blobs**: load a dual image, edit ONLY message 1, re-save → layer 2 must still decode with its ORIGINAL password (ciphertext preserved verbatim via `encode_dual_image_from_blobs`).

## 13. Editing discipline (how to change code safely)

1. Never edit from memory. Have the user paste the exact current bytes of the target region first (e.g. via a read command you provide).
2. Write changes as a self-contained Python script saved to the project folder (e.g. `_patch_x.py`) that: (a) asserts the expected anchor text exists, (b) aborts with a clear message if not, (c) applies the replacement, (d) prints a census of what changed.
3. The user runs the script, pastes the output; you verify before any app relaunch.
4. After every verified pass: user runs `Save.bat` so the tree is committed.
5. Do NOT use Aider's SEARCH/REPLACE for structural changes — its model loops. Scripts only.
