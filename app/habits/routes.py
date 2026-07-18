from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Habit, HabitLog
from app.habits.forms import HabitForm
from app.utils import log_activity, get_page_arg
from app.export import export_csv, export_excel, export_pdf

habits_bp = Blueprint("habits", __name__, template_folder="../templates/habits")


def _build_filtered_query():
    query = Habit.query.filter_by(user_id=current_user.id)

    keyword = request.args.get("q")
    if keyword:
        query = query.filter(Habit.name.ilike(f"%{keyword}%"))

    status = request.args.get("status")
    if status == "active":
        query = query.filter(Habit.active.is_(True))
    elif status == "inactive":
        query = query.filter(Habit.active.is_(False))

    frequency = request.args.get("frequency")
    if frequency:
        query = query.filter(Habit.frequency == frequency)

    sort = request.args.get("sort", "-created_at")
    sort_field = sort.lstrip("-")
    sort_column = getattr(Habit, sort_field, Habit.created_at)
    query = query.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    return query


@habits_bp.route("/")
@login_required
def list_habits():
    query = _build_filtered_query()
    page = get_page_arg()
    pagination = query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)

    today = date.today()
    habit_rows = []
    for h in pagination.items:
        today_log = HabitLog.query.filter_by(habit_id=h.id, log_date=today).first()
        habit_rows.append({
            "habit": h,
            "streak": h.current_streak(),
            "rate": h.completion_rate(30),
            "done_today": bool(today_log and today_log.completed),
        })

    return render_template("habits/list.html", pagination=pagination, habit_rows=habit_rows)


@habits_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_habit():
    form = HabitForm()
    if form.validate_on_submit():
        h = Habit(
            user_id=current_user.id, name=form.name.data, description=form.description.data,
            frequency=form.frequency.data, target_count=form.target_count.data,
            color=form.color.data or "#6C63FF", icon=form.icon.data, active=form.active.data,
        )
        db.session.add(h)
        db.session.commit()
        log_activity("habit_created", f"Created habit: {h.name}")
        flash("Habit created.", "success")
        return redirect(url_for("habits.list_habits"))
    return render_template("habits/form.html", form=form, title="Add Habit")


@habits_bp.route("/<int:habit_id>/edit", methods=["GET", "POST"])
@login_required
def edit_habit(habit_id):
    h = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    form = HabitForm(obj=h)
    if form.validate_on_submit():
        form.populate_obj(h)
        db.session.commit()
        log_activity("habit_updated", f"Updated habit #{h.id}")
        flash("Habit updated.", "success")
        return redirect(url_for("habits.list_habits"))
    return render_template("habits/form.html", form=form, title="Edit Habit")


@habits_bp.route("/<int:habit_id>/delete", methods=["POST"])
@login_required
def delete_habit(habit_id):
    h = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    db.session.delete(h)
    db.session.commit()
    log_activity("habit_deleted", f"Deleted habit #{habit_id}")
    flash("Habit deleted.", "info")
    return redirect(url_for("habits.list_habits"))


@habits_bp.route("/<int:habit_id>/checkin", methods=["POST"])
@login_required
def checkin(habit_id):
    h = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    today = date.today()
    log = HabitLog.query.filter_by(habit_id=h.id, log_date=today).first()
    if log:
        log.completed = not log.completed
    else:
        log = HabitLog(habit_id=h.id, user_id=current_user.id, log_date=today, completed=True)
        db.session.add(log)
    db.session.commit()
    log_activity("habit_checkin", f"Checked in habit: {h.name}")
    return redirect(request.referrer or url_for("habits.list_habits"))


@habits_bp.route("/export/<fmt>")
@login_required
def export_habits(fmt):
    items = _build_filtered_query().all()
    rows = [
        {
            "name": h.name, "frequency": h.frequency, "target_count": h.target_count,
            "active": "Yes" if h.active else "No", "current_streak": h.current_streak(),
            "completion_rate_30d": f"{h.completion_rate(30)}%",
        }
        for h in items
    ]
    if fmt == "csv":
        return export_csv(rows, "calmora_habits")
    if fmt == "xlsx":
        return export_excel(rows, "calmora_habits", "Habits")
    if fmt == "pdf":
        return export_pdf(rows, "calmora_habits", "Calmora - Habits Report")
    flash("Unknown export format.", "danger")
    return redirect(url_for("habits.list_habits"))
