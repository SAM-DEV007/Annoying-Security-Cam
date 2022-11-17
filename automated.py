import security_cam, RoastList
import soundfile as sf

import os, threading, time, random
import cv2, pynput, smtplib, socket, mediapipe
import win32api, keyboard
import pyaudio, wave, librosa

from moviepy.editor import VideoFileClip, vfx
from pydub import AudioSegment
from pydub.playback import play
from gtts import gTTS

global_frame, rec_frame = None, None
con_on, face_on, secure_mode, global_speak, audio_thread = False, False, False, False, False
global_run, secure, vid_rec, force_close, mic_open, timeout = False, False, False, False, False, False
db = False
global_folder = (os.path.abspath(os.path.join(os.path.dirname(__file__))) + "\\Recorded Files\\")
global_model = (os.path.abspath(os.path.join(os.path.dirname(__file__))))

message = []

class stopwatch:
    def __init__(self):
        self.seconds = 0
    
    def update(self):
        self.seconds = time.time()
    
    def reset(self):
        self.seconds = 0
    
    def show_seconds(self):
        if self.seconds != 0:
            return int(time.time()-self.seconds)
        return 0

def speak_text():
    global message, global_speak

    if not global_speak:
        global_speak = True
        threading.Thread(target=say_cmd, daemon=True).start()

def say_cmd(txt=None):
    global global_speak, message

    if txt is None: txt = message[0]
    obj = gTTS(text=txt, lang='en', slow=False)
    obj.save("temp_audio.wav")

    aud = "temp_audio.wav"

    x, _ = librosa.load(f'./temp_audio.wav', sr=16000)
    sf.write(f'temp_audio.wav', x, 16000)

    audio = AudioSegment.from_wav(aud)
    play(audio)

    os.remove('temp_audio.wav')
    message.clear()
    global_speak = False

def record_audio(file_path):
    global mic_open, secure_mode

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024
    )
    aud_frames = []

    while mic_open:
        data = stream.read(1024)
        aud_frames.append(data)
    
    stream.stop_stream()
    stream.close()
    audio.terminate()

    sound_file = wave.open(file_path, 'wb')
    sound_file.setnchannels(1)
    sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    sound_file.setframerate(44100)
    sound_file.writeframes(b''.join(aud_frames))
    sound_file.close()

def check_file(filePath):
    global global_folder

    if os.path.exists(filePath):
        numb = 1
        while True:
            ext = os.path.splitext(filePath)[1]
            newPath = f"{os.path.join(global_folder, str(numb))}{ext}"
            if os.path.exists(newPath):
                numb += 1
            else:
                return newPath
    return filePath

def record_vid():
    global global_folder, secure, vid_rec, global_frame, mic_open, secure_mode

    if vid_rec or not secure_mode: 
        return
    
    vid_rec, mic_open = True, True

    size = (640, 480)
    file = check_file(os.path.join(global_folder, "0.mp4"))
    result = cv2.VideoWriter(f'{file}',
						cv2.VideoWriter_fourcc(*'mp4v'),
						60, size)

    aud_file = check_file(os.path.join(global_folder, "0.wav"))
    threading.Thread(target=record_audio, args=(aud_file,), daemon=False).start()

    while secure or secure_mode:
        result.write(rec_frame)
    else:
        result.release()
        threading.Thread(target=increase_fps, args=(file,), daemon=False).start()
        vid_rec, mic_open = False, False

def increase_fps(filen):
    global global_folder

    filetup = os.path.splitext(filen)
    clip = VideoFileClip(filen)
    final = clip.fx(vfx.speedx, 3)
    f_name = check_file(os.path.join(global_folder, f"{filetup[0]}_video{filetup[1]}"))
    final.write_videofile(f_name)

    fileremoved = False
    while not fileremoved:
        try:
            os.remove(filen)
            fileremoved = True
        except PermissionError: pass

def on_press(key):
    if not secure_mode: return
    if hasattr(key, 'char'):
        if key is None: pass
        elif not key.char in ("s", "S"):
            if secure_mode:
                threading.Thread(target=intruder, daemon=True).start()
    elif not key.name in ("ctrl_l", "ctrl_r", "alt_l", "alt_r", "shift"):
        if secure_mode:
            threading.Thread(target=intruder, daemon=True).start()

def thread_listener():
    while True:
        with pynput.keyboard.Listener(on_press=on_press) as listen:
            listen.join()

def close():
    global force_close
    send_email(
        "SECURITY CAMERA SHUTDOWN REQUEST",
        "We have received shutdown request of the security system from the server. \n\nIf you did not process it, please contact your operator."
    )
    force_close = True

