from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from app.models import MoodEntry


class JournalForm(FlaskForm):
    entry_date = DateField("Date", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    content = TextAreaField("What's on your mind?", validators=[DataRequired()])
    mood_tag = SelectField("Mood Tag", choices=[("", "None")] + [(m, m.capitalize()) for m in MoodEntry.MOOD_TYPES], validators=[Optional()])
    tags = StringField("Tags (comma-separated)", validators=[Optional(), Length(max=255)])
    is_favorite = BooleanField("Mark as favorite")
    submit = SubmitField("Save Journal Entry")
