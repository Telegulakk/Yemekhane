from app.routes.auth import auth_bp
from app.routes.density import density_bp
from app.routes.menus import menus_bp
from app.routes.comments import comments_bp, comment_actions_bp

__all__ = ['auth_bp', 'menus_bp', 'comments_bp', 'density_bp', 'comment_actions_bp']