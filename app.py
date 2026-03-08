from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
from dotenv import load_dotenv
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta
import datetime
from functools import wraps
import logging
import smtplib
from email.message import EmailMessage
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from flask import session, redirect

load_dotenv()

SMTP_EMAIL = os.getenv("EMAIL_ADDRESS")
SMTP_PASS = os.getenv("EMAIL_PASSWORD")


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

IS_PRODUCTION = os.getenv("FLASK_ENV") == "production"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  #//live siis True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[] #MuudanKuiLive
)
limiter.init_app(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def worker_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "worker" or "worker_id" not in session:
            return redirect("/worker-login")
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()

        # ---------------- USERS tabel ----------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                reset_token TEXT,
                reset_token_expiry TEXT
            )
        """)

        # ---------------- PERSONS tabel ----------------
        c.execute("""
    CREATE TABLE IF NOT EXISTS persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        access_token TEXT,
        token_expiry TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
""")

        c.execute("PRAGMA table_info(persons);")
        columns = [col[1] for col in c.fetchall()]

        if "password" not in columns:
            c.execute("ALTER TABLE persons ADD COLUMN password TEXT;")

        if "email" not in columns:
            c.execute("ALTER TABLE persons ADD COLUMN email TEXT;")

        if "access_token" not in columns:
            c.execute("ALTER TABLE persons ADD COLUMN access_token TEXT;")

        if "token_expiry" not in columns:
            c.execute("ALTER TABLE persons ADD COLUMN token_expiry TEXT;")

        # ---------------- TASKS tabel ----------------
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                task_date TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT,
                contact TEXT,
                completed INTEGER DEFAULT NULL,
                FOREIGN KEY(person_id) REFERENCES persons(id)
            )
        """)

        conn.commit()
        print("Database initialized successfully.")


init_db()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def send_email(to_email, subject, body_text=None, body_html=None):
    """
    Üldine e-maili saatmise funktsioon.
    
    to_email   : string -> adressaadi e-mail
    subject    : string -> e-maili teema
    body_text  : string -> tavatekstiline sisu (plain text)
    body_html  : string -> HTML sisu (valikuline)
    """

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"KoodiOrav <{SMTP_EMAIL}>"
    msg["To"] = to_email

    if body_text is None:
        body_text = "Tere! Sinu e-maili sisu puudub."

    msg.set_content(body_text)

    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.zone.eu", 465) as smtp:
            smtp.login(SMTP_EMAIL, SMTP_PASS)
            smtp.send_message(msg)
        print(f"EMAIL SENT to {to_email}")
    except Exception as e:
        logging.exception("Email saatmise error")
        print(f"EMAIL ERROR: {e}")

reset_link = "https://example.com/reset/abc123"

body_text = f"""
Tere!

Olete soovinud parooli lähtestamist.
Klikkige allolevale lingile, et oma parool uuendada:

{reset_link}

Kui te ei palunud parooli lähtestamist, ignoreerige seda kirja.
"""

body_html = f"""
<html>
  <body>
    <p>Hea kasutaja!</p>
    <p>Klikkige allolevale nupule, et uuendada oma parool:</p>
    <a href="{reset_link}">Lähtesta parool</a>
  </body>
</html>
"""

person_name = "Jaagup"
description = "Kontrolli inventari"
date = "01/03/2026"
location = "Tallinn"
contact = "555-1234"

body_text = f"""
Tere {person_name}!

Sul on uus tööülesanne:

Kirjeldus: {description}
Kuupäev: {date}
Asukoht: {location}
Kontakt: {contact}

Parimate soovidega,
KoodiOrav
"""

body_html = f"""
<html>
  <body>
    <p>Tere {person_name}!</p>
    <p>Sul on uus tööülesanne:</p>
    <ul>
      <li><b>Kirjeldus:</b> {description}</li>
      <li><b>Kuupäev:</b> {date}</li>
      <li><b>Asukoht:</b> {location}</li>
      <li><b>Kontakt:</b> {contact}</li>
    </ul>
    <p>Parimate soovidega,<br>KoodiOrav</p>
  </body>
</html>
"""


