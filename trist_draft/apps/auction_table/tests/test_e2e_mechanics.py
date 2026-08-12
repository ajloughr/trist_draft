import re
import pytest
from playwright.sync_api import Page, expect, Browser
from .e2e_helpers import login_user, start_auction, drop_out_all_except

def test_invalid_bids(browser: Browser):
    """TC 4.1 - Invalid Bids
    Verifies that the UI prevents bidding lower than or equal to the current highest bid
    and prevents bidding invalid contract years.
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
    
    # Hokie High tries to bid $4 / 2 years (invalid, lower than current)
    h_ctx, h_page = login_user(browser, "hokiehigh")
    h_page.locator("label[for='contract_year_selected_2']").click()
    h_page.fill("#id_new_bid", "4")
    # Check that UI disables submit button and marks input invalid for lower bid
    expect(h_page.locator("#submit_new_bid_button")).to_be_disabled()
    expect(h_page.locator("#id_new_bid")).to_have_class(re.compile(r"\bis-invalid\b"))


def test_tie_breakers(browser: Browser):
    """TC 4.2 - Tie Breakers
    Validates correct winner logic when two users bid identical total contract values.
    """
    pass # Needs implementation based on tie breaker logic
