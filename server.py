# GENERAL IMPORTS
import os
import pathlib
import requests
import datetime
from wtforms.fields.core import BooleanField

# WODBRAIN IMPORTS
from config import APP_KEY, DB_URL, GSHEET_KEY, GCLIENT_ID, WODB_REDIRECT
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

# GOOGLE SHEET IMPORTS
import gspread

app = Flask(__name__)
app.config['SECRET_KEY'] = APP_KEY
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#CONFIGURE TABLES
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
    move = db.Column(db.String(25))

# Create the Lift data Tables
class LiftData(db.Model):
    __tablename__ = "lift-log"
    wodbrainlift = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(25))
    liftid = db.Column(db.String(2))
    load = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    onerm = db.Column(db.Integer)
    actual_lift = db.Column(db.Boolean)
    date = db.Column(db.Date)
    lvl = db.Column(db.String(3))

# CREAT ALL TABLES IN DB
db.create_all()

# GOOGLE LOGIN HANDLING
# Allows Google to pass info to local test environment
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = GCLIENT_ID
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri=WODB_REDIRECT
    )

# GOOGLE SHEET SETUP
gc = gspread.service_account(filename="gsheet_credentials.json")
sh = gc.open_by_key(GSHEET_KEY)
worksheet = sh.sheet1

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return(redirect("/login"))
        else:
            return function()
    return wrapper



# WODBRAIN CUSTOM FUNCTIONS
def one_rm_calc(rep, load):
    if rep > 30:
        rep = 30
    rep_factor = rep_reduction[rep]
    pure_onerme = load / rep_factor
    one_rm_result = int(pure_onerme - pure_onerme % 5)
    return one_rm_result

def bw_adjust_calc(bw, sex):
    bwt = int(bw - bw % 10)
    if bwt < 90 and sex == 'f':
        bwt = 90
    elif bwt < 110:
        bwt = 110
    elif bwt > 260 and sex == 'f':
        bwt = 260
    elif bwt > 310:
        bwt = 310
    bw_adjust = bwt
    return bw_adjust

def lift_target_list_calc(move, sex, bw, age):
    if age < 14:
        age = 14
    elif age > 89:
        age = 89
    age_reducer = age_reduction[age]
    result = lift_tgt_dict[move][sex][bw]
    tgt_list = []
    for x in range(5):
        tgt = result[x] * age_reducer * bw
        tgt = int(tgt - tgt % 5)
        tgt_list.append(tgt)
    return tgt_list

def lift_lvl_calc(age, bw, sex, move, rep, load):
    bwt = bw_adjust_calc(bw=bw, sex=sex)
    onerme = one_rm_calc(rep, load)
    tgt_list = lift_target_list_calc(move, sex, bwt, age)
    if onerme < tgt_list[0]:
        level = "n/a"
    elif onerme < tgt_list[1]:
        level = "I"
    elif onerme < tgt_list[2]:
        level = "II"
    elif onerme < tgt_list[3]:
        level = "III"
    elif onerme < tgt_list [4]:
        level = "IV"
    else:
        level = "V"
    return level

def get_lift_catalog():
    liftnames = MovementCatalog.query.all()
    catalog = []
    for lift in liftnames:
        catalog.append(str(lift.move))
    return catalog

def get_user_journal():
    journal = {} # Blank dictionary
    liftnames = MovementCatalog.query.all() #SQL lift name and numbers
    liftdata = LiftData.query.filter_by(userid=current_user.id).all() #SQL all lifts for current user
    liftcatalog = get_lift_catalog()

    # Create blank journal with lift names
    for lift in liftnames:
        movename = liftcatalog[int(lift.id)-1]
        journal[movename] = {}

    # Populate blank journal with actual data
    for data in liftdata:
        movename = liftcatalog[int(data.liftid)-1]
        wdbkey = data.wodbrainlift
        entry = {
                'rep': data.reps,
                'load': data.load,
                'onerm': data.onerm,
                'date': data.date,
                'actual': data.actual_lift,
                'level': data.lvl
                }
        journal[movename][wdbkey] = entry

    return journal

def get_pr_journal():
    journal = {} # Blank dictionary
    liftnames = MovementCatalog.query.all() # SQL movement name and numbers
    liftcatalog = get_lift_catalog()
    current_journal = get_user_journal()

    # Create blank PR Journal with lift names
    for lift in liftnames:
        movename = liftcatalog[int(lift.id)-1]
        journal[movename] = {
                'rep': 0,
                'load': 0,
                'onerm': 0,
                'date': 0,
                'actual': True,
                'level': 0
                }

    # Fill in blank PR journal with actual 1RM/E's
    for move in liftcatalog:
        logged_onerm = 0
        for lifts in current_journal[move].items():
            possible_onerm = lifts[1]['onerm']
            if possible_onerm > logged_onerm:
                journal[move] = lifts[1]
                logged_onerm = possible_onerm
    return journal

