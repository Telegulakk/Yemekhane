from app import create_app
from app.extensions import db
from app.models.menu import Menu
from app.utils.scraper import scrape_todays_menu


def update_todays_menu():
    """Her gün çalışacak task"""
    app = create_app()

    with app.app_context():
        menu_data = scrape_todays_menu()

        if menu_data:
            # Aynı tarihli menü var mı?
            existing = Menu.query.filter_by(tarih=menu_data['tarih']).first()

            if existing:
                # Güncelle
                existing.yemekler = menu_data['yemekler']
            else:
                # Yeni ekle
                new_menu = Menu(
                    tarih=menu_data['tarih'],
                    yemekler=menu_data['yemekler']
                )
                db.session.add(new_menu)

            db.session.commit()
            print(f"Menü güncellendi: {menu_data['tarih']}")
        else:
            print("Menü çekilemedi")


if __name__ == '__main__':
    update_todays_menu()