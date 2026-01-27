from flask import Flask, render_template, request, redirect, session, url_for
import os
import time
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.camera_routes import camera_bp
from backend.database import db, User  # <-- Import DB
from backend.state import USERS_ONLINE

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.urandom(24)
app.config['SESSION_PERMANENT'] = False

# --- DATABASE CONFIG ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///traffic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) # Connect DB

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

app.register_blueprint(dashboard_bp)
app.register_blueprint(camera_bp)

# --- CREATE TABLES & ADMIN ---
with app.app_context():
    db.create_all()
    # Agar admin nahi hai, toh banao
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', role='admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ Database created and Admin user added!")

# --- ROUTES ---
@app.route("/", methods=["GET"])
def root():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return redirect(url_for("dashboard.dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # DATABASE QUERY: Check user in DB
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session.clear()
            session["logged_in"] = True
            session["username"] = user.username
            session["role"] = user.role
            
            USERS_ONLINE.add(user.username)
            # Login time track karne ke liye hum state use kar sakte hain ya DB update kar sakte hain
            # Abhi simple rakhte hain
            return redirect(url_for("dashboard.dashboard"))
        else:
            return "Invalid Credentials", 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    username = session.get("username")
    USERS_ONLINE.discard(username)
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)