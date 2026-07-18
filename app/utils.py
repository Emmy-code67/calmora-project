"""
Calmora - Shared Utilities
--------------------------
Small reusable helpers used across blueprints: role-based access control,
activity logging for the admin dashboard, and generic filter/pagination
helpers so every module (mood, journal, symptoms...) doesn't reimplement
the same query logic.
"""

from functools import wraps
from flask import abort, request
from flask_login import current_user

from app.extensions import db
from app.models import ActivityLog


def admin_required(view_func):
    """Restrict a view to users with role == 'admin'."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def log_activity(action: str, details: str = "", user_id=None):
    """Write a row to the ActivityLog table (used by the admin dashboard)."""
    try:
        uid = user_id or (current_user.id if current_user.is_authenticated else None)
        entry = ActivityLog(
            user_id=uid,
            action=action,
            details=details,
            ip_address=request.remote_addr if request else None,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()


def apply_date_range(query, model, field_name, date_from=None, date_to=None):
    """Apply optional date_from / date_to filters to a query."""
    column = getattr(model, field_name)
    if date_from:
        query = query.filter(column >= date_from)
    if date_to:
        query = query.filter(column <= date_to)
    return query


def get_page_arg():
    try:
        return max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        return 1
