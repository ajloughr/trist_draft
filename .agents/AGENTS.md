# Workspace Behavioral & Workflow Rules

## Player Selection Rules
- **Tabbed Interface**: The Player Selection card in UFA and Rookie drafts uses Bootstrap nav tabs (`#tab_search_db` and `#tab_manual_entry`) to separate database search from manual entry.
- **Search Direct Confirmation**: Selecting a player from the search database results table (`SELECT` button) directly triggers the modal confirmation (`#select_player_confirmation_modal`). It skips manual entry.
- **Manual Player Entry**: To nominate an unlisted player, users switch to the "Manual Entry" tab (`#tab_manual_entry`), fill in player details, and click Submit (`#submit_selected_player`). Form inputs align flush at the top of the tab container.
- **Search Results & Initial Load**: `#search_results_table_div` displays `"Enter search criteria above..."` on initial page load when search inputs are empty, and `"No Players found..."` when a query yields no results.
- **Position Badge Color System**: Position badges across Search Results, Now Auctioning, and Rosters use uniform colors: QB (`bg-primary`), RB (`bg-success`), WR (`bg-info text-dark`), TE (`bg-warning text-dark`), K (`bg-secondary`), DEF (`bg-dark`).

## Draft Admin Panel Rules
- **Dedicated Admin Route**: Draft administration is managed at `/draft-admin` (accessible to staff users).
- **Hidden Legacy Controls**: The legacy inline admin card on `/auction` is hidden (`#old_admin_panel_container`).
- **Clean Admin Navbar**: User-level navbar toggles (Help Mode, Bathroom Mode, Draft History) are hidden when on `/draft-admin`.

## Auction Table UI & Card Display Rules
- **Bootstrap `.d-flex` Specificity**: Bootstrap's `.d-flex` class applies `display: flex !important;`. To hide elements with `.d-flex` (e.g. `#current_player_card_container`), toggle `.d-none` vs `.d-flex` classes rather than setting inline `style="display: none;"`.
- **Current & Auction Status Card Visibility**: `#current_player_card_container` and `#auction_status_card_container` are hidden during the Rookie draft phase. In RFA and UFA draft phases, both cards remain visible even when no player is currently up for auction (displaying fallback 'None'/'-' text).
- **Bid Controls Disabled State**: `isPlayerUpForAuction` logic evaluates whether `player_for_auction_name` is present and not `"None"`. Bid inputs (`#id_new_bid`), Submit Bid buttons, Pass/Drop Out buttons, and Contract Years radio buttons must remain disabled/grayed out until a player is nominated for auction.
- **Last Player Sold Card**: `#last_player_sold_card_container` displays the most recently drafted player's name, position, winning team, price, and contract years.

## Team Roster Table Rules
- **Roster Section Structure**: `#roster_section_container` contains tabbed team rosters (`#roster_team_tabs` and `#pane_roster_<draft_order>`) in standard numerical draft order. The current user's team retains a star badge. Active tabs use solid dark navy styling (`#1e293b`).
- **Roster Section Tables**: Each team pane contains two tables: `Current Roster` (`#roster_table_<draft_order>`) and `Remaining RFAs` (`#rfa_table_<draft_order>`) backed by `user.get_current_rfa_players` and updated live over WebSockets (`update_team_rfa_roster_table`).
- **Dynamic Drafted Player Expiration & Salary**: When a player is drafted (`save_drafted_player`), their `salary` and calculated `final_year` (`datetime.now().year + winning_years_drafted - 1`) are saved directly to `nfl_player` so that team rosters update dynamically over WebSockets (`update_team_rosters`).

## Winner Celebration Modal & Confetti Rules
- **Celebration Trigger**: When a new player is drafted, `#winner_celebration_modal` displays player details and triggers 3 confetti bursts (`triggerThreeConfettiBursts()`).
- **DOM Stacking**: In JavaScript, invoke `$("#winner_celebration_modal").appendTo("body")` before calling `modal.show()` to ensure Bootstrap 5 renders the modal dialog card in front of the backdrop.
- **Undo / Deletion Protection**: The celebration modal only fires if `current_pk > window.last_seen_drafted_pk`. It must NOT trigger on admin undo/delete actions or initial page reloads.

## WebSocket & E2E Testing Rules
- **WebSocket Exception Handling**: Always use `.filter(...).first()` or `try / except` instead of `get_object_or_404()` inside Channels WebSocket consumers (`consumers.py`). `Http404` exceptions inside consumers crash the WebSocket worker thread instead of rendering an HTTP 404 response.
- **Winner Modal Dismissal in Tests**: E2E test helpers use `dismiss_winner_modal_if_present(page)` to click `#winner_celebration_close_btn` (`data-bs-dismiss="modal"`) and clear modal overlays before proceeding with test steps.
