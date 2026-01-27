from flask import Blueprint, render_template, request, jsonify, session, Response
from backend.auth.decorators import login_required
from backend.models import db, Hub, Camera
import cv2
import time

camera_bp = Blueprint("camera", __name__)
# Yellow light transition state tracker
TRANSITION = { "state": "idle", "from": None, "to": None, "start": 0 }

def generate_frames(path):
    cap = cv2.VideoCapture(path)
    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@camera_bp.route("/hub/<hub_id>")
@login_required
def hub_view(hub_id):
    hub = Hub.query.get(hub_id)
    if not hub: return "Hub Not Found", 404
    
    cameras = Camera.query.filter_by(hub_id=hub_id).all()
    cam_dict = {c.id: {"name": c.name, "ip": c.ip, "light": c.light, "vehicles": c.vehicles} for c in cameras}
    
    return render_template("hub.html", hub_id=hub_id, hub_name=hub.name, cameras=cam_dict, role=session.get("role"), global_mode="manual")

@camera_bp.route("/video_feed/<cid>")
def video_feed(cid):
    cam = Camera.query.get(cid)
    if cam:
        return Response(generate_frames(cam.ip), mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Error", 404

@camera_bp.route("/state")
def get_state():
    fsm_tick()
    all_cams = Camera.query.all()
    return jsonify({"cameras": {c.id: {"light": c.light, "vehicles": c.vehicles} for c in all_cams}})

def fsm_tick():
    global TRANSITION
    if TRANSITION["state"] == "yellow":
        if time.time() - TRANSITION["start"] >= 3:
            c_from = Camera.query.get(TRANSITION["from"])
            c_to = Camera.query.get(TRANSITION["to"])
            if c_from: c_from.light = "red"
            if c_to: c_to.light = "green"
            TRANSITION["state"] = "idle"
            db.session.commit()

@camera_bp.route("/set_light", methods=["POST"])
def set_light():
    global TRANSITION
    data = request.json
    target = data.get("id")
    hub_id = data.get("hub_id")
    
    current_green = Camera.query.filter_by(hub_id=hub_id, light="green").first()
    target_cam = Camera.query.get(target)

    if not current_green:
        if target_cam: 
            target_cam.light = "green"
            db.session.commit()
        return jsonify({"ok": True})

    if current_green.id == target: return jsonify({"ok": True})

    current_green.light = "yellow"
    TRANSITION = {"state": "yellow", "from": current_green.id, "to": target, "start": time.time()}
    db.session.commit()
    return jsonify({"yellow": current_green.id})

@camera_bp.route("/add_camera", methods=["POST"])
@login_required
def add_camera():
    data = request.json
    cid = str(int(time.time()))
    new_c = Camera(id=cid, hub_id=data['hub_id'], name=data['name'], ip=data['ip'], light="red")
    db.session.add(new_c)
    db.session.commit()
    return jsonify({"ok": True})