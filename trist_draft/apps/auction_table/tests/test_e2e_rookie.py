import pytest
from playwright.sync_api import Browser, expect
from .e2e_helpers import login_user, start_auction


def test_rookie_manual_entry(browser: Browser):
    """TC 4.2 - Rookie Selection via Manual Entry"""
    s_ctx, s_page = login_user(browser, "sentinels")
    
    # Start a Rookie auction for round 1
    start_auction(s_page, "rookie", "1")
    
    # Ensure we are on Sentinels turn
    expect(s_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)

    # Fill manual entry fields
    s_page.fill("#selected_player_name", "Patrick Mahomes")
    s_page.fill("#selected_player_team", "KC")
    s_page.fill("#selected_player_position", "QB")
    
    # Submit player
    s_page.click("#submit_selected_player")
    
    # Wait for Sentinels' turn to end
    expect(s_page.locator("#your_turn_to_bid_banner")).not_to_be_visible(timeout=10000)

    # Next team in Rookie Draft is hokiehigh (assuming standard setup)
    h_ctx, h_page = login_user(browser, "hokiehigh")
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)


def test_rookie_search_entry(browser: Browser):
    """TC 4.1 - Rookie Selection via Search"""
    s_ctx, s_page = login_user(browser, "sentinels")
    
    # Start a Rookie auction for round 1
    start_auction(s_page, "rookie", "1")
    
    # Ensure we are on Sentinels turn
    expect(s_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)

    # Search for a player
    s_page.fill("#player_search_value", "Josh Allen")
    s_page.press("#player_search_value", "Enter")
    
    # Wait for the search results table to appear
    s_page.wait_for_selector("#search_results_table tbody tr", state="attached", timeout=10000)
    
    # Click the + button in the first row
    s_page.click("#search_results_table tbody tr:nth-child(1) button.btn-success")
    
    # Click the modal confirm button
    s_page.click("#select_player_confirmed")
    
    # Wait for Sentinels' turn to end
    expect(s_page.locator("#your_turn_to_bid_banner")).not_to_be_visible(timeout=10000)

    # Next team in Rookie Draft is hokiehigh
    h_ctx, h_page = login_user(browser, "hokiehigh")
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)
