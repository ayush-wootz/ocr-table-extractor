from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from paddleocr import PaddleOCR
import asyncio
import os

# Initialize the OCR model at import time
print("Loading OCR model...")

# Initialize the OCR model with more conservative settings
ocr_model = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, enable_mkldnn=False)
print("OCR model loaded successfully!")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ayush-wootz.github.io", "*"],  # Add your specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# Remove the startup event since we're loading the model upfront
# @app.on_event("startup")
# async def startup_event():
#     global ocr_model
#     # Load the model in a thread so it doesn't block the event loop
#     ocr_model = await run_in_threadpool(PaddleOCR, use_angle_cls=True, lang='en')
#     print("OCR model loaded.")

def process_image_bytes(image_bytes: bytes):
    """
    Convert image bytes to an OpenCV image, optionally resize it,
    run OCR, and return the detected cells (each with y_center, text, and confidence).
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # More aggressive resizing for faster processing
        max_dim = 800
        height, width = img.shape[:2]
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)))
        
        image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        print(f"Running OCR on image of size {image_rgb.shape}")
        
        results = ocr_model.ocr(image_rgb, cls=True)
        cells = []
        
        if results and len(results) > 0 and len(results[0]) > 0:
            for box, (text, confidence) in results[0]:
                if text.strip():
                    y_center = int((box[0][1] + box[2][1]) / 2)
                    cells.append({"y_center": y_center, "text": text.strip(), "confidence": confidence})
            cells.sort(key=lambda c: c["y_center"])
        
        print(f"OCR completed, found {len(cells)} text elements")
        return cells
    except Exception as e:
        print(f"Error in OCR processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def cleanup_temp_data(session_id: str):
    """
    Placeholder cleanup function for removing temporary session data.
    Replace this with your own logic if needed.
    """
    print(f"Cleaning up temporary data for session: {session_id}")

# Add a simple health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "ocr_model_loaded": ocr_model is not None}

@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "API is working"}

# Handle HEAD requests
@app.head("/")
async def head_endpoint():
    return JSONResponse(content={"status": "ok"})

# Handle POST requests for OCR
@app.post("/")
async def ocr_post_endpoint(
    request: Request,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    try:
        # Log received request
        print(f"Received request with Content-Type: {request.headers.get('content-type')}")
        
        # Get form data
        form = await request.form()
        print(f"Form keys: {list(form.keys())}")
        
        # Extract image and mode
        if "image" not in form:
            return JSONResponse(status_code=400, content={"error": "Missing image parameter"})
        
        if "mode" not in form:
            return JSONResponse(status_code=400, content={"error": "Missing mode parameter"})
        
        image = form["image"]
        mode = form["mode"]
        
        print(f"Processing request: mode={mode}, image={image.filename}")
        
        # Read image with timeout protection
        try:
            image_bytes = await image.read()
            print(f"Image size: {len(image_bytes)} bytes")
            
            # Process with timeout
            cells = await asyncio.wait_for(
                asyncio.to_thread(process_image_bytes, image_bytes), 
                timeout=25  # 25 second timeout
            )
            
            # Set up session cleanup
            session_id = "dummy_session"
            background_tasks.add_task(cleanup_temp_data, session_id)
            
            # Return response based on mode
            if mode == "quick":
                extracted_text = "\n".join(cell["text"] for cell in cells)
                return {"mode": mode, "extracted_text": extracted_text, "cells": cells}
            elif mode == "table":
                return {"mode": mode, "table": cells}
            else:
                return JSONResponse(status_code=400, content={"error": "Invalid mode provided"})
                
        except asyncio.TimeoutError:
            print("OCR processing timed out")
            return JSONResponse(
                status_code=504,  # Gateway Timeout
                content={"error": "Processing timed out. Try with a smaller image."}
            )
            
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500, 
            content={"error": f"Server error: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