def send_email(sub: str, body: str):
    threading.Thread(target=send_email_thread, args=(sub, body), daemon=True).start()

def send_email_thread(sub: str, body: str):
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(security_cam.env_var['EMAIL_USER'], security_cam.env_var['EMAIL_PASS'])

        msg = f"Subject: {sub} \n\n {body}"
        smtp.sendmail(security_cam.env_var['EMAIL_USER'], security_cam.env_var['EMAIL_USER'], msg)

def movement_detected():
    global timeout, secure_mode

    if timeout or not secure_mode: return

    t = stopwatch()
    t.update()
    timeout = True

    send_email(
        "ALERT: SECURITY CAMERA [MOVEMENT DETECTED]",
        f"The camera installed detected movement. \n\n Please visit the web portal, if you would like to check the camera: \n{security_cam.short_url.dagd.short(socket.gethostbyname(socket.gethostname())+':80')}"
    )

    while timeout:
        if t.show_seconds() >= 300: 
            timeout = False

def list_order():
    return random.sample(RoastList.r_list, len(RoastList.r_list))

def death_audio():
    global secure_mode, audio_thread

    if not secure_mode or not audio_thread: return
    audio_thread = True
    list_ = list_order()
    aud = os.path.join(global_model, "Deadly_Audio.wav")

    audio = AudioSegment.from_wav(aud)
    vol = audio + 50
    while secure_mode:
        if random.randint(0, 1) == 0:
            say_cmd(list_[0])
            try:
                list_.remove(list_[0])
            except IndexError:
                list_ = list_order()
        play(vol)
    audio_thread = False

def intruder():
    global secure_mode, message, audio_thread, db

    if not secure_mode or db: return
    db = True
    message.clear()

    send_email(
        "ALERT: SECURITY CAMERA [INTRUDER WARNING]",
        f"The probability of an intruder has been detected! Please contact your neighbours or the local police to verify the warning! \n\n Please visit the link to open the web portal and turn off the secure mode to disable intruder warning: \n{security_cam.short_url.dagd.short(socket.gethostbyname(socket.gethostname())+':80')}"
    )

    if not audio_thread:
        audio_thread = True
        threading.Thread(target=death_audio, daemon=True).start()

def auto_start():
    global global_frame, global_run, secure, vid_rec, force_close, global_model, rec_frame, secure_mode, audio_thread

    cam = security_cam.cam
    keyboard.add_hotkey('ctrl+alt+shift+s', close)
    activated, key_listen = False, False
    activated_time, secure_time = stopwatch(), stopwatch()
    saved_pos = win32api.GetCursorPos()

    MLfaceDetection = mediapipe.solutions.face_detection
    faceDetection = MLfaceDetection.FaceDetection(0.5)

    while True:
        if not secure_mode: secure, activated = False, False

        global_run, idle = True, True

        _, frame = cam.read()
        _, second_frame = cam.read()
        _, recording = cam.read()

        rec_frame = recording
        global_frame = frame
        diff = cv2.absdiff(frame, second_frame)
        gray = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=1)
        result_face = faceDetection.process(frame)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if face_on and result_face.detections:
            for d in result_face.detections:
                boxC = d.location_data.relative_bounding_box
                h, w, _ = frame.shape
                box = int(boxC.xmin * w), int(boxC.ymin * h), \
                       int(boxC.width * w), int(boxC.height * h)
                cv2.rectangle(frame, box, (0, 0, 255), 3)

        for c in contours:
            if secure: idle = False
            if cv2.contourArea(c) < 100: continue

            if not activated:
                activated = True
                activated_time.update()

            if activated and activated_time.show_seconds() >= 2 and not secure:
                secure = True
                secure_time.update()

            if not vid_rec and secure:
                threading.Thread(target=movement_detected, daemon=True).start()
                threading.Thread(target=record_vid, daemon=True).start()

            if con_on:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        if not idle and secure: secure_time.update()

        if secure and result_face.detections and activated_time.show_seconds() >= 2:
            threading.Thread(target=intruder, daemon=True).start()

        if not key_listen:
            threading.Thread(target=thread_listener, daemon=True).start()
            key_listen = True

        curpos = win32api.GetCursorPos()
        if saved_pos != curpos:
            saved_pos = curpos
            if secure_mode:
                threading.Thread(target=intruder, daemon=True).start()

        if not audio_thread and idle and secure_time.show_seconds() >= 2:
            secure, activated = False, False
            secure_time.reset()
            activated_time.reset()

        if not global_run or force_close: break