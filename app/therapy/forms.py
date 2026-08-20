from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, TimeField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

from app.models import TherapyAppointment


class TherapyForm(FlaskForm):
    therapist_name = StringField("Therapist Name", validators=[DataRequired(), Length(max=120)])
    session_type = StringField("Session Type", validators=[Optional(), Length(max=80)], render_kw={"placeholder": "e.g. CBT, Individual, Group"})
    appointment_date = DateField("Date", validators=[DataRequired()])
    appointment_time = TimeField("Time", validators=[DataRequired()])
    duration_minutes = IntegerField("Duration (minutes)", validators=[Optional(), NumberRange(min=5, max=480)], default=50)
    location = StringField("Location", validators=[Optional(), Length(max=200)], render_kw={"placeholder": "Video Call or address"})
    status = SelectField("Status", choices=[(s, s.replace("_", " ").capitalize()) for s in TherapyAppointment.STATUSES], validators=[DataRequired()])
    reminder_enabled = BooleanField("Enable Reminder", default=True)
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save Appointment")
