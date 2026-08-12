# Refactoring Implementation Plan: Deep Infrastructure Dive

After a deeper audit of the backend schema, Channels architecture, and database interactions, I've identified several critical structural flaws. Below are the findings, each rated on a 1-5 scale for **Importance** (impact on system), **Complexity** (effort to fix), and **Risk** (chance of breaking existing features).

## 1. Critical Security & Performance Flaws

### Severe Data Leak over WebSockets
Currently, `serializers.serialize('json', User.objects.all())` broadcasts to all clients. This default serialization includes hashed passwords, `is_superuser` status, and emails.
- **Importance:** 5 (Critical security flaw)
- **Complexity:** 2 (Requires writing a custom serialization function)
- **Risk:** 2 (Low risk, easily verified)
- **Status:** Completed

### The O(N) Query Avalanche
`update_aution_user_current_roster_size()` fetches all users and runs a `nfl_player.objects.filter(...).count()` query inside a `for` loop, followed by a `.save()`. A single bid triggers roughly 12 `COUNT` queries and 12 `UPDATE` queries, choking the database.
- **Importance:** 5 (Will cause severe latency during live drafts)
- **Complexity:** 3 (Requires optimizing the query or moving the trigger point)
- **Risk:** 3 (Moderate risk of roster counts temporarily desyncing if handled incorrectly)
- **Status:** Completed

---

## 2. Database Schema & Model Redesign

### Lack of a Bid Ledger (Event Sourcing)
Bids are managed by mutating the `current_bid` field directly. There is no historical record or audit trail of the bids during an auction.
- **Importance:** 3 (Valuable for auditing, but current system functions without it)
- **Complexity:** 3 (Requires a new `Bid` model and updating consumer logic to write to it)
- **Risk:** 2 (Low risk, as it's an additive feature)

### Brittle Relationships & Normalization
In `drafted_player`, `team_drafted_by` is a simple `CharField`. If a team changes its name, references break. Additionally, `auction_manager` has redundant boolean fields (`auction_is_rookie`, etc.) alongside `auction_type`.
- **Importance:** 3 (Database hygiene)
- **Complexity:** 4 (Requires schema migrations and updating multiple query sites)
- **Risk:** 4 (Moderate-high risk of breaking existing queries that expect strings/booleans)

### Singleton Abuse & Naming Conventions
Models use python `snake_case` (e.g., `auction_manager`) instead of standard Django `PascalCase`. `auction_manager` implicitly assumes only one global lobby (`pk=1`).
- **Importance:** 2 (Code cleanliness and future-proofing)
- **Complexity:** 4 (Renaming models means changing almost every import and query in the app)
- **Risk:** 4 (High risk of missing a reference and causing a crash)

---

## 3. Architecture & Organization

### Sync Consumer Blocking
The `WebsocketConsumer` executes heavy DB operations synchronously, blocking the Channels event loop.
- **Importance:** 4 (Crucial for Websocket stability and performance)
- **Complexity:** 4 (Requires extracting all logic into a `services.py` layer and using `sync_to_async`)
- **Risk:** 4 (Could introduce subtle timing bugs or race conditions)

### Templates & JavaScript Spaghetti
`auction_table.html` has over 1,000 lines of inline JavaScript. Visibility is handled procedurally via hundreds of lines of jQuery `.show()`/`.hide()`.
- **Importance:** 4 (Crucial for maintainability and fixing UI bugs)
- **Complexity:** 4 (Requires splitting JS into modular files and transitioning to CSS-driven state visibility)
- **Risk:** 4 (UI state could break in subtle ways across different auction phases)

### Massive Payload Broadcasts
Instead of sending lightweight delta updates (e.g., `{"action": "new_bid", "amount": 15}`), the backend dumps the entire state of the database to every client on every interaction.
- **Importance:** 4 (Network bandwidth and rendering performance)
- **Complexity:** 5 (Requires overhauling both the backend payloads and the frontend rendering logic to handle deltas)
- **Risk:** 5 (High risk, completely changes the data flow paradigm of the application)

---

## Proposed Implementation Order

To balance risk and value, we should tackle these in phases, starting with isolated, high-impact fixes and ending with the most complex paradigm shifts. We will run the E2E test suite after every step.

**Phase 1: Critical Fixes (High Impact, Low Risk) - COMPLETED**
1. **Severe Data Leak:** Immediately patch the `User` object serialization.
2. **The O(N) Query Avalanche:** Optimize the roster count query to prevent database lockups.

**Phase 2: Database Integrity (Additive & Schema Changes)**
3. **Lack of a Bid Ledger:** Implement the `Bid` model to start recording history.
4. **Brittle Relationships & Normalization:** Migrate to Foreign Keys and remove redundant booleans.
5. **Singleton Abuse & Naming Conventions:** Rename models to PEP8 standards and prepare `AuctionManager` for multi-lobby support.

**Phase 3: Separation of Concerns (Structural Refactors)**
6. **Sync Consumer Blocking:** Abstract business logic from `consumers.py` into a robust `services.py` layer.
7. **Templates & JavaScript Spaghetti:** Extract JS into static modules and implement Data-Driven CSS visibility.

**Phase 4: Paradigm Shift (High Risk Overhaul)**
8. **Massive Payload Broadcasts:** Rework the WebSocket layer to broadcast lightweight delta payloads now that the backend and frontend are decoupled.
