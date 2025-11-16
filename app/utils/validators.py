# Email .edu.tr mi kontrol eder, puan 1-5 arası mı kontrol eder

import re
from email_validator import validate_email, EmailNotValidError


def validate_student_email(email):
    """Öğrenci emailini kontrol eder (.edu.tr uzantısı zorunlu)"""
    try:
        valid = validate_email(email)
        email = valid.email

        # .edu.tr uzantısı kontrolü
        if not email.endswith('.edu.tr'):
            return False, 'Email adresi .edu.tr uzantılı olmalıdır'

        return True, email
    except EmailNotValidError as e:
        return False, str(e)


def validate_password(password):
    """Şifre güvenlik kontrolü (en az 8 karakter, büyük/küçük harf, rakam)"""
    if len(password) < 8:
        return False, 'Şifre en az 8 karakter olmalıdır'

    if not re.search(r'[A-Z]', password):
        return False, 'Şifre en az bir büyük harf içermelidir'

    if not re.search(r'[a-z]', password):
        return False, 'Şifre en az bir küçük harf içermelidir'

    if not re.search(r'[0-9]', password):
        return False, 'Şifre en az bir rakam içermelidir'

    return True, 'Şifre geçerli'


def validate_rating(puan):
    """Puan kontrolü (1-5 arası tam sayı olmalı)"""
    if not isinstance(puan, int):
        return False, 'Puan bir tam sayı olmalıdır'

    if puan < 1 or puan > 5:
        return False, 'Puan 1 ile 5 arasında olmalıdır'

    return True, 'Puan geçerli'