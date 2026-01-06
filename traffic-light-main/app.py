from flask import Flask,render_template,Response,request,jsonify,send_from_directory
import cv2
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app=Flask(__name__)

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
    while True:
        if not cap.isOpened():
            print(" IP Camera not reachable")
            continue

        ret, frame = cap.read()
        if not ret:
            print(" Frame not received, retrying...")
            continue
        # 1. Get current date and time
        now = datetime.now()
        current_time = now.strftime("%d-%m-%Y %H:%M:%S")

        # 2. Setup font settings
        font = cv2.FONT_HERSHEY_SIMPLEX
        position = (50, 60)  
        font_scale = 2
        color = (0,0,255)
        thickness = 2

        # 3. Draw black background for text (Optional, for better readability)
        #cv2.rectangle(frame, (10, 15), (400, 60), (0, 0, 0), -1)

        #put text on the frame
        cv2.putText(frame, current_time, position, font, font_scale, color, thickness, cv2.LINE_AA)

        ret, jpeg = cv2.imencode('.jpg', frame)
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