def is_valid_email(email):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

# -------- ROUTES --------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register_page")
def register_page():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Vigane päring.", "success": False})
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "Palun täida kõik väljad.", "success": False})
    if not is_valid_email(email):
        return jsonify({"message": "Palun sisesta korrektne e-mail.", "success": False})

    hashed_password = generate_password_hash(password)

    try:
        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, hashed_password))
            conn.commit()
        return jsonify({"message": "Kasutaja loodud! ✅",
                         "success": True,
                           "note": "Suunan sind tagasi avalehele..."})
    except sqlite3.IntegrityError:
        return jsonify({"message": "Kasutajanimi või email juba olemas.", "success": False})

@app.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("SELECT id, password, username FROM users WHERE email = ?", (email,))
        user = c.fetchone()

    if user and check_password_hash(user[1], password):
        session["user"] = user[2]
        session["user_id"] = user[0]
        session.permanent = True
        return jsonify({"redirect": "/dashboard"})
    else:
        return jsonify({"message": "Vale e-mail või parool."}), 401

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/dashboard")
@login_required
def dashboard():
    username = session.get("user")
    return render_template("dashboard.html", username=username)

@app.route("/reset", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def resetPassword():
    if request.method == "GET":
        return render_template("reset.html")

    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"message": "Vigane päring."})

        email = data.get("email")
        if not email:
            return jsonify({"message": "Palun sisesta e-mail!"})

        try:
            with sqlite3.connect("users.db") as conn:
                c = conn.cursor()

                
                c.execute("SELECT id FROM users WHERE email = ?", (email,))
                user = c.fetchone()

                if user:
                    token = secrets.token_urlsafe(32)
                    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)

                    c.execute("""
                        UPDATE users
                        SET reset_token = ?, reset_token_expiry = ?
                        WHERE email = ?
                    """, (token, expiry.isoformat(), email))
                    conn.commit()

                    reset_link = url_for("new_password", token=token, _external=True)
                    send_email(email, "Parooli lähtestamise link", reset_link)

                else:
                    c.execute("SELECT id FROM persons WHERE email = ?", (email,))
                    person = c.fetchone()

                    if person:
                        token = secrets.token_urlsafe(32)
                        expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)

                        c.execute("""
                            UPDATE persons
                            SET access_token = ?, token_expiry = ?
                            WHERE email = ?
                        """, (token, expiry.isoformat(), email))
                        conn.commit()

                        reset_link = url_for("new_password", token=token, _external=True)
                        send_email(email, "Parooli lähtestamise link", reset_link)

            return jsonify({
                "message": "Kui sisestasite õige e-maili, saadetakse parooli lähtestamise link. Kui kirja ei leia, kontrollige ka rämpsposti kausta."
            })

        except Exception:
            logging.exception("Reset route error")
            return jsonify({"message": "Serveri viga."})

@app.route("/new-password/<token>", methods=["GET", "POST"])
def new_password(token):
    try:
        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()

            c.execute("SELECT id, reset_token_expiry FROM users WHERE reset_token = ?", (token,))
            user = c.fetchone()
            person = None

            if not user:
                c.execute("SELECT id, token_expiry FROM persons WHERE access_token = ?", (token,))
                person = c.fetchone()
                if not person:
                    return "Invalid token"

            expiry_time = datetime.datetime.fromisoformat(user[1] if user else person[1])
            if datetime.datetime.utcnow() > expiry_time:
                return "Token expired"

            if request.method == "POST":
                data = request.get_json() or {}
                new_password = (data.get("password") or "").strip()

                if len(new_password) < 8:
                    return jsonify({"message": "Parool peab olema vähemalt 8 tähemärki."})

                hashed = generate_password_hash(new_password)

                if user:
                    c.execute("""
                        UPDATE users
                        SET password = ?, reset_token = NULL, reset_token_expiry = NULL
                        WHERE id = ?
                    """, (hashed, user[0]))
                else:
                    c.execute("""
                        UPDATE persons
                        SET password = ?, access_token = NULL, token_expiry = NULL
                        WHERE id = ?
                    """, (hashed, person[0]))

                conn.commit()
                return jsonify({"message": "Parool edukalt muudetud!"})

        return render_template("new_password.html")

    except Exception:
        logging.exception("New password route error")
        return "Serveri viga."
    

