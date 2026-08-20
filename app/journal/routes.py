from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import JournalEntry
from app.journal.forms import JournalForm
from app.utils import log_activity, apply_date_range, get_page_arg
from app.export import export_csv, export_excel, export_pdf

journal_bp = Blueprint("journal", __name__, template_folder="../templates/journal")


def _build_filtered_query():
    query = JournalEntry.query.filter_by(user_id=current_user.id)

    keyword = request.args.get("q")
    if keyword:
        query = query.filter(
            (JournalEntry.title.ilike(f"%{keyword}%"))
            | (JournalEntry.content.ilike(f"%{keyword}%"))
            | (JournalEntry.tags.ilike(f"%{keyword}%"))
        )

    mood_tag = request.args.get("mood_tag")
    if mood_tag:
        query = query.filter(JournalEntry.mood_tag == mood_tag)

    if request.args.get("favorites_only") == "1":
        query = query.filter(JournalEntry.is_favorite.is_(True))

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        query = apply_date_range(query, JournalEntry, "entry_date", date_from=datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        query = apply_date_range(query, JournalEntry, "entry_date", date_to=datetime.strptime(date_to, "%Y-%m-%d").date())

    sort = request.args.get("sort", "-entry_date")
    sort_field = sort.lstrip("-")
    sort_column = getattr(JournalEntry, sort_field, JournalEntry.entry_date)
    query = query.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    return query


@journal_bp.route("/")
@login_required
def list_entries():
    query = _build_filtered_query()
    page = get_page_arg()
    pagination = query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)
    from app.models import MoodEntry
    return render_template(
        "journal/list.html", pagination=pagination, entries=pagination.items, mood_types=MoodEntry.MOOD_TYPES
    )


@journal_bp.route("/<int:entry_id>")
@login_required
def view_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    return render_template("journal/view.html", entry=entry)


@journal_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_entry():
    form = JournalForm(entry_date=date.today())
    if form.validate_on_submit():
        entry = JournalEntry(
            user_id=current_user.id,
            entry_date=form.entry_date.data,
            title=form.title.data,
            content=form.content.data,
            mood_tag=form.mood_tag.data or None,
            tags=form.tags.data,
            is_favorite=form.is_favorite.data,
        )
        db.session.add(entry)
        db.session.commit()
        log_activity("journal_created", f"New journal entry: {entry.title}")
        flash("Journal entry saved.", "success")
        return redirect(url_for("journal.list_entries"))
    return render_template("journal/form.html", form=form, title="New Journal Entry")


@journal_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    form = JournalForm(obj=entry)
    if form.validate_on_submit():
        form.populate_obj(entry)
        entry.mood_tag = form.mood_tag.data or None
        db.session.commit()
        log_activity("journal_updated", f"Updated journal entry #{entry.id}")
        flash("Journal entry updated.", "success")
        return redirect(url_for("journal.view_entry", entry_id=entry.id))
    return render_template("journal/form.html", form=form, title="Edit Journal Entry")


@journal_bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    log_activity("journal_deleted", f"Deleted journal entry #{entry_id}")
    flash("Journal entry deleted.", "info")
    return redirect(url_for("journal.list_entries"))


@journal_bp.route("/<int:entry_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    entry.is_favorite = not entry.is_favorite
    db.session.commit()
    return redirect(request.referrer or url_for("journal.list_entries"))


@journal_bp.route("/export/<fmt>")
@login_required
def export_entries(fmt):
    entries = _build_filtered_query().all()
    rows = [
        {
            "date": e.entry_date.isoformat(),
            "title": e.title,
            "mood_tag": e.mood_tag or "",
            "tags": e.tags or "",
            "favorite": "Yes" if e.is_favorite else "No",
            "content": (e.content[:200] + "...") if len(e.content) > 200 else e.content,
        }
        for e in entries
    ]
    if fmt == "csv":
        return export_csv(rows, "calmora_journal_entries")
    if fmt == "xlsx":
        return export_excel(rows, "calmora_journal_entries", "Journal")
    if fmt == "pdf":
        return export_pdf(rows, "calmora_journal_entries", "Calmora - Journal Report")
    flash("Unknown export format.", "danger")
    return redirect(url_for("journal.list_entries"))
