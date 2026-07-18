"""
Calmora - CLI Commands
-----------------------
Custom `flask` CLI commands:
    flask init-db        create all tables
    flask seed-demo       populate with a realistic demo dataset
"""

import random
from datetime import date, timedelta, time, datetime

import click

from app.extensions import db


def register_cli_commands(app):
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Seed the database with a demo admin + user and sample data."""
        from app.models import (
            User, MoodEntry, JournalEntry, Symptom, Medication, MedicationLog,
            TherapyAppointment, Habit, HabitLog, Notification,
        )

        db.create_all()

        if User.query.filter_by(username="admin").first() is None:
            admin = User(username="admin", email="admin@calmora.app", full_name="Calmora Admin", role="admin")
            admin.set_password("Admin123!")
            db.session.add(admin)

        demo = User.query.filter_by(username="demo").first()
        if demo is None:
            demo = User(username="demo", email="demo@calmora.app", full_name="Demo User", role="user",
                        bio="Just here to feel a little better every day.")
            demo.set_password("Demo1234!")
            db.session.add(demo)
            db.session.commit()

            moods = MoodEntry.MOOD_TYPES
            today = date.today()

            for i in range(60):
                d = today - timedelta(days=i)
                db.session.add(MoodEntry(
                    user_id=demo.id, entry_date=d,
                    mood_type=random.choice(moods),
                    intensity=random.randint(3, 9),
                    stress_level=random.randint(1, 10),
                    sleep_hours=round(random.uniform(4.5, 9.0), 1),
                    notes="Auto-generated demo entry." if i % 5 == 0 else None,
                ))

            journal_titles = ["A quiet morning", "Tough day at work", "Grateful for small things",
                               "Feeling anxious", "Weekend reset", "Therapy reflections"]
            for i in range(15):
                d = today - timedelta(days=i * 3)
                db.session.add(JournalEntry(
                    user_id=demo.id, entry_date=d,
                    title=random.choice(journal_titles),
                    content="This is a sample journal entry generated for demonstration purposes. "
                             "It captures thoughts, reflections, and small wins from the day.",
                    mood_tag=random.choice(moods),
                    tags="reflection,demo,gratitude",
                    is_favorite=(i % 4 == 0),
                ))

            symptom_names = ["Headache", "Insomnia", "Racing thoughts", "Fatigue", "Irritability", "Low appetite"]
            for i in range(25):
                d = today - timedelta(days=i * 2)
                db.session.add(Symptom(
                    user_id=demo.id, entry_date=d,
                    name=random.choice(symptom_names),
                    category=random.choice(["physical", "emotional", "cognitive"]),
                    severity=random.randint(1, 5),
                    duration_minutes=random.randint(10, 240),
                    triggers=random.choice(["work stress", "poor sleep", "social event", ""]),
                ))

            med = Medication(
                user_id=demo.id, name="Sertraline", dosage="50mg", frequency="Once daily",
                start_date=today - timedelta(days=90), prescribing_doctor="Dr. Amara Osei",
                reminder_times="08:00", active=True,
            )
            db.session.add(med)
            db.session.commit()
            for i in range(60):
                d = today - timedelta(days=i)
                status = "taken" if random.random() > 0.15 else random.choice(["missed", "skipped"])
                db.session.add(MedicationLog(medication_id=med.id, user_id=demo.id, log_date=d, status=status))

            for i in range(6):
                d = today + timedelta(days=i * 7 - 14)
                db.session.add(TherapyAppointment(
                    user_id=demo.id, therapist_name="Dr. Amara Osei", session_type="CBT",
                    appointment_date=d, appointment_time=time(15, 0), duration_minutes=50,
                    location="Video Call",
                    status="completed" if d < today else "scheduled",
                ))

            habit_defs = [
                ("Meditation", "daily", "#6C63FF", "bi-flower1"),
                ("Exercise", "daily", "#00C2A8", "bi-heart-pulse"),
                ("Gratitude journaling", "daily", "#FFB020", "bi-journal-heart"),
                ("Drink 8 glasses of water", "daily", "#4C9AFF", "bi-cup-straw"),
            ]
            habits = []
            for name, freq, color, icon in habit_defs:
                h = Habit(user_id=demo.id, name=name, frequency=freq, color=color, icon=icon, target_count=1)
                db.session.add(h)
                habits.append(h)
            db.session.commit()

            for h in habits:
                for i in range(30):
                    d = today - timedelta(days=i)
                    if random.random() > 0.25:
                        db.session.add(HabitLog(habit_id=h.id, user_id=demo.id, log_date=d, completed=True))

            db.session.add(Notification(user_id=demo.id, message="Welcome to Calmora! Start by logging today's mood.", category="info"))
            db.session.add(Notification(user_id=demo.id, message="Reminder: Sertraline dose at 08:00", category="reminder"))

            db.session.commit()
        else:
            db.session.commit()

        click.echo("Demo data seeded. Login: demo / Demo1234!  (admin / Admin123!)")