@app.route("/add-task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return jsonify({"error": "Pole sisse logitud"}), 401

    data = request.get_json()
    task_date = data.get("date")
    description = data.get("description")
    location = data.get("location")
    contact = data.get("contact")
    person_id = data.get("person_id")

    if not person_id:
        return jsonify({"error": "Andmed puuduvad"}), 400

    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO tasks (person_id, task_date, description, location, contact, completed)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (person_id, task_date, description, location, contact))
        conn.commit()

        c.execute("SELECT name, email FROM persons WHERE id = ?", (person_id,))
        person = c.fetchone()

    if person and person[1]:
        person_name = person[0]
        person_email = person[1]

        body_text = f"""
Tere {person_name}!

Sul on uus tööülesanne:

Kirjeldus: {description}
Kuupäev: {task_date}
Asukoht: {location or '-'}
Kontakt: {contact or '-'}

Parimate soovidega,
KoodiOrav
"""
        body_html = f"""
<html>
  <body>
    <p>Tere {person_name}!</p>
    <p>Sul on uus tööülesanne:</p>
    <ul>
      <li><b>Kirjeldus:</b> {description}</li>
      <li><b>Kuupäev:</b> {task_date}</li>
      <li><b>Asukoht:</b> {location or '-'}</li>
      <li><b>Kontakt:</b> {contact or '-'}</li>
    </ul>
    <p>Parimate soovidega,<br>KoodiOrav</p>
  </body>
</html>
"""
        send_email(to_email=person_email, subject="Uus tööülesanne", body_text=body_text, body_html=body_html)

    return jsonify({"message": "Ülesanne lisatud ja e-mail saadetud!"})


@app.route("/send-tasks-email/<int:person_id>", methods=["POST"])
def send_tasks_email(person_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Pole sisse logitud"}), 401

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        SELECT name, email FROM persons 
        WHERE id = ? AND user_id = ?
    """, (person_id, session["user_id"]))
    person = c.fetchone()

    if not person:
        conn.close()
        return jsonify({"success": False, "message": "Isik puudub"}), 404

    person_name, to_email = person

    if not to_email:
        conn.close()
        return jsonify({"success": False, "message": "Inimese e-mail puudub"}), 400

    c.execute("""
        SELECT description, task_date, location, contact, completed
        FROM tasks
        WHERE person_id = ?
    """, (person_id,))
    tasks = c.fetchall()

    if not tasks:
        conn.close()
        return jsonify({"success": False, "message": "Ülesandeid pole"}), 400

    token = secrets.token_urlsafe(32)
    expiry = datetime.datetime.utcnow() + datetime.timedelta(days=3)

    c.execute("""
        UPDATE persons
        SET access_token = ?, token_expiry = ?
        WHERE id = ? AND user_id = ?
    """, (token, expiry.isoformat(), person_id, session["user_id"]))

    if c.rowcount == 0:
        conn.close()
        return jsonify({"success": False, "message": "Tokeni salvestamine ebaõnnestus"}), 500

    conn.commit()
    conn.close()

    # 🔗 Loo access link
    access_link = f"http://127.0.0.1:8000/person/{token}"
    body_text = f"Tere {person_name}!\n\nSul on järgmised ülesanded:\n"
    body_html = f"<html><body><p>Tere {person_name}!</p><p>Sul on järgmised ülesanded:</p><ul>"

    for desc, date, loc, contact, completed in tasks:
        status = "Tehtud" if completed == 1 else "Tegemata"
        body_text += f"- {desc} | {date} | {loc} | {contact} | {status}\n"
        body_html += f"<li><b>{desc}</b> | {date} | {loc} | {contact} | {status}</li>"

    body_html += "</ul>"
    body_html += f"""
    <p>
        <a href="{access_link}" style="padding:12px 24px;background:#4CAF50;color:white;
        text-decoration:none;border-radius:8px;display:inline-block;">
        Ava oma ülesanded
        </a>
    </p>
    </body></html>
    """

    send_email(
        to_email=to_email,
        subject="Teie ülesanded",
        body_text=body_text,
        body_html=body_html
    )

    return jsonify({"success": True, "count": len(tasks)})

@app.route("/get-tasks/<date>")
@login_required
def get_tasks(date):
    person_id = request.args.get("person_id")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    query = """
        SELECT tasks.id, persons.name, tasks.description, tasks.location, tasks.contact, tasks.completed
        FROM tasks
        JOIN persons ON tasks.person_id = persons.id
        WHERE persons.user_id = ? AND tasks.task_date = ?
    """
    params = [session["user_id"], date]

    if person_id:
        query += " AND persons.id = ?"
        params.append(person_id)

    c.execute(query, params)
    tasks = c.fetchall()
    conn.close()

    return jsonify(tasks)

@app.route("/get-tasks-worker")
@worker_login_required
def get_tasks_worker():
    worker_id = session.get("worker_id")

    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, description, task_date, location, contact, completed
            FROM tasks
            WHERE person_id = ?
            ORDER BY task_date ASC
        """, (worker_id,))
        tasks = c.fetchall()

    result = [
        {
            "id": t[0],
            "description": t[1],
            "task_date": t[2],
            "location": t[3],
            "contact": t[4],
            "completed": t[5]
        } for t in tasks
    ]
    return jsonify(result)

