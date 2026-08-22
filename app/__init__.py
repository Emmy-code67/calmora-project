"""
Calmora - Application Factory
-----------------------------
The `create_app()` factory pattern lets us build multiple instances of
the app (e.g. one for tests, one for production) with different config,
and avoids circular imports because extensions are only bound to `app`
here, after all modules are safely importable.
"""

import os
from datetime import datetime, date

from flask import Flask, render_template, request
from flask_login import current_user

from config import config_map
from app.extensions import db, login_manager, csrf, migrate


def _ensure_dir(path):
    """Create a directory if possible, but never crash if it can't be.

    Serverless platforms (Vercel, AWS Lambda, etc.) deploy the app onto a
    read-only filesystem outside of /tmp. Folders that aren't already part
    of the deployed bundle (e.g. an empty `instance/` directory, which git
    doesn't track) can't be created at runtime there. Locally, and on
    traditional hosts with a writable disk, this behaves exactly like a
    normal os.makedirs(exist_ok=True) call.
    """
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # These are no-ops if the filesystem is read-only (e.g. on Vercel) — see
    # _ensure_dir's docstring. On Vercel you should be using Postgres/Supabase
    # (DATABASE_URL) rather than SQLite, so a missing instance/ folder is fine.
    _ensure_dir(app.instance_path)
    _ensure_dir(app.config["UPLOAD_FOLDER"])

    # --- Bind extensions ---------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # --- Register blueprints -------------------------------------------------
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.mood.routes import mood_bp
    from app.journal.routes import journal_bp
    from app.symptoms.routes import symptoms_bp
    from app.medications.routes import medications_bp
    from app.therapy.routes import therapy_bp
    from app.habits.routes import habits_bp
    from app.calendar_view.routes import calendar_bp
    from app.analytics.routes import analytics_bp
    from app.search.routes import search_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(mood_bp, url_prefix="/mood")
    app.register_blueprint(journal_bp, url_prefix="/journal")
    app.register_blueprint(symptoms_bp, url_prefix="/symptoms")
    app.register_blueprint(medications_bp, url_prefix="/medications")
    app.register_blueprint(therapy_bp, url_prefix="/therapy")
    app.register_blueprint(habits_bp, url_prefix="/habits")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(search_bp, url_prefix="/search")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # --- User loader ---------------------------------------------------------
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Template helpers ---------------------------------------------------
    @app.template_global()
    def merge_args(**overrides):
        """Merge current request query args with overrides (drop None values).
        Used by pagination/sorting links so filters persist across page changes."""
        args = request.args.to_dict(flat=True)
        args.update(overrides)
        return {k: v for k, v in args.items() if v is not None and v != ""}

    # --- Context processors ---------------------------------------------------
    @app.context_processor
    def inject_globals():
        unread_count = 0
        if current_user.is_authenticated:
            from app.models import Notification

            unread_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
        return {
            "current_year": datetime.utcnow().year,
            "today": date.today(),
            "unread_notification_count": unread_count,
            "app_name": "Calmora",
        }

    # --- Error handlers ---------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # --- CLI commands ---------------------------------------------------------
    from app.cli import register_cli_commands

    register_cli_commands(app)

    return app
