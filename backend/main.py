from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import asyncio
import logging
import httpx  # used to fecth drawing numbers (File name)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

print("🚀 Server has started and main.py is loaded")

# Configure CORS - explicitly allow your GitHub Pages d
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ayush-wootz.github.io", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# Paths to pre-downloaded model files
PADDLE_HOME = os.path.expanduser("~/.paddleocr")
DET_MODEL_DIR = os.path.join(PADDLE_HOME, "whl/det/en/en_PP-OCRv3_det_infer")
REC_MODEL_DIR = os.path.join(PADDLE_HOME, "whl/rec/en/en_PP-OCRv3_rec_infer")
CLS_MODEL_DIR = os.path.join(PADDLE_HOME, "whl/cls/ch_ppocr_mobile_v2.0_cls_infer")

# Check and log model paths on startup
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting OCR API with model paths:")
    logger.info(f"Detection model: {DET_MODEL_DIR} (exists: {os.path.exists(DET_MODEL_DIR)})")
    logger.info(f"Recognition model: {REC_MODEL_DIR} (exists: {os.path.exists(REC_MODEL_DIR)})")
    logger.info(f"Classification model: {CLS_MODEL_DIR} (exists: {os.path.exists(CLS_MODEL_DIR)})")

# Initialize OCR model
def get_ocr_model():
    from paddleocr import PaddleOCR
    logger.info("Initializing PaddleOCR model with pre-downloaded model files")
    return PaddleOCR(
        use_angle_cls=True,
        lang='en',
        det_model_dir=DET_MODEL_DIR,
        rec_model_dir=REC_MODEL_DIR,
        cls_model_dir=CLS_MODEL_DIR,
        use_gpu=False
    )

# Process image with OCR
def process_image(image_bytes):
    logger.info(f"Processing image of size {len(image_bytes)} bytes")
    
    # Convert to OpenCV format
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Resize image for faster processing
    max_dim = 800
    height, width = img.shape[:2]
    if max(height, width) > max_dim:
        scale = max_dim / max(height, width)
        img = cv2.resize(img, (int(width * scale), int(height * scale)))
        logger.info(f"Resized image to {img.shape[1]}x{img.shape[0]}")
    
    # Convert to RGB for OCR
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Process with OCR
    logger.info("Starting OCR processing")
    ocr_model = get_ocr_model()
    results = ocr_model.ocr(image_rgb, cls=True)
    cells = []
    
    if results and len(results) > 0 and len(results[0]) > 0:
        for box, (text, confidence) in results[0]:
            if text.strip():
                y_center = int((box[0][1] + box[2][1]) / 2)
                cells.append({"y_center": y_center, "text": text.strip(), "confidence": confidence})
        cells.sort(key=lambda c: c["y_center"])
    
    logger.info(f"OCR completed, found {len(cells)} text elements")
    return cells

# Health check endpoint
@app.get("/health")
async def health_check():
    model_paths_exist = all([
        os.path.exists(DET_MODEL_DIR),
        os.path.exists(REC_MODEL_DIR),
        os.path.exists(CLS_MODEL_DIR)
    ])
    return {
        "status": "ok", 
        "model_files_exist": model_paths_exist,
        "paddle_home": PADDLE_HOME
    }

# Test endpoint
@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "API is working"}

# Handle HEAD requests
@app.head("/")
async def head_endpoint():
    return JSONResponse(content={"status": "ok"})

# Main OCR endpoint
@app.post("/")
async def ocr_endpoint(request: Request):
    try:
        logger.info(f"Received OCR request with Content-Type: {request.headers.get('content-type')}")
        
        # Get form data
        form = await request.form()
        logger.info(f"Received form data with keys: {list(form.keys())}")
        
        # Validate required fields
        if "image" not in form:
            logger.warning("Missing image parameter in request")
            return JSONResponse(status_code=400, content={"error": "Missing image parameter"})
        
        if "mode" not in form:
            logger.warning("Missing mode parameter in request")
            return JSONResponse(status_code=400, content={"error": "Missing mode parameter"})
        
        # Get image and mode
        image = form["image"]
        mode = form["mode"]
        logger.info(f"Processing request in mode: {mode}, image filename: {image.filename}")
        
        # Read image
        image_bytes = await image.read()
        
        # Process with timeout protection
        try:
            cells = await asyncio.to_thread(process_image, image_bytes)
            
            # Return response based on mode
            if mode == "quick":
                extracted_text = "\n".join(cell["text"] for cell in cells)
                return {"mode": mode, "extracted_text": extracted_text, "cells": cells}
            elif mode == "table":
                return {"mode": mode, "table": cells}
            else:
                logger.warning(f"Invalid mode provided: {mode}")
                return JSONResponse(status_code=400, content={"error": "Invalid mode provided"})
                
        except asyncio.TimeoutError:
            logger.error("OCR processing timed out")
            return JSONResponse(
                status_code=504,
                content={"error": "Processing timed out. Try with a smaller image."}
            )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error processing request: {str(e)}")
        logger.error(f"Traceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Server error: {str(e)}"}
        )


# API code to fetch drawing numbers (File name)
GLIDE_API_KEY = "54333200-37b8-4742-929c-156d49cd7c64"
GLIDE_APP_ID = "1Ywfm3mzeWfqqAMNovPV"
GLIDE_TABLE = "native-table-unGdNRqsjTPlBDZB2629"

@app.post("/fetch-drawings")
async def fetch_drawings(request: Request):
    print("🎯 /fetch-drawings endpoint hit")

    try:
        payload = await request.json()
        project = payload.get("project")
        part_number = payload.get("part")

        print("📦 Incoming fetch-drawings request:", project, part_number)
        
        if not project or not part_number:
            return {"error": "Missing project or part"}

        # ✅ Correct API format
        body = {
            "appID": GLIDE_APP_ID,
            "queries": [
                {
                    "tableName": GLIDE_TABLE,
                    "utc": True
                }
            ]
        }
        
        print("📤 Sending request to Glide:", body)

        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.glideapp.io/api/function/queryTables",
                headers={
                    "Authorization": f"Bearer {GLIDE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=body
            )

        res.raise_for_status()
        
        try:
            full_data = res.json()
            print("✅ Full response from Glide:", full_data)
            # ✅ Extract and filter rows manually
            all_rows = full_data[0]["rows"]
            filtered = [
                row for row in all_rows
                if row.get("projName") == project and row.get("partNumber") == part_number
            ]

            print(f"✅ Filtered rows: {len(filtered)} match")
            return {"rows": filtered}
        
        except Exception:
            error_text = await res.aread()
            print("❌ Non-JSON response from Glide:", error_text.decode())
            raise


    except Exception as e:
        import traceback
        print("❌ Exception occurred:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/debug")
async def debug():
    print("✅ /debug route hit", flush=True)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
