---
description: Provides the business logic and rules for the three phases of the auction draft keeper league. The agent should reference this when modifying models, views, or draft logic.
---

# League Draft Rules

## App Scope & Data State
* **In Scope:** Managing draft mechanics, tracking phase transitions, assigning players to teams with contract lengths/prices, and maintaining real-time turn state.
* **Out of Scope:** Roster size limits, mid-season roster management, and drop penalties.
* **Contract Pricing:** All dollar amounts represent the **total contract price**, not a yearly salary.

## Bidding Mechanics & Turn Order
* **Sequential Turns:** Bidding follows the established draft order. When a player is nominated, bidding starts with the team immediately following the nominator.
* **Minimum Increment:** All bids must increase the total dollar amount by at least $1.
* **Dropping Out of an Auction:** A team can explicitly "Drop Out" on their turn. Once dropped, the turn rotation skips them for the remainder of that specific player's auction.
* **Uncontested Nominations:** If a player is nominated and every other team drops out without bidding, the nominator is forced to keep the player at the opening price/years.

## The "Pass Once" Rule & End-of-Auction Resolution
* During the active bidding phase, each non-nominating team gets **one pass** per player auction.
* **Scope of Pass:** Passing **only skips their current turn in the current bid**. It does not drop them from the auction, allowing them to participate in future turns for that same player.
* Once a team uses their pass, they **cannot pass again** on that specific player (subsequent turns require a valid raise or an explicit Drop Out).
* Passing is **disabled** when only two active bidders remain.
* Passing is **strictly prohibited** during any part of the RFA Owner Match phase.
* **End of Auction Resolution (UFA):** If all other active bidders drop out, the turn rotation loops back to any team that previously passed. That team must now either submit a valid bid or drop out.
* **End of Auction Resolution (RFA):** If all other active bidders drop out, and the only remaining non-owner team is one that previously passed, the active bidding phase ends immediately. The final bid is the price at which they passed, and the auction proceeds directly to the Owner Match phase.

## Budget Constraints
* **Budget Ceiling:** A user cannot submit a bid greater than their current remaining budget.
* **Priced Out:** If the current bid exceeds a user's remaining budget, they cannot use their pass and must manually drop out. *(Future Feature: System will automatically skip/drop out a user and display a notification if priced out).*

## Special Modes & Admin Actions
* **Bathroom Mode:** A courtesy toggle that automatically skips a team in all situations (bidding, passing, nomination) while away.
* **Admin Overrides:** An admin can manually force a "pass" or "drop out" action on behalf of any stalled user to keep the draft moving.

## Phase 1: Rookie Draft
* **Eligibility:** Only rookies.
* **Order:** Sequential snake draft (1-10, 10-1).
* **Cost:** Fixed at $1 total per player.
* **Bidding:** None. Teams simply make their pick in order.
* **Phase End Trigger:** Phase completes automatically once all picks are made.

## Phase 2: Restricted Free Agents (RFA)
* **Eligibility:** Expired contracts designated for RFA status by the original owner.
* **Nomination Order:** Standard draft order. Teams nominate their own RFAs. Teams with no remaining RFAs are skipped.
* **Opening Bid:** The owner locks in the contract length (1, 2, or 3 years). The price is strictly locked at a baseline of $1 and cannot be modified by the nominator.
* **Bidding Process:**
  1. Contract length (years) is strictly locked and **cannot be changed**.
  2. Other teams bid sequentially on the dollar amount until one winning bidder remains.
  3. **First Match:** Once a team wins the bidding, the original owner must either match the winning bid or decline.
  4. **Single Raise:** If the owner matches, the winning bidder gets exactly **one** opportunity to raise.
  5. **Final Match:** If raised, the owner gets **one** final opportunity to match or decline.
* **Phase End Trigger:** Phase completes automatically once all designated RFAs have been nominated and resolved.

## Phase 3: Unrestricted Free Agents (UFA)
* **Eligibility:** All remaining available players.
* **Nomination Order:** Standard sequential draft order. 
* **Permanent Selection Drop-Out:** A team can explicitly **drop out of player selection**, permanently removing them from the rotation to nominate players. They remain eligible to bid on players nominated by others.
* **Opening Bid:** The nominator must open with a bid of at least $1 and specify a contract length of 1, 2, or 3 years.
* **Bidding Process:**
  1. Bidding goes sequentially around the room.
  2. Teams can increase the dollar amount, the number of years, or both.
  3. Increasing the number of years **requires also increasing the dollar amount**.
* **Phase & Draft End Trigger:** The UFA phase (and the overall draft) completes when **all teams have dropped out of player selection**.