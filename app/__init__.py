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
    from app.routes.auth import auth_bp
    from app.routes.menus import menus_bp
    from app.routes.comments import comments_bp, comment_actions_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(menus_bp, url_prefix='/menus')
    app.register_blueprint(comments_bp, url_prefix='/menus')
    app.register_blueprint(comment_actions_bp, url_prefix='/comments')

    return app