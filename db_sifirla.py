from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Veritabanındaki tüm tabloları siler (Tertemiz yapar)
    db.drop_all()

    # alembic_version tablosu bazen kalabiliyor, onu da manuel siliyoruz
    try:
        db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
        db.session.commit()
    except:
        pass

    print("Veritabanı başarıyla sıfırlandı ve temizlendi!")