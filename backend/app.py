from flask import Flask, render_template, request, redirect, session, url_for
import os
import time
from backend.models import db, User
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.camera_routes import camera_bp

app = Flask(__name__, template_folder='templates', static_folder='static')

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///traffic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "PROJECT_SECRET_KEY_123" 

db.init_app(app)

with app.app_context():
    db.create_all()
    # Default Admin login: admin / admin123
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="admin123", role="admin", created_by="system")
        db.session.add(admin)
        db.session.commit()

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

app.register_blueprint(dashboard_bp)
app.register_blueprint(camera_bp)

@app.route("/")
def root():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return redirect(url_for("dashboard.dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            session["role"] = user.role
            user.login_time = time.time()
            db.session.commit()
            return redirect(url_for("dashboard.dashboard"))
        return "Invalid Credentials", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if user:
        user.login_time = None
        db.session.commit()
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)