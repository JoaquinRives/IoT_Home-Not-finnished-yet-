from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, DateTimeField, validators, IntegerField


class Timer_form(FlaskForm):
    time_on = DateTimeField("time_on", format='%H:%M', validators=[validators.required()])
    time_off = DateTimeField("time_off", format='%H:%M', validators=[validators.required()])
    repeat = BooleanField("repeat")

class Auto_form(FlaskForm):
    temperature = IntegerField("temperature", validators=[validators.required()])
    temp_range = IntegerField("temp_range", validators=[validators.required()])
