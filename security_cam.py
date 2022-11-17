import live_stream, automated

import threading, os, json
import cv2, pyshorteners

env_var = json.loads(os.environ['PROJECT_VAR'])

short_url = pyshorteners.Shortener()
cam = cv2.VideoCapture(0)

if __name__ == '__main__':
    threading.Thread(target=live_stream.livestream, daemon=True).start()
    threading.Thread(target=automated.auto_start, daemon=False).start()