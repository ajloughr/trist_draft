# Workspace Behavioral & Workflow Rules

## Player Selection Rules
- **Tabbed Interface**: The Player Selection card in UFA and Rookie drafts uses Bootstrap nav tabs (`#tab_search_db` and `#tab_manual_entry`) to separate database search from manual entry.
- **Search Direct Confirmation**: Selecting a player from the search database results table (`+` button) directly triggers the modal confirmation (`#select_player_confirmation_modal`). It skips manual entry.
- **Manual Player Entry**: To nominate an unlisted player, users switch to the "Manual Entry" tab (`#tab_manual_entry`), fill in player details, and click Submit (`#submit_selected_player`).

## Draft Admin Panel Rules
- **Dedicated Admin Route**: Draft administration is managed at `/draft-admin` (accessible to staff users).
- **Hidden Legacy Controls**: The legacy inline admin card on `/auction` is hidden (`#old_admin_panel_container`).
- **Clean Admin Navbar**: User-level navbar toggles (Help Mode, Bathroom Mode, Draft History) are hidden when on `/draft-admin`.

## Auction Table UI & Card Display Rules
- **Bootstrap `.d-flex` Specificity**: Bootstrap's `.d-flex` class applies `display: flex !important;`. To hide elements with `.d-flex` (e.g. `#current_player_card_container`), toggle `.d-none` vs `.d-flex` classes rather than setting inline `style="display: none;"`.
- **Current Player Card Visibility**: `#current_player_card_container` is hidden during Rookie draft phase and whenever no player is up for auction.
- **Last Player Sold Card**: `#last_player_sold_card_container` displays the most recently drafted player's name, position, winning team, price, and contract years.

## Winner Celebration Modal & Confetti Rules
- **Celebration Trigger**: When a new player is drafted, `#winner_celebration_modal` displays player details and triggers 3 confetti bursts (`triggerThreeConfettiBursts()`).
- **DOM Stacking**: In JavaScript, invoke `$("#winner_celebration_modal").appendTo("body")` before calling `modal.show()` to ensure Bootstrap 5 renders the modal dialog card in front of the backdrop.
- **Undo / Deletion Protection**: The celebration modal only fires if `current_pk > window.last_seen_drafted_pk`. It must NOT trigger on admin undo/delete actions or initial page reloads.
