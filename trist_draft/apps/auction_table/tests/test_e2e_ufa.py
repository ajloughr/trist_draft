import pytest
from playwright.sync_api import Browser, expect
from .e2e_helpers import login_user, start_auction, drop_out_all_except


def test_ufa_bidding(browser: Browser):
    """TC 3.1 - Standard UFA Bidding"""
    s_ctx, s_page = login_user(browser, "sentinels")
    
    # Start a UFA auction for round 1
    start_auction(s_page, "ufa", "1")
    
    # Sentinels puts up Patrick Mahomes
    expect(s_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)
    s_page.fill("#player_search_value", "Patrick Mahomes")
    s_page.press("#player_search_value", "Enter")
    s_page.wait_for_selector("#search_results_table tbody tr button.btn-success:not([disabled])", timeout=10000)
    s_page.click("#search_results_table tbody tr button.btn-success:not([disabled])")
    s_page.click("#select_player_confirmed")
    s_page.wait_for_selector("#select_player_confirmation_modal", state="hidden", timeout=10000)
    try:
        s_page.wait_for_selector(".modal-backdrop", state="detached", timeout=3000)
    except Exception:
        pass
    
    # Everyone should see the bidding UI enabled
    expect(s_page.locator("#id_new_bid")).to_be_visible(timeout=10000)

    # Sentinels clicks 2-year radio to enable bid field
    s_page.locator("label[for='contract_year_selected_2']").click()
    s_page.fill("#id_new_bid", "5")
    s_page.click("#submit_new_bid_button")
    
    # Hokie High bids 10 (must bid at least 2 years since Sentinels bid 2 years)
    h_ctx, h_page = login_user(browser, "hokiehigh")
    h_page.locator("label[for='contract_year_selected_2']").click()
    h_page.fill("#id_new_bid", "10")
    h_page.click("#submit_new_bid_button")
    
    # Drop out everyone except hokiehigh (they are the winner)
    drop_out_all_except(browser, "10", exceptions=["hokiehigh"])
    
    # Winner (hokiehigh) receives UFA confirmation toast
    expect(h_page.locator("#ufa_end_confirm_toast")).to_be_visible(timeout=10000)
    
    # Winner confirms draft
    h_page.click("#ufa_confirm_button")
    
    # Wait for turn transition (next team)
    expect(h_page.locator("#your_turn_to_bid_banner")).not_to_be_visible(timeout=10000)

def test_ufa_pass_mechanic(browser: Browser):
    """TC 3.2 - UFA Pass Mechanic"""
    # Admin initiates UFA
    s_ctx, s_page = login_user(browser, "sentinels")
    start_auction(s_page, "ufa", "1")
    
    # It is Sentinels turn for round 1. Sentinels will pass player selection.
    s_page.click("#pass_player_selection")
    
    # After Sentinels passes, their turn ends.
    expect(s_page.locator("#your_turn_to_bid_banner")).not_to_be_visible(timeout=10000)
    
    # Now it is Hokie High's turn! (Since they are ufa_order=2)
    h_ctx, h_page = login_user(browser, "hokiehigh")
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)
    h_page.fill("#player_search_value", "Lamar Jackson")
    h_page.press("#player_search_value", "Enter")
    h_page.wait_for_selector("#search_results_table tbody tr button.btn-success:not([disabled])", timeout=10000)
    h_page.click("#search_results_table tbody tr button.btn-success:not([disabled])")
    h_page.click("#select_player_confirmed")
    
    # Hokie High must place the initial bid
    h_page.locator("label[for='contract_year_selected_1']").click()
    h_page.fill("#id_new_bid", "1")
    h_page.click("#submit_new_bid_button")
    
    # Now it is Russ Riders' turn to bid (order 3)
    r_ctx, r_page = login_user(browser, "russriders")
    expect(r_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)
    
    # Russ Riders uses a pass
    r_page.click("#pass_button")
    
    # Russ Riders' turn ends
    expect(r_page.locator("#your_turn_to_bid_banner")).not_to_be_visible(timeout=10000)
    
    # Now it is Sports Ballers' turn (order 4)
    p_ctx, p_page = login_user(browser, "sportsballers")
    expect(p_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)
