# GENERAL IMPORTS
import os
import pathlib
import requests
import datetime
from wtforms.fields.core import BooleanField

import pprint


# WODBRAIN IMPORTS
from lift_tables import rep_reduction, age_reduction, lift_tgt_dict, lift_dict_map
from forms import WODWeightForm, oneRMEForm, TargetWeightForm, LifterProfileForm, LogLiftForm

# FLASK IMPORTS
from flask import Flask, request, session, abort, redirect, render_template
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

# GOOGLE LOGIN IMPORTS
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///wodbrain-database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CONFIGURE TABLES
# Create the User Table
class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.String(25), primary_key=True)
    email = db.Column(db.String(50))
    name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    sex = db.Column(db.String(1))
    bw = db.Column(db.Float(6))

# Create the Lift Catalog Table
class MovementCatalog(db.Model):
    __tablename__ = "move-cat"
    id = db.Column(db.String(2), primary_key=True)
    lift_table_name = db.Column(db.String(25))
    move = db.Column(db.String(25))

# Create the Lift data Tables
class LiftData(db.Model):
    __tablename__ = "lift-log"
    wodbrainlift = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(2))
    liftid = db.Column(db.String(2))
    load = db.Column(db.Float(6))
    reps = db.Column(db.Integer)
    onerm = db.Column(db.Float(6))
    actual_lift = db.Column(db.Boolean)
    date = db.Column(db.Date)

# CREAT ALL TABLES IN DB
db.create_all()

# GOOGLE LOGIN HANDLING
# Allows Google to pass info to local test environment
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "246309898653-gh1r54ma97fjhc5eihbsijoaobk42fco.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
    )

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return(redirect("/login"))
        else:
            return function()
    return wrapper

def one_rm_calc(rep, load):
    if rep > 30:
        rep = 30
    rep_factor = rep_reduction[rep]
    pure_onerme = load / rep_factor
    one_rm_result = int(pure_onerme - pure_onerme % 5)
    return one_rm_result

