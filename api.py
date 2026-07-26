from io import BytesIO
from time import sleep

import requests
import utils
import uvicorn
from escpos.printer import Usb
from fastapi import FastAPI, File, Form, Query, UploadFile
from PIL import Image

app = FastAPI()

# vendor id, product id, lsusb -vvv -d 1504:0101 | grep bEndpointAddress
p = Usb(0x1504, 0x0101, out_ep=0x02, in_ep=0x81)
sleep(1)
p.charcode("CP850")


@app.post("/print/text")
async def print_text_api(text: str = Form(...), fast: bool = Query(False)):
    try:
        # Fix encoding issue for Norwegian characters
        decoded_text = text.encode('latin1').decode('utf-8')
        print("printer tekst:", decoded_text)
        if fast:
            p.text(decoded_text)
        else:
            p.image(utils.print_text(decoded_text))
        p.cut()
        return {"status": "success", "message": "Text printed successfully"}
    except (IOError, UnicodeDecodeError) as e:
        return {"status": "error", "message": f"Printing failed: {str(e)}"}


@app.post("/print/task")
async def print_task_api(text: str = Form(...), task_type: utils.TaskType = Form(...)):
    try:
        p.image(utils.print_task(text, task_type))
        p.cut()
        return {"status": "success", "message": "Image printed successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error printing task: {e}"}


@app.post("/print/image")
async def print_image_api(file: UploadFile = File(...)):
    if not file.content_type or "image" not in file.content_type:
        return {"status": "error", "message": "File is not recognized as an image"}

    try:
        image_data = await file.read()
        image = Image.open(BytesIO(image_data))

        # Resize image if width exceeds 512px
        max_width = 512
        if image.width > max_width:
            aspect_ratio = image.height / image.width
            new_height = int(max_width * aspect_ratio)
            image = image.resize((max_width, new_height))

        p.image(image)
        p.cut()
        return {"status": "success", "message": "Image printed successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to print image: {str(e)}"}


@app.post("/print/url")
async def print_from_url_api(url: str = Form(...)):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return {"status": "error", "message": f"Failed to download image: HTTP {response.status_code}"}

        # Check if response contains image data
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type:
            return {"status": "error", "message": "URL does not point to an image"}

        image = Image.open(BytesIO(response.content))

        # Resize image if width exceeds 512px
        max_width = 512
        if image.width > max_width:
            aspect_ratio = image.height / image.width
            new_height = int(max_width * aspect_ratio)
            image = image.resize((max_width, new_height))

        p.image(image)
        p.cut()
        return {"status": "success", "message": "Image from URL printed successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to print image from URL: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)