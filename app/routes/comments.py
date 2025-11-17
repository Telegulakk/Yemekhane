from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from app.extensions import db
from app.models.menu import Menu
from app.models.comment import Comment
from app.models.comment_like import CommentLike
from app.middleware.auth_middleware import token_required, student_required, current_user_or_test


comments_bp = Blueprint('comments', __name__)
comment_actions_bp = Blueprint('comment_actions', __name__)


@comments_bp.route('/<menu_id>/comments', methods=['GET'])
#@token_required
def get_menu_comments(menu_id):
    """Bir menünün yorumlarını listeler"""
    # Menü var mı?
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({'error': 'Menü bulunamadı'}), 404

    # Query parametreleri
    sort_by = request.args.get('sortBy', 'newest')
    limit = request.args.get('limit', 20, type=int)
    page = request.args.get('page', 1, type=int)

    # Base query
    query = Comment.query.filter_by(menu_id=menu_id)

    # Sıralama
    if sort_by == 'newest':
        query = query.order_by(desc(Comment.created_at))
    elif sort_by == 'oldest':
        query = query.order_by(Comment.created_at)
    elif sort_by == 'highest':
        # En çok beğenilen yorumlar (like - dislike)
        query = query.outerjoin(CommentLike).group_by(Comment.id).order_by(
            desc(db.func.count(db.case((CommentLike.begeni_tipi == 'like', 1))) -
                 db.func.count(db.case((CommentLike.begeni_tipi == 'dislike', 1))))
        )
    elif sort_by == 'lowest':
        # En az beğenilen yorumlar
        query = query.outerjoin(CommentLike).group_by(Comment.id).order_by(
            db.func.count(db.case((CommentLike.begeni_tipi == 'like', 1))) -
            db.func.count(db.case((CommentLike.begeni_tipi == 'dislike', 1)))
        )

    # Sayfalama
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'comments': [comment.to_dict() for comment in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'currentPage': page
    }), 200


@comments_bp.route('/<menu_id>/comment', methods=['POST'])
#@student_required
def create_comment(menu_id):
    """Bir menüye yorum yapar"""
    current_user_id = current_user_or_test()
    data = request.get_json()

    if 'yorumMetni' not in data or not data['yorumMetni'].strip():
        return jsonify({'error': 'Yorum metni gerekli'}), 400

    # Menü var mı?
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({'error': 'Menü bulunamadı'}), 404

    # Yorum oluştur
    new_comment = Comment(
        menu_id=menu_id,
        kullanici_id=current_user_id,
        yorum_metni=data['yorumMetni'].strip()
    )

    db.session.add(new_comment)
    db.session.commit()

    return jsonify({
        'message': 'Yorum eklendi',
        'comment': new_comment.to_dict()
    }), 201


@comment_actions_bp.route('/<comment_id>', methods=['PUT'])
#@student_required
def update_comment(comment_id):
    """Kendi yorumunu günceller"""
    current_user = get_current_user()
    data = request.get_json()

    if 'yorumMetni' not in data or not data['yorumMetni'].strip():
        return jsonify({'error': 'Yorum metni gerekli'}), 400

    # Yorum var mı?
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Yorum bulunamadı'}), 404

    # Yorumun sahibi mi?
    if comment.kullanici_id != current_user.id:
        return jsonify({'error': 'Bu yorumu güncelleme yetkiniz yok'}), 403

    # Güncelle
    comment.yorum_metni = data['yorumMetni'].strip()
    db.session.commit()

    return jsonify({
        'message': 'Yorum güncellendi',
        'comment': comment.to_dict()
    }), 200


@comment_actions_bp.route('/<comment_id>', methods=['DELETE'])
#@student_required
def delete_comment(comment_id):
    """Kendi yorumunu siler"""
    current_user = get_current_user()

    # Yorum var mı?
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Yorum bulunamadı'}), 404

    # Yorumun sahibi mi?
    if comment.kullanici_id != current_user.id:
        return jsonify({'error': 'Bu yorumu silme yetkiniz yok'}), 403

    # Sil
    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': 'Yorum silindi'}), 200


@comment_actions_bp.route('/<comment_id>/like', methods=['POST'])
#@student_required
def like_comment(comment_id):
    """Yorumu beğenir"""
    current_user = get_current_user()

    # Yorum var mı?
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Yorum bulunamadı'}), 404

    # Önceki tepki var mı?
    existing_like = CommentLike.query.filter_by(
        kullanici_id=current_user.id,
        yorum_id=comment_id
    ).first()

    if existing_like:
        if existing_like.begeni_tipi == 'like':
            return jsonify({'message': 'Zaten beğenmişsiniz'}), 200
        else:
            # Dislike'ı like'a çevir
            existing_like.begeni_tipi = 'like'
    else:
        # Yeni like oluştur
        new_like = CommentLike(
            kullanici_id=current_user.id,
            yorum_id=comment_id,
            begeni_tipi='like'
        )
        db.session.add(new_like)

    db.session.commit()

    return jsonify({
        'message': 'Yorum beğenildi',
        'comment': comment.to_dict()
    }), 200


@comment_actions_bp.route('/<comment_id>/like', methods=['DELETE'])
#@student_required
def unlike_comment(comment_id):
    """Beğeniyi geri çeker"""
    current_user = get_current_user()

    like = CommentLike.query.filter_by(
        kullanici_id=current_user.id,
        yorum_id=comment_id,
        begeni_tipi='like'
    ).first()

    if not like:
        return jsonify({'error': 'Beğeni bulunamadı'}), 404

    db.session.delete(like)
    db.session.commit()

    return jsonify({'message': 'Beğeni geri çekildi'}), 200


@comment_actions_bp.route('/<comment_id>/dislike', methods=['POST'])
#@student_required
def dislike_comment(comment_id):
    """Yorumu beğenmez"""
    current_user = get_current_user()

    # Yorum var mı?
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Yorum bulunamadı'}), 404

    # Önceki tepki var mı?
    existing_like = CommentLike.query.filter_by(
        kullanici_id=current_user.id,
        yorum_id=comment_id
    ).first()

    if existing_like:
        if existing_like.begeni_tipi == 'dislike':
            return jsonify({'message': 'Zaten beğenmemişsiniz'}), 200
        else:
            # Like'ı dislike'a çevir
            existing_like.begeni_tipi = 'dislike'
    else:
        # Yeni dislike oluştur
        new_dislike = CommentLike(
            kullanici_id=current_user.id,
            yorum_id=comment_id,
            begeni_tipi='dislike'
        )
        db.session.add(new_dislike)

    db.session.commit()

    return jsonify({
        'message': 'Yorum beğenilmedi',
        'comment': comment.to_dict()
    }), 200


@comment_actions_bp.route('/<comment_id>/dislike', methods=['DELETE'])
#@student_required
def remove_dislike(comment_id):
    """Beğenmeme tepkisini geri çeker"""
    current_user = get_current_user()

    dislike = CommentLike.query.filter_by(
        kullanici_id=current_user.id,
        yorum_id=comment_id,
        begeni_tipi='dislike'
    ).first()

    if not dislike:
        return jsonify({'error': 'Beğenmeme tepkisi bulunamadı'}), 404

    db.session.delete(dislike)
    db.session.commit()

    return jsonify({'message': 'Beğenmeme tepkisi geri çekildi'}), 200