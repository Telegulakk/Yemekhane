from app.extensions import db
from datetime import datetime


class CommentLike(db.Model):
    __tablename__ = 'comment_likes'

    id = db.Column(db.String(50), primary_key=True)
    kullanici_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    yorum_id = db.Column(db.String(50), db.ForeignKey('comments.id'), nullable=False)
    begeni_tipi = db.Column(db.String(10), nullable=False)  # 'like' veya 'dislike'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # UNIQUE: Bir kullanıcı bir yoruma sadece bir kez tepki verebilir
    __table_args__ = (
        db.UniqueConstraint('kullanici_id', 'yorum_id', name='unique_user_comment_like'),
    )

    # İlişkiler
    user = db.relationship('User', back_populates='comment_likes')
    comment = db.relationship('Comment', back_populates='likes')

    def __init__(self, kullanici_id, yorum_id, begeni_tipi):
        import uuid
        self.id = str(uuid.uuid4())
        self.kullanici_id = kullanici_id
        self.yorum_id = yorum_id
        self.begeni_tipi = begeni_tipi

    def to_dict(self):
        return {
            'id': self.id,
            'kullaniciId': self.kullanici_id,
            'yorumId': self.yorum_id,
            'begeniTipi': self.begeni_tipi
        }