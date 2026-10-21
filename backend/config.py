# Configuration Settings
# Picture Password Authentication System

import os
import sys
from cryptography.fernet import Fernet

def _get_base_dir():
    """Get writable base directory — exe folder when frozen, project root otherwise"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    """Application configuration"""

    # Flask settings
    _secret = os.environ.get('SECRET_KEY')
    if not _secret:
        import warnings
        warnings.warn(
            "SECRET_KEY environment variable is not set; Flask sessions are insecure.",
            stacklevel=2
        )
    SECRET_KEY = _secret or 'dev-insecure-key-set-SECRET_KEY-env'

    # Database settings (SQLite fallback path — not used when MySQL is active)
    DATABASE_PATH = os.path.join(_get_base_dir(), 'database', 'database.db')

    # Image settings
    AUTH_IMAGES = ['auth1.jpg', 'auth2.jpg', 'auth3.jpg', 'auth4.jpg']
    DECOY_IMAGES = ['decoy1.jpg', 'decoy2.jpg', 'decoy3.jpg']

    # Authentication settings
    TIME_LIMIT_PER_IMAGE = 10  # seconds
    CLICK_TOLERANCE = 20       # pixels
    MAX_WRONG_ATTEMPTS = 2     # wrong clicks before lockout

    # Encryption key — stored in writable location
    _key_path = os.path.join(_get_base_dir(), 'database', 'encryption.key')

    @classmethod
    def _load_or_create_key(cls):
        key_dir = os.path.dirname(cls._key_path)
        os.makedirs(key_dir, exist_ok=True)
        if os.path.exists(cls._key_path):
            with open(cls._key_path, 'rb') as f:
                return f.read()
        key = Fernet.generate_key()
        with open(cls._key_path, 'wb') as f:
            f.write(key)
        return key

    ENCRYPTION_KEY = None  # set below

    # Admin settings
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    UPLOAD_FOLDER = 'frontend/static/images'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Load persistent encryption key
Config.ENCRYPTION_KEY = Config._load_or_create_key()
