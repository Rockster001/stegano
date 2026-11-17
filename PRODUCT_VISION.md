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
