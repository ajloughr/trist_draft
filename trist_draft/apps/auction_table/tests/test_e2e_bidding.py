import pytest
from playwright.sync_api import Page, expect

def test_login_and_view_auction(page: Page):
    # Navigate to the login page
    page.goto("http://localhost:8000/login/")
    
    # Fill in login credentials
    # Assuming standard django forms with name="username" and name="password"
    page.fill("input[name='username']", "sentinels")
    page.fill("input[name='password']", "Password!23")
    
    # Click the login button
    page.click("button[type='submit']")
    
    # We are redirected to the home page, click Continue to Draft
    expect(page).to_have_url("http://localhost:8000/")
    page.click("text=CONTINUE TO DRAFT")
    
    # Verify navigation to the auction table
    expect(page).to_have_url("http://localhost:8000/auction/")
    
    # Wait for the main UI to load, identifying the user
    expect(page.locator("body")).to_contain_text("Sentinels")
