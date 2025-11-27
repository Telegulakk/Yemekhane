from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    # Silmek istediğin mail adresini buraya yaz
    email_to_delete = "2022141006@cumhuriyet.edu.tr"

    user = User.query.filter_by(email=email_to_delete).first()

    if user:
        db.session.delete(user)
        db.session.commit()
        print(f"BAŞARILI: {email_to_delete} veritabanından silindi.")
    else:
        print("BİLGİ: Bu mail adresiyle kayıtlı bir kullanıcı zaten yok.")