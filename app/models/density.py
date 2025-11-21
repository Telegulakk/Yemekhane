from app.extensions import db
from datetime import datetime, timezone

class DensityVote(db.Model):
    __tablename__ = 'density_votes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<DensityVote {self.rating}>"