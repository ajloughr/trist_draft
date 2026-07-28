# TRIST Draft - Agent Handoff & Introduction

Welcome to the TRIST Draft project! This is a real-time fantasy football auction draft application built using **Django** and **Django Channels (WebSockets)**. 

This document serves as an introduction to the repository so you don't have to ask the user where things are located or how the system works.

## 📁 Key Files & Architecture

### Backend & Business Logic
- `trist_draft/apps/auction_table/consumers.py`: **The most important backend file.** This contains the Channels WebSocket consumer which handles almost all of the live auction logic. Functions like `update_auction_table`, `submit_new_bid`, `pass_user`, and `save_drafted_player` act as massive state machines here.
- `trist_draft/apps/auction_table/models.py`: Defines the primary database schema (`auction_user`, `auction_manager`, `drafted_player`, `nfl_player`). Note that models currently use python `snake_case` rather than Django's standard `PascalCase`.

### Frontend & UI
- `trist_draft/templates/auction_table/auction_table.html`: **The main frontend file.** This contains over a thousand lines of inline JavaScript and jQuery. It listens for WebSocket broadcasts and procedurally toggles UI visibility using `.show()` and `.hide()` based on the current draft phase (Rookie, RFA, UFA). 
- *Note:* Be careful when modifying UI templates. Partial components are injected into this main view, and using Django `{% extends %}` or full `{% block %}` wrappers inside those partials can break the DOM layout and visibility.

### E2E Testing Suite (Playwright)
- `trist_draft/apps/auction_table/tests/`: This directory contains our comprehensive Playwright end-to-end test suite (`test_e2e_rfa.py`, `test_e2e_ufa.py`, `test_e2e_rookie.py`, etc.).
- Testing commands usually look like this (but **ALWAYS ask the user for permission** before running docker commands):
  `bash scripts/test_setup.sh > /dev/null 2>&1 && bash scripts/reset_test_instance.sh > /dev/null 2>&1 && docker exec -i django-test pytest trist_draft/apps/auction_table/tests/test_e2e_ufa.py`

## 🛠️ Current Project State & Roadmap

We have recently completed "Phase 1" critical refactoring, which included fixing a severe `User` object data leak in the WebSocket broadcasts and eliminating an O(N) database query avalanche related to roster size calculations.

If you are picking up work on infrastructure or refactoring, **please refer to `.agents/UPDATE_PLAN.md`**. It contains a detailed breakdown of the remaining structural flaws (like sync consumer blocking and missing bid ledgers) and our prioritized roadmap for fixing them.

## ⚠️ Important Rules
1. **Never run docker commands without explicit user approval.**
2. When writing Playwright tests, note that Playwright's `.fill()` command does not trigger the necessary JavaScript `keyup` events for the player search bar. You must use `.press("Enter")` to simulate it.
3. If you need to verify rules about how the draft operates (RFA mechanics, passing rules, etc.), consult the `.agents/skills/league_rules/SKILL.md` file.
