from functools import wraps
import os
from flask_jwt_extended import current_user

TEST_USER_ID = os.getenv("TEST_USER_ID", None)

def current_user_or_test():
    if TEST_USER_ID:  #loginsiz test girişi (.env ye databaseden seçtğimiz bir user idsini koyarız)
        return TEST_USER_ID # böylece istediğimiz user idsi döner
    return current_user.id #aksi halde login ile giriş yapmış user arayacak ve onun idsini bulucak (normalde olması gereken)


def token_required(fn):
    """Geçici olarak devre dışı"""
    return fn

def student_required(fn):
    """Geçici olarak devre dışı"""
    return fn




# en en en son vakit kalırsa eklenecek
def admin_required(fn):
    """Geçici olarak devre dışı"""
    return fn