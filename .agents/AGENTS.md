# TRIST Draft - Agent Handoff & Rules

Welcome to the TRIST Draft project! This is a real-time fantasy football auction draft application built using **Django** and **Django Channels (WebSockets)**.

---

## 📁 Key Files & Architecture

### Environment & Repository Structure (Git Worktree)
The project uses a **single Git repository** with **Git Worktrees** to separate the live production instance from active development/testing:
- **`trist_draft_dev/` (Development & Testing)**: Contains the `.git` repository root. Active feature branches (`ui-redesign-concept-b`, etc.) are checked out here. Mounted into `django-test` container (port 8002).
- **`trist_draft_prod/` (Production Worktree)**: Git Worktree linked to `master`. Mounted into `django` container (port 8000).
- **Updating Production**: In `trist_draft_dev`, merge your branch into `master` (`git checkout master && git merge <branch> && git push origin master`). `trist_draft_prod` automatically reflects the latest `master` commit.

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

---

## 🛠️ Current Project State & Roadmap

We have recently completed "Phase 1" critical refactoring, which included fixing a severe `User` object data leak in the WebSocket broadcasts and eliminating an O(N) database query avalanche related to roster size calculations.

If you are picking up work on infrastructure or refactoring, **please refer to [.agents/UPDATE_PLAN.md](file:///mnt/user/docker/trist_draft/.agents/UPDATE_PLAN.md)**. It contains a detailed breakdown of the remaining structural flaws (like sync consumer blocking and missing bid ledgers) and our prioritized roadmap for fixing them.

---

## Workspace Behavioral & Workflow Rules

### Player Selection Rules
- **Tabbed Interface**: The Player Selection card in UFA and Rookie drafts uses Bootstrap nav tabs (`#tab_search_db` and `#tab_manual_entry`) to separate database search from manual entry.
- **Search Direct Confirmation**: Selecting a player from the search database results table (`SELECT` button) directly triggers the modal confirmation (`#select_player_confirmation_modal`). It skips manual entry.
- **Manual Player Entry**: To nominate an unlisted player, users switch to the "Manual Entry" tab (`#tab_manual_entry`), fill in player details, and click Submit (`#submit_selected_player`). Form inputs align flush at the top of the tab container.
- **Search Results & Initial Load**: `#search_results_table_div` displays `"Enter search criteria above..."` on initial page load when search inputs are empty, and `"No Players found..."` when a query yields no results.
- **Position Badge Color System**: Position badges across Search Results, Now Auctioning, Rosters, and Draft History use uniform colors: QB (`bg-primary`), RB (`bg-success`), WR (`bg-info text-dark`), TE (`bg-warning text-dark`), K (`bg-secondary`), DEF (`bg-dark`).

### Draft Admin Panel Rules
- **Dedicated Admin Route**: Draft administration is managed at `/draft-admin` (accessible to staff users).
- **Hidden Legacy Controls**: The legacy inline admin card on `/auction` is hidden (`#old_admin_panel_container`).
- **Clean Admin Navbar**: User-level navbar toggles (Help Mode, Bathroom Mode, Draft History) are hidden when on `/draft-admin`.
- **NFL Player Team Modification**: Staff users can search NFL players by name on `/draft-admin`, view their assigned team, and modify their team assignment (including `Undrafted`) via modal dropdown (`#edit_player_team_modal`).
- **RFA Management**: User RFA lists (initial and current) can be edited on `/draft-admin` using comma-separated integer input fields (`#edit_rfas_<draft_order>`).
- **Rookie Draft Order Editing**: The rookie draft pick sequence can be modified directly on `/draft-admin`.

### Auction Table UI, Toast & Card Display Rules
- **Bootstrap `.d-flex` Specificity**: Bootstrap's `.d-flex` class applies `display: flex !important;`. To hide elements with `.d-flex` (e.g. `#current_player_card_container`), toggle `.d-none` vs `.d-flex` classes rather than setting inline `style="display: none;"`.
- **Current & Auction Status Card Visibility**: `#current_player_card_container` and `#auction_status_card_container` are hidden during the Rookie draft phase. In RFA and UFA draft phases, both cards remain visible even when no player is currently up for auction (displaying fallback 'None'/'-' text).
- **Bid Controls Disabled State**: `isPlayerUpForAuction` logic evaluates whether `player_for_auction_name` is present and not `"None"`. Bid inputs (`#id_new_bid`), Submit Bid buttons, Pass/Drop Out buttons, and Contract Years radio buttons must remain disabled/grayed out until a player is nominated for auction.
- **Last Player Sold Card**: `#last_player_sold_card_container` displays the most recently drafted player's name, position, winning team, price, and contract years.
- **Toast Styling & Dark Navy Headers**: All confirmation and notification toasts (`#rfa_owner_match_request_1_toast`, `#rfa_owner_match_request_2_toast`, `#rfa_bid_winner_offer_raise_toast`, `#no_bid_last_auction_user_toast`, `#ufa_end_confirm_toast`, `#ufa_end_waiting_toast`) feature a dark navy top header (`#1e293b`) with white text and FontAwesome icons.
- **Toast Lifecycle & Target Preservation**: Toast display functions must use `bootstrap.Toast.getOrCreateInstance(el)` and invoke `dispose_all_toasts(targetId)` with the active target toast ID so WebSocket table updates (`update_auction_table`) do not prematurely hide active confirmation toasts.
- **Type-Safe Ownership Checking**: Frontend toast checks must use `checkIsOwner(initiated_auction)` and `checkIsWinner(auction_winner)` in `auction_table.html` to safely compare team names and draft order integers without type coercion failures.

### Draft History & CSV Export Rules
- **Draft History Offcanvas Drawer**: `#drafted_list_offcanvas` slides up from the bottom (sized to `32vh`), featuring a sticky dark table header (`#0f172a`), formatted draft type badges (`ROOKIE`, `RFA`, `UFA`), position badges, and `$X` prices.
- **CSV Download Route**: Draft record CSV downloads are served at `/export-draft-csv/` and accessible via the Download CSV button in the Draft History offcanvas header.

### Team Roster Table Rules
- **Roster Section Structure**: `#roster_section_container` contains tabbed team rosters (`#roster_team_tabs` and `#pane_roster_<draft_order>`) in standard numerical draft order. The current user's team retains a star badge. Active tabs use solid dark navy styling (`#1e293b`).
- **Roster Section Tables**: Each team pane contains two tables: `Current Roster` (`#roster_table_<draft_order>`) and `Remaining RFAs` (`#rfa_table_<draft_order>`) backed by `user.get_current_rfa_players` and updated live over WebSockets (`update_team_rfa_roster_table`).
- **Dynamic Drafted Player Expiration & Salary**: When a player is drafted (`save_drafted_player`), their `salary` and calculated `final_year` (`datetime.now().year + winning_years_drafted - 1`) are saved directly to `nfl_player` so that team rosters update dynamically over WebSockets (`update_team_rosters`).

### Winner Celebration Modal & Confetti Rules
- **Celebration Trigger**: When a new player is drafted, `#winner_celebration_modal` displays player details and triggers 3 confetti bursts (`triggerThreeConfettiBursts()`).
- **DOM Stacking**: In JavaScript, invoke `$("#winner_celebration_modal").appendTo("body")` before calling `modal.show()` to ensure Bootstrap 5 renders the modal dialog card in front of the backdrop.
- **Undo / Deletion Protection**: The celebration modal only fires if `current_pk > window.last_seen_drafted_pk`. It must NOT trigger on admin undo/delete actions or initial page reloads.

### WebSocket, Testing & Agent Recording Rules
- **WebSocket Exception Handling**: Always use `.filter(...).first()` or `try / except` instead of `get_object_or_404()` inside Channels WebSocket consumers (`consumers.py`). `Http404` exceptions inside consumers crash the WebSocket worker thread instead of rendering an HTTP 404 response.
- **Winner Modal Dismissal in Tests**: E2E test helpers use `dismiss_winner_modal_if_present(page)` to click `#winner_celebration_close_btn` (`data-bs-dismiss="modal"`) and clear modal overlays before proceeding with test steps.
- **How to Run Tests (Mandatory Script)**:
  - **All Tests (Full Suite)**: Execute `./scripts/run_tests.sh` (resets test DB, runs backend unit tests, resets test DB, and runs E2E test suites). Logs are automatically saved to `scripts/logs/`.
  - **Backend Unit Tests Only**: Execute `./scripts/run_tests.sh backend` (resets DB and executes backend unit tests).
  - **E2E Playwright Tests Only**: Execute `./scripts/run_tests.sh e2e` (resets DB and executes end-to-end tests).
  - **Custom Test Args**: Execute `./scripts/run_tests.sh <pytest args...>` (resets DB and passes custom pytest arguments).
- **Test Execution & Re-Run Communication Rules**:
  - Before requesting or executing test runs, always clearly explain what failed previously and why.
  - When making code changes or fixing bugs, agents MUST record the root cause, what files were modified, and how the changes were empirically verified in both `walkthrough.md` and user summaries.
- **Top-Level Modal Placement**: Modals like `#select_player_confirmation_modal` and `#drop_out_of_selection_confirmation_modal` must be placed at top-level `body` in `auction_table.html` (not nested inside flex column containers like `auction_player_search.html`) so Bootstrap 5 modal backdrop rendering and dismissal function properly without intercepting pointer events.

---

### Interactive Onboarding Tour (Driver.js) Rules
- **Phase-Specific Tour Workflows**: `startOnboardingTour()` drives distinct step-by-step guides for Rookie, RFA, and UFA draft phases.
- **Action Button Neutering**: All interactive draft actions (`#submit_new_bid_button`, `#pass_button`, `#drop_out_button`, `#pass_player_selection`, `#drop_out_of_selection_confirm`, `#select_rfa_player`, `#select_player_confirmed`) are guarded with `if (window.is_tour_active) return;` so user clicks during tour steps do not broadcast WebSocket events or alter backend state.
- **Modal Display Safeguards**: Confirmation modals like `#drop_out_confirmation_modal` and `#select_player_confirmation_modal` include `show.bs.modal` guards checking `window.is_tour_active` to prevent dialog popups during tour steps.
- **Clean State Restoration**: `onDestroyed()` in the Driver.js configuration calls `update_auction_table(auction_table_data, auction_manager_data, user_data)` upon tour completion or dismissal to instantly reset all DOM element states, form inputs, and button flags directly to active WebSocket data.

---

## ⚠️ Important Rules & Skill References
1. **Never run docker commands without explicit user approval.**
2. **Always ask the user for permission before running git commit commands.**
3. When writing Playwright tests, note that Playwright's `.fill()` command does not trigger the necessary JavaScript `keyup` events for the player search bar. You must use `.press("Enter")` to simulate it.
4. If you need to verify rules about how the draft operates (RFA mechanics, passing rules, etc.), consult the [.agents/skills/league_rules/SKILL.md](file:///mnt/user/docker/trist_draft/.agents/skills/league_rules/SKILL.md) file.
5. **Do not create scripts to make file changes**: Rely strictly on the multi_replace_file_content and replace_file_content tools for making code edits. Do not write python, bash, or other scripts to perform file modifications unless dealing with hidden characters or complex line break issues that the replacement tools cannot handle.