@app.route("/toggle-task/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):

    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tasks
            SET completed = CASE WHEN completed = 0 THEN 1 ELSE 0 END
            WHERE id = ? AND person_id IN (
                SELECT id FROM persons WHERE user_id = ?
            )
        """, (task_id, session["user_id"]))
        conn.commit()

    return jsonify({"success": True})

@app.route("/delete-task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("""
            DELETE FROM tasks
            WHERE id = ? AND person_id IN (
                SELECT id FROM persons WHERE user_id = ?
            )
        """, (task_id, session["user_id"]))
        conn.commit()

    return jsonify({"success": True})

@app.route("/mark-done/<int:task_id>", methods=["POST"])
def mark_done(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tasks
            SET completed = 1
            WHERE id = ? AND person_id IN (
                SELECT id FROM persons WHERE user_id = ?
            )
        """, (task_id, session["user_id"]))
        conn.commit()
    return jsonify({"success": True})

# Tegemata
@app.route("/mark-not-done/<int:task_id>", methods=["POST"])
def mark_not_done(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tasks
            SET completed = 0
            WHERE id = ? AND person_id IN (
                SELECT id FROM persons WHERE user_id = ?
            )
        """, (task_id, session["user_id"]))
        conn.commit()

        return jsonify({"success": True})

@app.route("/add-person", methods=["POST"])
@login_required
def add_person():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not name or not email:
        return jsonify({"error": "Täida vähemalt nimi ja e-mail!"}), 400


    if not password:
        password = secrets.token_urlsafe(8)
    hashed_password = generate_password_hash(password)

    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM persons WHERE user_id = ? AND email = ?", (session["user_id"], email))
        existing = c.fetchone()
        if existing:
            return jsonify({"success": True, "person_id": existing[0], "message": "Töötaja juba olemas."})

        c.execute(
            "INSERT INTO persons (user_id, name, email, password) VALUES (?, ?, ?, ?)",
            (session["user_id"], name, email, hashed_password)
        )
        conn.commit()
        person_id = c.lastrowid


    body_text = f"""
Tere {name}!

Sinu töötajakonto on loodud.

E-mail: {email}
Parool: {password}

Parimate soovidega,
KoodiOrav
"""
    body_html = f"""
<html>
  <body>
    <p>Tere {name}!</p>
    <p>Sinu töötajakonto on loodud:</p>
    <ul>
      <li><b>E-mail:</b> {email}</li>
      <li><b>Parool:</b> {password}</li>
    </ul>
    <p>Parimate soovidega,<br>KoodiOrav</p>
  </body>
</html>
"""
    send_email(to_email=email, subject="Töötaja login info", body_text=body_text, body_html=body_html)

    return jsonify({"success": True, "person_id": person_id, "message": "Töötaja lisatud ja e-mail saadetud!"})

@app.route("/get-persons")
@login_required
def get_persons():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM persons WHERE user_id = ?", (session["user_id"],))
    persons = c.fetchall()
    conn.close()
    return jsonify(persons)


@app.route("/person/<token>")
def person_dashboard(token):

    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()

        c.execute("""
            SELECT id, name, token_expiry
            FROM persons
            WHERE access_token = ?
        """, (token,))
        person = c.fetchone()

        if not person:
            return "Link ei kehti"

        person_id, name, expiry = person

        if expiry:
            expiry_time = datetime.datetime.fromisoformat(expiry)
            if datetime.datetime.utcnow() > expiry_time:
                return "Link on aegunud"

        c.execute("""
            SELECT description, task_date, location, contact, completed
            FROM tasks
            WHERE person_id = ?
        """, (person_id,))
        tasks = c.fetchall()

    return render_template("person_dashboard.html", name=name, tasks=tasks)

@app.route("/worker-login", methods=["GET", "POST"])
def worker_login():
    if request.method == "GET":

        return render_template("worker_login.html")


    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Täida kõik väljad!"})

    with sqlite3.connect("users.db") as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, password FROM persons WHERE email = ?", (email,))
        worker = c.fetchone()

    if worker and worker[2] and check_password_hash(worker[2], password):
        session["worker_id"] = worker[0]
        session["worker_name"] = worker[1]
        session["role"] = "worker"
        session.permanent = True
        return jsonify({"redirect": "/worker-dashboard"})
    else:
        return jsonify({"message": "Vale e-mail või parool."})
    
@app.route("/worker-dashboard")
@worker_login_required
def worker_dashboard():
    if session.get("role") != "worker" or "worker_id" not in session:
        return redirect("/worker-login")

    worker_name = session["worker_name"]

    return render_template("worker_dashboard.html", name=worker_name)

@app.route("/worker-new-password/<token>", methods=["GET", "POST"])
def worker_new_password(token):
    try:
        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()
            c.execute("SELECT id, reset_token_expiry FROM persons WHERE access_token = ?", (token,))
            worker = c.fetchone()
            if not worker:
                return "Link ei kehti"

            worker_id, expiry = worker
            if expiry:
                expiry_time = datetime.fromisoformat(expiry)
                if datetime.utcnow() > expiry_time:
                    return "Link on aegunud"

            if request.method == "POST":
                data = request.get_json() or {}
                new_password = (data.get("password") or "").strip()

                if len(new_password) < 8:
                    return jsonify({"message": "Parool peab olema vähemalt 8 tähemärki."})

                hashed = generate_password_hash(new_password)

                c.execute("ALTER TABLE persons ADD COLUMN IF NOT EXISTS password TEXT")
                c.execute("""
                    UPDATE persons
                    SET password = ?, access_token = NULL, token_expiry = NULL
                    WHERE id = ?
                """, (hashed, worker_id))
                conn.commit()

                return jsonify({"message": "Parool edukalt muudetud!"})

        return render_template("worker_new_password.html")

    except Exception:
        logging.exception("Worker new password route error")
        return "Serveri viga."

@app.route("/worker-logout")
def worker_logout():
    session.pop("worker_id", None)
    session.pop("worker_name", None)
    return redirect("/worker-login")

# -------- RUN APP --------
if __name__ == "__main__":
    app.run(port=8000, debug=True) #// live siis False