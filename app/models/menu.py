from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY


class Menu(db.Model):
    __tablename__ = 'menus'

    id = db.Column(db.String(50), primary_key=True)
    tarih = db.Column(db.Date, unique=True, nullable=False)  # Her gün bir menü
    yemekler = db.Column(ARRAY(db.String), nullable=False)  # PostgreSQL array tipi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişkiler
    ratings = db.relationship('Rating', back_populates='menu', cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='menu', cascade='all, delete-orphan')

    def __init__(self, tarih, yemekler):
        import uuid
        self.id = str(uuid.uuid4())
        self.tarih = tarih
        self.yemekler = yemekler

    @property
    def ortalama_puan(self):
        """Menünün ortalama puanını hesaplar"""
        if not self.ratings:
            return 0.0
        return round(sum(r.puan for r in self.ratings) / len(self.ratings), 1)

    @property
    def puanlayan_kisi_sayisi(self):
        """Kaç kişi puanladı"""
        return len(self.ratings)

    @property
    def yorum_sayisi(self):
        """Kaç yorum var"""
        return len(self.comments)

    def to_dict(self):
        return {
            'id': self.id,
            'tarih': self.tarih.isoformat(),
            'yemekler': self.yemekler,
            'ortalamaPuan': self.ortalama_puan,
            'puanlayanKisiSayisi': self.puanlayan_kisi_sayisi,
            'yorumSayisi': self.yorum_sayisi
        }