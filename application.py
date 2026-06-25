from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
import sqlite3
import os
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "collegebuddyai"

CSV_FILE = "college_buddy_dataset.csv"

if os.path.exists(CSV_FILE):
    data = pd.read_csv(CSV_FILE)
    data = data.rename(columns={
        "id": "college",
        "name": "city",
        "course": "branch",
        "score": "cutoff"
    })
else:
    data = pd.DataFrame(columns=["college", "city", "branch", "cutoff"])


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


@app.route("/")
def login():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


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
        conn.close()
        return "User already exists ❌"

    conn.close()
    return redirect("/")


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


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html", name=session["user"])


@app.route("/predict")
def predict():
    if "user" not in session:
        return redirect("/")

    return render_template("index.html")


@app.route("/result", methods=["POST"])
def result():
    if "user" not in session:
        return redirect("/")

    branch = request.form["branch"]
    percentile = float(request.form["percentile"])
    city = request.form.get("city", "")

    if not data.empty:
        filtered = data[data["branch"].str.lower() == branch.lower()]

        if city:
            city_filtered = filtered[filtered["city"].str.lower() == city.lower()]
            if not city_filtered.empty:
                filtered = city_filtered
    else:
        filtered = pd.DataFrame(columns=["college", "city", "branch", "cutoff"])

    safe = filtered[filtered["cutoff"] <= percentile].sort_values(
        by="cutoff", ascending=False
    ).head(5)

    target = filtered[
        (filtered["cutoff"] > percentile) &
        (filtered["cutoff"] <= percentile + 5)
    ].sort_values(by="cutoff", ascending=True).head(5)

    dream = filtered[filtered["cutoff"] > percentile + 5].sort_values(
        by="cutoff", ascending=True
    ).head(5)

    conn = sqlite3.connect("collegebuddy.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO predictions(student,branch,percentile)
        VALUES(?,?,?)
    """, (session["user"], branch, percentile))

    conn.commit()
    conn.close()

    probability = min(100, round(percentile))
    match_score = min(100, round((percentile * 0.5) + 40))

    if probability >= 80:
        recommendation_level = "Safe"
    elif probability >= 50:
        recommendation_level = "Target"
    else:
        recommendation_level = "Dream"

    placement_score = min(100, round(percentile * 0.85 + 10))
    avg_package = round(3 + (percentile / 100) * 10, 1)
    roi_score = round(min(10, avg_package / 1.2), 1)

    if percentile >= 90:
        scholarship_status = "High Chance"
    elif percentile >= 75:
        scholarship_status = "Available"
    else:
        scholarship_status = "Limited"

    return render_template(
        "result.html",
        safe=safe.to_dict("records"),
        target=target.to_dict("records"),
        dream=dream.to_dict("records"),
        probability=probability,
        match_score=match_score,
        recommendation_level=recommendation_level,
        placement_score=placement_score,
        avg_package=avg_package,
        roi_score=roi_score,
        scholarship_status=scholarship_status
    )


@app.route("/scholarship")
def scholarship():
    if "user" not in session:
        return redirect("/")
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


@app.route("/placement")
def placement():
    if "user" not in session:
        return redirect("/")
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


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if "user" not in session:
        return redirect("/")

    answer = ""

    if request.method == "POST":
        question = request.form["question"].lower()

        if "85" in question and "pune" in question and ("cse" in question or "computer" in question):
            answer = """
            Based on 85 percentile, Pune city, and CSE preference:

            Safe Colleges:
            - Sinhgad Pune
            - MIT WPU Pune

            Target Colleges:
            - AISSMS Pune
            - Vishwakarma Pune

            Dream Colleges:
            - PICT Pune
            - PCCOE Pune

            Scholarship: Available
            Placement Potential: Good
            """

        elif "cse" in question or "computer" in question:
            answer = "CSE is a high-demand branch with strong placement scope in software, AI, data science, and cloud roles."

        elif "pune" in question:
            answer = "Pune is a strong education hub. COEP, PICT, VIT, PCCOE, MIT WPU, and AISSMS are popular options."

        elif "scholarship" in question:
            answer = "Scholarships depend on percentile, category, family income, and college policy."

        elif "placement" in question:
            answer = "Placement depends on college, branch, CGPA, skills, internships, and projects."

        else:
            answer = "Ask about colleges, branches, placement, scholarship, cutoff, city preference, or admission chance."

    return render_template("chatbot/chatbot.html", answer=answer)

@app.route("/comparison")
def comparison():
    if "user" not in session:
        return redirect("/")

    return render_template("comparison.html")


@app.route("/pdf")
def pdf():
    if "user" not in session:
        return redirect("/")

    pdf_name = "report.pdf"
    c = canvas.Canvas(pdf_name)

    c.drawString(100, 800, "CollegeBuddyAI Premium Report")
    c.drawString(100, 770, f"Student: {session['user']}")
    c.drawString(100, 740, "Features: Admission Prediction, Scholarship, Placement, Safe/Target/Dream")

    c.save()

    return send_file(pdf_name, as_attachment=True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)  