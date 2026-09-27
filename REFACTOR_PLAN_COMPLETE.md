# REFACTOR_PLAN.md — splitting Stegano.py into modules

Ground rules for EVERY step:
- One step = one Aider session: extract the listed code into the new module, AND update
  Stegano.py to import from that module, in the same session.
- Move only whole top-level classes and module-level functions. Methods of the
  SteganographyApp class always stay in Stegano.py.
- Stegano.py is always the program's entry point. Never rename it, never replace it.
- After every step: run the program, test the affected features, then save (save.bat).
- The program must still work after every step.

## Step 1 — audio_manager.py
Move: the AudioManager class.
Update Stegano.py to import AudioManager from audio_manager.

## Step 2 — password_utils.py
Move these module-level functions: estimate_password_strength, _password_strength_tier,
_has_common_word, _extract_alpha_runs, _has_pattern_weakness, _has_repeated_char_run,
_has_sequential_run, _has_keyboard_pattern.
Move these classes: PasswordStrengthMeter, SavedPasswordsDialog.
Update Stegano.py to import them.

## Step 3 — steganography_utils.py
Move these module-level functions: _encrypt_bytes_aes, _decrypt_bytes_aes, _encrypt_bytes,
estimate_encrypted_payload_len, check_image_for_message, decode_image, _embed_bits_and_save,
encode_image, encode_dual_image, _extract_raw_lsb_bytes, detect_message_format,
_extract_dual_layers, _try_decrypt_payload, decode_dual_image.
Update Stegano.py to import them.
(This is the heart of the program — if the step feels too big, split it in two:
encryption functions first, image encoding/decoding second.)

## Step 4 — ui_components.py
Move these classes: ToastNotification, LoadingSpinner, CustomHelpTooltip, ZoomImageViewer,
_SuppressStderr. Move the function _format_size and the function convert_links_to_html.
Update Stegano.py to import them.

## Step 5 — workers.py
Move these classes: EncodeWorker, DecodeWorker, ImageLoadWorker.
Update Stegano.py to import them.

## Step 6 — finish
Stegano.py now contains only: constants, the SteganographyApp class, and the main block —
importing everything else from the new modules. No new entry point is ever created.