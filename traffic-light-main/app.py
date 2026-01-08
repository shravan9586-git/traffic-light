from flask import Flask,render_template,Response,request,jsonify,send_from_directory
import cv2
import os
import time
from werkzeug.utils import secure_filename
from datetime import datetime
from ultralytics import YOLO

app=Flask(__name__)

model = YOLO('yolo11n.pt')
camera=0
cap = cv2.VideoCapture(camera,cv2.CAP_FFMPEG)

UPLOAD_FOLDER=os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS={'png','jpg','jpeg','gif'}

app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER,exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def generate():
    global cap
    frame_counter=0
    frame_skip=3
    while True:
        if not cap.isOpened():
            print("IP Camera not reachable")
            time.sleep(1)
            continue

        ret, frame = cap.read()
        if not ret:
            print("Frame not received")
            time.sleep(0.1)
            continue
        frame_counter += 1
        if frame_counter % frame_skip != 0:
            results = model(frame, imgsz=416)  # or 320
            annotated_frame = results[0].plot()

        # Timestamp
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cv2.putText(
            annotated_frame,
            current_time,
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )

        ret, jpeg = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/set-camera', methods=['POST'])
def set_camera():
    global cap, camera
    data = request.json
    new = data.get('camera')

    if new is None:
        return jsonify({'error': 'no source provided'}), 400

    cap.release()

    try:
        camera = int(new)
    except:
        camera = new

    cap = cv2.VideoCapture(camera, cv2.CAP_FFMPEG)
    return jsonify({'message': 'camera source updated'})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload-image',methods=['POST'])
def upload_image():
    print("Upload called")
    if 'image' not in request.files:
        return jsonify({'error':'no file part'}),400
    file=request.files['image']

    if file.filename=='':
        return jsonify({'error':'no selected file'}),400
    
    if file and allowed_file(file.filename):
        filename=secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))

        return jsonify({
            'message':'file upload successfully',
            'filename':filename
        }),200
    return jsonify({'error':'invalid file type'}),400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

if __name__=="__main__":
    app.run(port=8000,debug=True)