# WODBRAIN LOGIN HANDLING
@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    # Recieve google callback info
    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    # Store Google Info for current session
    session["google_id"] = id_info.get("sub")
    session["google_email"] = id_info.get("email")
    session["name"] = id_info.get("name")

    if User.query.filter_by(id=session["google_id"]).first():
        print("in database")
        g_userid = session.get('google_id')
        existing_user = User.query.get(g_userid)
        login_user(existing_user)
        return redirect("/mobile")
    else:
        print("not in database")        
        new_id = str(session["google_id"])
        new_email = str(session["google_email"])
        new_name = str(session["name"])

        new_user = User(
            id = new_id,
            email = new_email,
            name = new_name,
            age = "18",
            sex = "m",
            bw = 165,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect("/edit_profile")


@app.route("/logout")
def logout():
    session.clear()
    logout_user()
    return redirect("/mobile")




# WODBRAIN USER PROFILE
@app.route("/edit_profile", methods=["GET","POST"])
@login_is_required
def edit_profile():
    g_userid = session.get('google_id')
    current_user = User.query.get(g_userid)
    edit_form = LifterProfileForm(
        name = current_user.name,
        sex = current_user.sex,
        age = current_user.age,
        bw = current_user.bw
    )
    if edit_form.validate_on_submit():
        current_user.name = edit_form.name.data
        current_user.sex = edit_form.sex.data
        current_user.age = edit_form.age.data
        current_user.bw = edit_form.bw.data
        db.session.commit()
        return redirect("/mobile")
    return(render_template("editprofile.html", page_class="index-page", form=edit_form, name=edit_form.name.data, current_user=current_user))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if current_user.is_authenticated:
        liftnames = MovementCatalog.query.all()
        # CREATES A LIST OF LIFT NAMES AND AN EMPTY LIFT DICTIONARY TO PASS INTO JINJA TEMPLATE
        liftcatalog = []
        current_journal = {}
        pr_journal = {}

        # ADD EACH LIFT NAME TO THE LIFT CATALOG
        for lift in liftnames:
            liftcatalog.append(str(lift.move))
            movename = liftcatalog[int(lift.id)-1]
            current_journal[movename] = {}
            pr_journal[movename] = {
                'rep': 0,
                'load': 0,
                'onerm': 0,
                'date': 0,
                'actual': True
            }

        # ADD ALL OF THE CURRENT USER'S LOGGED LIFTS TO THE LIFT DICTIONARY
        liftdata = LiftData.query.filter_by(userid=current_user.id).all()

        for data in liftdata:
            movename = liftcatalog[int(data.liftid)-1]
            wdbkey = data.wodbrainlift
            entry = {
                'rep': data.reps,
                'load': data.load,
                'onerm': data.onerm,
                'date': data.date,
                'actual': data.actual_lift
            }
            current_journal[movename][wdbkey] = entry
        
        # MAKE A PR TABLE FROM CURRENT_USER_LIFTS TABLE WITH MAX'S ONLY
        # LOOP THROUGH EACH MOVEMENT SUB-DICTIONARY
        for move in liftcatalog:
            logged_onerm = 0
            
            # LOOP THROUGH EACH SUB-DICTIONARY LIFT TO FIND MAX
            for lifts in current_journal[move].items():
                # PULL ONE RME VALUE FROM CURRENT_JOURNAL
                possible_onerm = lifts[1]['onerm']
                if possible_onerm > logged_onerm:
                    logged_onerm = possible_onerm
                    # OVERWRITE PR JOURNAL WITH NEW MAX
                    pr_journal[move] = lifts[1]
        return(render_template("profile.html", page_class="profile-page", current_user=current_user, liftcatalog=liftcatalog, liftdata=current_journal, pr_journal=pr_journal, liftnumbers=lift_dict_map))
    return(redirect("/login"))



# WODBRAIN LOG LIFT (USERS ONLY)
@app.route("/loglift/<int:lift_id>", methods=["GET","POST"])
def loglift(lift_id):
    if lift_id is not 0:
        logform = LogLiftForm(
            date = datetime.date.today()
        )
        if current_user.is_authenticated:
            if logform.validate_on_submit():
                onerme = one_rm_calc(
                    rep=logform.rep.data,
                    load=logform.load.data
                    )
                if logform.rep.data == 1:
                    actual = True
                else:
                    actual = False
                new_lift = LiftData(
                    userid = current_user.id,
                    liftid = logform.movement.data,
                    load = logform.load.data,
                    reps = logform.rep.data,
                    onerm = onerme,
                    actual_lift = actual,
                    date = logform.date.data
                )
                db.session.add(new_lift)
                db.session.commit()
                return(render_template("loglift.html", form=logform, page_class="index-page", current_user=current_user, liftlogged="yes"))
            else:
                return(render_template("loglift.html", form=logform, page_class="index-page", current_user=current_user, liftlogged="no"))
    else:
        print(lift_id)
        return(redirect("/login"))
    
# WODBRAIN ROUTING PAGES
@app.route("/")
def home():
    return render_template("index.html", page_class="index-page", current_user=current_user)

@app.route("/phone")
def phone():
    return render_template("phoneapp.html", page_class="index-page", current_user=current_user)

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
        return render_template("wodweight.html", page_class="index-page", liftstring=liftstring, rep=wod_reps, lift=lift, form=wodform, scrollToAnchor="results", current_user=current_user)
    return render_template("wodweight.html", page_class="index-page", form=wodform, lifstring="", current_user=current_user)

@app.route("/onerme", methods=["GET","POST"])
def onerme():
    one_rme_form = oneRMEForm()
    if one_rme_form.validate_on_submit():
        rep=one_rme_form.multirep.data
        load=one_rme_form.multirepload.data
        onerme = one_rm_calc(rep=rep , load=load)
        onermestring = f"Lifting {load}# for {rep} repetitions is equivalent to a one rep lift of {onerme}#."
        return render_template("1rme.html", page_class="index-page", onermestring=onermestring, onerme=onerme, form=one_rme_form, scrollToAnchor="results", current_user=current_user)
    return render_template("1rme.html", page_class="index-page", form=one_rme_form, onermestring="", current_user=current_user)

@app.route("/targets", methods=["GET","POST"])
def targets():
    if current_user.is_authenticated:
        print("logged in")
        form = TargetWeightForm(
            sex = current_user.sex,
            age = current_user.age,
            bw = current_user.bw
        )
    else:
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
        move_descr = str(db.session.query(MovementCatalog.move).filter_by(id=tw_mvmt).first()).strip(")(,'")
        return render_template("target_weight.html", page_class="index-page", form=form, tgt1=tgt1, tgt2=tgt2, tgt3=tgt3, tgt4=tgt4, tgt5=tgt5, move=move_descr, resultsmode="true", scrollToAnchor="results", current_user=current_user)
    return render_template("target_weight.html", page_class="index-page", form=form, resultsmode="", current_user=current_user)

@app.route("/mobile")
def mobile():
    return render_template("mobile_splash.html", page_class="index-page", current_user=current_user)



if __name__ == '__main__':
    app.run(debug=True)