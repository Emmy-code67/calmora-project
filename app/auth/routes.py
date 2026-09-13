"""
Calmora - Auth Routes
---------------------
Handles registration, login/logout, and profile/password management.
"""

import os
import uuid
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import User
from app.auth.forms import RegisterForm, LoginForm, ProfileForm, ChangePasswordForm
from app.utils import log_activity

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip(),
            age=form.age.data,
            gender=form.gender.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_activity("user_registered", f"New account: {user.username}", user_id=user.id)
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username.data.strip()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active_account:
                flash("This account has been deactivated. Contact an administrator.", "danger")
                return redirect(url_for("auth.login"))
            login_user(user, remember=form.remember_me.data)
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            log_activity("user_login", f"{user.username} logged in")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        flash("Invalid username/email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_activity("user_logout", f"{current_user.username} logged out")
    logout_user()
    flash("You have been logged out. See you soon!", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.email = form.email.data.strip().lower()
        current_user.bio = form.bio.data
        current_user.timezone = form.timezone.data

        file = form.avatar.data
        if file:
            # On serverless platforms (Vercel) the filesystem is read-only
            # outside /tmp, so writing an uploaded avatar to disk will fail.
            # Rather than crash the whole request, we catch that and let the
            # user know their other profile changes still saved. A production
            # deployment should point this at a cloud bucket (e.g. Supabase
            # Storage) instead of local disk — see UPLOAD_FOLDER in config.py.
            try:
                ext = os.path.splitext(secure_filename(file.filename))[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                current_user.avatar = filename
            except OSError:
                flash(
                    "Your other changes were saved, but profile picture uploads aren't "
                    "available on this deployment yet.",
                    "warning",
                )

        db.session.commit()
        log_activity("profile_updated", f"{current_user.username} updated profile")
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form)


@auth_bp.route("/profile/password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            log_activity("password_changed", f"{current_user.username} changed password")
            flash("Password updated successfully.", "success")
            return redirect(url_for("auth.profile"))

    return render_template("auth/change_password.html", form=form)


@auth_bp.route("/theme/toggle", methods=["POST"])
@login_required
def toggle_theme():
    current_user.theme_pref = "dark" if current_user.theme_pref == "light" else "light"
    db.session.commit()
    return {"theme": current_user.theme_pref}
