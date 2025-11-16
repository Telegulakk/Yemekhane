from app.extensions import db
from datetime import datetime


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.String(50), primary_key=True)
    menu_id = db.Column(db.String(50), db.ForeignKey('menus.id'), nullable=False)
    kullanici_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    yorum_metni = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişkiler
    user = db.relationship('User', back_populates='comments')
    menu = db.relationship('Menu', back_populates='comments')
    likes = db.relationship('CommentLike', back_populates='comment', cascade='all, delete-orphan')

    def __init__(self, menu_id, kullanici_id, yorum_metni):
        import uuid
        self.id = str(uuid.uuid4())
        self.menu_id = menu_id
        self.kullanici_id = kullanici_id
        self.yorum_metni = yorum_metni

    @property
    def begeni_sayisi(self):
        """Like sayısını hesapla"""
        return len([l for l in self.likes if l.begeni_tipi == 'like'])

    @property
    def begenmeme_sayisi(self):
        """Dislike sayısını hesapla"""
        return len([l for l in self.likes if l.begeni_tipi == 'dislike'])

    def to_dict(self):
        return {
            'id': self.id,
            'menuId': self.menu_id,
            'kullaniciId': self.kullanici_id,
            'yorumMetni': self.yorum_metni,
            'tarih': self.created_at.isoformat(),
            'begeniSayisi': self.begeni_sayisi,
            'begenmemeSayisi': self.begenmeme_sayisi,
            'kullanici': {
                'ad': self.user.ad,
                'soyad': self.user.soyad
            } if self.user else None
        }