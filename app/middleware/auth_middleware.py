from functools import wraps

def token_required(fn):
    """Geçici olarak devre dışı"""
    return fn

def student_required(fn):
    """Geçici olarak devre dışı"""
    return fn

def get_current_user():
    """Geçici olarak None döner"""
    return None

def admin_required(fn):
    """Geçici olarak devre dışı"""
    return fn