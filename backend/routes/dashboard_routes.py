from flask import Blueprint, render_template, session, request, jsonify
from backend.auth.decorators import login_required
from backend.database import db, Hub, User # Import Models
from backend.state import USERS_ONLINE
import uuid

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    current_role = session.get("role", "viewer")

    # 1. Fetch Hubs from Database
    all_hubs = Hub.query.all()
    
    # Format for template
    hubs_data = [(h.id, h) for h in all_hubs]
    
    # Sort by traffic (Python list sorting)
    hubs_sorted = sorted(hubs_data, key=lambda x: x[1].traffic, reverse=True)

    # 2. Users Panel Logic
    my_users = []
    if current_role in ["admin", "manager"]:
        # DB se users fetch karo (Simple logic for now)
        db_users = User.query.filter(User.role != 'admin').all()
        for u in db_users:
            status = "Online" if u.username in USERS_ONLINE else "Offline"
            my_users.append({"username": u.username, "duration": status})

    return render_template("dashboard.html", hubs=hubs_sorted, my_users=my_users, role=current_role)

@dashboard_bp.route("/add_hub", methods=["POST"])
@login_required
def add_hub():
    data = request.json
    name = data.get("name")
    
    if not name: return jsonify({"error": "Name required"}), 400

    # Create new Hub in DB
    new_id = f"hub_{uuid.uuid4().hex[:6]}" # Random Unique ID
    new_hub = Hub(id=new_id, name=name, traffic=0)
    
    db.session.add(new_hub)
    db.session.commit()

    return jsonify({"success": True})

@dashboard_bp.route("/delete_hub", methods=["POST"])
@login_required
def delete_hub():
    data = request.json
    hub_id = data.get("id")
    
    hub = Hub.query.get(hub_id)
    if hub:
        db.session.delete(hub)
        db.session.commit()
        return jsonify({"success": True})
    
    return jsonify({"error": "Not found"}), 404

@dashboard_bp.route("/create_user", methods=["POST"])
@login_required
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 400

    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"success": True})


@dashboard_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    data = request.json
    old_pass = data.get("old_password")
    new_pass = data.get("new_password")
    
    # Session se current user nikalo
    current_username = session.get("username")
    user = User.query.filter_by(username=current_username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check agar purana password sahi hai
    if user.password == old_pass:
        user.password = new_pass # Naya password save karo
        db.session.commit()
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Incorrect old password!"}), 400