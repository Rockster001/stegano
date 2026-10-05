# STEGANO — PHASE 2 DESIGN DECISIONS
# A record of ratified design changes from the design session (date: 02/10/2026).
# This document states WHAT must be achieved and WHY — not how the current code
# is structured. The codebase may have evolved since these decisions were made;
# locate the relevant mechanisms by behaviour, not by the names in this document.
# All items are DECIDED, not proposals. Part 5 lists decisions that must not be
# quietly reversed.

## PART 1 — RECENTLY COMPLETED WORK (for orientation; verify against current code)

1.1 Error visibility: error-type status messages now announce themselves —
    one audible alert plus a brief, bright/dim pulsing of the status text
    (brightness-based so it works for colourblind users), settling briefly
    before returning to normal. Ordinary (non-error) status messages remain
    quiet and static. New error messages should automatically inherit this.

1.2 Duplicate audible-alert calls, placed alongside error-status calls in
    individual handlers, were removed — the central status-display routine
    now owns the sound, so those were causing double-alerts.

1.3 Dead-code cleanup: a large block of duplicated definitions (password
    helpers, a strength meter, and a passwords dialog that were shadowed by
    later imports) was removed. The canonical versions now live in the
    dedicated password-utility module. A missing widget import in that
    module was fixed so its dialog's confirmation and information pop-ups work.

1.4 Consequence: any line-number references in older notes are unreliable.
    Locate code by function and behaviour.

## PART 2 — SETTINGS DIALOG (new feature)

2.1 Add a Settings dialog, styled consistently with the application's
    existing appearance. Reachable from the main window (propose placement
    to the user after inspecting the current layout — do not assume a spot).
    Persisted using the application's existing settings storage. All changes
    take effect immediately; the program must never require a restart.

2.2 The four settings, with ratified behaviour:

    S1 "Warn when decoding a legacy message" — DEFAULT ON.
        When a hidden message is successfully decoded using the older,
        weaker legacy encryption method, display a small, persistent,
        non-blocking badge while that message is shown — informational only:
        it must never block, interrupt, or require dismissal. The purpose is
        honesty about data-protection level, not restriction.
        Implementation note: the decode process must be able to report WHICH
        method succeeded (modern vs legacy). If it currently cannot, extend
        it without breaking any existing caller.
        IMPORTANT: the ability to decode legacy messages is unconditional
        and must never be toggleable (see Part 5).

    S2 "Keep passwords after saving" — DEFAULT ON.
        ON: after a successful save, the password fields keep their contents,
        so a user iterating on a message does not retype passwords. Fields
        clear when a DIFFERENT image is loaded (a genuinely new context).
        OFF: the previous behaviour — both password fields cleared after
        every successful save.

    S3 "Error sound" — DEFAULT ON. Enables/disables the audible error alert.

    S4 "Error flash" — DEFAULT ON. Enables/disables the visual pulse.

2.3 Alert escalation (the combined behaviour of S3 and S4):
    - Both ON: pulse + sound (current behaviour).
    - Either OFF: the remaining alert carries the message alone.
    - BOTH OFF — the "Highlight Bar": error text is displayed STATICALLY and
      PERSISTENTLY as inverted, high-contrast text (a bright background strip
      with contrasting font — like highlighted text in a document). No motion,
      no sound. This is the designed fallback for users who disable both
      sensory alerts: salience through DURATION and inversion instead of
      motion and sound. Exact colours to be chosen with the user at build time.
      The highlight clears when the user performs their next meaningful action
      (decode, save, load, password entry) or when a new status message
      replaces it — it must never linger into a genuinely new task.

## PART 3 — SAVED-PASSWORDS LIST REDESIGN

3.1 At rest, every saved password displays as a uniform row of mask
    characters (e.g. eight bullets), regardless of its true length — no
    partial characters visible by default.

3.2 The list is ordered most-recent-first. This ordering is SILENT: no dates,
    no timestamps are ever displayed. (Rationale: the program is offline-first
    and must be fully self-explanatory to a user returning after months;
    a date without context is meaningless to such a user.)

3.3 Each row gains a graduated reveal control (an "eye" icon), operating
    independently per row:
      Click 1 → partial reveal (first four + last four characters, e.g.
                "pass••••word"; passwords of eight characters or fewer
                reveal fully at this stage).
      Click 2 → full plaintext reveal.
      Click 3 → re-mask to the uniform bullet row.
    The control needs a tooltip teaching the three steps.
    Double-click on a row KEEPS ITS CURRENT MEANING (select and use the
    password in the relevant password field). Revealing belongs exclusively
    to the eye control — do not overload the double-click gesture.

3.4 Design rationale (for context): the mask-at-rest protects against
    observation; the graduated, deliberate clicks make every level of reveal
    a conscious act; the first-4+last-4 stage exists because the user's real
    problem is distinguishing password VARIANTS that share opening
    characters. Hover-reveal was considered and REJECTED (hover is
    accidental, not deliberate — industry password managers use deliberate
    reveal controls for the same reason).

## PART 4 — ERROR EXPLANATIONS (to be built LAST)

4.1 Every error message gains a pre-written companion explanation, shown as
    a tooltip when the user hovers the error text. Content pattern:
    what happened / why it happened / what to do about it — plain English
    throughout.

4.2 Two hard rules:
    - Explanations are AUTHORED, static data paired with each error at the
      moment the error text is written. Nothing is procedurally generated at
      runtime. The complete set of error sites must be enumerated, and the
      USER must write/approve the wording for each before implementation.
    - Tooltips EXPLAIN only. They never contain actions, buttons, or links.

## PART 5 — DECISIONS THAT MUST NOT BE REVERSED (the reasoning is binding)

- Legacy decoding is UNCONDITIONAL. There is deliberately no setting to
  disable or restrict it. The user regards multi-format detection and
  decoding as a core strength: the program recognises and can decode every
  format it has ever produced. (Unencrypted/plaintext hidden messages
  already display immediately on load — existing behaviour, keep.)
- Encryption strength is NOT a user setting. The program always uses the
  strongest method by default. A future phase may add OPTIONAL cipher
  profiles (including the legacy method, for decoy/test scenarios) — that
  requires designing how an image records which cipher it used, and is
  explicitly out of scope here.
- No alert may depend on colour alone (colourblind users). Alerts must be
  carried by brightness contrast, motion, sound, and/or duration.
- Design principle: this is an OFFLINE-FIRST, casual-use, owner's desktop
  tool. No network access, no accounts. Every feature must work identically
  for a user who opens the program twice a year; nothing may assume frequent
  use, memory of past sessions, or connectivity.
- Passwords-after-save defaults to KEEPING them: the user's position is that
  saving a work-in-progress is a normal act, not a security event.

## PART 6 — OUT OF SCOPE (known issues deliberately NOT addressed in this phase)

- User-selectable cipher profiles / decoy encoding (future phase; needs a
  file-format mechanism for tagging which cipher was used).
- Password replacement: currently, entering a new password after a successful
  decode triggers a fresh decode attempt with the new password, which fails
  by design and destroys the decoded message. The desired future behaviour is
  "apply the new password on save without attempting to decode."
- The layer-switching behaviour triggered by focusing the second password
  field can silently change which message slot the user is editing — a known
  usability fault, logged, not fixed here.
- Upgrading saved-password storage to stronger, OS-backed protection, and
  adding tamper-evidence to hidden messages, are logged future upgrades.
- The password-strength indicator currently reacts to only the first
  password field — pre-existing gap, logged.
- Output formats remain lossless-only. Do not add lossy formats.