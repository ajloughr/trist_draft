import pytest
from playwright.sync_api import Page, expect, Browser
from .e2e_helpers import login_user, start_auction

def test_budget_exceeded(browser: Browser):
    """TC 5.1 - Bid Exceeds Budget"""
    # Verify that a user cannot submit a bid higher than their max bid budget
    pass

def test_budget_forced_priced_out(browser: Browser):
    """TC 5.2 - Forced Priced Out"""
    # Verify that if the current bid is higher than a user's budget when their turn arrives,
    # they are forced to drop out (or UI blocks them from raising).
    pass
