from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta
from sqlalchemy import desc, func
from app.extensions import db
from app.models.menu import Menu
from app.models.rating import Rating
from app.models.comment import Comment
from app.middleware.auth_middleware import token_required, student_required, current_user_or_test
from app.utils.validators import validate_rating



menus_bp = Blueprint('menus', __name__)


@menus_bp.route('/today', methods=['GET'])
# @token_required  # Şimdilik kapalı
def get_today_menu():
    """O günün menüsünü getirir"""
    today = date.today()
    menu = Menu.query.filter_by(tarih=today).first()

    if not menu:
        return jsonify({'error': 'Bugün için menü bulunamadı'}), 404

    return jsonify(menu.to_dict()), 200


@menus_bp.route('/stats', methods=['GET'])


# @token_required  # Şimdilik kapalı
def get_menu_stats():
    """ İstatistikleri getirir """
    sort_by = request.args.get('sortBy', 'newest')
    limit = request.args.get('limit', 5, type=int) # Sayfa başına kayıt : 5
    page = request.args.get('page', 1, type=int) # sayda numarası : 1

    # Base query - tüm menüler
    query = Menu.query

    # Sıralama türüne göre
    if sort_by == 'highest_rated':
        # En yüksek puanlı menüler (en az 1 puan almış olmalı)
        query = query.join(Rating).group_by(Menu.id).having(
            func.count(Rating.id) > 0
        ).order_by(
            desc(func.avg(Rating.puan))
        )

    elif sort_by == 'lowest_rated':
        # En düşük puanlı menüler (en az 1 puan almış olmalı)
        query = query.join(Rating).group_by(Menu.id).having(
            func.count(Rating.id) > 0
        ).order_by(
            func.avg(Rating.puan)
        )

    elif sort_by == 'most_rated':
        # En çok puanlanan menüler
        query = query.outerjoin(Rating).group_by(Menu.id).order_by(
            desc(func.count(Rating.id))
        )

    elif sort_by == 'most_commented':
        # En çok yorumlanan menüler
        query = query.outerjoin(Comment).group_by(Menu.id).order_by(
            desc(func.count(Comment.id))
        )

    else:  # newest (default)
        # En yeni menüler
        query = query.order_by(desc(Menu.tarih))

    # Sayfalama
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'menus': [menu.to_dict() for menu in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page,
        'sortBy': sort_by
    }), 200


@menus_bp.route('/<menu_id>', methods=['GET'])
# @token_required  # Şimdilik kapalı
def get_menu_details(menu_id):
    """Belirli bir menünün detaylarını getirir"""
    menu = Menu.query.get(menu_id)

    if not menu:
        return jsonify({'error': 'Menü bulunamadı'}), 404

    # Detaylı bilgilerle döndür
    menu_data = menu.to_dict()

    # Yorumları ekle (sadece sayı değil, ilk 5 yorum)
    comments = Comment.query.filter_by(menu_id=menu_id).order_by(
        desc(Comment.created_at)
    ).limit(5).all()

    menu_data['yorumlar'] = [comment.to_dict() for comment in comments]

    return jsonify(menu_data), 200


@menus_bp.route('/<menu_id>/rate', methods=['POST'])
def rate_menu(menu_id):
    """Bir menüye puan verir veya günceller"""
    data = request.get_json()

    if 'puan' not in data:
        return jsonify({'error': 'Puan gerekli'}), 400

    is_valid, message = validate_rating(data['puan'])
    if not is_valid:
        return jsonify({'error': message}), 400

    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({'error': 'Menü bulunamadı'}), 404

    current_user_id = current_user_or_test()

    existing_rating = Rating.query.filter_by(
        kullanici_id=current_user_id,
        menu_id=menu_id
    ).first()

    if existing_rating:
        existing_rating.puan = data['puan']
        message_text = 'Puan güncellendi'
    else:
        new_rating = Rating(
            kullanici_id=current_user_id,
            menu_id=menu_id,
            puan=data['puan']
        )
        db.session.add(new_rating)
        message_text = 'Puan verildi'

    db.session.commit()

    return jsonify({
        'message': message_text,
        'menu': menu.to_dict()
    }), 200
