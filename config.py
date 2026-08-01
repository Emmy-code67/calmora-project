"""
Calmora - Application Configuration
------------------------------------
Centralized configuration using the standard Flask config-object pattern.
Educational note: keeping config in one place (instead of scattering
os.environ calls through the codebase) makes it trivial to swap between
Development / Testing / Production setups.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def _normalize_db_url(url: str) -> str:
    """Some providers (Heroku-style) hand out 'postgres://' URLs, but
    SQLAlchemy 1.4+ requires the 'postgresql://' scheme."""
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

class Config:
    """Base configuration shared by every environment."""

    # Secret key used to sign session cookies & CSRF tokens.
    # In production this MUST be overridden via the CALMORA_SECRET_KEY env var.
    SECRET_KEY = os.environ.get("CALMORA_SECRET_KEY", "dev-secret-key-change-me")

    # SQLite database lives inside /instance so it is never committed to VCS.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "CALMORA_DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'calmora.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-WTF CSRF protection is on globally by default; explicit for clarity.
    WTF_CSRF_ENABLED = True

    # Pagination defaults used across all list views.
    ITEMS_PER_PAGE = 10

    # Uploaded avatar images (must live inside app/static so url_for('static', ...) can serve them)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "img", "avatars")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB max upload

    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 14  # 14 days


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
