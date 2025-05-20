from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import asyncio
import logging
import re
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
def simple_cells(img_rgb):
    """
    Run PaddleOCR on an RGB image and return one cell per detected box,
    sorted by its vertical (y) center.
    """
    ocr_model = get_ocr_model()
    raw = ocr_model.ocr(img_rgb, cls=True)[0]

    cells = []
    for box, (text, confidence) in raw:
        if not text.strip():
            continue
        # compute the vertical midpoint for sorting
        y_center = int((box[0][1] + box[2][1]) / 2)
        cells.append({
            "y_center": y_center,
            "text": text.strip(),
            "confidence": confidence
        })

    # stable sort top→bottom
    cells.sort(key=lambda c: c["y_center"])
    # drop the y_center before returning
    return [{"text": c["text"], "confidence": c["confidence"]} for c in cells]

def advanced_cells(img):
    # … your existing decode/resize/RGB logic …
    # 1) Binarize & invert
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)

    # 2) Narrow horizontal kernel
    h, w = img.shape[:2]
    kern = cv2.getStructuringElement(cv2.MORPH_RECT, (max(5, w//80), 1))
    horiz = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kern)

    # 3) Hough for even short lines
    lines = cv2.HoughLinesP(
        horiz, rho=1, theta=np.pi/180,
        threshold=30, minLineLength=w//40, maxLineGap=5
    )

    # 4) Cluster y’s into row_bounds
    ys = []
    if lines is not None:
        for x1,y1,x2,y2 in lines[:,0]:
            ys += [y1,y2]
    ys.sort()
    clusters = []
    for y in ys:
        if not clusters or abs(y - clusters[-1][0]) > 15:
            clusters.append([y])
        else:
            clusters[-1].append(y)
    row_bounds = [int(sum(c)/len(c)) for c in clusters]

    # 5) FALLBACK if no or too few bounds
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    if lines is None or len(row_bounds) < 2:
        return simple_cells(rgb)

    # 6) Do one OCR pass & collect
    raw = get_ocr_model().ocr(rgb, cls=True)[0]
    cells = []
    for box, (t, c) in raw:
        if not t.strip(): continue
        x = int((box[0][0]+box[2][0])/2)
        y = int((box[0][1]+box[2][1])/2)
        cells.append({"x":x,"y":y,"text":t.strip(),"conf":c})

    rows = []
    # handle head (above first line)
    head = [c for c in cells if c["y"] < row_bounds[0]]
    if head:
        head.sort(key=lambda c:(c["y"],c["x"]))
        rows.append({
          "text":" ".join(c["text"] for c in head),
          "confidence":min(c["conf"] for c in head)
        })

    # handle bands between
    for top,bot in zip(row_bounds, row_bounds[1:]):
        band = [c for c in cells if top <= c["y"] < bot]
        if not band: continue
        band.sort(key=lambda c:(c["y"],c["x"]))
        rows.append({
          "text":" ".join(c["text"] for c in band),
          "confidence":min(c["conf"] for c in band)
        })

    # handle tail (below last line)
    tail = [c for c in cells if c["y"] >= row_bounds[-1]]
    if tail:
        tail.sort(key=lambda c:(c["y"],c["x"]))
        rows.append({
          "text":" ".join(c["text"] for c in tail),
          "confidence":min(c["conf"] for c in tail)
        })

    return rows

# def process_image(image_bytes):
#     import cv2, numpy as np

#     # —————————————————————————————
#     # 1) Decode & resize exactly as before
#     nparr = np.frombuffer(image_bytes, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#     max_dim = 800
#     h, w = img.shape[:2]
#     if max(h, w) > max_dim:
#         scale = max_dim / max(h, w)
#         img = cv2.resize(img, (int(w*scale), int(h*scale)))
    
#     # 2) Prepare a gray/binary image for line detection
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     _, bw = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
    
#     # 3) Extract long horizontal strokes (the table grid‐lines)
#     horiz_kernel = cv2.getStructuringElement(
#         cv2.MORPH_RECT, (max(20, img.shape[1]//30), 1)
#     )
#     horiz = cv2.morphologyEx(bw, cv2.MORPH_OPEN, horiz_kernel)
    
#     # 4) Hough‐detect those strokes
#     lines = cv2.HoughLinesP(
#         horiz, rho=1, theta=np.pi/180, threshold=100,
#         minLineLength=img.shape[1]//2, maxLineGap=20
#     )
#     ys = []
#     if lines is not None:
#         for x1, y1, x2, y2 in lines[:,0]:
#             ys += [y1, y2]
#     ys.sort()
    
#     # 5) Cluster y’s that are within 5px of each other → true row boundaries
#     clusters = []
#     for y in ys:
#         if not clusters or abs(y - clusters[-1][0]) > 5:
#             clusters.append([y])
#         else:
#             clusters[-1].append(y)
#     row_bounds = sorted(int(sum(c)/len(c)) for c in clusters)
    
#     # —————————————————————————————
#     # 6) Finally run your OCR on the (RGB) image
#     image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     results = get_ocr_model().ocr(image_rgb, cls=True)[0]
    
#     # 7) Compute each snippet’s center
#     cells = []
#     for box, (text, conf) in results:
#         if not text.strip(): 
#             continue
#         x_c = int((box[0][0] + box[2][0]) / 2)
#         y_c = int((box[0][1] + box[2][1]) / 2)
#         cells.append({"x": x_c, "y": y_c, "text": text.strip(), "conf": conf})
    
#     # 8) Group into bands between each consecutive pair of row_bounds
#     rows = []
#     for i in range(len(row_bounds) - 1):
#         top, bot = row_bounds[i], row_bounds[i+1]
#         band = [c for c in cells if top <= c["y"] < bot]
#         if not band:
#             continue
#         band.sort(key=lambda c: c["x"])
#         merged_text = " ".join(c["text"] for c in band)
#         merged_conf = min(c["conf"] for c in band)
#         rows.append({"text": merged_text, "confidence": merged_conf})
    
#     return rows

    
# def process_image(image_bytes):
#     logger.info(f"Processing image of size {len(image_bytes)} bytes")
    
#     # Convert to OpenCV format
#     nparr = np.frombuffer(image_bytes, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
#     # Resize image for faster processing
#     max_dim = 800
#     height, width = img.shape[:2]
#     if max(height, width) > max_dim:
#         scale = max_dim / max(height, width)
#         img = cv2.resize(img, (int(width * scale), int(height * scale)))
#         logger.info(f"Resized image to {img.shape[1]}x{img.shape[0]}")
    
#     # Convert to RGB for OCR
#     image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
#     # Process with OCR
#     logger.info("Starting OCR processing")
#     ocr_model = get_ocr_model()
#     results = ocr_model.ocr(image_rgb, cls=True)
#     cells = []
    
#     if results and len(results) > 0 and len(results[0]) > 0:
#         for box, (text, confidence) in results[0]:
#             if text.strip():
#                 y_center = int((box[0][1] + box[2][1]) / 2)
#                 cells.append({"y_center": y_center, "text": text.strip(), "confidence": confidence})
#         cells.sort(key=lambda c: c["y_center"])
    
#     logger.info(f"OCR completed, found {len(cells)} text elements")
#     return cells

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

        # 1) Get form + fields
        form = await request.form()
        logger.info(f"Received form data with keys: {list(form.keys())}")

        if "image" not in form:
            logger.warning("Missing image parameter in request")
            return JSONResponse(status_code=400, content={"error": "Missing image parameter"})
        if "mode" not in form:
            logger.warning("Missing mode parameter in request")
            return JSONResponse(status_code=400, content={"error": "Missing mode parameter"})
        # ← NEW: optional “column” tag
        column_id = form.get("column", None)

        image_file = form["image"]
        mode       = form["mode"]
        logger.info(f"Processing request in mode: {mode}, image filename: {image_file.filename}, column: {column_id}")

        # 2) Read the bytes
        image_bytes = await image_file.read()

        # 3) Decode once to a CV2 image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 4) Dispatch to the right OCR routine under a worker thread
        def do_ocr():
            # quick mode: just raw text join
            if mode == "quick":
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                # reuse simple_cells to get list of dicts
                cells = simple_cells(rgb)
                extracted_text = "\n".join(c["text"] for c in cells)
                return {"mode": mode, "extracted_text": extracted_text, "cells": cells}

            # table mode: choose by column tag
            elif mode == "table":
                # quantity gets the old per‐line logic
                if column_id == "quantity":
                    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    table_cells = simple_cells(rgb)
                # everything else uses the fancy line‐based
                else:
                    table_cells = advanced_cells(img)
                return {"mode": mode, "table": table_cells}

            else:
                raise ValueError(f"Invalid mode provided: {mode}")

        # 5) Run OCR with timeout protection
        try:
            result = await asyncio.to_thread(do_ocr)
            return result

        except asyncio.TimeoutError:
            logger.error("OCR processing timed out")
            return JSONResponse(
                status_code=504,
                content={"error": "Processing timed out. Try with a smaller image."}
            )

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error processing request: {e}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Server error: {str(e)}"}
        )

# @app.post("/")
# async def ocr_endpoint(request: Request):
#     try:
#         logger.info(f"Received OCR request with Content-Type: {request.headers.get('content-type')}")
        
#         # Get form data
#         form = await request.form()
#         logger.info(f"Received form data with keys: {list(form.keys())}")
        
#         # Validate required fields
#         if "image" not in form:
#             logger.warning("Missing image parameter in request")
#             return JSONResponse(status_code=400, content={"error": "Missing image parameter"})
        
#         if "mode" not in form:
#             logger.warning("Missing mode parameter in request")
#             return JSONResponse(status_code=400, content={"error": "Missing mode parameter"})
        
#         # Get image and mode
#         image = form["image"]
#         mode = form["mode"]
#         logger.info(f"Processing request in mode: {mode}, image filename: {image.filename}")
        
#         # Read image
#         image_bytes = await image.read()
        
#         # Process with timeout protection
#         try:
#             cells = await asyncio.to_thread(process_image, image_bytes)
            
#             # Return response based on mode
#             if mode == "quick":
#                 extracted_text = "\n".join(cell["text"] for cell in cells)
#                 return {"mode": mode, "extracted_text": extracted_text, "cells": cells}
#             elif mode == "table":
#                 return {"mode": mode, "table": cells}
#             else:
#                 logger.warning(f"Invalid mode provided: {mode}")
#                 return JSONResponse(status_code=400, content={"error": "Invalid mode provided"})
                
#         except asyncio.TimeoutError:
#             logger.error("OCR processing timed out")
#             return JSONResponse(
#                 status_code=504,
#                 content={"error": "Processing timed out. Try with a smaller image."}
#             )
#     except Exception as e:
#         import traceback
#         error_trace = traceback.format_exc()
#         logger.error(f"Error processing request: {str(e)}")
#         logger.error(f"Traceback: {error_trace}")
#         return JSONResponse(
#             status_code=500,
#             content={"error": f"Server error: {str(e)}"}
#         )

# Extracts Drawing number from File Name
def extract_drawing_number(url: str):
    if not url:
        return ""
    match = re.search(r"/([^/]+)\.pdf$", url)
    return match.group(1) if match else ""

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
                if row.get("VQlMl") == project and row.get("nlHAO") == part_number
            ]

            print(f"✅ Filtered rows: {len(filtered)} match")
            # ✅ Add extracted drawingNumber from drawing link
            filtered_trimmed = [
                {
                    "project": row.get("VQlMl"),
                    "partNumber": row.get("nlHAO"),
                    "partName": row.get("Name"),
                    "drawingLink": row.get("9iB5E"),
                    "drawingNumber": extract_drawing_number(row.get("9iB5E"))
                }
                for row in filtered
            ]
        
            return {"rows": filtered_trimmed}
        
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
