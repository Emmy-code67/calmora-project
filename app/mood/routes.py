"""
Calmora - Mood Tracking Blueprint
---------------------------------
Full CRUD for mood entries plus search/filter/sort/pagination and exports.
This module is the template pattern repeated (with variations) across
journal, symptoms, medications, therapy, and habits.
"""

from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import MoodEntry
from app.mood.forms import MoodForm
from app.utils import log_activity, apply_date_range, get_page_arg
from app.export import export_csv, export_excel, export_pdf

mood_bp = Blueprint("mood", __name__, template_folder="../templates/mood")


def _build_filtered_query():
    query = MoodEntry.query.filter_by(user_id=current_user.id)

    mood_type = request.args.get("mood_type")
    if mood_type:
        query = query.filter(MoodEntry.mood_type == mood_type)

    keyword = request.args.get("q")
    if keyword:
        query = query.filter(MoodEntry.notes.ilike(f"%{keyword}%"))

    min_stress = request.args.get("min_stress", type=int)
    if min_stress:
        query = query.filter(MoodEntry.stress_level >= min_stress)

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        query = apply_date_range(query, MoodEntry, "entry_date", date_from=datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        query = apply_date_range(query, MoodEntry, "entry_date", date_to=datetime.strptime(date_to, "%Y-%m-%d").date())

    sort = request.args.get("sort", "-entry_date")
    sort_field = sort.lstrip("-")
    sort_column = getattr(MoodEntry, sort_field, MoodEntry.entry_date)
    query = query.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    return query


@mood_bp.route("/")
@login_required
def list_moods():
    query = _build_filtered_query()
    page = get_page_arg()
    pagination = query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)
    return render_template(
        "mood/list.html",
        pagination=pagination,
        moods=pagination.items,
        mood_types=MoodEntry.MOOD_TYPES,
    )


@mood_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_mood():
    form = MoodForm(entry_date=date.today())
    if form.validate_on_submit():
        entry = MoodEntry(
            user_id=current_user.id,
            entry_date=form.entry_date.data,
            mood_type=form.mood_type.data,
            intensity=form.intensity.data,
            stress_level=form.stress_level.data,
            sleep_hours=form.sleep_hours.data,
            notes=form.notes.data,
        )
        db.session.add(entry)
        db.session.commit()
        log_activity("mood_created", f"Logged mood: {entry.mood_type}")
        flash("Mood entry saved.", "success")
        return redirect(url_for("mood.list_moods"))
    return render_template("mood/form.html", form=form, title="Log a Mood")


@mood_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_mood(entry_id):
    entry = MoodEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    form = MoodForm(obj=entry)
    if form.validate_on_submit():
        form.populate_obj(entry)
        db.session.commit()
        log_activity("mood_updated", f"Updated mood entry #{entry.id}")
        flash("Mood entry updated.", "success")
        return redirect(url_for("mood.list_moods"))
    return render_template("mood/form.html", form=form, title="Edit Mood Entry")


@mood_bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_mood(entry_id):
    entry = MoodEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    log_activity("mood_deleted", f"Deleted mood entry #{entry_id}")
    flash("Mood entry deleted.", "info")
    return redirect(url_for("mood.list_moods"))


@mood_bp.route("/export/<fmt>")
@login_required
def export_moods(fmt):
    entries = _build_filtered_query().all()
    rows = [
        {
            "date": e.entry_date.isoformat(),
            "mood_type": e.mood_type,
            "intensity": e.intensity,
            "stress_level": e.stress_level,
            "sleep_hours": e.sleep_hours,
            "emotional_score": e.emotional_score,
            "notes": e.notes or "",
        }
        for e in entries
    ]
    if fmt == "csv":
        return export_csv(rows, "calmora_mood_entries")
    if fmt == "xlsx":
        return export_excel(rows, "calmora_mood_entries", "Mood Entries")
    if fmt == "pdf":
        return export_pdf(rows, "calmora_mood_entries", "Calmora - Mood Entries Report")
    flash("Unknown export format.", "danger")
    return redirect(url_for("mood.list_moods"))
