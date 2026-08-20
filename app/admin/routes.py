"""
Calmora - Admin Blueprint
-------------------------
Restricted to users with role == 'admin'. Provides a system-wide dashboard,
user management (activate/deactivate, promote/demote), and an activity log
viewer for monitoring platform usage.
"""

from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, ActivityLog, MoodEntry, JournalEntry, Symptom, Medication, TherapyAppointment, Habit
from app.utils import admin_required, log_activity, get_page_arg

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active_account=True).count()
    admins = User.query.filter_by(role="admin").count()

    week_ago = date.today() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()

    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "admins": admins,
        "new_users_week": new_users_week,
        "total_moods": MoodEntry.query.count(),
        "total_journals": JournalEntry.query.count(),
        "total_symptoms": Symptom.query.count(),
        "total_medications": Medication.query.count(),
        "total_appointments": TherapyAppointment.query.count(),
        "total_habits": Habit.query.count(),
    }

    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(15).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template("admin/dashboard.html", stats=stats, recent_activity=recent_activity, recent_users=recent_users)


@admin_bp.route("/users")
@login_required
@admin_required
def user_list():
    query = User.query
    keyword = request.args.get("q")
    if keyword:
        query = query.filter(
            (User.username.ilike(f"%{keyword}%")) | (User.email.ilike(f"%{keyword}%")) | (User.full_name.ilike(f"%{keyword}%"))
        )
    role = request.args.get("role")
    if role:
        query = query.filter_by(role=role)

    query = query.order_by(User.created_at.desc())
    page = get_page_arg()
    pagination = query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)
    return render_template("admin/users.html", pagination=pagination, users=pagination.items)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin.user_list"))
    user.is_active_account = not user.is_active_account
    db.session.commit()
    log_activity("admin_toggle_user", f"{'Activated' if user.is_active_account else 'Deactivated'} {user.username}")
    flash(f"{user.username} has been {'activated' if user.is_active_account else 'deactivated'}.", "success")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/toggle-role", methods=["POST"])
@login_required
@admin_required
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot change your own role.", "warning")
        return redirect(url_for("admin.user_list"))
    user.role = "user" if user.role == "admin" else "admin"
    db.session.commit()
    log_activity("admin_toggle_role", f"Set {user.username} role to {user.role}")
    flash(f"{user.username}'s role is now {user.role}.", "success")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for("admin.user_list"))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    log_activity("admin_delete_user", f"Deleted user {username}")
    flash(f"User {username} deleted.", "info")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/activity")
@login_required
@admin_required
def activity_log():
    query = ActivityLog.query.order_by(ActivityLog.created_at.desc())
    keyword = request.args.get("q")
    if keyword:
        query = query.filter(ActivityLog.action.ilike(f"%{keyword}%") | ActivityLog.details.ilike(f"%{keyword}%"))
    page = get_page_arg()
    pagination = query.paginate(page=page, per_page=25, error_out=False)
    return render_template("admin/activity.html", pagination=pagination, logs=pagination.items)
