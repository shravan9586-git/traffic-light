from flask import Blueprint, render_template, request, Response, jsonify, session
from backend.auth.decorators import login_required
from backend.database import db, Hub, Camera
import cv2
import time
import uuid

camera_bp = Blueprint("camera", __name__)
GLOBAL_MODE = "manual"

# State Dictionary
TRANSITION = { "state": "idle", "from": None, "to": None, "start": 0 }

def generate_frames(path):
    cap = cv2.VideoCapture(path)
    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        _, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

# ==========================================
# 1. FSM TICK (Timer Logic for Yellow Light)
# ==========================================
def fsm_tick():
    # Agar Yellow light nahi chal rahi, to kuch mat karo
    if TRANSITION["state"] != "yellow": return

    # Check karo 3 second pure hue ya nahi
    if time.time() - TRANSITION["start"] >= 3:
        
        # Step 1: Purani Light (jo Yellow thi) ko RED karo
        if TRANSITION["from"]:
            prev_cam = Camera.query.get(TRANSITION["from"])
            if prev_cam:
                prev_cam.light = "red"
        
        # Step 2: Nayi Light ko GREEN karo
        if TRANSITION["to"]:
            next_cam = Camera.query.get(TRANSITION["to"])
            if next_cam:
                next_cam.light = "green"
        
        db.session.commit()
        
        # Logic Reset
        TRANSITION["state"] = "idle"
        TRANSITION["from"] = None
        TRANSITION["to"] = None
        TRANSITION["start"] = 0

@camera_bp.route("/hub/<hub_id>")
@login_required
def hub(hub_id):
    fsm_tick()
    hub = Hub.query.get_or_404(hub_id)
    cameras = Camera.query.filter_by(hub_id=hub_id).all()
    cameras_dict = {c.id: c for c in cameras}
    
    return render_template(
        "hub.html", 
        hub_id=hub.id, hub_name=hub.name, 
        cameras=cameras_dict, 
        global_mode=GLOBAL_MODE, 
        role=session.get("role")
    )

@camera_bp.route("/add_camera", methods=["POST"])
@login_required
def add_camera():
    data = request.json
    new_id = f"cam_{uuid.uuid4().hex[:6]}"
    new_cam = Camera(
        id=new_id, name=data["name"], ip=data["ip"],
        hub_id=data["hub_id"], light="red", vehicles=0
    )
    db.session.add(new_cam)
    db.session.commit()
    return jsonify({"ok": True})

@camera_bp.route("/edit_camera", methods=["POST"])
@login_required
def edit_camera():
    data = request.json
    cam = Camera.query.get(data["id"])
    if cam:
        cam.name = data["name"]
        cam.ip = data["ip"]
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@camera_bp.route("/delete_camera", methods=["POST"])
@login_required
def delete_camera():
    data = request.json
    cam = Camera.query.get(data["id"])
    if cam:
        db.session.delete(cam)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@camera_bp.route("/video/<cid>")
def video(cid):
    cam = Camera.query.get(cid)
    if not cam: return "", 404
    return Response(generate_frames(cam.ip), mimetype="multipart/x-mixed-replace; boundary=frame")

@camera_bp.route("/state")
def state():
    fsm_tick()
    all_cams = Camera.query.all()
    cams_dict = {c.id: {"light": c.light, "vehicles": c.vehicles} for c in all_cams}
    return jsonify({ "cameras": cams_dict })

# ==========================================
# 2. SET GREEN (Initiate Yellow Transition)
# ==========================================
@camera_bp.route("/set_green", methods=["POST"])
def set_green():
    target_id = request.json["id"]
    target_cam = Camera.query.get(target_id)
    
    if not target_cam:
        return jsonify({"error": "Camera not found"}), 404

    # Pata lagao ki abhi isi Hub mein kaunsi light GREEN hai
    current_green = Camera.query.filter_by(hub_id=target_cam.hub_id, light="green").first()
    
    # Agar koi bhi Green nahi hai, toh seedha Target ko Green kar do
    if not current_green:
        target_cam.light = "green"
        db.session.commit()
        return jsonify({"success": True})

    # Agar Target hi pehle se Green hai, toh kuch mat karo
    if current_green.id == target_id:
        return jsonify({"success": True})

    # ACTION: Current Green ko YELLOW karo
    current_green.light = "yellow"
    db.session.commit()

    # Timer Start karo (State = yellow)
    TRANSITION["state"] = "yellow"
    TRANSITION["from"] = current_green.id
    TRANSITION["to"] = target_id
    TRANSITION["start"] = time.time()
    
    return jsonify({"success": True})