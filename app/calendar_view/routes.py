"""
Calmora - Calendar Blueprint
----------------------------
Renders a FullCalendar-powered view aggregating events from every module
(mood, journal, symptoms, medications, therapy, habits) with color coding,
and exposes a JSON API FullCalendar consumes, plus a drag-and-drop update
endpoint for movable event types (therapy appointments, mood, journal, symptoms).
"""

from datetime import datetime

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import MoodEntry, JournalEntry, Symptom, Medication, TherapyAppointment, Habit, HabitLog
from app.utils import log_activity

calendar_bp = Blueprint("calendar_view", __name__, template_folder="../templates/calendar_view")

EVENT_COLORS = {
    "mood": "#6C63FF",
    "journal": "#00C2A8",
    "symptom": "#FF5A6E",
    "medication": "#FFB020",
    "therapy": "#4C9AFF",
    "habit": "#24C38C",
}


@calendar_bp.route("/")
@login_required
def calendar_home():
    return render_template("calendar_view/calendar.html", event_colors=EVENT_COLORS)


@calendar_bp.route("/events")
@login_required
def events_feed():
    """Returns all calendar-relevant events within the requested date window
    (FullCalendar sends ?start=...&end=... automatically)."""
    uid = current_user.id
    start = request.args.get("start")
    end = request.args.get("end")
    start_date = datetime.fromisoformat(start.split("T")[0]).date() if start else None
    end_date = datetime.fromisoformat(end.split("T")[0]).date() if end else None

    events = []

    moods = MoodEntry.query.filter_by(user_id=uid)
    journals = JournalEntry.query.filter_by(user_id=uid)
    symptoms = Symptom.query.filter_by(user_id=uid)
    appts = TherapyAppointment.query.filter_by(user_id=uid)
    habit_logs = HabitLog.query.filter_by(user_id=uid, completed=True)

    if start_date and end_date:
        moods = moods.filter(MoodEntry.entry_date.between(start_date, end_date))
        journals = journals.filter(JournalEntry.entry_date.between(start_date, end_date))
        symptoms = symptoms.filter(Symptom.entry_date.between(start_date, end_date))
        appts = appts.filter(TherapyAppointment.appointment_date.between(start_date, end_date))
        habit_logs = habit_logs.filter(HabitLog.log_date.between(start_date, end_date))

    for m in moods.all():
        events.append({
            "id": f"mood-{m.id}", "title": f"Mood: {m.mood_type.capitalize()}",
            "start": m.entry_date.isoformat(), "allDay": True,
            "color": EVENT_COLORS["mood"], "extendedProps": {"type": "mood", "editable": True},
        })

    for j in journals.all():
        events.append({
            "id": f"journal-{j.id}", "title": f"Journal: {j.title}",
            "start": j.entry_date.isoformat(), "allDay": True,
            "color": EVENT_COLORS["journal"], "extendedProps": {"type": "journal", "editable": True},
        })

    for s in symptoms.all():
        events.append({
            "id": f"symptom-{s.id}", "title": f"Symptom: {s.name}",
            "start": s.entry_date.isoformat(), "allDay": True,
            "color": EVENT_COLORS["symptom"], "extendedProps": {"type": "symptom", "editable": True},
        })

    for a in appts.all():
        start_dt = datetime.combine(a.appointment_date, a.appointment_time)
        events.append({
            "id": f"therapy-{a.id}", "title": f"Therapy: {a.therapist_name}",
            "start": start_dt.isoformat(), "allDay": False,
            "color": EVENT_COLORS["therapy"], "extendedProps": {"type": "therapy", "editable": True, "status": a.status},
        })

    for h in habit_logs.all():
        habit = Habit.query.get(h.habit_id)
        if habit:
            events.append({
                "id": f"habit-{h.id}", "title": f"✓ {habit.name}",
                "start": h.log_date.isoformat(), "allDay": True,
                "color": habit.color, "extendedProps": {"type": "habit", "editable": False},
            })

    return jsonify(events)


@calendar_bp.route("/events/<event_type>/<int:obj_id>/move", methods=["POST"])
@login_required
def move_event(event_type, obj_id):
    """Handles FullCalendar drag-and-drop: updates the underlying record's date."""
    data = request.get_json(silent=True) or {}
    new_date_str = data.get("date")
    if not new_date_str:
        return jsonify({"success": False, "error": "Missing date"}), 400
    new_date = datetime.fromisoformat(new_date_str.split("T")[0]).date()

    model_map = {
        "mood": (MoodEntry, "entry_date"),
        "journal": (JournalEntry, "entry_date"),
        "symptom": (Symptom, "entry_date"),
    }

    if event_type == "therapy":
        obj = TherapyAppointment.query.filter_by(id=obj_id, user_id=current_user.id).first()
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        obj.appointment_date = new_date
        db.session.commit()
        log_activity("therapy_rescheduled", f"Moved appointment #{obj.id} to {new_date}")
        return jsonify({"success": True})

    if event_type in model_map:
        Model, field = model_map[event_type]
        obj = Model.query.filter_by(id=obj_id, user_id=current_user.id).first()
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        setattr(obj, field, new_date)
        db.session.commit()
        log_activity(f"{event_type}_rescheduled", f"Moved {event_type} #{obj.id} to {new_date}")
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Unsupported event type"}), 400
