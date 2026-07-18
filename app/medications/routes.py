from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Medication, MedicationLog
from app.medications.forms import MedicationForm, MedicationLogForm
from app.utils import log_activity, get_page_arg
from app.export import export_csv, export_excel, export_pdf

medications_bp = Blueprint("medications", __name__, template_folder="../templates/medications")


def _build_filtered_query():
    query = Medication.query.filter_by(user_id=current_user.id)

    keyword = request.args.get("q")
    if keyword:
        query = query.filter(
            (Medication.name.ilike(f"%{keyword}%")) | (Medication.notes.ilike(f"%{keyword}%"))
        )

    status = request.args.get("status")
    if status == "active":
        query = query.filter(Medication.active.is_(True))
    elif status == "inactive":
        query = query.filter(Medication.active.is_(False))

    sort = request.args.get("sort", "-start_date")
    sort_field = sort.lstrip("-")
    sort_column = getattr(Medication, sort_field, Medication.start_date)
    query = query.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    return query


@medications_bp.route("/")
@login_required
def list_medications():
    query = _build_filtered_query()
    page = get_page_arg()
    pagination = query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)
    return render_template("medications/list.html", pagination=pagination, medications=pagination.items)


@medications_bp.route("/<int:med_id>")
@login_required
def view_medication(med_id):
    med = Medication.query.filter_by(id=med_id, user_id=current_user.id).first_or_404()
    log_form = MedicationLogForm(log_date=date.today())
    recent_logs = MedicationLog.query.filter_by(medication_id=med.id).order_by(MedicationLog.log_date.desc()).limit(30).all()
    return render_template("medications/view.html", medication=med, log_form=log_form, recent_logs=recent_logs)


@medications_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_medication():
    form = MedicationForm(start_date=date.today())
    if form.validate_on_submit():
        med = Medication(
            user_id=current_user.id, name=form.name.data, dosage=form.dosage.data, frequency=form.frequency.data,
            start_date=form.start_date.data, end_date=form.end_date.data, prescribing_doctor=form.prescribing_doctor.data,
            reminder_times=form.reminder_times.data, notes=form.notes.data, active=form.active.data,
        )
        db.session.add(med)
        db.session.commit()
        log_activity("medication_created", f"Added medication: {med.name}")
        flash("Medication added.", "success")
        return redirect(url_for("medications.list_medications"))
    return render_template("medications/form.html", form=form, title="Add Medication")


@medications_bp.route("/<int:med_id>/edit", methods=["GET", "POST"])
@login_required
def edit_medication(med_id):
    med = Medication.query.filter_by(id=med_id, user_id=current_user.id).first_or_404()
    form = MedicationForm(obj=med)
    if form.validate_on_submit():
        form.populate_obj(med)
        db.session.commit()
        log_activity("medication_updated", f"Updated medication #{med.id}")
        flash("Medication updated.", "success")
        return redirect(url_for("medications.list_medications"))
    return render_template("medications/form.html", form=form, title="Edit Medication")


@medications_bp.route("/<int:med_id>/delete", methods=["POST"])
@login_required
def delete_medication(med_id):
    med = Medication.query.filter_by(id=med_id, user_id=current_user.id).first_or_404()
    db.session.delete(med)
    db.session.commit()
    log_activity("medication_deleted", f"Deleted medication #{med_id}")
    flash("Medication deleted.", "info")
    return redirect(url_for("medications.list_medications"))


@medications_bp.route("/<int:med_id>/log", methods=["POST"])
@login_required
def log_dose(med_id):
    med = Medication.query.filter_by(id=med_id, user_id=current_user.id).first_or_404()
    form = MedicationLogForm()
    if form.validate_on_submit():
        entry = MedicationLog(
            medication_id=med.id, user_id=current_user.id, log_date=form.log_date.data,
            status=form.status.data, notes=form.notes.data,
            taken_at=datetime.utcnow() if form.status.data == "taken" else None,
        )
        db.session.add(entry)
        db.session.commit()
        log_activity("medication_dose_logged", f"{med.name}: {form.status.data}")
        flash("Dose logged.", "success")
    return redirect(url_for("medications.view_medication", med_id=med.id))


@medications_bp.route("/export/<fmt>")
@login_required
def export_medications(fmt):
    items = _build_filtered_query().all()
    rows = [
        {
            "name": m.name, "dosage": m.dosage or "", "frequency": m.frequency or "",
            "start_date": m.start_date.isoformat() if m.start_date else "",
            "end_date": m.end_date.isoformat() if m.end_date else "",
            "active": "Yes" if m.active else "No",
            "adherence_rate": f"{m.adherence_rate}%" if m.adherence_rate is not None else "N/A",
            "prescribing_doctor": m.prescribing_doctor or "",
        }
        for m in items
    ]
    if fmt == "csv":
        return export_csv(rows, "calmora_medications")
    if fmt == "xlsx":
        return export_excel(rows, "calmora_medications", "Medications")
    if fmt == "pdf":
        return export_pdf(rows, "calmora_medications", "Calmora - Medications Report")
    flash("Unknown export format.", "danger")
    return redirect(url_for("medications.list_medications"))
