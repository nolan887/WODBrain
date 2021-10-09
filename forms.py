from typing import AsyncGenerator
from flask_wtf import FlaskForm
from wtforms.widgets.html5 import TelInput, DateInput
from wtforms import StringField, SubmitField, IntegerField
from wtforms.fields.core import DateField, FloatField, RadioField, SelectField
from wtforms.validators import DataRequired
from wtforms.widgets.core import Select

class WODWeightForm(FlaskForm):
    one_rm = IntegerField("What is your 1RM?",widget=TelInput())
    wod_reps = IntegerField("How many reps is your workout?",widget=TelInput())
    submit = SubmitField("Calculate WODWeight")

class oneRMEForm(FlaskForm):
    multirepload = IntegerField("How much weight did you lift?",widget=TelInput())
    multirep = IntegerField("How many unbroken reps?",widget=TelInput())
    submit = SubmitField("Calculate 1RME")

class LifterProfileForm(FlaskForm):
    sex = RadioField(label="Gender",choices=[('m',"♂ Male"),('f',"♀ Female")])
    name = StringField("Name")
    age = IntegerField("Age (years)",widget=TelInput())
    bw = FloatField("Body Weight (lb)",widget=TelInput())
    submit = SubmitField("Save Profile")

class TargetWeightForm(FlaskForm):
    sex = RadioField(label='Gender',choices=[('m',"♂ Male"),('f',"♀ Female")],default='m')
    age = IntegerField("Age (years)",widget=TelInput())
    bw = FloatField("Body Weight (lb)",widget=TelInput())
    movement = SelectField(
        "Barbell Movement",
        choices=[
            ('01','Front Squat'),
            ('02','Back Squat'),
            ('03','Overhead Squat'),
            ('04','Clean (Squat Clean)'),
            ('05','Power Clean'),
            ('06','Clean & Jerk'),
            ('07','Deadlift'),
            ('08','Snatch (Squat Snatch)'),
            ('09','Power Snatch'),
            ('10','Strict Press'),
            ('11','Push Press'),
            ('12','Push Jerk'),
            ('13','Thruster'),
            ('14','Bench Press'),
            ]
    )
    submit = SubmitField("Calculate Targets")

class LogLiftForm(FlaskForm):
    movement = SelectField(
        "Barbell Movement",
            choices=[
                ('01','Front Squat'),
                ('02','Back Squat'),
                ('03','Overhead Squat'),
                ('04','Clean (Squat Clean)'),
                ('05','Power Clean'),
                ('06','Clean & Jerk'),
                ('07','Deadlift'),
                ('08','Snatch (Squat Snatch)'),
                ('09','Power Snatch'),
                ('10','Strict Press'),
                ('11','Push Press'),
                ('12','Push Jerk'),
                ('13','Thruster'),
                ('14','Bench Press'),
                ]
    )
    rep = IntegerField("How many unbroken reps?", widget=TelInput())
    load = IntegerField("How much weight did you lift?",widget=TelInput())
    date = DateField("Date", widget=DateInput())
    submit = SubmitField("Log Lift")