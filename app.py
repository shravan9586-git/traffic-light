from flask import Flask,render_template,Response,request,jsonify,send_from_directory
import cv2
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from ultralytics import YOLO
import numpy as np

app=Flask(__name__, static_folder='static', static_url_path='/static')

# Load YOLOv11 nano model
try:
    model = YOLO('yolov11n.pt')
    print("YOLOv11 nano model loaded successfully")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

camera=0
cap = cv2.VideoCapture(camera,cv2.CAP_FFMPEG)
selected_object = ""
video_selected_object = ""
vehicle_count = 0
current_light_state = "RED"
green_time = 0

UPLOAD_FOLDER=os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS={'png','jpg','jpeg','gif'}

app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER,exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def detect_objects_in_image(image_path, target_object=""):
    """Detect objects in an image using YOLOv11"""
    if model is None:
        return None, 0
    
    try:
        results = model(image_path)
        img = cv2.imread(image_path)
        
        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes
            
            count = 0
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = box.conf[0].item()
                cls_name = model.names[cls_id]
                
                # Filter by selected object if specified
                if target_object and target_object.lower() != cls_name.lower():
                    continue
                
                if conf > 0.5:  # Confidence threshold
                    count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img, f"{cls_name} {conf:.2f}", (x1, y1 - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Save annotated image
            output_path = image_path.replace('.', '_detected.')
            cv2.imwrite(output_path, img)
            return output_path, count
    except Exception as e:
        print(f"Error in detection: {e}")
    
    return image_path, 0

def generate():
    global cap, video_selected_object, vehicle_count
    while True:
        if not cap.isOpened():
            print(" IP Camera not reachable")
            continue

        ret, frame = cap.read()
        if not ret:
            print(" Frame not received, retrying...")
            continue
        
        # Resize frame for faster processing
        frame_resized = cv2.resize(frame, (640, 480))
        
        # YOLO detection on live video
        if model is not None:
            try:
                results = model(frame_resized)
                vehicle_count = 0
                
                if results and len(results) > 0:
                    result = results[0]
                    boxes = result.boxes
                    
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        conf = box.conf[0].item()
                        cls_name = model.names[cls_id]
                        
                        # Filter by selected object if specified
                        if video_selected_object and video_selected_object.lower() != cls_name.lower():
                            continue
                        
                        if conf > 0.5:  # Confidence threshold
                            vehicle_count += 1
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame_resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame_resized, f"{cls_name} {conf:.2f}", (x1, y1 - 10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            except Exception as e:
                print(f"YOLO detection error: {e}")
        
        # Add timestamp
        now = datetime.now()
        current_time = now.strftime("%d-%m-%Y %H:%M:%S")
        font = cv2.FONT_HERSHEY_SIMPLEX
        position = (10, 30)  
        font_scale = 0.7
        color = (0, 0, 255)
        thickness = 2
        cv2.putText(frame_resized, current_time, position, font, font_scale, color, thickness, cv2.LINE_AA)
        
        # Add vehicle count
        cv2.putText(frame_resized, f"Objects: {vehicle_count}", (10, 60), font, font_scale, (0, 255, 0), thickness, cv2.LINE_AA)

        ret, jpeg = cv2.imencode('.jpg', frame_resized)
        frame = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/set-camera',methods=['POST'])
def set_camera():
    global cap,camera
    data=request.json
    new=data.get('camera')

    if not new:
        return jsonify({'error':'no source provide'}),400
    
    cap.release()
    camera=new
    cap=cv2.VideoCapture(camera,cv2.CAP_FFMPEG)

    return jsonify({'message':'camera source update'})


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/set-object', methods=['POST'])
def set_object():
    global selected_object
    data = request.json
    selected_object = data.get('object', '')
    return jsonify({'message': f'Object detection set to: {selected_object if selected_object else "All Objects"}', 'object': selected_object})

@app.route('/set-video-object', methods=['POST'])
def set_video_object():
    global video_selected_object
    data = request.json
    video_selected_object = data.get('object', '')
    return jsonify({'message': f'Video object detection set to: {video_selected_object if video_selected_object else "All Objects"}', 'object': video_selected_object})

@app.route('/start-light', methods=['POST'])
def start_light():
    return jsonify({'message': 'Traffic light started!'})

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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'],filename)
        file.save(filepath)
        
        # Run YOLO detection
        detected_image, obj_count = detect_objects_in_image(filepath, selected_object)
        
        # Return detected image if available
        if detected_image and detected_image != filepath:
            detected_filename = os.path.basename(detected_image)
            return jsonify({
                'message': f'file upload successfully - {obj_count} objects detected',
                'filename': detected_filename,
                'object_count': obj_count
            }), 200

        return jsonify({
            'message':'file upload successfully',
            'filename':filename,
            'object_count': obj_count
        }),200
    return jsonify({'error':'invalid file type'}),400

@app.route('/signal-status')
def signal_status():
    global vehicle_count, current_light_state, green_time
    return jsonify({
        'current': current_light_state,
        'vehicle_count': vehicle_count,
        'green_time': green_time
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

if __name__=="__main__":
    app.run(port=8000,debug=True)
