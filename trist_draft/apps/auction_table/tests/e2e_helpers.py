from playwright.sync_api import Page, expect, Browser

USERS = [
    "sentinels", "hokiehigh", "russriders", "sportsballers", "dabears",
    "darkenergy", "alwaysnextyear", "easymarks", "showmethemoney", "whatdats"
]

def login_user(browser: Browser, username: str, password: str = "Password!23") -> tuple[any, Page]:
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost:8000/login/")
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.click("button[type='submit']")
    expect(page).to_have_url("http://localhost:8000/")
    page.click("text=CONTINUE TO DRAFT")
    expect(page).to_have_url("http://localhost:8000/auction/")
    expect(page.locator("body")).to_contain_text("Auction", ignore_case=True)
    return context, page

def start_auction(admin_page: Page, auction_type: str, draft_order: str):
    admin_page.goto("http://localhost:8000/draft-admin")
    admin_page.select_option("#select_phase", auction_type)
    admin_page.select_option("#select_start_bidder", str(draft_order))
    admin_page.click("#btn_start_phase")
    admin_page.click("#admin_confirm_modal_btn")
    admin_page.goto("http://localhost:8000/auction/")
    # Wait for the UI to sync via websocket and announce it is this user's turn
    expect(admin_page.locator("#your_turn_to_bid_banner")).to_be_visible(timeout=10000)

def drop_out_all_except(browser: Browser, current_price: str, exceptions: list[str]):
    """Logs in all users except the ones provided, clicks drop out, and closes their context."""
    for u in USERS:
        if u not in exceptions:
            ctx, page = login_user(browser, u)
            expect(page.locator("#current_highest_bid")).to_have_text(current_price, timeout=10000)
            
            # Assert they can't bid if it's not their turn, unless they are dropping out when it IS their turn
            # But they can drop out early!
            page.click("#drop_out_confirmation_button")
            page.wait_for_selector("#drop_out_confirmation_modal")
            page.click("#drop_out_button")
            ctx.close()
