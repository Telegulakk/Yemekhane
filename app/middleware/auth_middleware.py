from functools import wraps
import os
from flask_jwt_extended import current_user
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

TEST_USER_ID = os.getenv("TEST_USER_ID", None)


def token_required(fn):
    """
    Sadece giriş yapılmış mı diye kontrol eder.
    Rol ayrımı yapmaz (Öğrenci veya Admin olabilir).
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # 1. İstekte Token var mı ve geçerli mi kontrol et
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({'error': 'Geçersiz veya eksik token! Lütfen giriş yapın.'}), 401

        return fn(*args, **kwargs)

    return wrapper


def student_required(fn):
    """
    Hem giriş yapılmış mı, HEM DE rolü 'ogrenci' mi diye kontrol eder.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # 1. Token kontrolü
            verify_jwt_in_request()

            # 2. Token'dan kullanıcının ID'sini al
            user_id = get_jwt_identity()

            # 3. Veritabanından kullanıcıyı bul
            user = User.query.get(user_id)

            # 4. Kullanıcı yoksa veya rolü öğrenci değilse engelle
            if not user:
                return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

            if user.rol != 'ogrenci':
                return jsonify({'error': 'Bu işlem için öğrenci yetkisi gerekiyor!'}), 403

        except Exception as e:
            return jsonify({'error': 'Yetkilendirme hatası: ' + str(e)}), 401

        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """
    Sadece 'admin' rolüne sahip kullanıcılar girebilir.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user or user.rol != 'admin':
                return jsonify({'error': 'Bu alana sadece yöneticiler girebilir!'}), 403

        except Exception as e:
            return jsonify({'error': 'Yetkilendirme hatası'}), 401

        return fn(*args, **kwargs)

    return wrapper