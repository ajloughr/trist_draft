import pytest
from playwright.sync_api import Browser, expect
from .e2e_helpers import login_user


def test_admin_page_access_control(browser: Browser):
    """Test non-staff user cannot access /draft-admin."""
    # hokiehigh is a regular user (is_staff=False)
    s_ctx, s_page = login_user(browser, "hokiehigh")
    s_page.goto("http://localhost:8000/draft-admin")
    
    # Should be redirected to /auction/
    s_page.wait_for_url("http://localhost:8000/auction/", timeout=10000)
    assert "/auction" in s_page.url


def test_admin_page_staff_access(browser: Browser):
    """Test staff user can access /draft-admin."""
    # Log in as sentinels (is_staff=True)
    a_ctx, a_page = login_user(browser, "sentinels")
    a_page.goto("http://localhost:8000/draft-admin")
    
    # Should stay on /draft-admin and see title
    expect(a_page.locator("h2")).to_contain_text("TRIST Draft Administration Panel", timeout=10000)


def test_admin_panel_actions(browser: Browser):
    """Test admin features from the /draft-admin UI."""
    a_ctx, a_page = login_user(browser, "sentinels")
    a_page.goto("http://localhost:8000/draft-admin")
    
    # Test initiating phase
    a_page.select_option("#select_phase", "ufa")
    a_page.select_option("#select_start_bidder", "1")
    
    # Click start phase and confirm via Bootstrap modal
    a_page.click("#btn_start_phase")
    a_page.click("#admin_confirm_modal_btn")
    
    # Verify current phase badge updates
    expect(a_page.locator("#admin_current_phase")).to_contain_text("UFA", timeout=10000)
    
    # Test set active bidder
    a_page.select_option("#select_active_bidder", "3")
    a_page.click("#btn_set_active_bidder")
    a_page.click("#admin_confirm_modal_btn")
    expect(a_page.locator("#admin_active_bidder")).to_contain_text("3", timeout=10000)

    # Test updating budget for Team 1
    a_page.fill("#input_budget_1", "125")
    a_page.click("#btn_save_budget_1")
    
    # Verify updated budget in input box
    expect(a_page.locator("#input_budget_1")).to_have_value("125", timeout=10000)

    # Test force pass player selection
    a_page.click("#btn_force_pass_selection")
