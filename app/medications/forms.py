from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class MedicationForm(FlaskForm):
    name = StringField("Medication Name", validators=[DataRequired(), Length(max=120)])
    dosage = StringField("Dosage", validators=[Optional(), Length(max=60)], render_kw={"placeholder": "e.g. 50mg"})
    frequency = StringField("Frequency", validators=[Optional(), Length(max=60)], render_kw={"placeholder": "e.g. Once daily"})
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[Optional()])
    prescribing_doctor = StringField("Prescribing Doctor", validators=[Optional(), Length(max=120)])
    reminder_times = StringField("Reminder Times (comma-separated HH:MM)", validators=[Optional(), Length(max=120)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=1000)])
    active = BooleanField("Currently Active", default=True)
    submit = SubmitField("Save Medication")


class MedicationLogForm(FlaskForm):
    log_date = DateField("Date", validators=[DataRequired()])
    status = SelectField("Status", choices=[("taken", "Taken"), ("missed", "Missed"), ("skipped", "Skipped")], validators=[DataRequired()])
    notes = StringField("Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Log Dose")
