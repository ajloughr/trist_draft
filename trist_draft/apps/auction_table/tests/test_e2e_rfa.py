import pytest
from playwright.sync_api import Page, expect, Browser
from .e2e_helpers import login_user, start_auction, drop_out_all_except, select_first_available_rfa, dismiss_winner_modal_if_present

def test_rfa_uncontested_bid(browser: Browser):
    """TC 2.2 - Uncontested Opening Bid"""
    s_ctx, s_page = login_user(browser, "sentinels")
    dismiss_winner_modal_if_present(s_page)
    start_auction(s_page, "rfa", "1")
    select_first_available_rfa(s_page)
    
    # Assert input is disabled for RFA opener and locked at $1
    s_page.wait_for_selector("#id_new_bid", state="attached", timeout=2000)
    s_page.locator("label[for='contract_year_selected_1']").click()
    expect(s_page.locator("#id_new_bid")).to_be_disabled()
    expect(s_page.locator("#id_new_bid")).to_have_value("1")
    s_page.click("#submit_new_bid_button")
    
    # All other 9 users drop out
    drop_out_all_except(browser, "1", exceptions=["sentinels"])
    
    # Sentinels is awarded the player for $1
    h_ctx, h_page = login_user(browser, "hokiehigh")
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=2000)

def test_rfa_owner_declines_match(browser: Browser):
    """TC 2.3 - Owner Declines Match"""
    s_ctx, s_page = login_user(browser, "sentinels")
    dismiss_winner_modal_if_present(s_page)
    start_auction(s_page, "rfa", "1")
    select_first_available_rfa(s_page)
    s_page.locator("label[for='contract_year_selected_1']").click()
    s_page.click("#submit_new_bid_button")
    
    h_ctx, h_page = login_user(browser, "hokiehigh")
    expect(h_page.locator("#current_highest_bid")).to_have_text("1", timeout=2000)
    
    # Assert Hokie High can't change years
    expect(h_page.locator("label[for='contract_year_selected_2']")).to_be_hidden()
    
    h_page.fill("#id_new_bid", "10")
    h_page.click("#submit_new_bid_button")
    
    # Drop out everyone else so Hokie High is the only remaining bidder
    drop_out_all_except(browser, "10", exceptions=["sentinels", "hokiehigh"])
    
    # Wait for the Owner Match prompt for Sentinels
    expect(s_page.locator("#rfa_owner_match_request_1_toast")).to_be_visible(timeout=2000)
    
    # Sentinels declines
    s_page.click("#rfa_owner_confirm_match_1_reject")
    
    # Hokie High wins
    # Next turn goes to Hokie High
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=2000)

def test_rfa_owner_matches_winner_declines(browser: Browser):
    """TC 2.4 - Owner Matches, Winner Declines Raise"""
    s_ctx, s_page = login_user(browser, "sentinels")
    dismiss_winner_modal_if_present(s_page)
    start_auction(s_page, "rfa", "1")
    select_first_available_rfa(s_page)
    s_page.locator("label[for='contract_year_selected_1']").click()
    s_page.click("#submit_new_bid_button")
    
    h_ctx, h_page = login_user(browser, "hokiehigh")
    h_page.fill("#id_new_bid", "10")
    h_page.click("#submit_new_bid_button")
    
    drop_out_all_except(browser, "10", exceptions=["sentinels", "hokiehigh"])
    
    # Sentinels matches
    s_page.click("#rfa_owner_confirm_match_1_match")
    
    # Hokie High is prompted to submit their one allowed raise
    expect(h_page.locator("#rfa_bid_winner_offer_raise_toast")).to_be_visible(timeout=2000)
    
    # Hokie High declines to raise (drops out)
    h_page.click("#rfa_winner_drop_out")
    
    # Sentinels wins
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=2000)

def test_rfa_full_exhaustion(browser: Browser):
    """TC 2.6 - Full Exhaustion (Owner Matches Final)"""
    s_ctx, s_page = login_user(browser, "sentinels")
    dismiss_winner_modal_if_present(s_page)
    start_auction(s_page, "rfa", "1")
    select_first_available_rfa(s_page)
    s_page.locator("label[for='contract_year_selected_1']").click()
    s_page.click("#submit_new_bid_button")
    
    h_ctx, h_page = login_user(browser, "hokiehigh")
    h_page.fill("#id_new_bid", "10")
    h_page.click("#submit_new_bid_button")
    
    drop_out_all_except(browser, "10", exceptions=["sentinels", "hokiehigh"])
    
    s_page.click("#rfa_owner_confirm_match_1_match")
    
    h_page.fill("#rfa_raise_bid", "15")
    h_page.click("#rfa_winner_raise")
    
    # Sentinels gets one last chance to match
    s_page.click("#rfa_owner_confirm_match_2_match")
    
    expect(h_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=2000)
