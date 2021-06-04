from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.fields.core import FloatField, RadioField, SelectField
from wtforms.validators import DataRequired
import requests
from wtforms.widgets.core import Select
from lift_tables import rep_reduction, age_reduction, lift_tgt_dict
app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
Bootstrap(app)

# # SQLAlchemy
# # Creates the new database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lift-log.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)


# # Creates the new table
# class Lift(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
# db.create_all()

class WODWeightForm(FlaskForm):
    one_rm = IntegerField("What is your 1RM?")
    wod_reps = IntegerField("How many reps is your workout?")
    submit = SubmitField("Calculate WODWeight")

class oneRMEForm(FlaskForm):
    multirepload = IntegerField("How much weight did you lift?")
    multirep = IntegerField("How many unbroken reps?")
    submit = SubmitField("Calculate 1RME")

class TargetWeightForm(FlaskForm):
    sex = RadioField(label="Gender",choices=[('m',"♂ Male"),('f',"♀ Female")],default='m')
    age = IntegerField("Age (years)")
    bw = FloatField("Body Weight (lb)")
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


@app.route("/")
def home():
    return render_template("index.html", page_class="index-page")

@app.route("/phone")
def phone():
    return render_template("phoneapp.html", page_class="index-page")

@app.route("/templates")
def templates():
    return render_template("template_html_sheet.html", page_class="index-page")

@app.route("/wodweight", methods=["GET","POST"])
def wodweight():
    wodform = WODWeightForm()
    if wodform.validate_on_submit():
        one_rm = wodform.one_rm.data
        wod_reps = wodform.wod_reps.data
        if wod_reps > 30:
            wod_reps = 30
        rep_reduction_factor = rep_reduction[wod_reps]
        wod_weight = one_rm * rep_reduction_factor
        lift = int(wod_weight - wod_weight % 5)
        liftstring = f"For a 1RM of {one_rm}#, the recommended weight is no more than {lift}# for {wod_reps} reps."
        return render_template("wodweight.html", page_class="index-page", liftstring=liftstring, rep=wod_reps, lift=lift, form=wodform, scrollToAnchor="results")
    return render_template("wodweight.html", page_class="index-page", form=wodform, lifstring="")

@app.route("/onerme", methods=["GET","POST"])
def onerme():
    one_rme_form = oneRMEForm()
    if one_rme_form.validate_on_submit():
        rep_lifted = one_rme_form.multirep.data
        weight_lifted = one_rme_form.multirepload.data
        if rep_lifted > 30:
            rep_lifted = 30
        rep_factor = rep_reduction[rep_lifted]
        pure_onerme = weight_lifted / rep_factor
        onerme = int(pure_onerme - pure_onerme % 5)
        onermestring = f"Lifting {weight_lifted}# for {rep_lifted} repetitions is equivalent to a one rep lift of {onerme}#."
        return render_template("1rme.html", page_class="index-page", onermestring=onermestring, onerme=onerme, form=one_rme_form, scrollToAnchor="results")
    return render_template("1rme.html", page_class="index-page", form=one_rme_form, onermestring="")

@app.route("/targets", methods=["GET","POST"])
def targets():
    form = TargetWeightForm()
    if form.validate_on_submit():
        # Store form data as variables
        tw_sex = form.sex.data
        tw_age = form.age.data
        tw_bodywt = form.bw.data
        tw_mvmt = form.movement.data
        # Move age to within acceptable bounds
        if tw_age < 14:
            tw_age = 14
        elif tw_age > 89:
            tw_age = 89
        # Calculate factor for age reduction
        age_reducer = age_reduction[tw_age]
        # Round body weight to the nearest 10 lb increment
        bwt = int(tw_bodywt - tw_bodywt % 10)
        # Move weight to within acceptable bounds
        if bwt < 90 and tw_sex == 'f':
            bwt = 90
        elif bwt < 110:
            bwt = 110
        elif bwt > 260 and tw_sex == 'f':
            bwt = 260
        elif bwt > 310:
            bwt = 310
        result = lift_tgt_dict[tw_mvmt][tw_sex][bwt]
        tgt1 = result[0] * age_reducer * bwt
        tgt2 = result[1] * age_reducer * bwt
        tgt3 = result[2] * age_reducer * bwt
        tgt4 = result[3] * age_reducer * bwt
        tgt5 = result[4] * age_reducer * bwt
        tgt1 = int(tgt1 - tgt1 % 5)
        tgt2 = int(tgt2 - tgt2 % 5)
        tgt3 = int(tgt3 - tgt3 % 5)
        tgt4 = int(tgt4 - tgt4 % 5)
        tgt5 = int(tgt5 - tgt5 % 5)
        return render_template("target_weight.html", page_class="index-page", form=form, tgt1=tgt1, tgt2=tgt2, tgt3=tgt3, tgt4=tgt4, tgt5=tgt5)
    return render_template("target_weight.html", page_class="index-page", form=form)

@app.route("/mobile")
def mobile():
    return render_template("mobile_splash.html", page_class="index-page")

if __name__ == '__main__':
    app.run(debug=True)