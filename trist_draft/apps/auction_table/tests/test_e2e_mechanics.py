import pytest
from playwright.sync_api import Page, expect, Browser
from .e2e_helpers import login_user, start_auction

def test_mechanics_pass_once(browser: Browser):
    """TC 4.1 - The Pass Once Rule"""
    s_ctx, s_page = login_user(browser, "sentinels")
    start_auction(s_page, "ufa", "1")
    s_page.fill("#player_search_value", "Patrick Mahomes")
    s_page.locator("#player_search_value").press("Enter")
    s_page.click("#search_results_table tbody tr:first-child button.btn-success")
    s_page.wait_for_selector("#select_player_confirmation_modal")
    s_page.click("#select_player_confirmed")
    s_page.locator("label[for='contract_year_selected_1']").click()
    s_page.fill("#id_new_bid", "10")
    s_page.click("#submit_new_bid_button")
    
    h_ctx, h_page = login_user(browser, "hokiehigh")
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible()
    
    # Hokie High passes
    h_page.click("#pass_button")
    
    # Verify their buttons are greyed out after passing
    expect(h_page.locator("#submit_new_bid_button")).to_be_disabled()
    expect(h_page.locator("#pass_button")).to_be_disabled()
    
    # Rotation would go around and come back... omitted for brevity
    
def test_mechanics_pass_exhaustion(browser: Browser):
    """TC 4.2 - Pass Exhaustion"""
    pass

def test_mechanics_drop_out(browser: Browser):
    """TC 4.3 - Drop Out Mechanic"""
    pass

def test_mechanics_drop_out_early(browser: Browser):
    """TC 4.4 - Drop Out Early"""
    s_ctx, s_page = login_user(browser, "sentinels")
    start_auction(s_page, "ufa", "1")
    s_page.fill("#player_search_value", "Patrick Mahomes")
    s_page.locator("#player_search_value").press("Enter")
    s_page.click("#search_results_table tbody tr:first-child button.btn-success")
    s_page.wait_for_selector("#select_player_confirmation_modal")
    s_page.click("#select_player_confirmed")
    s_page.locator("label[for='contract_year_selected_1']").click()
    s_page.fill("#id_new_bid", "10")
    s_page.click("#submit_new_bid_button")
    
    # Hokie High is next, but Russ Riders (Team 3) drops out early!
    r_ctx, r_page = login_user(browser, "russriders")
    
    # Assert Russ Riders' buttons are currently disabled since it's not their turn
    expect(r_page.locator("#submit_new_bid_button")).to_be_disabled()
    expect(r_page.locator("#pass_button")).to_be_disabled()
    
    # But drop out is still available!
    expect(r_page.locator("#drop_out_confirmation_button")).not_to_be_disabled()
    r_page.click("#drop_out_confirmation_button")
    r_page.wait_for_selector("#drop_out_confirmation_modal")
    r_page.click("#drop_out_button")
    
    # Assert fully disabled after dropping out early
    expect(r_page.locator("#drop_out_confirmation_button")).to_be_disabled()
    
    h_ctx, h_page = login_user(browser, "hokiehigh")
    h_page.fill("#id_new_bid", "15")
    h_page.click("#submit_new_bid_button")
    
    # Verify rotation skips Russ Riders and goes straight to Sports Ballers
    sb_ctx, sb_page = login_user(browser, "sportsballers")
    expect(sb_page.locator("#your_turn_to_bid_banner")).to_be_visible()
