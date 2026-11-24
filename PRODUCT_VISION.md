# Stegano Product Vision

Owner-approved direction, recorded 15 November 2026. Read this before proposing
or implementing product changes. This document captures intent; it is not
permission to implement every idea listed here.

## Vision

Stegano is a focused, dependable, offline-first Windows desktop tool for hiding
and reading one or two independent messages in lossless images. It should remain
understandable to an owner who may return to it after months away: the current
task and layer are clear, actions have predictable results, and errors explain
what happened without putting the user's work at risk.

The goal is not to add features for their own sake or replace the existing
interface. Refine the app into a coherent, trustworthy version of what it
already is.

## Decisions to preserve

- The main application stays full-screen and fixed-size. This was chosen to
  prevent interface elements from appearing outside the visible window. Do not
  propose restoring resizing without a concrete reason and owner approval.
- Focusing or clicking Pass 1 / Pass 2 intentionally switches the active layer,
  like selecting a tab. Preserve that behavior. Improvements may make the active
  layer clearer, but must not silently change the interaction model.
- The saved-password list's partial masking is intentional, chosen after
  considering and rejecting alternatives. Do not replace it or add a new reveal
  scheme without the owner's direction.
- Keep the app offline-first and local. Do not add accounts, uploads, or network
  dependencies. Opening a message link may launch the user's browser.
- New password-protected messages use the strongest current format
  (AES-GCM); legacy decoding remains available. Do not add a setting that
  disables legacy decoding or weakens the default encryption.
- Keep output lossless and preserve the source image by saving encoded output
  separately.

## Desired experience

- Image selection, preview, viewing, and replacement have clear, distinct
  outcomes. Clicking outside the image viewer dismisses it as though its close
  control was used; an in-app click used to dismiss it must not also activate
  the control underneath.
- The same click-away rule applies to the saved-password dialog: dismissing it
  must not select or use a password, or activate an underlying control.
- The message area makes it clear whether the user is viewing, composing, or
  editing, and what Save or Cancel will do.
- Password and layer actions preserve the user's message and make the result
  clear. In particular, verify the documented password-replacement workflow
  before changing it; agree on the intended behavior first.
- Security and format limitations are explained accurately and plainly.
- The interface remains useful without requiring frequent use or memorization
  of hidden rules.

## Owner-requested worklist

These are accepted items to investigate or address; they are not yet
implemented.

1. Investigate startup sequencing: background music can be heard for several
   seconds before the main window appears. Identify why this happens and agree
   on the desired startup behavior before changing it.
2. Revisit how Load and Save locations should be remembered. Separate
   preferences may be appropriate, but simple per-operation "most recently
   used folder" behavior may not be sufficient. Discuss the desired behavior
   and first-run defaults before implementation; no location-memory behavior
   has been approved yet.
3. Consider replacing the current UI gadgets with custom-designed graphics.
   The scope and design are open for future discussion; do not treat this as
   approval to begin a visual redesign.
4. **Implement the Scratchpad.** It is a non-modal floating plain-text window,
   independent of the selected image, message, or layer. Open it from a
   title-bar control or Ctrl+Shift+N. Provide Clear, Restore, and Save controls.
   Clear empties the current text but leaves the saved snapshot available to
   Restore; Restore asks before replacing nonempty current text; Save writes
   the current snapshot. Load an existing snapshot automatically at startup.
   On normal application close, silently save nonempty text and delete the
   snapshot if the pad is empty.

   Keep one local encrypted text snapshot in a nondescript file. The key is
   deterministically derived from the timestamp of a persistent per-user copy
   of the bundled background image and embedded in that image using Stegano's
   existing image encoding. This is intended as local concealment and
   protection against casual inspection, not as protection against a
   determined examiner. If the key-bearing image or its timestamp is lost,
   the prior snapshot may be unrecoverable; this limited loss is accepted.
5. Discuss whether and how to provide a Settings function. `PHASE2_DESIGN.md`
   already records a deferred Settings dialog with four proposed settings.
   Revisit its priority and scope, including whether Scratchpad persistence
   belongs there. This is a discussion item, not approval to implement it.
6. Keep local random-passphrase generation as a future option for the password
   workflow. Any generator must be independent of saved-password storage.
   Decide its format, UI, and retention behavior before implementation. The
   current strength-scoring method remains in place; the proposed `zxcvbn`
   library trial was declined, and no estimator library has been adopted.
7. Review the intended scope and presentation of the Undo/Redo controls. They
   currently apply to message-text editing only. Decide whether that scope is
   appropriate and make their purpose clear as part of the UI review; do not
   assume they should undo broader application actions.

## Exploratory idea

The owner is considering whether future versions could embed and recover image,
audio, or video files in addition to text. This is not yet a scoped or approved
feature. The owner currently leans toward built-in media handling rather than
relying on external applications, but has not made a final decision. Explore
capacity, format-support, and workflow tradeoffs before implementation. File
recovery does not inherently require built-in playback: Stegano could save the
recovered file and let the operating system open it. Any design must preserve
the independence of message layers and existing text compatibility.

Parked subtopic for future discussion: whether a much larger media payload
(the example raised was a 250 MB audio file associated with a 10 MB image)
could be carried alongside an image in a way that some software still displays
as an image. This is distinct from pixel embedding, is not supported by the
current app, and cannot be assumed to work with all image software or remain
inconspicuous. The owner asked to set the idea aside for now. Revisit only when
requested; do not treat it as an approved feature or implementation task.

## How to evolve the app

1. Treat deliberate owner choices as product requirements, not defects.
2. Separate confirmed bugs from usability suggestions and future features.
3. Before changing behavior, state the intended outcome and get owner approval
   where the design is not already decided.
4. Make small, focused changes with tests for the behavior they alter; manually
   validate important GUI workflows on Windows when practical.
5. Report what was tested. Passing automated tests is not the same as a full
   manual or packaged-app validation.

The settings, legacy-warning, error-explanation, and other items recorded in
`PHASE2_DESIGN.md` remain subject to that design document and owner prioritization.
They are not automatically in scope for every future task.
