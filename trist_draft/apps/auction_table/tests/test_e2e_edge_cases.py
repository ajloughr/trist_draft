import pytest
from playwright.sync_api import Page, expect, Browser
from .e2e_helpers import login_user, start_auction, drop_out_all_except

def test_late_drop_out_and_bidding_disabled(browser: Browser):
    """TC 6.1 - Late Drop Out & Bidding Disabled
    Verifies that when a user drops out, they can no longer interact with the bid buttons,
    even before the official dropout completes (e.g. they should be immediately disabled locally).
    """
    s_ctx, s_page = login_user(browser, "sentinels")
    start_auction(s_page, "ufa", "1")
    
    # Sentinels puts up Josh Allen and bids 5/2 years
    s_page.fill("#player_search_value", "Josh Allen")
    s_page.press("#player_search_value", "Enter")
    s_page.wait_for_selector("#search_results_table tbody tr", state="attached")
    s_page.click("#search_results_table tbody tr:nth-child(1) button.btn-success")
    s_page.click("#select_player_confirmed")
    
    s_page.locator("label[for='contract_year_selected_2']").click()
    s_page.fill("#id_new_bid", "5")
    s_page.click("#submit_new_bid_button")
    
    # Russ Riders (draft order 3) drops out LATE (during Hokie High's turn)
    r_ctx, r_page = login_user(browser, "russriders")
    
    # Assert Russ Riders is not the active bidder
    expect(r_page.locator("#your_turn_to_bid_banner")).not_to_be_visible()
    
    # Drop out
    r_page.click("#drop_out_confirmation_button")
    r_page.click("#drop_out_button")
    
    # Immediately check that bidding input and buttons are disabled for Russ Riders
    expect(r_page.locator("#id_new_bid")).to_be_disabled()
    expect(r_page.locator("#submit_new_bid_button")).to_be_disabled()
    expect(r_page.locator("#pass_button")).to_be_disabled()

def test_reconnect_state_recovery(browser: Browser):
    """TC 6.2 - Reconnect State Recovery
    Verifies that a user can refresh the page and accurately recover their bidding UI state.
    """
    s_ctx, s_page = login_user(browser, "sentinels")
    start_auction(s_page, "ufa", "1")
    
    # Hokie High logs in
    h_ctx, h_page = login_user(browser, "hokiehigh")
    
    # Refresh the page mid-auction
    h_page.reload()
    
    # Assert state is recovered
    expect(h_page.locator("#current_auction_type")).to_have_text("Unrestricted Free Agent")
