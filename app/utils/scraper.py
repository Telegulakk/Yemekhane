import requests
from bs4 import BeautifulSoup
from datetime import date


def scrape_todays_menu():
    """Bugünün menüsünü web'den çeker"""
    url = "https://www.cumhuriyet.edu.tr/yemeklistesi/index.php?yemek=1"

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Bugünün tarihini bul
        today = date.today().strftime("%d-%m-%Y")

        # Menü itemlarını bul
        menu_items = soup.find_all('div', class_='men-item')

        for item in menu_items:
            # Tarihi bul
            date_elem = item.find('h4')
            if date_elem and today in date_elem.text:
                # Yemekleri al
                text = item.get_text(separator='|', strip=True)
                yemekler = text.split('|')[1:]  # İlk eleman tarih
                yemekler = [y.strip() for y in yemekler if y.strip()]

                return {
                    'tarih': date.today(),
                    'yemekler': yemekler
                }

        return None

    except Exception as e:
        print(f"Scraping hatası: {e}")
        return None