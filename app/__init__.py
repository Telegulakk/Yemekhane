from flask import Flask
from app.config import config
from app.extensions import db, migrate, jwt, cors


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Extension'ları başlat
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])

    # Blueprint'leri kaydet
    from app.routes import auth_bp
    from app.routes import menus_bp
    from app.routes import comments_bp, comment_actions_bp, density_bp

    # Blueprint'leri Flask uygulamasına kaydet
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(menus_bp, url_prefix='/menus')
    app.register_blueprint(comments_bp, url_prefix='/menus')
    app.register_blueprint(comment_actions_bp, url_prefix='/comments')
    app.register_blueprint(density_bp, url_prefix='/density')

    return app