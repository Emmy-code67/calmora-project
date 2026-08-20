"""
Calmora - Analytics Blueprint
-----------------------------
Computes aggregated, chart-ready data server-side (kept simple and
readable for learning purposes) and hands it to Chart.js on the front end.
"""

from datetime import date, timedelta
from collections import defaultdict

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.models import MoodEntry, Symptom, Medication, MedicationLog, Habit, HabitLog, JournalEntry

analytics_bp = Blueprint("analytics", __name__, template_folder="../templates/analytics")


@analytics_bp.route("/")
@login_required
def overview():
    uid = current_user.id
    days = request.args.get("days", 30, type=int)
    today = date.today()
    window_start = today - timedelta(days=days - 1)

    # --- Mood trend + emotional score over time -----------------------------
    moods = MoodEntry.query.filter(MoodEntry.user_id == uid, MoodEntry.entry_date >= window_start).order_by(MoodEntry.entry_date).all()
    date_range = [window_start + timedelta(days=i) for i in range(days)]
    daily_scores = defaultdict(list)
    daily_stress = defaultdict(list)
    daily_sleep = defaultdict(list)
    for m in moods:
        daily_scores[m.entry_date].append(m.emotional_score)
        if m.stress_level is not None:
            daily_stress[m.entry_date].append(m.stress_level)
        if m.sleep_hours is not None:
            daily_sleep[m.entry_date].append(m.sleep_hours)

    trend_labels = [d.strftime("%b %d") for d in date_range]
    trend_scores = [round(sum(daily_scores[d]) / len(daily_scores[d]), 2) if daily_scores[d] else None for d in date_range]
    stress_series = [round(sum(daily_stress[d]) / len(daily_stress[d]), 2) if daily_stress[d] else None for d in date_range]
    sleep_series = [round(sum(daily_sleep[d]) / len(daily_sleep[d]), 2) if daily_sleep[d] else None for d in date_range]

    # --- Mood type distribution ------------------------------------------------
    mood_counts = defaultdict(int)
    for m in moods:
        mood_counts[m.mood_type] += 1
    mood_dist_labels = list(mood_counts.keys())
    mood_dist_values = list(mood_counts.values())

    # --- Stress vs Sleep correlation (scatter) --------------------------------
    scatter_points = [
        {"x": m.sleep_hours, "y": m.stress_level}
        for m in moods if m.sleep_hours is not None and m.stress_level is not None
    ]

    # --- Symptom frequency by name --------------------------------------------
    symptoms = Symptom.query.filter(Symptom.user_id == uid, Symptom.entry_date >= window_start).all()
    symptom_freq = defaultdict(int)
    symptom_severity_sum = defaultdict(int)
    for s in symptoms:
        symptom_freq[s.name] += 1
        symptom_severity_sum[s.name] += s.severity
    symptom_labels = sorted(symptom_freq, key=lambda k: -symptom_freq[k])[:8]
    symptom_values = [symptom_freq[k] for k in symptom_labels]
    symptom_avg_severity = [round(symptom_severity_sum[k] / symptom_freq[k], 1) for k in symptom_labels]

    symptom_category_counts = defaultdict(int)
    for s in symptoms:
        symptom_category_counts[s.category or "uncategorized"] += 1

    # --- Habit completion rates + streaks -------------------------------------
    habits = Habit.query.filter_by(user_id=uid, active=True).all()
    habit_labels = [h.name for h in habits]
    habit_rates = [h.completion_rate(days) for h in habits]
    habit_streaks = [h.current_streak() for h in habits]

    # --- Medication adherence --------------------------------------------------
    medications = Medication.query.filter_by(user_id=uid).all()
    med_labels = [m.name for m in medications]
    med_adherence = [m.adherence_rate if m.adherence_rate is not None else 0 for m in medications]

    med_logs = MedicationLog.query.filter(MedicationLog.user_id == uid, MedicationLog.log_date >= window_start).all()
    status_counts = defaultdict(int)
    for log in med_logs:
        status_counts[log.status] += 1

    # --- Journal activity (entries per week) -----------------------------------
    journals = JournalEntry.query.filter(JournalEntry.user_id == uid, JournalEntry.entry_date >= window_start).all()
    journal_week_counts = defaultdict(int)
    for j in journals:
        week_label = j.entry_date.strftime("Week of %b %d")
        journal_week_counts[week_label] += 1

    # --- Wellness insight (very simple heuristic, transparent + explainable) --
    insights = []
    valid_scores = [s for s in trend_scores if s is not None]
    if valid_scores:
        avg_score = sum(valid_scores) / len(valid_scores)
        if avg_score >= 2:
            insights.append(("success", "Your average mood score has been positive this period — keep up what's working!"))
        elif avg_score <= -2:
            insights.append(("warning", "Your average mood score has trended low. Consider reaching out to your therapist or a trusted person."))
        else:
            insights.append(("info", "Your mood has been relatively balanced this period."))

    if scatter_points:
        low_sleep_high_stress = [p for p in scatter_points if p["x"] < 6 and p["y"] >= 7]
        if len(low_sleep_high_stress) >= max(3, len(scatter_points) * 0.3):
            insights.append(("warning", "There's a pattern of higher stress on days with less than 6 hours of sleep."))

    if habit_rates and (sum(habit_rates) / len(habit_rates)) >= 70:
        insights.append(("success", "Great habit consistency — your 30-day completion rate is strong."))

    if med_adherence and any(a < 80 for a in med_adherence):
        insights.append(("warning", "Some medications have adherence below 80%. Consider setting extra reminders."))

    if not insights:
        insights.append(("info", "Log more entries to unlock personalized wellness insights."))

    return render_template(
        "analytics/overview.html",
        days=days,
        trend_labels=trend_labels,
        trend_scores=trend_scores,
        stress_series=stress_series,
        sleep_series=sleep_series,
        mood_dist_labels=mood_dist_labels,
        mood_dist_values=mood_dist_values,
        scatter_points=scatter_points,
        symptom_labels=symptom_labels,
        symptom_values=symptom_values,
        symptom_avg_severity=symptom_avg_severity,
        symptom_category_counts=dict(symptom_category_counts),
        habit_labels=habit_labels,
        habit_rates=habit_rates,
        habit_streaks=habit_streaks,
        med_labels=med_labels,
        med_adherence=med_adherence,
        status_counts=dict(status_counts),
        journal_week_counts=dict(journal_week_counts),
        insights=insights,
    )
