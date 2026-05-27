from flask import Flask, render_template, request, redirect, session, flash
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
import re

app = Flask(__name__)
app.secret_key = "secret123"


def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def valid_password(p):
    return (
        len(p) >= 8 and
        re.search(r"[A-Z]", p) and
        re.search(r"[a-z]", p) and
        re.search(r"[0-9]", p)
    )

def valid_voter_id(voter_id):
    return re.fullmatch(r"[A-Z]{3}[0-9]{7}", voter_id)

def valid_aadhar(aadhar):
    return re.fullmatch(r"[2-9][0-9]{11}", aadhar)

# ---------------- HOME ----------------

@app.route("/")
def home():
    return redirect("/dashboard")

# ✅ NEW ADDED ROUTE
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        voter_id = request.form["voter_id"].upper()
        aadhar = request.form["aadhar"]
        dob = date.fromisoformat(request.form["dob"])
        password = request.form["password"]

        if not valid_voter_id(voter_id):
            flash("Invalid Voter ID")
            return redirect("/register")

        if not valid_aadhar(aadhar):
            flash("Invalid Aadhaar Number")
            return redirect("/register")

        if calculate_age(dob) < 18:
            flash("Age must be 18 or above")
            return redirect("/register")

        if not valid_password(password):
            flash("Weak password")
            return redirect("/register")

        db = get_db_connection()
        cur = db.cursor()

        try:
            cur.execute(
                "INSERT INTO voters (voter_id,aadhar,dob,password_hash) VALUES (%s,%s,%s,%s)",
                (voter_id, aadhar, dob, generate_password_hash(password))
            )
            db.commit()
            flash("Registration successful")
            return redirect("/login")
        except:
            db.rollback()
            flash("User already exists")
            return redirect("/register")

    return render_template("register.html")

# ---------------- USER LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        voter_id = request.form["voter_id"]
        password = request.form["password"]

        db = get_db_connection()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM voters WHERE voter_id=%s", (voter_id.upper(),))
        user = cur.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["voter"] = user["id"]
            return redirect("/vote")

        flash("Invalid Voter ID or Password")

    return render_template("login.html")

# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT * FROM admin WHERE username=%s", (username,))
        admin = cur.fetchone()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin"] = admin["id"]
            return redirect("/admin/dashboard")

        flash("Invalid Admin Credentials")

    return render_template("admin.html")


@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "voter" not in session:
        return redirect("/login")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM votes WHERE voter_id=%s", (session["voter"],))
    already_voted = cur.fetchone()

    message = ""

    if request.method == "POST" and not already_voted:
        party = request.form["party"]

        cur.execute(
            "INSERT INTO votes (voter_id, party_id) VALUES (%s,%s)",
            (session["voter"], party)
        )
        db.commit()

        message = "Your vote has been recorded successfully!"
        already_voted = True

    cur.execute("SELECT * FROM parties")
    parties = cur.fetchall()

    return render_template(
        "vote.html",
        parties=parties,
        already_voted=already_voted,
        message=message
    )

# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total FROM voters")
    total_voters = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM votes")
    total_votes = cur.fetchone()["total"]

    cur.execute("""
        SELECT parties.name, COUNT(votes.party_id) AS vote_count
        FROM parties
        LEFT JOIN votes ON parties.id = votes.party_id
        GROUP BY parties.id
    """)
    results = cur.fetchall()

    return render_template("admin_dashboard.html",
                           total_voters=total_voters,
                           total_votes=total_votes,
                           results=results)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)