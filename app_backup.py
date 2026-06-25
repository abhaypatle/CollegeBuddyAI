from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
import sqlite3
import os
from reportlab.pdfgen import canvas

app = Flask(__name__)

app.secret_key = "collegebuddyai"

# -------------------------------
# SAFE CSV LOADING (NO CRASH)
# -------------------------------
CSV_FILE = "college_buddy_dataset.csv"

if os.path.exists(CSV_FILE):
    data = pd.read_csv(CSV_FILE)
    data = data.rename(columns={"id": "college", "name": "city", "course": "branch", "score": "cutoff"})
else:
    data = pd.DataFrame(columns=["college", "city", "branch", "cutoff"])

# -------------------------------
# DATABASE INIT
# -------------------------------
def init_db():
    conn = sqlite3.connect("collegebuddy.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        branch TEXT,
        percentile REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------------------
# LOGIN PAGE
# -------------------------------
@app.route("/")
def login():
    return render_template("login.html")

# -------------------------------
# REGISTER PAGE
# -------------------------------
@app.route("/register")
def register():
    return render_template("register.html")

# -------------------------------
# REGISTER USER
# -------------------------------
@app.route("/register_user", methods=["POST"])
def register_user():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("collegebuddy.db")
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, password)
        )
        conn.commit()
    except:
        return "User already exists ❌"

    conn.close()

    return redirect("/")

# -------------------------------
# LOGIN USER
# -------------------------------
@app.route("/login_user", methods=["POST"])
def login_user():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("collegebuddy.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cur.fetchone()
    conn.close()

    if user:
        session["user"] = user[1]
        return redirect("/dashboard")

    return "Invalid Login ❌"

# -------------------------------
# DASHBOARD
# -------------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html", name=session["user"])

# -------------------------------
# COLLEGE PREDICTOR PAGE
# -------------------------------
@app.route("/predict")
def predict():
    return render_template("index.html")

# -------------------------------
# RESULT LOGIC (SAFE)
# -------------------------------
@app.route("/result", methods=["POST"])
def result():
    if "user" not in session:
        return redirect("/")

    branch = request.form["branch"]
    percentile = float(request.form["percentile"])

    filtered = data[data["branch"].str.lower() == branch.lower()] if not data.empty else pd.DataFrame()

    safe = filtered[filtered["cutoff"] <= percentile]
    target = filtered[(filtered["cutoff"] > percentile) & (filtered["cutoff"] <= percentile + 5)]
    dream = filtered[filtered["cutoff"] > percentile + 5]

    conn = sqlite3.connect("collegebuddy.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO predictions(student,branch,percentile)
        VALUES(?,?,?)
    """, (session["user"], branch, percentile))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        safe=safe.to_dict("records"),
        target=target.to_dict("records"),
        dream=dream.to_dict("records")
    )

# -------------------------------
# SCHOLARSHIP
# -------------------------------
@app.route("/scholarship")
def scholarship():
    return render_template("scholarship.html")

@app.route("/scholarship_result", methods=["POST"])
def scholarship_result():
    percentile = float(request.form["percentile"])
    income = int(request.form["income"])

    scholarships = []

    if percentile >= 90:
        scholarships.append("Merit Scholarship")

    if income <= 200000:
        scholarships.append("EBC Scholarship")

    if percentile >= 75:
        scholarships.append("Private Scholarship")

    return render_template("scholarship_result.html", scholarships=scholarships)

# -------------------------------
# PLACEMENT
# -------------------------------
@app.route("/placement")
def placement():
    return render_template("placement.html")

@app.route("/placement_result", methods=["POST"])
def placement_result():
    cgpa = float(request.form["cgpa"])

    if cgpa >= 9:
        chance = "95%"
    elif cgpa >= 8:
        chance = "80%"
    elif cgpa >= 7:
        chance = "65%"
    else:
        chance = "40%"

    return render_template("placement_result.html", chance=chance)

# -------------------------------
# HISTORY
# -------------------------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("collegebuddy.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM predictions WHERE student=?",
        (session["user"],)
    )

    rows = cur.fetchall()
    conn.close()

    return render_template("history.html", rows=rows)

# -------------------------------
# PDF REPORT
# -------------------------------
@app.route("/pdf")
def pdf():
    if "user" not in session:
        return redirect("/")

    pdf_name = "report.pdf"
    c = canvas.Canvas(pdf_name)

    c.drawString(100, 800, "College Buddy AI Report")
    c.drawString(100, 770, f"Student: {session['user']}")
    
    c.save()

    return send_file(pdf_name, as_attachment=True)

# -------------------------------
# LOGOUT
# -------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)