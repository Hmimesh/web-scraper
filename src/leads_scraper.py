from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.masham.org.il/רשויות-מקומיות/")
        page.wait_for_timeout(5000)  # מחכה 5 שניות לטעינת JS
        html = page.content()

        with open("page.html", "w", encoding="utf-8") as f:
            f.write(html)

        browser.close()

if __name__ == "__main__":
    main()
