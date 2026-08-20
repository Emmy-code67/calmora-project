from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import TherapyAppointment
from app.therapy.forms import TherapyForm
from app.utils import log_activity, apply_date_range, get_page_arg
from app.export import export_csv, export_excel, export_pdf

therapy_bp = Blueprint("therapy", __name__, template_folder="../templates/therapy")


def _build_filtered_query():
    query = TherapyAppointment.query.filter_by(user_id=current_user.id)

    keyword = request.args.get("q")
    if keyword:
        query = query.filter(
            (TherapyAppointment.therapist_name.ilike(f"%{keyword}%"))
            | (TherapyAppointment.notes.ilike(f"%{keyword}%"))
            | (TherapyAppointment.location.ilike(f"%{keyword}%"))
        )

    status = request.args.get("status")
    if status:
        query = query.filter(TherapyAppointment.status == status)

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        query = apply_date_range(query, TherapyAppointment, "appointment_date", date_from=datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        query = apply_date_range(query, TherapyAppointment, "appointment_date", date_to=datetime.strptime(date_to, "%Y-%m-%d").date())

    sort = request.args.get("sort", "-appointment_date")
    sort_field = sort.lstrip("-")
    sort_column = getattr(TherapyAppointment, sort_field, TherapyAppointment.appointment_date)
    query = query.order_by(sort_column.desc() if sort.startswith("-") else sort_column.asc())

    return query


@therapy_bp.route("/")
@login_required
def list_appointments():
    query = _build_filtered_query()
    page = get_page_arg()
    pagination = query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)
    return render_template(
        "therapy/list.html", pagination=pagination, appointments=pagination.items,
        statuses=TherapyAppointment.STATUSES,
    )


@therapy_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_appointment():
    form = TherapyForm(appointment_date=date.today(), status="scheduled")
    if form.validate_on_submit():
        appt = TherapyAppointment(
            user_id=current_user.id, therapist_name=form.therapist_name.data, session_type=form.session_type.data,
            appointment_date=form.appointment_date.data, appointment_time=form.appointment_time.data,
            duration_minutes=form.duration_minutes.data or 50, location=form.location.data,
            status=form.status.data, reminder_enabled=form.reminder_enabled.data, notes=form.notes.data,
        )
        db.session.add(appt)
        db.session.commit()
        log_activity("therapy_created", f"Scheduled appointment with {appt.therapist_name}")
        flash("Appointment scheduled.", "success")
        return redirect(url_for("therapy.list_appointments"))
    return render_template("therapy/form.html", form=form, title="Schedule Appointment")


@therapy_bp.route("/<int:appt_id>/edit", methods=["GET", "POST"])
@login_required
def edit_appointment(appt_id):
    appt = TherapyAppointment.query.filter_by(id=appt_id, user_id=current_user.id).first_or_404()
    form = TherapyForm(obj=appt)
    if form.validate_on_submit():
        form.populate_obj(appt)
        db.session.commit()
        log_activity("therapy_updated", f"Updated appointment #{appt.id}")
        flash("Appointment updated.", "success")
        return redirect(url_for("therapy.list_appointments"))
    return render_template("therapy/form.html", form=form, title="Edit Appointment")


@therapy_bp.route("/<int:appt_id>/delete", methods=["POST"])
@login_required
def delete_appointment(appt_id):
    appt = TherapyAppointment.query.filter_by(id=appt_id, user_id=current_user.id).first_or_404()
    db.session.delete(appt)
    db.session.commit()
    log_activity("therapy_deleted", f"Deleted appointment #{appt_id}")
    flash("Appointment deleted.", "info")
    return redirect(url_for("therapy.list_appointments"))


@therapy_bp.route("/export/<fmt>")
@login_required
def export_appointments(fmt):
    items = _build_filtered_query().all()
    rows = [
        {
            "date": a.appointment_date.isoformat(), "time": a.appointment_time.strftime("%H:%M"),
            "therapist": a.therapist_name, "type": a.session_type or "", "duration_minutes": a.duration_minutes,
            "location": a.location or "", "status": a.status,
        }
        for a in items
    ]
    if fmt == "csv":
        return export_csv(rows, "calmora_therapy_appointments")
    if fmt == "xlsx":
        return export_excel(rows, "calmora_therapy_appointments", "Therapy")
    if fmt == "pdf":
        return export_pdf(rows, "calmora_therapy_appointments", "Calmora - Therapy Appointments Report")
    flash("Unknown export format.", "danger")
    return redirect(url_for("therapy.list_appointments"))
