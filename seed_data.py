"""
Test verisi ekleme scripti
Database'e örnek menüler, kullanıcılar ve yorumlar ekler
"""
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.menu import Menu
from app.models.comment import Comment
from app.models.rating import Rating
from datetime import date, timedelta


def seed_database():
    app = create_app()

    with app.app_context():
        print("🌱 Test verileri ekleniyor...")

        # Mevcut verileri temizle (opsiyonel)
        # Comment.query.delete()
        # Rating.query.delete()
        # Menu.query.delete()
        # User.query.delete()
        # db.session.commit()

        # Test kullanıcıları
        users = [
            User(ad="Ahmet", soyad="Yılmaz", email="ahmet.yilmaz@ogrenci.edu.tr", sifre="Sifre123"),
            User(ad="Ayşe", soyad="Demir", email="ayse.demir@ogrenci.edu.tr", sifre="Sifre123"),
            User(ad="Mehmet", soyad="Kaya", email="mehmet.kaya@ogrenci.edu.tr", sifre="Sifre123"),
        ]

        for user in users:
            db.session.add(user)

        db.session.commit()
        print(f"✅ {len(users)} kullanıcı eklendi")

        # Son 7 günün menüleri
        menu_data = [
            ["Mercimek Çorbası", "Izgara Tavuk", "Pirinç Pilavı", "Salata"],
            ["Tarhana Çorbası", "Köfte", "Makarna", "Cacık"],
            ["Domates Çorbası", "Tavuk Şinitzel", "Patates Kızartması", "Turşu"],
            ["Ezogelin Çorbası", "Karnıyarık", "Bulgur Pilavı", "Ayran"],
            ["Yayla Çorbası", "Balık", "Pilav", "Salata"],
            ["Mercimek Çorbası", "Etli Nohut", "Makarna", "Yoğurt"],
            ["Sebze Çorbası", "Tavuk Sote", "Pirinç Pilavı", "Meyve"],
        ]

        menus = []
        for i, yemekler in enumerate(menu_data):
            menu_date = date.today() - timedelta(days=len(menu_data) - 1 - i)
            menu = Menu(tarih=menu_date, yemekler=yemekler)
            menus.append(menu)
            db.session.add(menu)

        db.session.commit()
        print(f"✅ {len(menus)} menü eklendi")

        # Puanlar
        import random
        ratings_count = 0
        for menu in menus:
            # Her menüye rastgele 5-15 puan
            num_ratings = random.randint(5, 15)
            for _ in range(num_ratings):
                user = random.choice(users)

                # Aynı kullanıcı aynı menüye birden fazla puan vermesin
                existing = Rating.query.filter_by(
                    kullanici_id=user.id,
                    menu_id=menu.id
                ).first()

                if not existing:
                    rating = Rating(
                        kullanici_id=user.id,
                        menu_id=menu.id,
                        puan=random.randint(1, 5)
                    )
                    db.session.add(rating)
                    ratings_count += 1

        db.session.commit()
        print(f"✅ {ratings_count} puan eklendi")

        # Yorumlar
        sample_comments = [
            "Çok lezzetliydi, teşekkürler!",
            "Tavuk biraz sert olmuş ama idare eder.",
            "Bugünkü menü süperdi, özellikle çorba harika!",
            "Porsiyonlar biraz küçük geldi.",
            "Her zamanki gibi güzel bir öğle yemeği.",
            "Yemekler soğuktu, daha sıcak olabilirdi.",
            "10 numara, ellerinize sağlık!",
            "Makarna çok güzeldi ama salata eksikti.",
        ]

        comments_count = 0
        for menu in menus[-3:]:  # Son 3 menüye yorum
            num_comments = random.randint(2, 5)
            for _ in range(num_comments):
                user = random.choice(users)
                comment_text = random.choice(sample_comments)

                comment = Comment(
                    menu_id=menu.id,
                    kullanici_id=user.id,
                    yorum_metni=comment_text
                )
                db.session.add(comment)
                comments_count += 1

        db.session.commit()
        print(f"✅ {comments_count} yorum eklendi")

        print("\n🎉 Test verileri başarıyla eklendi!")
        print("\n📝 Test kullanıcı bilgileri:")
        print("Email: ahmet.yilmaz@ogrenci.edu.tr")
        print("Şifre: Sifre123")


if __name__ == '__main__':
    seed_database()