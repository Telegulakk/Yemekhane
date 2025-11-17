from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.extensions import db
from app.models.user import User
from app.middleware.auth_middleware import token_required, current_user_or_test
from app.utils.validators import validate_student_email, validate_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Yeni öğrenci hesabı oluşturur"""
    data = request.get_json()
    # Zorunlu alanlar kontrolü
    required_fields = ['ad', 'soyad', 'email', 'sifre']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} alanı zorunludur'}), 400

    # Email validasyonu
    is_valid, message = validate_student_email(data['email'])
    if not is_valid:
        return jsonify({'error': message}), 400

    # Şifre validasyonu
    is_valid, message = validate_password(data['sifre'])
    if not is_valid:
        return jsonify({'error': message}), 400

    # Email zaten kayıtlı mı?
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Bu email adresi zaten kayıtlı'}), 409

    # Yeni kullanıcı oluştur
    new_user = User(
        ad=data['ad'],
        soyad=data['soyad'],
        email=data['email'],
        sifre=data['sifre']
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'Kayıt başarılı',
        'user': new_user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Sisteme giriş yapar ve token döner"""
    data = request.get_json()

    if 'email' not in data or 'sifre' not in data:
        return jsonify({'error': 'Email ve şifre gerekli'}), 400

    # Kullanıcıyı bul
    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['sifre']):
        return jsonify({'error': 'Email veya şifre hatalı'}), 401

    # JWT token oluştur
    access_token = create_access_token(identity=user.id)

    return jsonify({
        'message': 'Giriş başarılı',
        'token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
def get_me():
    """Giriş yapmış kullanıcının kendi bilgilerini getirir"""
    user_id = current_user_or_test()  # ID döner (test user veya gerçek JWT)
    current_user = User.query.get(user_id)  # User objesine çevir

    if not current_user:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

    return jsonify(current_user.to_dict()), 200