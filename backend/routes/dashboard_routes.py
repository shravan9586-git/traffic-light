from flask import Blueprint, render_template, session, request, jsonify
from backend.auth.decorators import login_required
from backend.models import db, User, Hub
import time

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    current_user = session.get("username")
    current_role = session.get("role")

    # DB se Hubs lana
    all_hubs = Hub.query.all()
    hubs_list = [(h.id, {"name": h.name, "traffic": h.traffic}) for h in all_hubs]

    # Side panel ke liye users filter karna
    my_users = []
    if current_role == "manager":
        users = User.query.filter_by(created_by=current_user).all()
        for u in users:
            if u.login_time:
                dur = int((time.time() - u.login_time) / 60)
                my_users.append({"username": u.username, "duration": f"{dur} mins"})
    elif current_role == "admin":
        users = User.query.filter(User.role != 'admin').all()
        for u in users:
            if u.login_time:
                my_users.append({"username": u.username, "duration": "Active"})

    return render_template("dashboard.html", role=current_role, hubs=hubs_list, users=my_users)

@dashboard_bp.route("/add_hub", methods=["POST"])
@login_required
def add_hub():
    data = request.json
    hid = "hub" + str(int(time.time()))
    new_h = Hub(id=hid, name=data['name'], traffic=0)
    db.session.add(new_h)
    db.session.commit()
    return jsonify({"success": True})

@dashboard_bp.route("/delete_hub", methods=["POST"])
@login_required
def delete_hub():
    hid = request.json.get("id")
    hub = Hub.query.get(hid)
    if hub:
        db.session.delete(hub)
        db.session.commit()
    return jsonify({"success": True})

@dashboard_bp.route("/create_user", methods=["POST"])
@login_required
def create_user():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User exists"}), 400
    
    new_u = User(
        username=data['username'],
        password=data['password'],
        role=data['role'],
        created_by=session.get("username")
    )
    db.session.add(new_u)
    db.session.commit()
    return jsonify({"success": True})