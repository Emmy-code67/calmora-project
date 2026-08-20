from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class SymptomForm(FlaskForm):
    entry_date = DateField("Date", validators=[DataRequired()])
    name = StringField("Symptom", validators=[DataRequired(), Length(max=120)])
    category = SelectField(
        "Category",
        choices=[("physical", "Physical"), ("emotional", "Emotional"), ("cognitive", "Cognitive"), ("behavioral", "Behavioral")],
        validators=[Optional()],
    )
    severity = IntegerField("Severity (1-5)", validators=[DataRequired(), NumberRange(min=1, max=5)])
    duration_minutes = IntegerField("Duration (minutes)", validators=[Optional(), NumberRange(min=0)])
    triggers = StringField("Possible Triggers", validators=[Optional(), Length(max=255)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save Symptom")
