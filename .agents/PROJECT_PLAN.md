# Project Plan: Refactoring and Testing League Draft Logic

## Phase 1: Discovery

- **Analyze Existing Models:** Review the `auction_user`, `auction_manager`, `nfl_player`, and `drafted_player` models to understand their current capabilities.
- **Map Current Flow vs. Required Flow:** Compare the fields in the database to the rules outlined in `skills/league_rules/SKILL.md` (e.g., phases like Rookie, RFA, and UFA; bid resolution; special RFA matching rules).
- **Identify Missing State Fields:** Determine which new fields need to be added to track complex states such as RFA owner match phases, nominator tracking, and the differentiation between users who "passed" versus those who explicitly "dropped out".

## Phase 2: Test Harness Setup

- **Dependencies:** Install and configure `pytest-django` and `factory_boy`.
- **Configuration:** Set up a `pytest.ini` file for the Django project to ensure proper environment loading for testing.
- **Factory Creation:** Create model factories for `auction_user`, `auction_manager`, `nfl_player`, and `drafted_player` to allow for rapid creation of test data.
- **Fixtures:** Develop standard fixtures (e.g., a full 10-team league setup, a mock draft state with various active/passed/dropped users) to easily test scenarios without repetitive setup code.

## Phase 3: Rule Alignment (Violations & Gaps)

Based on a preliminary review, here is where the current code likely violates or falls short of the `SKILL.md` rules:

1. **RFA Owner Match Logic:** The complex 3-step RFA resolution (First Match, Single Raise, Final Match) is not currently represented in the `auction_manager` model. It lacks the state fields required to pause bidding and handle these exclusive owner interactions.
2. **"Pass Once" Rule & Resolution Loop Back:** The `auction_user` model has `pass_available` and `dropped_out_of_bid_early`, but the system must specifically distinguish between a team that passed (who gets looped back in at the end if everyone else drops out) and a team that dropped out (who is removed completely).
3. **UFA Bidding Constraints:** The rule stating "increasing the number of years requires also increasing the dollar amount" needs explicit enforcement.
4. **RFA Locked Contract Length:** In RFA auctions, contract length is locked to the opening bid. The logic must reject any bid that attempts to alter the years during the RFA phase.
5. **Uncontested Nominations:** There must be logic to automatically award the player to the nominator at the opening bid if every other team drops out initially.
6. **Bathroom Mode/Skip Logic:** The turn progression system needs to accurately respect `bathroom_mode_enabled` and ensure those users are seamlessly skipped in all contexts.

## Phase 4: Front-End Testing (Next Step)

Given the complexity of the client-side logic and WebSockets (and the messy state of the current JavaScript), we need to establish a frontend testing harness before we rip out and refactor the backend. This will ensure we don't accidentally break the UI when we change `consumers.py`.

- **Choose a Testing Framework:** Introduce an End-to-End (E2E) testing framework like **Playwright** or **Cypress**. Since the app relies heavily on WebSockets and real-time updates across multiple screens, an E2E framework is the best way to test the "ugly" JavaScript in its natural environment without having to rewrite it first.
- **Setup E2E Environment:** Configure the testing framework to boot up the Django server, connect to the test database, and open multiple headless browser instances simultaneously to simulate different team owners.
- **Write Baseline UI Tests:** Write tests to verify that when User A bids, User B's screen (DOM) updates correctly with the new bid and timer.
- **Refactor JS (Optional/Iterative):** Once the E2E tests are green, begin extracting the inline, messy JavaScript out of the HTML templates and into modular, testable `.js` files if desired.

## Phase 5: Refactoring & Next Action Items

Based on the extensive testing completed today, the following specific action items have been scheduled for our next session:

1. **RFA "Pass then Bid" Logic Revision:** Currently, the system has a hacky edge case where if a user passes initially and later tries to jump back in with a bid, it breaks the RFA match flow. We need to revise `pass_user` and `submit_new_bid` to properly handle this edge case, likely by forcing an immediate UFA-style resolution for that turn before continuing RFA rules.
2. **Backend Validation Security:** Add explicit backend validation to `submit_new_bid` in `consumers.py` to ensure that a user actually has enough `budget_remaining` to make a bid, and that `contract_years` does not exceed the league maximum (currently lacking backend enforcement).
3. **Bathroom Mode Restrictions:** Add a safeguard in `toggle_bathroom_mode` to prevent the active initiator of an auction (the nominator or RFA owner) from toggling Bathroom Mode mid-auction. 
4. **Extract Business Logic (Service Layer):** `consumers.py` currently handles massive blocks of state-machine logic. Move the bidding mechanics, turn rotation logic (`get_next_bidder`), and auction resolution out of the WebSocket consumer and into a dedicated service layer (e.g., `services.py`). This ensures the domain logic is decoupled from the web layer and is highly testable.
5. **Integrate & Final QA:** Hook the updated, verified logic back into the Django views and WebSocket consumers, ensuring real-time state updates function flawlessly across the UFA, RFA, and Rookie flows we just verified.