def mailchimp_gsheet(id, name, fname, lname, email):
    chimp_list = worksheet.col_values(1) #all Column 1 User ID Values from MailChimp GSheet
    if id not in chimp_list:
        user = [id, name, fname, lname, email]
        worksheet.append_row(user)
    return

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
    session["first_name"] = id_info.get("given_name")
    session["last_name"] = id_info.get("family_name")

    if User.query.filter_by(id=session["google_id"]).first():
        # IN DATABASE
        g_userid = session.get('google_id')
        existing_user = User.query.get(g_userid)
        login_user(existing_user)
        return redirect("/load/mobile")
    else:
        # NOT IN DATABASE / NEW USER
        new_id = str(session["google_id"])
        new_email = str(session["google_email"])
        new_name = str(session["name"])
        new_fname = str(session["first_name"])
        new_lname = str(session["last_name"])

        # ADD USER TO MAILCHIP USER GROUP GOOGLE SHEET
        mailchimp_gsheet(
            id = new_id,
            name = new_name, 
            fname = new_fname,
            lname = new_lname,
            email = new_email
            )

        # CREATE NEW SQL USER
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
        return redirect("/load/edit_profile")

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
        return(render_template("editprofile.html", page_class="index-page", form=edit_form, name=edit_form.name.data, current_user=current_user, editsubmit="yes"))
    return(render_template("editprofile.html", page_class="index-page", form=edit_form, name=edit_form.name.data, current_user=current_user, editsubmit=""))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if current_user.is_authenticated:
        liftcatalog = get_lift_catalog()
        current_journal = get_user_journal()
        pr_journal = get_pr_journal()
        return(render_template("profile.html", page_class="profile-page", current_user=current_user, liftcatalog=liftcatalog, liftdata=current_journal, pr_journal=pr_journal, liftnumbers=lift_dict_map))
    return(redirect("/login"))

# Loading Screen
@app.route("/load/<destination>")
def load(destination):
    return(render_template("loading.html", pagetoload=destination))


# WODBRAIN LOG LIFT INTERACTIONS
@app.route("/loglift/<lift_id>/<wt>/<reps>/<liftlogged>", methods=["GET","POST"])
def loglift(lift_id, wt, reps,liftlogged):
    if reps != "new": # Sent from WodWeight or 1RME will always have reps and load
        logform = LogLiftForm(
            rep = str(reps),
            load = str(wt),
            date = datetime.date.today()
        )
    elif lift_id != "new": # Sent from Targets or Profile will always have movement only
        logform = LogLiftForm(
            movement = str(lift_id),
            date = datetime.date.today()
        )
    else: # If no data, always pass in today's date by default
        logform = LogLiftForm(
            date = datetime.date.today()
        )

    # Commit loglift form to SQL if the user is logged in and submits form
    if current_user.is_authenticated:
        if logform.validate_on_submit():

            level = lift_lvl_calc(
                age=current_user.age,
                bw=current_user.bw,
                sex=current_user.sex,
                move=logform.movement.data,
                rep=logform.rep.data,
                load=logform.load.data
            )

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
                date = logform.date.data,
                lvl = level
            )
            db.session.add(new_lift)
            db.session.commit()
            return(redirect("/loglift/new/new/new/yes"))
        else:
            return(render_template("loglift.html", form=logform, page_class="index-page", current_user=current_user, liftlogged=liftlogged))
    return(redirect("/login"))

@app.route("/editlift/<int:id>", methods=["GET", "POST"])
def editlift(id):
    # Verify user is logged in
    if current_user.is_authenticated:
        # Pull SQL data for lift to edit
        lift_to_edit = LiftData.query.get(id)
        # Pre-populate the form with SQL data
        editform = LogLiftForm(
                movement = lift_to_edit.liftid,
                rep = lift_to_edit.reps,
                load = lift_to_edit.load,
                date = lift_to_edit.date,
        )
        # Create new lift for submitted form
        if editform.validate_on_submit():
            onerme = one_rm_calc(
                rep=editform.rep.data,
                load=editform.load.data
                )
            if editform.rep.data == 1:
                actual = True
            else:
                actual = False
            level = lift_lvl_calc(
                age=current_user.age,
                bw=current_user.bw,
                sex=current_user.sex,
                move=editform.movement.data,
                rep=editform.rep.data,
                load=editform.load.data
                )
            new_lift = LiftData(
                userid = current_user.id,
                liftid = editform.movement.data,
                load = editform.load.data,
                reps = editform.rep.data,
                onerm = onerme,
                actual_lift = actual,
                date = editform.date.data,
                lvl = level
            )
            # Add new lift, delete "edit" lift, commit to database
            db.session.add(new_lift)
            db.session.delete(lift_to_edit)
            db.session.commit()
            return(redirect("/load/profile"))
        return(render_template("editlift.html", form=editform, page_class="index-page", current_user=current_user))
    return(redirect("/login"))

