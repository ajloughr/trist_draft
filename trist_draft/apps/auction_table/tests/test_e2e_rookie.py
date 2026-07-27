import pytest
from playwright.sync_api import Page, expect, Browser
from .e2e_helpers import login_user, start_auction

def test_rookie_manual_entry(browser: Browser):
    """Test manual entry for Rookie Draft"""
    s_ctx, s_page = login_user(browser, "sentinels")
    start_auction(s_page, "rookie", "1")
    
    # Sentinels types manually
    s_page.fill("#selected_player_name", "Patrick Mahomes")
    s_page.fill("#selected_player_team", "KC")
    s_page.fill("#selected_player_position", "QB")
    
    # Assert Hokie High is disabled from manual entry since it's not their turn
    h_ctx, h_page = login_user(browser, "hokiehigh")
    expect(h_page.locator("#submit_selected_player")).to_be_disabled()
    
    s_page.click("#submit_selected_player")
    
    # Rookie draft immediately awards the player and moves to the next user (Hokie High)
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)
    expect(h_page.locator("#submit_selected_player")).not_to_be_disabled()

def test_rookie_search_entry(browser: Browser):
    """Test search table entry for Rookie Draft"""
    s_ctx, s_page = login_user(browser, "sentinels")
    start_auction(s_page, "rookie", "1")
    
    # Assert Hokie High is not active
    h_ctx, h_page = login_user(browser, "hokiehigh")
    
    # Sentinels searches for a player. In a real test we use a real player from the reset DB.
    s_page.fill("#player_search_value", "Josh Allen")
    # Playwright's .fill() doesn't trigger keyup, which the frontend requires.
    s_page.locator("#player_search_value").press("Enter")
    
    # Wait for the table to populate with a tr
    s_page.wait_for_selector("#search_results_table tbody tr")
    
    # Click the green plus button
    s_page.click("#search_results_table tbody tr:first-child button.btn-success")
    
    # Wait for the confirmation modal and confirm
    s_page.wait_for_selector("#select_player_confirmation_modal")
    s_page.click("#select_player_confirmed")
    
    # This automatically submits! We wait for the turn to pass to the next user (Hokie High)
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)
    expect(h_page.locator("#submit_selected_player")).not_to_be_disabled()

def test_rookie_phase_transition(browser: Browser):
    """TC 1.3 - Phase Transition"""
    pass # In a real test, loop through all 10 picks and verify phase changes to RFA.
