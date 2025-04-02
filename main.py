from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

import cv2
import numpy as np
from paddleocr import PaddleOCR

app = FastAPI()
ocr_model = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# Preload the OCR model asynchronously at startup
@app.on_event("startup")
async def startup_event():
    global ocr_model
    # Load the model in a thread so it doesn't block the event loop
    ocr_model = await run_in_threadpool(PaddleOCR, use_angle_cls=True, lang='en')
    print("OCR model loaded.")

def process_image_bytes(image_bytes: bytes):
    """
    Convert image bytes to an OpenCV image, optionally resize it,
    run OCR, and return the detected cells (each with y_center, text, and confidence).
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Optional: Resize large images for faster processing
    max_dim = 1024
    height, width = img.shape[:2]
    if max(height, width) > max_dim:
        scale = max_dim / max(height, width)
        img = cv2.resize(img, (int(width * scale), int(height * scale)))
    
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = ocr_model.ocr(image_rgb, cls=True)
    cells = []
    
    if results and len(results) > 0 and len(results[0]) > 0:
        for box, (text, confidence) in results[0]:
            if text.strip():
                y_center = int((box[0][1] + box[2][1]) / 2)
                cells.append({"y_center": y_center, "text": text.strip(), "confidence": confidence})
        cells.sort(key=lambda c: c["y_center"])
    return cells

def cleanup_temp_data(session_id: str):
    """
    Placeholder cleanup function for removing temporary session data.
    Replace this with your own logic if needed.
    """
    print(f"Cleaning up temporary data for session: {session_id}")

@app.api_route("/", methods=["POST", "HEAD"])
async def ocr_endpoint(
    request: Request,
    background_tasks: BackgroundTasks = None,
    image: UploadFile = None,
    mode: str = None
):

    if request.method == "HEAD":
        return JSONResponse(content={"status": "ok"})
    
    # For POST requests, require the parameters
    if request.method == "POST":
        if not image or not mode:
            return JSONResponse(
                status_code=400, 
                content={"error": "Missing required parameters"}
            )


    """
    Accepts an image and a mode ("quick" or "table").
    Processes the image using PaddleOCR and returns:
      - For mode "quick": a concatenated text string.
      - For mode "table": the raw OCR cells as JSON.
    Also schedules cleanup of session data after processing.
    """
    image_bytes = await image.read()
    cells = process_image_bytes(image_bytes)
    
    # In a real application, obtain a proper session id (from cookies or authentication)
    session_id = "dummy_session"
    background_tasks.add_task(cleanup_temp_data, session_id)
    
    if mode == "quick":
        extracted_text = "\n".join(cell["text"] for cell in cells)
        return {"mode": mode, "extracted_text": extracted_text, "cells": cells}
    elif mode == "table":
        return {"mode": mode, "table": cells}
    else:
        return JSONResponse(status_code=400, content={"error": "Invalid mode provided"})

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
