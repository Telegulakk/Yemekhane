from email.header import Header
from email.utils import make_msgid
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_mail import Message
import random

# Proje dosyaları
from app.extensions import db, mail
from app.models.user import User
from app.utils.validators import validate_student_email, validate_password

auth_bp = Blueprint('auth', __name__)


# -------------------------------------------------------------------
# 1. KAYIT OLMA (REGISTER)
# -------------------------------------------------------------------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Zorunlu alan kontrolü
    required_fields = ['ad', 'soyad', 'email', 'sifre']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} alanı zorunludur'}), 400

    # Validasyonlar
    is_valid_email, message_email = validate_student_email(data['email'])
    if not is_valid_email:
        return jsonify({'error': message_email}), 400

    is_valid_pass, message_pass = validate_password(data['sifre'])
    if not is_valid_pass:
        return jsonify({'error': message_pass}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Bu email adresi zaten kayıtlı'}), 409

    # --- KULLANICI OLUŞTURMA ---
    generated_code = str(random.randint(100000, 999999))

    try:
        new_user = User(
            ad=data['ad'],
            soyad=data['soyad'],
            email=data['email'],
            sifre=data['sifre'],
            is_verified=False,
            verification_code=generated_code
        )

        db.session.add(new_user)
        db.session.flush()

        # --- MAIL AYARLARI ---

        # 1. Konu Başlığı (Türkçe karakterleri 'Header' ile sarıyoruz)
        subject_header = Header("Yemekhane Uygulaması Doğrulama Kodu", 'utf-8').encode()

        # 2. Gönderici İsmi (Temiz isim kullanıyoruz)
        safe_sender = ("Yemekhane App", os.environ.get('MAIL_USERNAME'))

        msg = Message(
            subject=subject_header,
            sender=safe_sender,
            recipients=[data['email']],
            charset='utf-8'
        )

        # --- KRİTİK DÜZELTME BURADA ---
        # Bilgisayar isminde 'ü' varsa (örn: Hüseyin-PC) hata vermemesi için
        # domain kısmını elle 'gmail.com' veya 'localhost' yapıyoruz.
        msg.msgId = make_msgid(domain='yemekhane.local')

        # İçerik
        msg.body = f"Merhaba {data['ad']}, Doğrulama Kodun: {generated_code}"

        mail.send(msg)

        db.session.commit()

        return jsonify({
            'message': 'Kayıt başarılı! Lütfen mailinize gelen kodu giriniz.',
            'email': data['email']
        }), 201

    except Exception as e:
        db.session.rollback()
        # Hatayı konsola tam yazdıralım ki görelim
        import traceback
        traceback.print_exc()
        print(f"Kayıt Hatası: {e}")
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500

# -------------------------------------------------------------------
# 2. DOĞRULAMA (VERIFY)
# -------------------------------------------------------------------
@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        return jsonify({'error': 'Email ve kod gereklidir'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

    if user.is_verified:
        return jsonify({'message': 'Hesap zaten doğrulanmış'}), 200

    if user.verification_code == code:
        user.is_verified = True
        user.verification_code = None
        db.session.commit()
        return jsonify({'message': 'Hesap doğrulandı! Giriş yapabilirsiniz.'}), 200
    else:
        return jsonify({'error': 'Hatalı kod'}), 400


# -------------------------------------------------------------------
# 3. GİRİŞ YAPMA (LOGIN)
# -------------------------------------------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if 'email' not in data or 'sifre' not in data:
        return jsonify({'error': 'Email ve şifre gerekli'}), 400

    user = User.query.filter_by(email=data['email']).first()

    # --- ŞİFRE KONTROLÜ ---

    if user and user.check_password(data['sifre']):

        # Doğrulama kontrolü
        if not user.is_verified:
            return jsonify({'error': 'Lütfen önce hesabınızı doğrulayın.'}), 403

        # Token oluştur
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'message': 'Giriş başarılı',
            'token': access_token,
            'user': user.to_dict()
        }), 200

    else:
        return jsonify({'error': 'Email veya şifre hatalı'}), 401


from app.middleware.auth_middleware import token_required, student_required
from flask_jwt_extended import get_jwt_identity
from app.models.user import User


@auth_bp.route('/profile', methods=['GET'])
@student_required  # <--- BAK BURAYA KİLİDİ KOYDUK!
def profile():
    """Sadece giriş yapmış öğrencilerin görebileceği özel alan"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    return jsonify({
        'message': f'Hoşgeldin {user.ad}, burası senin özel profilin!',
        'veri': 'Bu veriyi sadece token sahibi görebilir.'
    }), 200