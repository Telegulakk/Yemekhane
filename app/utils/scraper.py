import requests
from bs4 import BeautifulSoup
import re
from datetime import date

def scrape_todays_menu():
    """Bugünün menüsünü web'den çeker (sadece 'BUGÜN' kısmını alır)"""
    url = "https://www.cumhuriyet.edu.tr/yemeklistesi/index.php?yemek=1"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1) 'h4' başlığı "BUGÜN" olan elementi bul
        today_header = soup.find('h4', string=re.compile('BUGÜN'))
        if not today_header:
            print("BUGÜN başlığı bulunamadı.")
            return None

        parent_div = today_header.find_parent('div', class_=lambda x: x and 'mitem' in x)
        if not parent_div:
            print("BUGÜN başlığını içeren ebeveyn div bulunamadı.")
            return None

        text = parent_div.get_text(separator='|', strip=True)
        parts = text.split('|')

        yemekler = []
        for part in parts:
            part = part.strip()
            if part.upper() == "BUGÜN":
                continue
            # Boş değilse ve makul uzunluktaysa ekle
            if part:
                yemekler.append(part)

        return {
            'tarih': date.today(),
            'yemekler': yemekler
        }

    except Exception as e:
        print(f"Scraping hatası: {e}")
        return None
