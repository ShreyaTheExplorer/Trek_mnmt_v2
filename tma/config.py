import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tma-super-secret-key-mad2-2026')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'tma-jwt-secret-key-mad2-2026')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)) # 24 hours

    # Database: SQLite tma.db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'tma.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cache & Celery Redis URL
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_URL = os.environ.get('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/2')

    # Mail Settings (read from env with defaults)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 1025))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ('true', '1')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('true', '1')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@tma.com')

    # Webhook Settings
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'http://localhost:5000/webhook')

    # Exports Directory
    EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')

    # Admin Seeding Settings (strictly admin@tma.com / admin123)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@tma.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    ADMIN_NAME = os.environ.get('ADMIN_NAME', 'System Administrator')
