import pytest
from playwright.sync_api import Page, expect, Browser

def test_two_user_rfa_bidding(browser: Browser):
    # Context 1: Sentinels (Admin & Draft order 1)
    s_context = browser.new_context()
    s_page = s_context.new_page()
    s_page.goto("http://localhost:8000/login/")
    s_page.fill("input[name='username']", "sentinels")
    s_page.fill("input[name='password']", "Password!23")
    s_page.click("button[type='submit']")
    
    expect(s_page).to_have_url("http://localhost:8000/")
    s_page.click("text=CONTINUE TO DRAFT")
    expect(s_page).to_have_url("http://localhost:8000/auction/")
    
    # Wait for the main UI to load
    expect(s_page.locator("body")).to_contain_text("Sentinels")
    
    # Sentinels (as admin) starts RFA round on user 1
    s_page.locator("label[for='admin_auction_type_selected_rfa']").click()
    s_page.fill("#new_bid_start_num", "1")
    s_page.click("#start_new_bid_button")
    
    # Sentinels now sees their RFA list populated via WebSocket
    s_page.wait_for_function('document.querySelectorAll("#rfa_selector option").length > 1 || document.querySelector("#rfa_selector").textContent.includes("|")')
    
    # Select the first RFA player
    s_page.select_option("#rfa_selector", index=0)
    s_page.click("#select_rfa_player")
    
    # Sentinels submits their opening bid (fixed at $1 for 1 year for RFA opener)
    try:
        s_page.wait_for_selector("#id_new_bid")
        s_page.locator("label[for='contract_year_selected_1']").click()
        s_page.click("#submit_new_bid_button")
    except Exception as e:
        s_page.screenshot(path="/mnt/user/docker/trist_draft/screenshot.png")
        raise e
    
    # Ensure the bid went through and state updated to $1
    expect(s_page.locator("#current_highest_bid")).to_have_text("1", timeout=10000)
    
    # Context 2: Hokie High (Draft order 2)
    h_context = browser.new_context()
    h_page = h_context.new_page()
    h_page.goto("http://localhost:8000/login/")
    h_page.fill("input[name='username']", "hokiehigh")
    h_page.fill("input[name='password']", "Password!23")
    h_page.click("button[type='submit']")
    
    expect(h_page).to_have_url("http://localhost:8000/")
    h_page.click("text=CONTINUE TO DRAFT")
    expect(h_page).to_have_url("http://localhost:8000/auction/")
    
    # Hokie High sees the player and the highest bid is 1
    expect(h_page.locator("#current_highest_bid")).to_have_text("1", timeout=10000)
    
    # Hokie High raises the bid to 15
    h_page.fill("#id_new_bid", "15")
    h_page.click("#submit_new_bid_button")
    
    # Verify both pages reflect the new highest bid of 15 synchronously via websockets!
    expect(h_page.locator("#current_highest_bid")).to_have_text("15", timeout=10000)
    expect(s_page.locator("#current_highest_bid")).to_have_text("15", timeout=10000)