@app.route("/xlift/<liftid>")
def xlift(liftid):
    if current_user.is_authenticated:
        return render_template("deletelift.html", page_class="index-page", current_user=current_user, liftid=liftid)
    return redirect("/login")

@app.route("/deletelift/<id>", methods=["GET", "POST"])
def deletelift(id):
    if current_user.is_authenticated:
        lift_to_delete = LiftData.query.get(id)
        db.session.delete(lift_to_delete)
        db.session.commit()
        return(redirect("/load/profile"))
    return(redirect("/login"))


# WODBRAIN ROUTING PAGES
@app.route("/")
def home():
    return redirect("/mobile")

@app.route("/about")
def about():
    return render_template("about.html", page_class="index-page", current_user=current_user)

@app.route("/phone")
def phone():
    return render_template("phoneapp.html", page_class="index-page", current_user=current_user)

@app.route("/wodweight/<lift_id>/<wt>", methods=["GET","POST"])
def wodweight(lift_id, wt):
    if lift_id == "new":
        wodform = WODWeightForm()
    else:
        wodform = WODWeightForm(
            one_rm = int(float(wt))
        )
    if wodform.validate_on_submit():
        one_rm = wodform.one_rm.data
        wod_reps = wodform.wod_reps.data
        if wod_reps > 30:
            wod_reps = 30
        rep_reduction_factor = rep_reduction[wod_reps]
        wod_weight = one_rm * rep_reduction_factor
        lift = int(wod_weight - wod_weight % 5)
        liftstring = f"For a 1RM of {one_rm}#, the recommended weight is no more than {lift}# for {wod_reps} reps."
        return render_template("wodweight.html", page_class="index-page", liftstring=liftstring, rep=wod_reps, lift=lift, form=wodform, lid = lift_id, scrollToAnchor="results", current_user=current_user)
    return render_template("wodweight.html", page_class="index-page", form=wodform, lifstring="", current_user=current_user)

@app.route("/onerme", methods=["GET","POST"])
def onerme():
    one_rme_form = oneRMEForm()
    if one_rme_form.validate_on_submit():
        rep=one_rme_form.multirep.data
        load=one_rme_form.multirepload.data
        onerme = one_rm_calc(rep=rep , load=load)
        onermestring = f"Lifting {load}# for {rep} repetitions is equivalent to a one rep lift of {onerme}#."
        return render_template("1rme.html", page_class="index-page", onermestring=onermestring, load=load, rep=rep, onerme=onerme, form=one_rme_form, scrollToAnchor="results", current_user=current_user, liftnumbers=lift_dict_map)
    return render_template("1rme.html", page_class="index-page", form=one_rme_form, onermestring="", current_user=current_user)

@app.route("/targets/<lift_id>/<load>/<lvl>", methods=["GET","POST"])
def targets(lift_id, load, lvl):
    if current_user.is_authenticated:
        form = TargetWeightForm(
            sex = current_user.sex,
            age = current_user.age,
            bw = current_user.bw,
            movement = str(lift_id)
        )
    else:
        form = TargetWeightForm()
    if form.validate_on_submit():
        # Store form data as variables
        tw_sex = form.sex.data
        tw_age = form.age.data
        tw_bodywt = form.bw.data
        tw_mvmt = form.movement.data

        bwt = bw_adjust_calc(bw=tw_bodywt, sex=tw_sex)
        targets = lift_target_list_calc(move=tw_mvmt, sex=tw_sex, bw=bwt, age=tw_age)

        # Pass in movement name
        move_descr = str(db.session.query(MovementCatalog.move).filter_by(id=tw_mvmt).first()).strip(")(,'")
        return render_template("target_weight.html", page_class="index-page", form=form, targets=targets, move=move_descr, onerm=load, liftlvl=lvl, resultsmode="true", scrollToAnchor="results", current_user=current_user, liftnumbers=lift_dict_map)
    return render_template("target_weight.html", page_class="index-page", form=form, resultsmode="", current_user=current_user)

@app.route("/mobile")
def mobile():
    if current_user.is_authenticated:
        return(redirect("/load/profile"))
    return render_template("home.html", page_class="index-page", current_user=current_user)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("404.html"), 404


if __name__ == '__main__':
    app.run(debug=True)