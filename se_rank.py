from playwright.sync_api import sync_playwright

def get_se_result(se, keyword):
    with sync_playwright() as p:
        chrome = p.chromium.launch(headless=True)
        