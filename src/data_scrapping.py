from bs4 import BeautifulSoup
import pandas as pd

def main():
    with open('iframe_page.html', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    data = []

    buttons = soup.select('button.mapMarker')

    for button in buttons:
        city_name = button.text.strip()
        category = button.get('data-marker-cat', "").strip()
        onclick = button.get('onclick', "")

        if 'window.open' in onclick:
            start = onclick.find("'") + 1
            end = onclick.rfind("'")
            url = onclick[start:end]
            full_url = f'https://www.masham.org.il{url}'
        
        else:
            full_url = None

        data.append({
            "עיר": city_name,
            "איזור": category,
            "קישור": full_url
        })

    df = pd.DataFrame(data)
    df.to_csv("cities_links.csv", index=False, encoding='utf-8-sig')
    print('saved cities_links.csv!')

if __name__ == "__main__":
    main()