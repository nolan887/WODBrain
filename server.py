from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.fields.core import FloatField, RadioField, SelectField
from wtforms.validators import DataRequired
import requests
from wtforms.widgets.core import Select
from lift_tables import rep_reduction, age_reduction, backsquat, clean_and_jerk, bench_press, deadlift, front_squat, overhead_squat, power_clean, power_snatch, clean, snatch, strict_press, push_press, push_jerk, thruster

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
    bw = IntegerField("Body Weight (lb)")
    movement = SelectField("Barbell Movement",choices=[('s1','Select 1'),('s2','Select 2')])
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
        print('form submitted')
    return render_template("target_weight.html", page_class="index-page", form=form)

@app.route("/mobile")
def mobile():
    return render_template("mobile_splash.html", page_class="index-page")

if __name__ == '__main__':
    app.run(debug=True)