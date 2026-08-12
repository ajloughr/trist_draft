import pytest
from playwright.sync_api import Page, expect, Browser
from .e2e_helpers import login_user, start_auction, dismiss_winner_modal_if_present

def test_draft_onboarding_tour_rfa(browser: Browser):
    """TC 5.1 - RFA Onboarding Tour Execution"""
    s_ctx, s_page = login_user(browser, "sentinels")
    dismiss_winner_modal_if_present(s_page)
    start_auction(s_page, "rfa", "1")

    # Verify Draft Guide button exists in navbar
    guide_btn = s_page.locator("#start_onboarding_tour_btn")
    expect(guide_btn).to_be_visible()
    guide_btn.click()

    # Verify Driver.js popover opens
    popover = s_page.locator(".driver-popover")
    expect(popover).to_be_visible(timeout=5000)
    expect(s_page.locator(".driver-popover-title")).to_contain_text("Restricted Free Agent")

    # Step through tour steps
    next_btn = s_page.locator(".driver-popover-next-btn")
    for _ in range(6):
        next_btn.click()
        s_page.wait_for_timeout(300)

    # Verify mock toast step for RFA owner match prompt (Andrew Loughran, $69, 3 Yrs)
    expect(s_page.locator("#rfa_owner_match_request_1_toast")).to_be_visible()
    expect(s_page.locator("#rfa_owner_match_request_1_toast .current_highest_bid_toast")).to_contain_text("$69")

    # Finish tour
    close_btn = s_page.locator(".driver-popover-close-btn")
    close_btn.click()
    expect(popover).to_be_hidden()

def test_draft_onboarding_tour_rookie(browser: Browser):
    """TC 5.2 - Rookie Onboarding Tour Execution with Search & Modal Demos"""
    s_ctx, s_page = login_user(browser, "sentinels")
    dismiss_winner_modal_if_present(s_page)
    start_auction(s_page, "rookie", "1")

    guide_btn = s_page.locator("#start_onboarding_tour_btn")
    expect(guide_btn).to_be_visible()
    guide_btn.click()

    popover = s_page.locator(".driver-popover")
    expect(popover).to_be_visible(timeout=5000)
    expect(s_page.locator(".driver-popover-title")).to_contain_text("Rookie Draft Phase")

    next_btn = s_page.locator(".driver-popover-next-btn")
    next_btn.click() # Pick selection
    next_btn.click() # DB Search filters
    expect(s_page.locator(".driver-popover-title")).to_contain_text("Database Search")

    next_btn.click() # Search results table
    expect(s_page.locator("#search_results_table")).to_be_visible()

    next_btn.click() # Confirmation modal demo
    expect(s_page.locator("#select_player_confirmation_modal")).to_be_visible()

    next_btn.click() # Manual Entry tab
    expect(s_page.locator("#select_player_confirmation_modal")).to_be_hidden()

    s_page.locator(".driver-popover-close-btn").click()
    expect(popover).to_be_hidden()

def test_draft_onboarding_tour_ufa(browser: Browser):
    """TC 5.3 - UFA Onboarding Tour Execution"""
    s_ctx, s_page = login_user(browser, "sentinels")
    dismiss_winner_modal_if_present(s_page)
    start_auction(s_page, "ufa", "1")

    expect(s_page.locator("#current_auction_type")).to_contain_text("Unrestricted Free Agent", timeout=5000)
    guide_btn = s_page.locator("#start_onboarding_tour_btn")
    guide_btn.click()

    popover = s_page.locator(".driver-popover")
    expect(popover).to_be_visible(timeout=5000)
    expect(s_page.locator(".driver-popover-title")).to_contain_text("Unrestricted Free Agent")

    s_page.locator(".driver-popover-close-btn").click()
    expect(popover).to_be_hidden()

def test_manual_entry_confirmation_modal(browser: Browser):
    """TC 5.4 - Manual Entry Nomination Confirmation Modal"""
    s_ctx, s_page = login_user(browser, "sentinels")
    dismiss_winner_modal_if_present(s_page)
    start_auction(s_page, "ufa", "1")

    # Switch to manual entry tab
    s_page.locator("#tab_manual_entry").click()
    s_page.fill("#selected_player_name", "Travis Kelce")
    s_page.fill("#selected_player_team", "KC")
    s_page.fill("#selected_player_position", "TE")

    # Click Submit Player
    s_page.click("#submit_selected_player")

    # Verify confirmation modal pops up with filled info
    modal = s_page.locator("#select_player_confirmation_modal")
    expect(modal).to_be_visible()
    expect(s_page.locator("#selected_player_name_confirm")).to_have_text("Travis Kelce")
    expect(s_page.locator("#selected_player_team_confirm")).to_have_text("KC")
    expect(s_page.locator("#selected_player_position_confirm")).to_have_text("TE")

    # Dismiss modal
    s_page.locator("#select_player_confirmation_modal .btn-outline-secondary").click()
    expect(modal).to_be_hidden()

