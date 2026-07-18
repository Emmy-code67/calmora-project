from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, TextAreaField, DateField, FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Length

from app.models import MoodEntry


class MoodForm(FlaskForm):
    entry_date = DateField("Date", validators=[DataRequired()])
    mood_type = SelectField("Mood", choices=[(m, m.capitalize()) for m in MoodEntry.MOOD_TYPES], validators=[DataRequired()])
    intensity = IntegerField("Intensity (1-10)", validators=[DataRequired(), NumberRange(min=1, max=10)])
    stress_level = IntegerField("Stress Level (1-10)", validators=[Optional(), NumberRange(min=1, max=10)])
    sleep_hours = FloatField("Sleep (hours)", validators=[Optional(), NumberRange(min=0, max=24)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save Mood Entry")
