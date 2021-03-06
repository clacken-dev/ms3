import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
def home():
    return render_template("landing.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@app.route("/patients")
def get_info():
    patients = list(mongo.db.patients.find())
    return render_template("patients.html", patients=patients)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
              existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Logged in as:  {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("landing.html")


@app.route("/overview")
def overview():
    patients = list(mongo.db.patients.find())
    total_patients = len(patients)
    ward_a = list(mongo.db.patients.find({"ward": "a"}))
    total_ward_a = len(ward_a)
    ward_b = list(mongo.db.patients.find({"ward": "b"}))
    total_ward_b = len(ward_b)
    ward_c = list(mongo.db.patients.find({"ward": "c"}))
    total_ward_c = len(ward_c)
    ward_d = list(mongo.db.patients.find({"ward": "d"}))
    total_ward_d = len(ward_d)
    critical_patients = list(mongo.db.patients.find({"is_critical": "on"}))
    total_critical = len(critical_patients)
    return render_template(
        "overview.html", total_patients=total_patients,
        patients=patients, total_ward_a=total_ward_a,
        total_ward_b=total_ward_b, total_ward_c=total_ward_c,
        total_ward_d=total_ward_d, total_critical=total_critical)


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return redirect(url_for("overview", username=username))

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    session.pop("user")
    return render_template("landing.html")


@app.route("/add_patient", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        is_critical = "on" if request.form.get("is_critical") else "off"
        patient = {
            "first_name": request.form.get("first_name").lower(),
            "last_name": request.form.get("last_name").lower(),
            "dob": request.form.get("dob"),
            "ward": request.form.get("ward").lower(),
            "is_critical": is_critical,
            "notes": request.form.get("notes"),
            "added_by": session["user"]
        }
        mongo.db.patients.insert_one(patient)
        flash("Patient Successfully Added")
        return redirect(url_for("get_info"))
    return render_template("add_patient.html")


@app.route("/edit_patient/<patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    if request.method == "POST":
        is_critical = "on" if request.form.get("is_critical") else "off"
        submit = {
            "first_name": request.form.get("first_name").lower(),
            "last_name": request.form.get("last_name").lower(),
            "dob": request.form.get("dob"),
            "ward": request.form.get("ward").lower(),
            "is_critical": is_critical,
            "notes": request.form.get("notes"),
            "added_by": session["user"]
        }
        mongo.db.patients.update({"_id": ObjectId(patient_id)}, submit)
        flash("Patient Successfully Updated")
        return redirect(url_for("get_info"))

    patient = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    return render_template("edit_patient.html", patient=patient)


@app.route("/delete_patient/<patient_id>")
def delete_patient(patient_id):
    mongo.db.patients.remove({"_id": ObjectId(patient_id)})
    flash("Patient Successfully Deleted")
    return redirect(url_for("get_info"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
