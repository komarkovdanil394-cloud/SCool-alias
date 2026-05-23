# SCool Alias Patch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the approved Flet/Python patch for SCool Alias with round review, school dictionary expansion, settings improvements, swipe fixes, and battery optimizations.

**Architecture:** Add reviewed-word state to the core session model and let final UI recalculate results from that state. Keep Flet UI changes scoped to `main.py` and core behavior in `core/`.

**Tech Stack:** Python, Flet, unittest, existing project modules.

---

### Task 1: Round Review Model

**Files:**
- Modify: `core/models.py`
- Modify: `core/session.py`
- Modify: `core/engine.py`
- Test: `tests/test_round_review.py`

- [ ] Add `ReviewedWord` data and status constants.
- [ ] Record each shown word as pending.
- [ ] Update pending word status on answer.
- [ ] Recalculate score from reviewed words.

### Task 2: Final Review UI

**Files:**
- Modify: `main.py`
- Test: `tests/test_main_ui_structure.py`

- [ ] Store reviewed words in `last_round_result`.
- [ ] Add compact reaction buttons to the final screen.
- [ ] Recalculate the final result when a reaction is changed.

### Task 3: Settings, Branding, And Content

**Files:**
- Modify: `main.py`
- Modify: `datawords.py`
- Modify: `build_apk.ps1`
- Test: `tests/test_main_ui_structure.py`

- [ ] Rename app branding to `SCool Alias`.
- [ ] Add round duration setting.
- [ ] Expand school dictionary and add design themes.
- [ ] Densify settings layout.

### Task 4: Swipe And Battery Pass

**Files:**
- Modify: `ui/swipe_handlers.py`
- Modify: `main.py`
- Test: `tests/test_swipe_handlers.py`

- [ ] Make swipe commits favor velocity direction only for meaningful drags.
- [ ] Reduce default background animation and update frequency.
- [ ] Keep existing swipe tests passing.

### Verification

- [ ] Run `python -m unittest discover -s tests`.
- [ ] Run a Python compile check for edited modules.
- [ ] Build APK if the local Flet Android toolchain is available.
