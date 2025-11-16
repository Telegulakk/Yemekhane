from app.extensions import db
from datetime import datetime


class Rating(db.Model):
    __tablename__ = 'ratings'

    id = db.Column(db.String(50), primary_key=True)
    kullanici_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    menu_id = db.Column(db.String(50), db.ForeignKey('menus.id'), nullable=False)
    puan = db.Column(db.Integer, nullable=False)  # 1-5 arası
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # UNIQUE: Bir kullanıcı bir menüye sadece bir kez puan verebilir
    __table_args__ = (
        db.UniqueConstraint('kullanici_id', 'menu_id', name='unique_user_menu_rating'),
    )

    # İlişkiler
    user = db.relationship('User', back_populates='ratings')
    menu = db.relationship('Menu', back_populates='ratings')

    def __init__(self, kullanici_id, menu_id, puan):
        import uuid
        self.id = str(uuid.uuid4())
        self.kullanici_id = kullanici_id
        self.menu_id = menu_id
        self.puan = puan

    def to_dict(self):
        return {
            'id': self.id,
            'kullaniciId': self.kullanici_id,
            'menuId': self.menu_id,
            'puan': self.puan
        }