# Data Dictionary & Process Flow

This document outlines the entire data model and the life cycle of actions during the draft. Mapping this out is an excellent idea—because the draft relies on a custom turn-based rotation and WebSockets, understanding exactly how fields mutate and how turns progress is essential for both refactoring and long-term maintenance. 

---

## 1. Data Dictionary (Models)

### `auction_manager` (Singleton)
This single database row (PK=1) tracks the global state of the draft at any given second.

* **Turn Tracking**
  * `active_bidder`: Integer. The `draft_order` of the team whose turn it currently is.
  * `initiated_auction`: Integer. The `draft_order` of the team that nominated the current player (Note: For RFAs, this is the original owner).
  * `team_with_highest_bid`: Integer. The `draft_order` of the team currently winning the auction.
* **Auction Details**
  * `auction_type`: String (`'rookie'`, `'rfa'`, `'ufa'`).
  * `auction_state`: String. Critical enum-like field controlling the frontend UI modes:
    * `'bidding'`: Active sequential bidding phase.
    * `'rfa_owner_match_request_1'`: RFA phase paused; waiting for original owner's first match decision.
    * `'rfa_bid_winner_offer_raise'`: RFA phase paused; winning bidder is offered a single chance to raise.
    * `'rfa_owner_match_request_2'`: RFA phase paused; waiting for original owner's final match decision.
    * `'ufa_confirmation_request'` / `'ufa_auction_end'`: Post-bidding phase before player is finalized.
  * `highest_bid`: Integer. The current winning dollar amount.
  * `highest_contract_years`: Integer. The current winning contract length.
  * `initial_bid` / `initial_bid_years`: Integers. The opening bid amounts, used to detect uncontested RFA scenarios.
* **Player Details**
  * `player_for_auction_name`, `_team`, `_position`, `_bye`: Details of the player currently on the block.
* **Legacy/Other**
  * `bid_timer`, `bid_timer_active`: Legacy fields (unused/deprecated).
  * `rookie_draft_order` / `rookie_draft_current_position`: Array/Int used exclusively for the fixed Rookie draft progression.

### `auction_user` (Team State)
Represents a team in the league. There is one row per user.

* **Identity & Budget**
  * `team_name`: String.
  * `user`: OneToOne Auth User link.
  * `draft_order`: Integer. The fundamental ID used for sequencing turns.
  * `budget_remaining`: Integer.
  * `current_roster_size`: Integer.
* **Current Player Auction State**
  * `still_in_auction`: Boolean. `True` if actively participating in the *current* player's auction. Becomes `False` when they explicitly Drop Out.
  * `pass_available`: Boolean. Starts `True`. Becomes `False` when they use their one pass.
  * `current_bid` / `contract_years_bid`: Integers. The team's most recent submitted bid values.
* **Global Draft State**
  * `dropped_out_of_selection`: Boolean. Becomes `True` when the user permanently drops out of nominating UFA players.
  * `bathroom_mode_enabled`: Boolean. If `True`, the turn-rotation logic skips them automatically.
  * `dropped_out_of_bid_early`: Boolean. Flag to catch edge cases where a user wants out immediately before their turn.
* **RFA Specifics**
  * `initial_rfa_list` / `current_rfa_list`: Array of Integers (Player IDs).
  * `rfas_remaining`: Integer count.
* **Legacy/Conflicting Fields**
  * `initiated_auction`: Boolean. (Note: `auction_manager` tracks this more effectively via integer draft order).

---

## 2. High-Level Process Flows

The backend acts as a giant event loop managed by `consumers.py`. 

### A. Submitting a New Bid (`submit_new_bid`)
1. **Trigger:** Client sends `{"new_bid": ...}` via WebSocket.
2. **Validation:** System checks that `new_bid > highest_bid` and `new_bid_contract_years >= highest_contract_years`. *(Note: RFA year-locking is currently not strictly enforced here).*
3. **State Update:** Updates `auction_user`'s current bid. Updates `auction_manager`'s `highest_bid`, `highest_contract_years`, and sets `team_with_highest_bid = user.draft_order`.
4. **Turn Rotation:** Calls `get_next_bidder()` to find the next valid team.
5. **Broadcast:** Sends the new state to all clients via `update_auction_table('all')`.

### B. Passing (`pass_user`)
1. **Trigger:** Client sends `{"pass": ...}` via WebSocket.
2. **Validation:** Checks if enough teams remain to allow a pass (disallowed if only 2 teams remain in UFA, or 3 teams in RFA including the nominator).
3. **State Update:** Sets user's `pass_available = False`. 
   * **Crucial Rule:** It keeps `still_in_auction = True`. This is how the "loop back" rule is enforced. Since they are still in the auction, the rotation will eventually land on them again.
4. **Turn Rotation & Broadcast:** Moves to the next bidder and updates clients.

### C. Dropping Out (`drop_out_user`)
1. **Trigger:** Client sends `{"drop_out": ...}` via WebSocket.
2. **State Update:** Sets user's `still_in_auction = False`.
3. **Auction End Check:** 
   * Counts active users: `num_auction_users_still_in`.
   * **RFA Scenario:** If count <= 2 (meaning only the nominator and the winning bidder are left), active bidding ends. If `highest_bid == 1` (no one bid), it fast-tracks to the owner keeping the player. Otherwise, it updates `auction_state` to `'rfa_owner_match_request_1'` to trigger the RFA sub-phase.
   * **UFA Scenario:** If count == 1, bidding ends. Updates `auction_state` to `'ufa_confirmation_request'`.
