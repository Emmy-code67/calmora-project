"""
Calmora - Database Models
-------------------------
All SQLAlchemy models live in this single module for a beginner-friendly
codebase (easy to see the whole schema at a glance). In a larger project
you might split this into app/models/ with one file per model.

Relationships are declared with `back_populates` (explicit, readable)
rather than `backref` (implicit) to keep things clear for learners.
"""

from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# ---------------------------------------------------------------------------
# Helper mixin
# ---------------------------------------------------------------------------
class TimestampMixin:
    """Adds created_at / updated_at columns to any model that inherits it."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# ---------------------------------------------------------------------------
# User & Auth
# ---------------------------------------------------------------------------
class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    avatar = db.Column(db.String(255), default="default.png")
    role = db.Column(db.String(20), default="user", nullable=False)  # 'user' | 'admin'
    theme_pref = db.Column(db.String(10), default="light")  # 'light' | 'dark'
    timezone = db.Column(db.String(64), default="UTC")
    is_active_account = db.Column(db.Boolean, default=True)
    bio = db.Column(db.Text)
    last_login_at = db.Column(db.DateTime)

    # Relationships (cascade delete keeps data consistent when a user is removed)
    moods = db.relationship("MoodEntry", back_populates="user", cascade="all, delete-orphan")
    journals = db.relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    symptoms = db.relationship("Symptom", back_populates="user", cascade="all, delete-orphan")
    medications = db.relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    appointments = db.relationship("TherapyAppointment", back_populates="user", cascade="all, delete-orphan")
    habits = db.relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    activity_logs = db.relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username}>"


# ---------------------------------------------------------------------------
# Mood Tracking
# ---------------------------------------------------------------------------
class MoodEntry(TimestampMixin, db.Model):
    __tablename__ = "mood_entries"

    MOOD_TYPES = ["happy", "sad", "anxious", "angry", "calm", "excited", "neutral", "stressed", "tired", "grateful"]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    entry_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    mood_type = db.Column(db.String(20), nullable=False)
    intensity = db.Column(db.Integer, nullable=False)  # 1-10 scale
    stress_level = db.Column(db.Integer)  # 1-10 scale
    sleep_hours = db.Column(db.Float)
    notes = db.Column(db.Text)

    user = db.relationship("User", back_populates="moods")

    # Rough numeric score used for trend charts (-5..+5)
    MOOD_SCORES = {
        "happy": 5, "excited": 5, "grateful": 4, "calm": 3, "neutral": 0,
        "tired": -1, "stressed": -3, "anxious": -3, "sad": -4, "angry": -5,
    }

    @property
    def emotional_score(self):
        base = self.MOOD_SCORES.get(self.mood_type, 0)
        # Weight the base sentiment by the reported intensity (1-10 -> 0.1-1.0)
        return round(base * (self.intensity / 10), 2)


# ---------------------------------------------------------------------------
# Journaling
# ---------------------------------------------------------------------------
class JournalEntry(TimestampMixin, db.Model):
    __tablename__ = "journal_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    entry_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mood_tag = db.Column(db.String(20))
    tags = db.Column(db.String(255))  # comma-separated keywords
    is_favorite = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="journals")

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",")] if self.tags else []


# ---------------------------------------------------------------------------
# Symptom Monitoring
# ---------------------------------------------------------------------------
class Symptom(TimestampMixin, db.Model):
    __tablename__ = "symptoms"

    SEVERITY_LEVELS = [1, 2, 3, 4, 5]  # 1=mild ... 5=severe

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    entry_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60))  # e.g. physical, emotional, cognitive
    severity = db.Column(db.Integer, nullable=False)
    duration_minutes = db.Column(db.Integer)
    triggers = db.Column(db.String(255))
    notes = db.Column(db.Text)

    user = db.relationship("User", back_populates="symptoms")


# ---------------------------------------------------------------------------
# Medication Management
# ---------------------------------------------------------------------------
class Medication(TimestampMixin, db.Model):
    __tablename__ = "medications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(60))
    frequency = db.Column(db.String(60))  # e.g. "Once daily", "Twice daily"
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date)
    prescribing_doctor = db.Column(db.String(120))
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    reminder_times = db.Column(db.String(120))  # comma-separated "HH:MM"

    user = db.relationship("User", back_populates="medications")
    logs = db.relationship("MedicationLog", back_populates="medication", cascade="all, delete-orphan")

    @property
    def adherence_rate(self):
        total = len(self.logs)
        if total == 0:
            return None
        taken = sum(1 for log in self.logs if log.status == "taken")
        return round((taken / total) * 100, 1)


class MedicationLog(db.Model):
    __tablename__ = "medication_logs"

    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey("medications.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    log_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    status = db.Column(db.String(20), default="taken")  # taken | missed | skipped
    taken_at = db.Column(db.DateTime)
    notes = db.Column(db.String(255))

    medication = db.relationship("Medication", back_populates="logs")


# ---------------------------------------------------------------------------
# Therapy Appointments
# ---------------------------------------------------------------------------
class TherapyAppointment(TimestampMixin, db.Model):
    __tablename__ = "therapy_appointments"

    STATUSES = ["scheduled", "completed", "cancelled", "no_show"]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    therapist_name = db.Column(db.String(120), nullable=False)
    session_type = db.Column(db.String(80))  # e.g. "Individual", "Group", "CBT"
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=50)
    location = db.Column(db.String(200))  # address or "Video Call"
    status = db.Column(db.String(20), default="scheduled")
    notes = db.Column(db.Text)
    reminder_enabled = db.Column(db.Boolean, default=True)

    user = db.relationship("User", back_populates="appointments")


# ---------------------------------------------------------------------------
# Habit Tracking
# ---------------------------------------------------------------------------
class Habit(TimestampMixin, db.Model):
    __tablename__ = "habits"

    FREQUENCIES = ["daily", "weekly"]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    frequency = db.Column(db.String(20), default="daily")
    target_count = db.Column(db.Integer, default=1)  # times per period
    color = db.Column(db.String(20), default="#6C63FF")
    icon = db.Column(db.String(40), default="bi-check-circle")
    active = db.Column(db.Boolean, default=True)

    user = db.relationship("User", back_populates="habits")
    logs = db.relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")

    def completion_rate(self, days=30):
        """% of the last `days` days that had at least one completion logged."""
        from datetime import timedelta
        cutoff = date.today() - timedelta(days=days)
        recent = [log for log in self.logs if log.log_date >= cutoff and log.completed]
        if days == 0:
            return 0
        return round((len(recent) / days) * 100, 1)

    def current_streak(self):
        """Consecutive days (ending today) with a completed log."""
        from datetime import timedelta
        completed_dates = {log.log_date for log in self.logs if log.completed}
        streak = 0
        cursor = date.today()
        while cursor in completed_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak


class HabitLog(db.Model):
    __tablename__ = "habit_logs"

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    log_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    completed = db.Column(db.Boolean, default=True)
    count = db.Column(db.Integer, default=1)
    notes = db.Column(db.String(255))

    habit = db.relationship("Habit", back_populates="logs")

    __table_args__ = (db.UniqueConstraint("habit_id", "log_date", name="uq_habit_date"),)


# ---------------------------------------------------------------------------
# Notifications & Reminders
# ---------------------------------------------------------------------------
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(40), default="info")  # info | reminder | alert | success
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")


# ---------------------------------------------------------------------------
# Admin: Activity Logging
# ---------------------------------------------------------------------------
class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.String(255))
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="activity_logs")
