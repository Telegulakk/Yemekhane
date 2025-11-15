import os
from app import create_app
from app.extensions import db

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    with app.app_context():
        # İlk çalıştırmada tabloları oluştur
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5000)