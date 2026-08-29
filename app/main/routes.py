"""
Calmora - Main Blueprint (Dashboard)
------------------------------------
Renders the home dashboard: summary cards, recent activity, and small
"at a glance" charts. Heavier analytics live in the `analytics` blueprint.
"""

from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    MoodEntry, JournalEntry, Symptom, Medication, MedicationLog,
    TherapyAppointment, Habit, HabitLog, Notification,
)

main_bp = Blueprint("main", __name__, template_folder="../templates/main")


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    uid = current_user.id
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    mood_this_week = MoodEntry.query.filter(
        MoodEntry.user_id == uid, MoodEntry.entry_date >= week_ago
    ).all()
    avg_mood_score = (
        round(sum(m.emotional_score for m in mood_this_week) / len(mood_this_week), 2)
        if mood_this_week else None
    )

    journal_count = JournalEntry.query.filter_by(user_id=uid).count()
    symptom_count_month = Symptom.query.filter(
        Symptom.user_id == uid, Symptom.entry_date >= month_ago
    ).count()

    active_meds = Medication.query.filter_by(user_id=uid, active=True).all()
    med_logs_month = MedicationLog.query.filter(
        MedicationLog.user_id == uid, MedicationLog.log_date >= month_ago
    ).all()
    adherence = (
        round(sum(1 for l in med_logs_month if l.status == "taken") / len(med_logs_month) * 100, 1)
        if med_logs_month else None
    )

    upcoming_appt = (
        TherapyAppointment.query.filter(
            TherapyAppointment.user_id == uid,
            TherapyAppointment.appointment_date >= today,
            TherapyAppointment.status == "scheduled",
        )
        .order_by(TherapyAppointment.appointment_date.asc())
        .first()
    )

    habits = Habit.query.filter_by(user_id=uid, active=True).all()
    habit_data = [
        {"habit": h, "streak": h.current_streak(), "rate": h.completion_rate(30)}
        for h in habits
    ]
    avg_habit_rate = (
        round(sum(h["rate"] for h in habit_data) / len(habit_data), 1) if habit_data else None
    )

    trend_days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    trend_map = {}
    for m in MoodEntry.query.filter(
        MoodEntry.user_id == uid, MoodEntry.entry_date >= trend_days[0]
    ).all():
        trend_map.setdefault(m.entry_date, []).append(m.emotional_score)
    trend_labels = [d.strftime("%b %d") for d in trend_days]
    trend_values = [
        round(sum(trend_map[d]) / len(trend_map[d]), 2) if d in trend_map else None
        for d in trend_days
    ]

    recent_journals = (
        JournalEntry.query.filter_by(user_id=uid)
        .order_by(JournalEntry.entry_date.desc())
        .limit(4)
        .all()
    )

    upcoming_appointments = (
        TherapyAppointment.query.filter(
            TherapyAppointment.user_id == uid,
            TherapyAppointment.appointment_date >= today,
        )
        .order_by(TherapyAppointment.appointment_date.asc())
        .limit(3)
        .all()
    )

    return render_template(
        "main/dashboard.html",
        avg_mood_score=avg_mood_score,
        journal_count=journal_count,
        symptom_count_month=symptom_count_month,
        active_meds_count=len(active_meds),
        adherence=adherence,
        upcoming_appt=upcoming_appt,
        habit_data=habit_data,
        avg_habit_rate=avg_habit_rate,
        trend_labels=trend_labels,
        trend_values=trend_values,
        recent_journals=recent_journals,
        upcoming_appointments=upcoming_appointments,
    )


@main_bp.route("/notifications/mark-all-read")
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(url_for("main.dashboard"))
