import io
import requests
from picamera2 import Picamera2

# Create a Picamera2 object
picam2 = Picamera2()

# Configure the camera for still capture
# You can customize the resolution and other parameters as needed
camera_config = picam2.create_still_configuration()
picam2.configure(camera_config)

# Start the camera
picam2.start()

# Create an in-memory binary stream
virtual_file = io.BytesIO()

# Capture the image to the virtual file
# The format can be specified (e.g., "jpeg", "png", "bmp")
picam2.capture_file(virtual_file, format="jpeg")

# Stop the camera
picam2.stop()

# Reset the stream position to the beginning
virtual_file.seek(0)

# POST the image to the specified URL
url = "http://192.168.50.19:8000/print/image"
files = {"file": ("image.jpeg", virtual_file, "image/jpeg")}

try:
    response = requests.post(url, files=files)
    print(f"POST request status code: {response.status_code}")
    print(f"Response: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error sending POST request: {e}")