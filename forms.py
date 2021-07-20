from typing import AsyncGenerator
from flask_wtf import FlaskForm
# from flask_wtf.html5 import TelInput, DateInput
from wtforms.widgets.html5 import TelInput, DateInput
from wtforms import StringField, SubmitField, IntegerField
from wtforms.fields.core import FloatField, RadioField, SelectField
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
    name = StringField("Name")
    sex = RadioField(label="Gender",choices=[('m',"♂ Male"),('f',"♀ Female")])
    age = IntegerField("Age (years)",widget=TelInput())
    bw = FloatField("Body Weight (lb)",widget=TelInput())
    submit = SubmitField("Save Profile")

class TargetWeightForm(FlaskForm):
    sex = RadioField(label="Gender",choices=[('m',"♂ Male"),('f',"♀ Female")],default='m')
    age = IntegerField("Age (years)",widget=TelInput())
    bw = FloatField("Body Weight (lb)",widget=TelInput())
    movement = SelectField(
        "Barbell Movement",
        choices=[
            ('front_squat','Front Squat'),
            ('backsquat','Back Squat'),
            ('overhead_squat','Overhead Squat'),
            ('clean','Clean (Squat Clean)'),
            ('power_clean','Power Clean'),
            ('clean_and_jerk','Clean & Jerk'),
            ('deadlift','Deadlift'),
            ('snatch','Snatch (Squat Snatch)'),
            ('power_snatch','Power Snatch'),
            ('strict_press','Strict Press'),
            ('push_press','Push Press'),
            ('push_jerk','Jerk Press'),
            ('thruster','Thruster'),
            ('bench_press','Bench Press'),
            ]
    )
    submit = SubmitField("Calculate Targets")