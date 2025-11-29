from app.extensions import db
from datetime import datetime

class BannedUser(db.Model):
    __tablename__ = 'banned_users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False) # Yasaklanan mail
    ban_date = db.Column(db.DateTime, default=datetime.utcnow)     # Ne zaman yasaklandı?

    def __init__(self, email):
        self.email = email