4. **Turn Rotation & Broadcast:** If the auction hasn't ended, finds the next bidder and updates clients.

### D. The RFA Match Flow (`receive_auction_results_response`)
1. **Match 1:** If the original owner matches (`rfa_owner_match_1_matched`), the state changes to `'rfa_bid_winner_offer_raise'`, and the UI prompts the winning bidder.
2. **The Raise:** The winning bidder submits a raise. The backend processes this like a normal bid, but immediately changes state to `'rfa_owner_match_request_2'`.
3. **Final Match:** The original owner matches or declines. The player is awarded to the appropriate team, the database is updated via `save_drafted_player`, and a new nomination phase starts.

---

## 3. The `get_next_bidder` Logic (The Engine)

The turn progression logic isn't wacky—it's actually quite clever! It creates an ordered loop of all draft slots starting from the *current* turn and wrapping back around to the beginning, checking conditions until it finds a valid user.

**The Loop Order:** `[active_bidder ... Last_Team] + [Team_1 ... active_bidder-1]`

**The Evaluation Checklist:**
For the system to stop on a user and declare it "their turn", the user must pass *all* these checks:
1. `still_in_auction == True`: They haven't explicitly dropped out.
2. `draft_order != active_bidder_draft_order`: It's not the person who literally just acted.
3. `bathroom_mode_enabled == False`: They aren't AFK.
4. `draft_order != team_with_highest_bid`: A user can't bid against themselves.
5. **RFA specific exception:** `not (auction_type == 'rfa' and draft_order == initiated_auction)`. The original owner is completely skipped during the sequential dollar-bidding phase, because they wait exclusively for the Match phases at the end.

*(If it checks every single user and finds no one eligible, it returns the current active bidder, usually triggering an auction end sequence).*

---

## 4. Key Workflows & Specialized Actions

Beyond basic bidding, the system handles several specialized flows driven by specific UI interactions.

### A. Selecting a Rookie
1. **Trigger:** A team selects a rookie during the Phase 1 Rookie Draft.
2. **WebSocket Input:** `{"submitted_player_name": ...}` -> `submit_auction_player()`.
3. **Execution:** Because the `auction_type` is `"rookie"`, it entirely bypasses the bidding phase. It immediately calls `save_drafted_player()` and assigns the player for a fixed $1/1-year contract.
4. **Rotation:** Calls `get_next_bidder(is_player_selection=True)` which reads from the fixed, snake-ordered array `rookie_draft_order` to find the next pick.

### B. Nominating an RFA & Setting Years
1. **Trigger:** A team clicks a player from their RFA list (populated via `get_rfas_for_user()`).
2. **WebSocket Input:** `{"submitted_player_name": ...}` -> `submit_auction_player()`.
3. **Setup:** Populates `auction_manager` with the player's details and sets the nominator as the `active_bidder` and `initiated_auction`.
4. **Initial Submission:** Immediately after, the frontend expects the nominator to submit the opening bid with their chosen contract length (1-3 years) via the standard `submit_new_bid()` flow. *(This is where the years are locked in for the rest of the RFA auction).*

### C. Nominating a UFA (Player Search)
1. **Search Trigger:** User types in the search bar.
2. **WebSocket Input:** `{"player_search_text": ...}` -> `get_player_search_results()`. 
3. **Search Execution:** Backend queries `nfl_player` using `icontains` filters for name, team, and position, returning a serialized list of up to 5 results to the frontend.
4. **Selection Trigger:** User clicks a search result.
5. **WebSocket Input:** `{"submitted_player_name": ...}` -> `submit_auction_player()`.
6. **Execution:** Identical to RFA setup, it makes the nominator the `active_bidder`, putting them on the clock to submit the mandatory opening bid.

### D. Dropping Out Early
1. **Trigger:** A user clicks "Drop Out" while it is *not* their turn.
2. **WebSocket Input:** `{"drop_out": ...}` -> `drop_out_user()`.
3. **Execution:** The backend detects it is not their turn. Instead of setting `still_in_auction = False`, it flags `dropped_out_of_bid_early = True`.
4. **Resolution:** At the end of every state broadcast (`update_auction_table`), a cleanup function `check_if_next_bidder_early_dropped_out()` fires. When the turn rotation finally lands on that user, the backend automatically issues a drop out on their behalf.

### E. Dropping out of Player Selection (UFA Phase)
1. **Trigger:** A team is done nominating UFAs and clicks "Drop out of selection" when it's their turn to nominate.
2. **WebSocket Input:** `{"drop_out_player_selection": ...}` -> `drop_out_of_or_pass_player_selection()`.
3. **Execution:** Sets `dropped_out_of_selection = True`. 
4. **Rotation:** Calls `get_next_bidder(is_player_selection=True)`. The rotation loop now ignores this user for all future UFA nominations, though they remain eligible to bid on players nominated by others.

### F. Bathroom Mode
1. **Trigger:** User toggles "Bathroom Mode" in the UI.
2. **WebSocket Input:** `{"bathroom_mode_toggled": ...}` -> `toggle_bathroom_mode()`.
3. **Execution:** Sets the `bathroom_mode_enabled` flag on their `auction_user`.
4. **Impact:** The `get_next_bidder()` engine unconditionally skips them until they toggle it back off. They are essentially a ghost in the rotation.

### G. Draft History Request
1. **Trigger:** User opens the Draft History modal.
2. **WebSocket Input:** `{"draft_history_request": ...}` -> `send_draft_history()`.
3. **Execution:** Backend queries `drafted_player.objects.all().order_by('pk')` (reversed) and broadcasts it back to the clients via a `draft_history_response` event.
