"""
Database configuration for SPA Management System
Uses MySQL via XAMPP. Settings are loaded from settings.ini if present.
"""
import mysql.connector
from mysql.connector import Error
import bcrypt
import configparser
import os

# ─── DB CONFIG ──────────────────────────────────────────────
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',        # XAMPP default: empty password
    'database': 'spa_system',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True,
}

# Load overrides from settings.ini if it exists
_settings_file = os.path.join(os.path.dirname(__file__), 'settings.ini')
if os.path.exists(_settings_file):
    _cfg = configparser.ConfigParser()
    _cfg.read(_settings_file, encoding='utf-8')
    if _cfg.has_section('database'):
        DB_CONFIG['host']     = _cfg.get('database', 'host',     fallback=DB_CONFIG['host'])
        DB_CONFIG['port']     = int(_cfg.get('database', 'port', fallback=str(DB_CONFIG['port'])))
        DB_CONFIG['user']     = _cfg.get('database', 'user',     fallback=DB_CONFIG['user'])
        DB_CONFIG['password'] = _cfg.get('database', 'password', fallback=DB_CONFIG['password'])
        DB_CONFIG['database'] = _cfg.get('database', 'database', fallback=DB_CONFIG['database'])


def get_connection():
    """Return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"Неуспешно свързване с базата данни: {e}")


def test_connection():
    """Test if DB connection works."""
    try:
        conn = get_connection()
        conn.close()
        return True, "Успешно свързване"
    except ConnectionError as e:
        return False, str(e)


# ─── AUTH HELPERS ────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def authenticate_user(username: str, password: str):
    """Returns user dict if credentials valid, else None."""
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password(password, user['password_hash']):
            return user
        return None
    except Exception:
        return None
