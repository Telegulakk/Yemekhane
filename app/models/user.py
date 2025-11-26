from app.extensions import db
import bcrypt # şifreleri güvenli bir şekilde saklamak için


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    soyad = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    sifre_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='ogrenci', nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)

    ratings = db.relationship('Rating', back_populates='user', cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='user', cascade='all, delete-orphan')
    comment_likes = db.relationship('CommentLike', back_populates='user', cascade='all, delete-orphan')

    def __init__(self, ad, soyad, email, sifre, rol='ogrenci', verification_code=None, is_verified=False):
        import uuid # id çakışmasını önler
        self.id = str(uuid.uuid4())
        self.ad = ad
        self.soyad = soyad
        self.email = email
        self.set_password(sifre)
        self.rol = rol
        self.is_verified = is_verified
        self.verification_code = verification_code

    def set_password(self, sifre):
        self.sifre_hash = bcrypt.hashpw(sifre.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, sifre):
        return bcrypt.checkpw(sifre.encode('utf-8'), self.sifre_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'id': self.id,
            'ad': self.ad,
            'soyad': self.soyad,
            'email': self.email,
            'rol': self.rol
        }