"""
Calmora - Global Search Blueprint
---------------------------------
A single search box that queries across mood notes, journal entries,
symptoms, medications, and therapy appointments for the current user.
"""

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.models import MoodEntry, JournalEntry, Symptom, Medication, TherapyAppointment, Habit

search_bp = Blueprint("search", __name__, template_folder="../templates/search")


@search_bp.route("/")
@login_required
def global_search():
    q = request.args.get("q", "").strip()
    results = {"mood": [], "journal": [], "symptoms": [], "medications": [], "therapy": [], "habits": []}
    total = 0

    if q:
        uid = current_user.id
        like = f"%{q}%"

        results["mood"] = MoodEntry.query.filter(
            MoodEntry.user_id == uid, MoodEntry.notes.ilike(like)
        ).order_by(MoodEntry.entry_date.desc()).limit(20).all()

        results["journal"] = JournalEntry.query.filter(
            JournalEntry.user_id == uid,
            (JournalEntry.title.ilike(like)) | (JournalEntry.content.ilike(like)) | (JournalEntry.tags.ilike(like)),
        ).order_by(JournalEntry.entry_date.desc()).limit(20).all()

        results["symptoms"] = Symptom.query.filter(
            Symptom.user_id == uid,
            (Symptom.name.ilike(like)) | (Symptom.notes.ilike(like)) | (Symptom.triggers.ilike(like)),
        ).order_by(Symptom.entry_date.desc()).limit(20).all()

        results["medications"] = Medication.query.filter(
            Medication.user_id == uid,
            (Medication.name.ilike(like)) | (Medication.notes.ilike(like)),
        ).order_by(Medication.name).limit(20).all()

        results["therapy"] = TherapyAppointment.query.filter(
            TherapyAppointment.user_id == uid,
            (TherapyAppointment.therapist_name.ilike(like)) | (TherapyAppointment.notes.ilike(like)),
        ).order_by(TherapyAppointment.appointment_date.desc()).limit(20).all()

        results["habits"] = Habit.query.filter(
            Habit.user_id == uid,
            (Habit.name.ilike(like)) | (Habit.description.ilike(like)),
        ).order_by(Habit.name).limit(20).all()

        total = sum(len(v) for v in results.values())

    return render_template("search/results.html", q=q, results=results, total=total)
