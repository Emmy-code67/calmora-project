from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

from app.models import Habit


class HabitForm(FlaskForm):
    name = StringField("Habit Name", validators=[DataRequired(), Length(max=120)])
    description = StringField("Description", validators=[Optional(), Length(max=255)])
    frequency = SelectField("Frequency", choices=[(f, f.capitalize()) for f in Habit.FREQUENCIES], validators=[DataRequired()])
    target_count = IntegerField("Target Count (per period)", validators=[DataRequired(), NumberRange(min=1, max=20)], default=1)
    color = StringField("Color", default="#6C63FF")
    icon = SelectField(
        "Icon",
        choices=[
            ("bi-flower1", "Meditation"), ("bi-heart-pulse", "Exercise"), ("bi-journal-heart", "Journaling"),
            ("bi-cup-straw", "Hydration"), ("bi-moon-stars", "Sleep"), ("bi-book", "Reading"),
            ("bi-people", "Social"), ("bi-brush", "Creativity"), ("bi-check-circle", "General"),
        ],
    )
    active = BooleanField("Active", default=True)
    submit = SubmitField("Save Habit")
