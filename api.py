from io import BytesIO
from typing import Optional
import random
import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
from escpos.printer import Usb
import requests

app = FastAPI(title="Thermal Printer API", description="API for controlling thermal receipt printer")

# Initialize printer - same config as bot.py
try:
    p = Usb(0x1504, 0x0101, out_ep=0x02, in_ep=0x81)
except Exception as e:
    print(f"Warning: Could not initialize printer: {e}")
    p = None

class TextPrintRequest(BaseModel):
    text: str
    cut: bool = True

class ReceiptItem(BaseModel):
    name: str
    price: float
    quantity: int = 1

class Receipt(BaseModel):
    items: list[ReceiptItem]
    store_name: str = "Receipt Printer Store"
    cut: bool = True

@app.get("/")
async def root():
    return {"message": "Thermal Printer API", "status": "running"}

@app.get("/printer/status")
async def printer_status():
    """Check if printer is connected and accessible"""
    if p is None:
        return {"status": "disconnected", "error": "Printer not initialized"}
    try:
        # Try to access printer (this will fail if disconnected)
        return {"status": "connected", "vendor_id": "0x1504", "product_id": "0x0101"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/print/text")
async def print_text(request: TextPrintRequest):
    """Print text to thermal printer"""
    if p is None:
        raise HTTPException(status_code=503, detail="Printer not available")
    
    try:
        p.text(request.text)
        if request.cut:
            p.cut()
        return {"message": "Text printed successfully", "text": request.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to print: {str(e)}")

@app.post("/print/image")
async def print_image(file: UploadFile = File(...), cut: bool = True):
    """Print image to thermal printer"""
    if p is None:
        raise HTTPException(status_code=503, detail="Printer not available")
    
    if not file.content_type or "image" not in file.content_type:
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image from uploaded file
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        
        # Resize image if width exceeds 512px (same logic as bot.py)
        max_width = 512
        if image.width > max_width:
            aspect_ratio = image.height / image.width
            new_height = int(max_width * aspect_ratio)
            image = image.resize((max_width, new_height))
        
        p.image(image)
        if cut:
            p.cut()
        
        return {
            "message": "Image printed successfully", 
            "filename": file.filename,
            "original_size": f"{image.width}x{image.height}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to print image: {str(e)}")

@app.post("/print/image-url")
async def print_image_url(url: str, cut: bool = True):
    """Print image from URL"""
    if p is None:
        raise HTTPException(status_code=503, detail="Printer not available")
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download image from URL")
        
        image = Image.open(BytesIO(response.content))
        
        # Resize image if width exceeds 512px
        max_width = 512
        if image.width > max_width:
            aspect_ratio = image.height / image.width
            new_height = int(max_width * aspect_ratio)
            image = image.resize((max_width, new_height))
        
        p.image(image)
        if cut:
            p.cut()
        
        return {
            "message": "Image printed successfully", 
            "url": url,
            "size": f"{image.width}x{image.height}"
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to print image: {str(e)}")

@app.post("/print/receipt")
async def print_receipt(receipt: Receipt):
    """Print a formatted receipt"""
    if p is None:
        raise HTTPException(status_code=503, detail="Printer not available")
    
    try:
        # Header
        p.set(align='center', text_type='B')
        p.text(f"{receipt.store_name}\n")
        p.set(align='center', text_type='normal')
        p.text(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        p.text("-" * 32 + "\n")
        
        # Items
        p.set(align='left')
        total = 0
        for item in receipt.items:
            item_total = item.price * item.quantity
            total += item_total
            p.text(f"{item.name[:20]:<20}\n")
            p.text(f"  {item.quantity}x {item.price:.2f} = {item_total:.2f}\n")
        
        # Total
        p.text("-" * 32 + "\n")
        p.set(text_type='B')
        p.text(f"{'TOTAL:':<20} {total:.2f}\n")
        p.set(text_type='normal')
        p.text("\n")
        p.set(align='center')
        p.text("Takk for handelen!\n")
        
        if receipt.cut:
            p.cut()
        
        return {
            "message": "Receipt printed successfully", 
            "total": total,
            "items_count": len(receipt.items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to print receipt: {str(e)}")

@app.post("/print/joke")
async def print_joke():
    """Print a random joke"""
    if p is None:
        raise HTTPException(status_code=503, detail="Printer not available")
    
    jokes = [
        "Why don't scientists trust atoms?\nBecause they make up everything!",
        "Why did the scarecrow win an award?\nHe was outstanding in his field!",
        "Why don't eggs tell jokes?\nThey'd crack each other up!",
        "What do you call a fake noodle?\nAn impasta!",
        "Why did the math book look so sad?\nBecause of all of its problems!",
        "What do you call a bear with no teeth?\nA gummy bear!",
        "Why can't a bicycle stand up by itself?\nIt's two tired!",
        "What do you call a fish wearing a bowtie?\nSofishticated!"
    ]
    
    try:
        joke = random.choice(jokes)
        p.set(align='center', text_type='B')
        p.text("🤣 JOKE TIME 🤣\n\n")
        p.set(align='center', text_type='normal')
        p.text(joke)
        p.text("\n\n")
        p.cut()
        
        return {"message": "Joke printed successfully", "joke": joke}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to print joke: {str(e)}")

@app.post("/print/qr")
async def print_qr(text: str, cut: bool = True):
    """Print QR code with text"""
    if p is None:
        raise HTTPException(status_code=503, detail="Printer not available")
    
    try:
        p.set(align='center')
        p.qr(text)
        p.text(f"\n{text}\n")
        if cut:
            p.cut()
        
        return {"message": "QR code printed successfully", "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to print QR code: {str(e)}")

@app.post("/print/barcode")
async def print_barcode(code: str, barcode_type: str = "CODE128", cut: bool = True):
    """Print barcode"""
    if p is None:
        raise HTTPException(status_code=503, detail="Printer not available")
    
    try:
        p.set(align='center')
        p.barcode(code, barcode_type)
        p.text(f"\n{code}\n")
        if cut:
            p.cut()
        
        return {"message": "Barcode printed successfully", "code": code, "type": barcode_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to print barcode: {str(e)}")

@app.post("/print/fortune")
async def print_fortune():
    """Print a fortune cookie message"""
    if p is None:
        raise HTTPException(status_code=503, detail="Printer not available")
    
    fortunes = [
        "The best time to plant a tree was 20 years ago. The second best time is now.",
        "Your future is bright, like a thermal printer receipt!",
        "Good things come to those who print.",
        "Today's accomplishments were yesterday's impossibilities.",
        "The journey of a thousand miles begins with a single print.",
        "You will find luck in unexpected places.",
        "A wise person learns from the mistakes of others.",
        "Your hard work will pay off soon.",
        "Adventure awaits those who dare to print.",
        "Success is just around the corner."
    ]
    
    try:
        fortune = random.choice(fortunes)
        p.set(align='center', text_type='B')
        p.text("🔮 FORTUNE 🔮\n\n")
        p.set(align='center', text_type='normal')
        p.text(fortune)
        p.text("\n\n")
        p.set(align='center', text_type='B')
        p.text("Lucky numbers: ")
        lucky_numbers = [str(random.randint(1, 99)) for _ in range(6)]
        p.text(", ".join(lucky_numbers))
        p.text("\n\n")
        p.cut()
        
        return {"message": "Fortune printed successfully", "fortune": fortune, "lucky_numbers": lucky_numbers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to print fortune: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)