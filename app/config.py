import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

APP_ENV = os.getenv('CAREERAI_ENV', 'development').lower()
SECRET = os.getenv('CAREERAI_SECRET', '')
if APP_ENV == 'production' and len(SECRET) < 32:
    raise RuntimeError('CAREERAI_SECRET must be set to a random value of at least 32 characters in production.')
if not SECRET:
    SECRET = 'dev-only-change-this-careerai-secret-please'

DB_PATH = Path(os.getenv('CAREERAI_DB_PATH', str(DATA_DIR / 'careerai.db')))
UPLOAD_DIR = Path(os.getenv('CAREERAI_UPLOAD_DIR', str(DATA_DIR / 'uploads')))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_MB = int(os.getenv('CAREERAI_MAX_UPLOAD_MB', '5'))
ALLOWED_ORIGINS = [x.strip() for x in os.getenv('CAREERAI_ALLOWED_ORIGINS', 'http://127.0.0.1:8000,http://localhost:8000').split(',') if x.strip()]
COOKIE_SECURE = APP_ENV == 'production'
