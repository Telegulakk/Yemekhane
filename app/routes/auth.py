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

    # Email zaten var mı?
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Bu email adresi zaten kayıtlı'}), 409

    # --- KULLANICI OLUŞTURMA ---
    generated_code = str(random.randint(100000, 999999))

    try:
        # DİKKAT: Şifreyi hashlemeden (ham haliyle) veriyoruz, modelin içinde o hashleniyor.
        new_user = User(
            ad=data['ad'],
            soyad=data['soyad'],
            email=data['email'],
            sifre=data['sifre'],  # Model bunu alıp set_password ile hashleyecek
            is_verified=False,
            verification_code=generated_code
        )

        db.session.add(new_user)
        db.session.commit()

        # Mail Gönderme
        msg = Message(
            subject="Yemekhane Uygulaması Doğrulama Kodu",
            sender=data['email'],
            recipients=[data['email']]
        )
        msg.body = f"Merhaba {data['ad']}, Doğrulama Kodun: {generated_code}"
        mail.send(msg)

        return jsonify({
            'message': 'Kayıt başarılı! Lütfen mailinize gelen kodu giriniz.',
            'email': data['email']
        }), 201

    except Exception as e:
        db.session.rollback()
        # Hatanın ne olduğunu görmek için print ekledik
        print(f"Kayıt Hatası: {e}")
        return jsonify({'error': 'Sunucu hatası oluştu.'}), 500


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


# -------------------------------------------------------------------
# 4. ŞİFREMİ UNUTTUM (KOD GÖNDERME)
# -------------------------------------------------------------------
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Kullanıcı mail adresini girer.
    Sistem kullanıcının varlığını kontrol eder.
    Var ise veritabanına bir doğrulama kodu yazar ve mail atar.
    """
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Lütfen mail adresinizi girin'}), 400

    # 1. Kullanıcıyı bul
    user = User.query.filter_by(email=email).first()

    if not user:
        # Güvenlik önlemi: Kullanıcı yoksa bile "Yok" demeyiz,
        # kötü niyetli kişiler rastgele mail deneyip kimin üye olduğunu anlamasın diye
        # sanki göndermiş gibi yaparız veya genel bir hata döneriz.
        return jsonify({'error': 'Bu mail adresiyle kayıtlı kullanıcı bulunamadı'}), 404

    # 2. Yeni bir kod oluştur (Örn: 381920)
    reset_code = str(random.randint(100000, 999999))

    # 3. Kodu veritabanına kaydet
    # Mevcut verification_code sütununu bu iş için tekrar kullanabiliriz.
    user.verification_code = reset_code
    db.session.commit()

    # 4. Mail Gönder
    try:
        msg = Message(
            subject="Şifre Sıfırlama Kodu - Yemekhane App",
            sender=email,  # Config'deki mail adresi
            recipients=[email]
        )
        msg.body = f"Merhaba {user.ad},\n\nŞifreni sıfırlamak için gereken kod: {reset_code}\n\nEğer bu işlemi sen yapmadıysan bu maili görmezden gel."
        mail.send(msg)

        return jsonify({'message': 'Sıfırlama kodu mail adresinize gönderildi.'}), 200

    except Exception as e:
        return jsonify({'error': 'Mail gönderilirken bir hata oluştu.'}), 500


# -------------------------------------------------------------------
# 5. ŞİFRE SIFIRLAMA (YENİ ŞİFRE BELİRLEME)
# -------------------------------------------------------------------
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Kullanıcı mailini, gelen kodu ve YENİ şifresini gönderir.
    Kod doğruysa ve şifre eskisinden farklıysa güncellenir.
    """
    data = request.get_json()

    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')

    # 1. Eksik bilgi kontrolü
    if not email or not code or not new_password:
        return jsonify({'error': 'Email, kod ve yeni şifre gereklidir'}), 400

    # 2. Şifre kurallarına uyuyor mu?
    is_valid_pass, message_pass = validate_password(new_password)
    if not is_valid_pass:
        return jsonify({'error': message_pass}), 400

    # 3. Kullanıcıyı bul
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

    # --- YENİ EKLENEN KISIM: ESKİ ŞİFRE KONTROLÜ ---
    # Kullanıcının girdiği 'new_password', mevcut şifresiyle aynı mı?
    if user.check_password(new_password):
        return jsonify({'error': 'Yeni şifreniz eski şifrenizle aynı olamaz. Lütfen farklı bir şifre belirleyin.'}), 400
    # -----------------------------------------------

    # 4. Kod Doğru mu?
    if user.verification_code == code:

        user.set_password(new_password)  # Yeni şifreyi kaydet
        user.verification_code = None  # Kodu sil

        db.session.commit()

        return jsonify({'message': 'Şifreniz başarıyla değiştirildi! Yeni şifrenizle giriş yapabilirsiniz.'}), 200
    else:
        return jsonify({'error': 'Girdiğiniz kod hatalı veya süresi dolmuş.'}), 400