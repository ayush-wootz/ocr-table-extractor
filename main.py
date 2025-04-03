from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import time
import pathlib

app = FastAPI()

# Create PaddleOCR home directory if it doesn't exist
paddle_home = os.path.join(os.path.expanduser("~"), ".paddleocr")
pathlib.Path(paddle_home).mkdir(parents=True, exist_ok=True)

# Ensure the directory is writable
os.chmod(paddle_home, 0o755)

# Initialize OCR model with explicit model paths
def get_ocr_model():
    from paddleocr import PaddleOCR
    # Specify the exact model paths to avoid downloading
    det_model_dir = os.path.join(paddle_home, "whl/det/en/en_PP-OCRv3_det_infer")
    rec_model_dir = os.path.join(paddle_home, "whl/rec/en/en_PP-OCRv3_rec_infer")
    cls_model_dir = os.path.join(paddle_home, "whl/cls/ch_ppocr_mobile_v2.0_cls_infer")
    
    # Check if models exist
    if os.path.exists(det_model_dir) and os.path.exists(rec_model_dir) and os.path.exists(cls_model_dir):
        print("Using pre-downloaded model files")
        return PaddleOCR(
            use_angle_cls=True, 
            lang='en',
            det_model_dir=det_model_dir,
            rec_model_dir=rec_model_dir,
            cls_model_dir=cls_model_dir,
            use_gpu=False
        )
    else:
        print("Model files not found, using default download behavior")
        return PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)



# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# Simple endpoints for testing connectivity
@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "API is working", "timestamp": time.time()}

@app.head("/")
async def head_endpoint():
    return JSONResponse(content={"status": "ok"})

# Initialize OCR model only when needed
def get_ocr_model():
    from paddleocr import PaddleOCR
    return PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)

# Process image with OCR
def process_image(image_bytes):
    # Convert to OpenCV format
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Resize to reduce processing time
    max_dim = 800
    height, width = img.shape[:2]
    if max(height, width) > max_dim:
        scale = max_dim / max(height, width)
        img = cv2.resize(img, (int(width * scale), int(height * scale)))
    
    # Convert to RGB for OCR
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Initialize OCR model (only when needed)
    ocr_model = get_ocr_model()
    
    # Process with OCR
    results = ocr_model.ocr(image_rgb, cls=True)
    cells = []
    
    if results and len(results) > 0 and len(results[0]) > 0:
        for box, (text, confidence) in results[0]:
            if text.strip():
                y_center = int((box[0][1] + box[2][1]) / 2)
                cells.append({"y_center": y_center, "text": text.strip(), "confidence": confidence})
        cells.sort(key=lambda c: c["y_center"])
    
    return cells

@app.post("/")
async def ocr_endpoint(request: Request):
    try:
        # Get form data
        form = await request.form()
        
        # Check for required parameters
        if "image" not in form:
            return JSONResponse(status_code=400, content={"error": "Missing image parameter"})
        
        if "mode" not in form:
            return JSONResponse(status_code=400, content={"error": "Missing mode parameter"})
        
        # Get parameters
        image = form["image"]
        mode = form["mode"]
        
        # Read image
        image_bytes = await image.read()
        
        # Check PaddleOCR directory
        paddle_home = os.path.join(os.path.expanduser("~"), ".paddleocr")
        model_paths = {
            "det": os.path.join(paddle_home, "whl/det/en/en_PP-OCRv3_det_infer"),
            "rec": os.path.join(paddle_home, "whl/rec/en/en_PP-OCRv3_rec_infer"),
            "cls": os.path.join(paddle_home, "whl/cls/ch_ppocr_mobile_v2.0_cls_infer")
        }
        
        # Log directory status
        dir_status = {path: os.path.exists(path) for name, path in model_paths.items()}
        print(f"Model directory status: {dir_status}")
        
        # Process with timeout
        import asyncio
        try:
            # Run OCR in a background thread
            cells = await asyncio.to_thread(process_image, image_bytes)
            
            # Return response based on mode
            if mode == "quick":
                extracted_text = "\n".join(cell["text"] for cell in cells)
                return {"mode": mode, "extracted_text": extracted_text, "cells": cells}
            elif mode == "table":
                return {"mode": mode, "table": cells}
            else:
                return JSONResponse(status_code=400, content={"error": "Invalid mode provided"})
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"error": "Processing timed out. Try with a smaller image."}
            )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Server error: {str(e)}", "trace": error_trace}
        )

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("app:app", host="0.0.0.0", port=port)
