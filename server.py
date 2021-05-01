from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import requests

rep_reduction = {
    1: 1.00,
    2: 0.97,
    3: 0.94,
    4: 0.92,
    5: 0.89,
    6: 0.86,
    7: 0.83,
    8: 0.81,
    9: 0.78,
    10: 0.75,
    11: 0.73,
    12: 0.71,
    13: 0.70,
    14: 0.68,
    15: 0.67,
    16: 0.65,
    17: 0.64,
    18: 0.63,
    19: 0.61,
    20: 0.60,
    21: 0.59,
    22: 0.58,
    23: 0.57,
    24: 0.56,
    25: 0.55,
    26: 0.54,
    27: 0.53,
    28: 0.52,
    29: 0.51,
    30: 0.50
}

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

# # WTForm
class WODWeightForm(FlaskForm):
    one_rm = IntegerField("What is your 1RM?")
    wod_reps = IntegerField("How many reps is your workout?")
    submit = SubmitField("Calculate")
#
# class AddMovieForm(FlaskForm):
#     title = StringField("Movie Title", validators=[DataRequired()])
#     submit = SubmitField("Add Movie")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/templates")
def templates():
    return render_template("template_html_sheet.html")

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
        print(liftstring)
        return render_template("wodweight.html", liftstring=liftstring, form=wodform)
    return render_template("wodweight.html", form=wodform, lifstring="")



if __name__ == '__main__':
    app.run(debug=True)