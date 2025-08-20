import io
import requests
import threading
from datetime import datetime
from signal import pause
from gpiozero import MotionSensor
from picamera2 import Picamera2

def capture_and_post_image():
    picam2 = Picamera2()
    
    try:
        camera_config = picam2.create_still_configuration()
        picam2.configure(camera_config)
        picam2.start()
        
        virtual_file = io.BytesIO()
        picam2.capture_file(virtual_file, format="jpeg")
        virtual_file.seek(0)
        
        url = "http://192.168.50.19:8000/print/image"
        files = {"file": ("image.jpeg", virtual_file, "image/jpeg")}
        
        response = requests.post(url, files=files)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} - Image captured and posted. Status: {response.status_code}")
        
    except Exception as e:
        print(f"Error capturing or posting image: {e}")
    finally:
        picam2.stop()

pir = MotionSensor(14)
cooldown_timer = None
can_capture = True

def motion_detected():
    global cooldown_timer, can_capture
    
    if can_capture:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} - Motion detected, capturing image...")
        capture_and_post_image()
        can_capture = False
        start_cooldown_timer()
    else:
        start_cooldown_timer()
        print("Motion detected during cooldown - timer reset to 60 seconds")

def no_motion():
    print("Motion stopped.")

def start_cooldown_timer():
    global cooldown_timer
    
    if cooldown_timer:
        cooldown_timer.cancel()
    
    cooldown_timer = threading.Timer(60.0, reset_capture)
    cooldown_timer.start()

def reset_capture():
    global can_capture
    can_capture = True
    print("Cooldown complete. Ready to capture again.")

pir.when_motion = motion_detected
pir.when_no_motion = no_motion

print("Motion detection system started. Waiting for motion...")
pause()