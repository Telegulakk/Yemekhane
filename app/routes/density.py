from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.density import DensityVote
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from app.middleware.auth_middleware import token_required, student_required, current_user_or_test


density_bp = Blueprint('density', __name__, url_prefix='/density')


# Son 30 dakikanın ortalamasını getirir
@density_bp.route('/', methods=['GET'])
def get_current_density():
    # Son 30 dknın verileri
    thirty_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)

    # ortalama hesaplama
    average = db.session.query(func.avg(DensityVote.rating)) \
        .filter(DensityVote.timestamp >= thirty_minutes_ago) \
        .scalar()

    if average is None:
        return jsonify({"average": 0, "status": "Veri yok"}), 200

    return jsonify({
        "average": round(float(average), 1),
    }), 200


# Kullanıcıdan yoğunluk puanı alır
@density_bp.route('/rate', methods=['POST'])
# @token_required
def rate_density():
    current_user_id = current_user_or_test()
    data = request.get_json()

    # Puan 1-5 arasında mı ?
    rating = data.get('puan')
    if not rating or not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"error": "Puan 1 ile 5 arasında olmalıdır."}), 400


    # Kullanıcı son 30 dk içinde zaten oy verdiyse yeni satır eklemek yerine eskisini güncelliyoruz
    thirty_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)

    existing_vote = DensityVote.query.filter(
        DensityVote.user_id == current_user_id,
        DensityVote.timestamp >= thirty_minutes_ago
    ).first()

    if existing_vote:
        existing_vote.rating = rating
        existing_vote.timestamp = datetime.now(timezone.utc)  # // Süreyi sıfırla
        db.session.commit()
        return jsonify({"message": "Mevcut oyunuz güncellendi.", "rating": rating}), 200

    # // Yeni oy kaydı
    new_vote = DensityVote(
        user_id=current_user_id,
        rating=rating
    )

    db.session.add(new_vote)
    db.session.commit()

    return jsonify({"message": "Yoğunluk puanınız kaydedildi.", "rating": rating}), 201