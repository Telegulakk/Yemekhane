import os # .env dosyasından çevre değişkenlerini okur
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv() # .env dosyasını yükle


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key') # SECRET_KEY yoksa varsayılan dev-secret-key (test) okunur
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') # database'e bağlanır
    SQLALCHEMY_TRACK_MODIFICATIONS = False # manuel veri kaydetme (false = commit ile)

    # JWT ayarları
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)  # JWT token'ın geçerlilik süresi (Kullanıcı tekrar login olmalı)

    # CORS ayarları (frontend için)
    CORS_ORIGINS = ["*"] # flutter

    # Mail Ayarları
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


class DevelopmentConfig(Config): # Test ortamı
    DEBUG = True


class ProductionConfig(Config): # Canlı ortam
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}