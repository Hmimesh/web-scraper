from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        
        # טען את הדף הראשי
        page.goto("https://www.masham.org.il/רשויות-מקומיות/")
        
        # המתן ל־iframe
        frame = page.frame(url=lambda url: "rashuyot" in url)
        
        # בדוק אם הצלחנו למצוא את ה־iframe
        if not frame:
            print("לא נמצא iframe עם כתובת 'rashuyot'")
            return

        # מצא את כל כפתורי הרשויות
        buttons = frame.locator("button.mapMarker")
        count = buttons.count()
        print(f"נמצאו {count} רשויות מקומיות:\n")

        for i in range(count):
            button = buttons.nth(i)
            name = button.inner_text()
            region = button.get_attribute("data-marker-cat")
            print(f"{name} - ({region})")

        browser.close()

if __name__ == "__main__":
    main()
