from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:8765"


def main() -> None:
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        initial = page.locator("#removal_rate").inner_text()
        page.locator("#down_force").fill("4.2")
        changed = page.locator("#removal_rate").inner_text()
        assert initial != "—", "model did not load"
        assert initial != changed, "slider did not update prediction"
        assert page.locator("#decision").inner_text() in {"PASS", "REVIEW"}
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.locator("main").evaluate("el => el.scrollWidth <= el.clientWidth")
        assert not errors, f"browser console errors: {errors}"
        browser.close()
    print({"status": "ok", "initial": initial, "changed": changed, "mobile_width": 390})


if __name__ == "__main__":
    main()
