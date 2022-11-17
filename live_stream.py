import automated, security_cam
import secrets
import cv2

from flask import Flask, render_template, Response, request, redirect, url_for, session
from flask_socketio import SocketIO
from functools import wraps

def livestream():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
    socketio = SocketIO(app, async_mode="threading")

    def require_login(x):
        @wraps(x)
        def wrap(*args, **kwargs):
            if 'logged_in' in session:
                return x(*args, **kwargs)
            else:
                return redirect(url_for('login'))
        return wrap

    def gen_frames():
        while True:
            frame = automated.global_frame
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    @socketio.on('secure_button')
    def handle_it(val):
        if val['check'] == 'check_msg':
            automated.secure_mode = not automated.secure_mode
            if not automated.secure_mode: automated.db = False
        msg = (lambda: "Turn on secure mode", lambda: "Turn off secure mode")[automated.secure_mode]()
        socketio.emit('pass_msg', msg, broadcast=True)

    @socketio.on('text_receiver')
    def receive(dictionary):
        if dictionary['text'] != '':
            value = ''
            if automated.audio_thread:
                value = 'Error: Cannot send message when intruder alarm is activated! Turn off the alarm by turning off the secure system!'
            elif len(automated.message) == 0:
                automated.message.append(dictionary['text'])
                automated.speak_text()
            elif len(automated.message) > 0:
                value = 'Error: The system is still speaking the text previously sent!'
            socketio.emit('get_succ', value, broadcast=True)
    
    @socketio.on('get_value')
    def send_value():
        info = []
        (lambda: info.append('OFF'), lambda: info.append('ON'))[automated.con_on]()
        (lambda: info.append('OFF'), lambda: info.append('ON'))[automated.face_on]()
        socketio.emit('get_val_response', tuple(info), broadcast=True)

    @app.route('/logout')
    @require_login
    def logout():
        session.pop('logged_in', None)
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error, user, pwd = None, None, None
        if request.method == 'POST':
            if request.form['username'] == '' or request.form['password'] == '':
                error = 'Please enter the required fields'
                if request.form['username'] == '':
                    user = 'The username field is empty!'
                if request.form['password'] == '':
                    pwd = 'The password field is empty!'
            elif request.form['username'] != security_cam.env_var['SECURITY_USER'] or request.form['password'] != security_cam.env_var['SECURITY_PASS']:
                error = 'Invalid Credentials. Please try again.'
            else:
                session['logged_in'] = True
                return redirect(url_for('index'))
        return render_template('login.html', error=error, user=user, pwd=pwd)

    @app.route('/video_feed')
    def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/', methods=['GET', 'POST'])
    @require_login
    def index():
        if request.method == 'POST':
            if request.form.get('action1') == "Turn on Movement Detector":
                automated.con_on = True
            elif request.form.get('action2') == "Turn off Movement Detector":
                automated.con_on = False
            elif request.form.get('action3') == "Turn on Face Detector":
                automated.face_on = True
            elif request.form.get('action4') == "Turn off Face Detector":
                automated.face_on = False

        return render_template("index.html")

    socketio.run(app, host='0.0.0.0', port='4000')