from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Symptom
from app.symptoms.forms import SymptomForm
from app.utils import log_activity, apply_date_range, get_page_arg
from app.export import export_csv, export_excel, export_pdf

symptoms_bp = Blueprint("symptoms", __name__, template_folder="../templates/symptoms")


def _build_filtered_query():
    query = Symptom.query.filter_by(user_id=current_user.id)

    keyword = request.args.get("q")
    if keyword:
        query = query.filter(
            (Symptom.name.ilike(f"%{keyword}%"))
            | (Symptom.notes.ilike(f"%{keyword}%"))
            | (Symptom.triggers.ilike(f"%{keyword}%"))
        )

    category = request.args.get("category")
    if category:
        query = query.filter(Symptom.category == category)

    min_severity = request.args.get("min_severity", type=int)
    if min_severity:
        query = query.filter(Symptom.severity >= min_severity)

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        query = apply_date_range(query, Symptom, "entry_date", date_from=datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        query = apply_date_range(query, Symptom, "entry_date", date_to=datetime.strptime(date_to, "%Y-%m-%d").date())

    sort = request.args.get("sort", "-entry_date")
    sort_field = sort.lstrip("-")
    sort_column = getattr(Symptom, sort_field, Symptom.entry_date)
    query = query.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    return query


@symptoms_bp.route("/")
@login_required
def list_symptoms():
    query = _build_filtered_query()
    page = get_page_arg()
    pagination = query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)
    return render_template("symptoms/list.html", pagination=pagination, symptoms=pagination.items)


@symptoms_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_symptom():
    form = SymptomForm(entry_date=date.today())
    if form.validate_on_submit():
        s = Symptom(
            user_id=current_user.id, entry_date=form.entry_date.data, name=form.name.data,
            category=form.category.data, severity=form.severity.data,
            duration_minutes=form.duration_minutes.data, triggers=form.triggers.data, notes=form.notes.data,
        )
        db.session.add(s)
        db.session.commit()
        log_activity("symptom_created", f"Logged symptom: {s.name}")
        flash("Symptom logged.", "success")
        return redirect(url_for("symptoms.list_symptoms"))
    return render_template("symptoms/form.html", form=form, title="Log a Symptom")


@symptoms_bp.route("/<int:symptom_id>/edit", methods=["GET", "POST"])
@login_required
def edit_symptom(symptom_id):
    s = Symptom.query.filter_by(id=symptom_id, user_id=current_user.id).first_or_404()
    form = SymptomForm(obj=s)
    if form.validate_on_submit():
        form.populate_obj(s)
        db.session.commit()
        log_activity("symptom_updated", f"Updated symptom #{s.id}")
        flash("Symptom updated.", "success")
        return redirect(url_for("symptoms.list_symptoms"))
    return render_template("symptoms/form.html", form=form, title="Edit Symptom")


@symptoms_bp.route("/<int:symptom_id>/delete", methods=["POST"])
@login_required
def delete_symptom(symptom_id):
    s = Symptom.query.filter_by(id=symptom_id, user_id=current_user.id).first_or_404()
    db.session.delete(s)
    db.session.commit()
    log_activity("symptom_deleted", f"Deleted symptom #{symptom_id}")
    flash("Symptom deleted.", "info")
    return redirect(url_for("symptoms.list_symptoms"))


@symptoms_bp.route("/export/<fmt>")
@login_required
def export_symptoms(fmt):
    items = _build_filtered_query().all()
    rows = [
        {
            "date": s.entry_date.isoformat(), "name": s.name, "category": s.category or "",
            "severity": s.severity, "duration_minutes": s.duration_minutes or "",
            "triggers": s.triggers or "", "notes": s.notes or "",
        }
        for s in items
    ]
    if fmt == "csv":
        return export_csv(rows, "calmora_symptoms")
    if fmt == "xlsx":
        return export_excel(rows, "calmora_symptoms", "Symptoms")
    if fmt == "pdf":
        return export_pdf(rows, "calmora_symptoms", "Calmora - Symptom Report")
    flash("Unknown export format.", "danger")
    return redirect(url_for("symptoms.list_symptoms"))
