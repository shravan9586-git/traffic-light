from flask import Flask,render_template
import cv2

app=Flask(__name__)

cap=cv2.VideoCapture(1)

def generate():
    while True:
        ret,frame=cap.read()
        if not ret:
            break
        else:
            re,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()

            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n'+frame+b'\r\n')

@app.route('/video')
def video():
    return render_template('index.html')


if __name__=="__main__":
    app.run(port=8000,debug=True)