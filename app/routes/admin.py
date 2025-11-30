import os
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from sqlalchemy import desc

# Gerekli Modeller ve Eklentiler
from app.extensions import db
from app.models.user import User
from app.models.menu import Menu
from app.models.comment import Comment
from app.models.rating import Rating
from app.models.banned_user import BannedUser

from app.middleware.auth_middleware import admin_required

admin_bp = Blueprint('admin', __name__)


# Yardımcı Fonksiyon: Dosya Kontrolü
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


# ==============================================================================
# MENÜ YÖNETİMİ (EKLEME / DÜZENLEME / FOTOĞRAF)
# ==============================================================================

@admin_bp.route('/menus', methods=['POST'])
@admin_required
def upsert_menu():
    """
    Hem bugünün hem yarının (veya herhangi bir tarihin) menüsünü ekler veya günceller.
    Bot veriyi yanlış çektiyse Admin buradan düzeltebilir (Override).
    """
    # 1. Tarih Kontrolü
    tarih_str = request.form.get('tarih')
    if not tarih_str:
        return jsonify({'error': 'Tarih zorunludur (YYYY-MM-DD)'}), 400

    try:
        date_obj = datetime.strptime(tarih_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Geçersiz tarih formatı'}), 400

    # 2. Yemek Listesini Al (String olarak gelir, listeye çeviririz)
    # Örn: "Kuru Fasulye, Pilav, Cacık" -> ["Kuru Fasulye", "Pilav", "Cacık"]
    yemekler_str = request.form.get('yemekler')
    yemek_listesi = []
    if yemekler_str:
        yemek_listesi = [y.strip() for y in yemekler_str.split(',')]

    # 3. Resim İşlemleri
    filename = None
    if 'resim' in request.files:
        file = request.files['resim']
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"menu_{tarih_str}.{ext}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

    # 4. Veritabanı İşlemi (Varsa Güncelle, Yoksa Ekle)
    menu = Menu.query.filter_by(tarih=date_obj).first()

    if menu:
        # --- GÜNCELLEME ---
        if yemek_listesi:  # Eğer yeni yemek listesi girildiyse güncelle
            menu.yemekler = yemek_listesi

        if filename:  # Eğer yeni resim yüklendiyse güncelle
            menu.resim_yolu = filename

        message = 'Menü başarıyla güncellendi.'
    else:
        # --- YENİ KAYIT ---
        if not yemek_listesi:
            return jsonify({'error': 'Yeni menü oluştururken yemek listesi girilmelidir.'}), 400

        # Modelindeki __init__ yapısına uygun (tarih, yemekler, resim_yolu)
        menu = Menu(tarih=date_obj, yemekler=yemek_listesi, resim_yolu=filename)
        db.session.add(menu)
        message = 'Yeni menü oluşturuldu.'

    db.session.commit()
    return jsonify({'message': message, 'menu': menu.to_dict()}), 200


# ==============================================================================
# GEÇMİŞ MENÜLER LİSTESİ (FİLTRELEME)
# ==============================================================================

@admin_bp.route('/menus/list', methods=['GET'])
@admin_required
def list_all_menus():
    """Tüm menüleri listeler, sıralar ve sayfalar."""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    # Varsayılan olarak en yeni tarih en üstte
    menus_query = Menu.query.order_by(desc(Menu.tarih))

    pagination = menus_query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'menus': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


# ==============================================================================
# YORUM YÖNETİMİ
# ==============================================================================

@admin_bp.route('/comments', methods=['GET'])
@admin_required
def list_comments():
    """Son yorumları listeler (Moderasyon için)"""
    sort_by = request.args.get('sortBy', 'all')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    query = Comment.query

    if sort_by == 'reported_comments':
        query = query.filter(Comment.is_report == True).order_by(desc(Comment.created_at))
    else:
        query = query.order_by(desc(Comment.created_at))

    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    return jsonify({
        'comments': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200

@admin_bp.route('/comments/<comment_id>/false_report', methods=['POST'])
@admin_required
def false_report(comment_id):
    """Yorum şikayetini reddetmek"""

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Yorum bulunamadı'}), 404

    if comment.is_report:
        comment.is_report = False
    else:
        return jsonify({'message': 'Bu yorum zaten şikayet edilmemiş'}), 400

    db.session.commit()
    return jsonify({'message': 'Şikayet reddedildi'}), 200


@admin_bp.route('/comments/<comment_id>', methods=['DELETE'])
@admin_required
def delete_comment(comment_id):
    """Uygunsuz yorumu siler"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Yorum bulunamadı'}), 404

    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Yorum silindi'}), 200


@admin_bp.route('/comments/<comment_id>', methods=['PUT'])
@admin_required
def edit_comment(comment_id):
    """Yorum metnini düzenler (Sansürleme vb. için)"""
    data = request.get_json()
    new_text = data.get('yorum_metni')

    if not new_text:
        return jsonify({'error': 'Metin boş olamaz'}), 400

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Yorum bulunamadı'}), 404

    comment.yorum_metni = new_text
    db.session.commit()
    return jsonify({'message': 'Yorum güncellendi', 'comment': comment.to_dict()}), 200


@admin_bp.route('/comments/<comment_id>/reset-likes', methods=['POST'])
@admin_required
def reset_comment_likes(comment_id):
    """Bir yoruma gelen beğeni ve beğenmemeleri sıfırlar"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Yorum bulunamadı'}), 404

    # SQLAlchemy relationship üzerinden temizleme
    # cascade="all, delete-orphan" olduğu için listeyi temizlemek yeterli olabilir
    # ama en garantisi ilişkili like'ları silmektir.

    # Yöntem 1: İlişkiyi boşalt (SQLAlchemy otomatik silerse)
    comment.likes = []

    # Yöntem 2: Manuel silme (Eğer ilişki ayarı yetmezse bu devreye girer)
    # db.session.query(CommentLike).filter_by(comment_id=comment_id).delete()

    db.session.commit()
    return jsonify({'message': 'Beğeniler sıfırlandı'}), 200


# ==============================================================================
# KULLANICI YÖNETİMİ
# ==============================================================================

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """Kullanıcıları listeler"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    users = User.query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'users': [u.to_dict() for u in users.items],
        'total': users.total
    }), 200


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Kullanıcıyı siler ve mailini kara listeye ekler"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

    if user.rol == 'admin':
        return jsonify({'error': 'Yöneticiler silinemez'}), 403

    # 1. Kullanıcının mailini al
    email_to_ban = user.email

    # 2. Maili Kara Listeye Ekle (Eğer zaten yoksa)
    if not BannedUser.query.filter_by(email=email_to_ban).first():
        banned_user = BannedUser(email=email_to_ban)
        db.session.add(banned_user)

    # 3. Kullanıcıyı ve verilerini sil
    db.session.delete(user)

    # Hepsini tek seferde kaydet
    db.session.commit()

    return jsonify({'message': f'Kullanıcı silindi ve {email_to_ban} adresi engellendi.'}), 200


# ==============================================================================
# ADMIN PROFİL
# ==============================================================================

@admin_bp.route('/me', methods=['GET'])
@admin_required
def admin_profile():
    """Admin 'Ben kimim?' kontrolü"""
    # Middleware sayesinde buraya sadece adminler girebilir
    return jsonify({
        'message': 'Admin oturumu aktif',
        'rol': 'admin',
        'server_time': datetime.now().isoformat()
    }), 200


# ==============================================================================
# YASAKLI KULLANICI YÖNETİMİ (BAN SİSTEMİ)
# ==============================================================================

@admin_bp.route('/banned-users', methods=['GET'])
@admin_required
def list_banned_users():
    """Yasaklanmış mail adreslerini listeler"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    # En son yasaklanan en üstte görünsün
    query = BannedUser.query.order_by(desc(BannedUser.ban_date))
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'banned_users': [{
            'id': b.id,  # Yasağı kaldırmak için bu ID lazım olacak
            'email': b.email,
            'ban_date': b.ban_date.isoformat()
        } for b in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    }), 200


@admin_bp.route('/banned-users/<int:ban_id>', methods=['DELETE'])
@admin_required
def unban_user(ban_id):
    """
    ID'si verilen yasağı kaldırır.
    Böylece o mail adresi tekrar kayıt olabilir.
    """
    banned_record = BannedUser.query.get(ban_id)

    if not banned_record:
        return jsonify({'error': 'Yasaklı kaydı bulunamadı'}), 404

    email = banned_record.email  # Bilgi mesajı için saklayalım

    db.session.delete(banned_record)
    db.session.commit()

    return jsonify({
        'message': f'{email} adresinin yasağı kaldırıldı. Artık tekrar kayıt olabilir.'
    }), 200