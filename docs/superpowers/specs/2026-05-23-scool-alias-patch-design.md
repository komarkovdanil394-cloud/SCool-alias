# SCool Alias Patch Design

## Goal

Release a Flet/Python patch for SCool Alias that improves school content, round correction, mobile usability, swipe reliability, and battery use.

## Scope

- Rename visible app branding from `Scool Alias` to `SCool Alias`.
- Expand the Russian school-program dictionary with more subjects and words per difficulty.
- Keep each round limited to the selected subject and difficulty.
- Add a round duration setting independent from difficulty.
- Track every shown word during the round.
- Show a final review list where each word can be marked with compact reaction icons:
  - thumbs up means correct and uses the theme `ok` color when selected.
  - neutral means ignored and uses a muted warm/neutral color when selected.
  - thumbs down means skipped and uses the theme `bad` color when selected.
- Treat the last unanswered word as ignored by default when the timer ends.
- Make settings denser so common phone screens need less scrolling.
- Make the default performance profile lighter and reduce decorative background updates.
- Add more design themes while keeping the color choices tied to the existing theme tokens.

## Architecture

Word history belongs to `RoundState` so game rules and UI can share the same source of truth. `GameSession.next_word()` records a pending word when it is shown, and `GameSession.apply_answer()` updates the current pending word when a swipe or button answer happens.

Final review recalculates score from the reviewed word statuses instead of trusting the original swipe count. Pending and ignored words do not affect score. Correct words use the same multiplier rules as live play, and skipped words apply the configured penalty.

The UI keeps the review compact: rows contain the word and three icon buttons. Selected icons receive a filled colored background; unselected icons are transparent and low-emphasis.

## Testing

Core tests cover word history, ignored last words, and score recalculation. UI structure tests cover the new branding and the existence of review controls. Existing custom-word and swipe tests must continue to pass.
