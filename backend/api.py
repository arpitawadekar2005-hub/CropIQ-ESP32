
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from datetime import datetime
from typing import Optional, Tuple

import numpy as np
import cv2
from io import BytesIO
from PIL import Image

from model_utils import run_inference_bgr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# STATE
# ===========================
latest_result: Optional[dict] = None
latest_image: Optional[bytes] = None
latest_image_mime: Optional[str] = None
pending_command: Optional[dict] = None
last_ping: Optional[datetime] = None
last_heartbeat: Optional[datetime] = None


# ===========================
# HELPERS
# ===========================
def decode_and_infer(content: bytes) -> Tuple[dict, str]:
    """
    Robustly decode image bytes using Pillow, convert to OpenCV BGR,
    run inference, and return (result_dict, mime).
    Raises HTTPException with helpful detail on failure.
    """
    if not content or len(content) < 2048:  # small threshold to catch empty/truncated frames
        raise HTTPException(status_code=400, detail=f"Empty or too-small image: {len(content)} bytes")

    # Decode with Pillow (more tolerant than cv2.imdecode)
    try:
        pil_img = Image.open(BytesIO(content))
        pil_img.load()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

    # Detect MIME from Pillow format
    fmt = (pil_img.format or "").upper()
    mime = {
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
        "BMP": "image/bmp",
        "TIFF": "image/tiff",
    }.get(fmt, "application/octet-stream")

    # Normalize to RGB (remove alpha if present)
    if pil_img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", pil_img.size, (255, 255, 255))
        bg.paste(pil_img, mask=pil_img.split()[-1])
        pil_img = bg
    elif pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    # Convert RGB PIL → BGR ndarray
    try:
        rgb = np.array(pil_img)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to convert image to BGR: {e}")

    # Run inference safely
    try:
        result = run_inference_bgr(bgr)
        if not isinstance(result, dict):
            raise ValueError("run_inference_bgr must return a dict")
    except Exception as e:
        # Print to server logs for debugging
        import traceback; traceback.print_exc()
        # Return a clear 500 error to the client
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    return result, mime


# ===========================
# IMAGE UPLOAD (ESP)
# ===========================
@app.post("/predict/raw")
async def predict_raw(request: Request):
    global latest_result, latest_image, latest_image_mime, last_ping

    content = await request.body()
    last_ping = datetime.utcnow()
    print(f"[predict/raw] bytes={len(content)}")  # simple diagnostic

    result, mime = decode_and_infer(content)

    latest_image = content
    latest_image_mime = mime
    latest_result = result

    return {"status": "ok", "result": result}


# ===========================
# IMAGE UPLOAD (Manual UI)
# ===========================
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    global latest_result, latest_image, latest_image_mime

    content = await file.read()
    print(f"[predict] bytes={len(content)}")

    result, mime = decode_and_infer(content)

    latest_image = content
    latest_image_mime = mime
    latest_result = result

    return {"status": "ok", "result": result}


# ===========================
# LIVE INFO
# ===========================
@app.get("/latest")
def get_latest():
    return latest_result or {"status": "no_data"}


@app.get("/latest/image")
def get_latest_image():
    if latest_image:
        return Response(latest_image, media_type=(latest_image_mime or "image/jpeg"))
    return JSONResponse({"status": "no_image"}, status_code=404)


# ===========================
# SPRAY CONTROL
# ===========================
@app.post("/spray")
def spray(volume_ml: float = 10.0):
    """
    Queue a spray command with the exact volume (in mL)
    the ESP should dispense using the flow sensor.
    """
    global pending_command
    pending_command = {"command": "spray", "volume_ml": volume_ml}
    return {"status": "queued"}

@app.post("/spray/stop")
def spray_stop():
    global pending_command
    pending_command = {"command": "stop"}
    return {"status": "queued"}


# ===========================
# CAPTURE
# ===========================
@app.post("/capture")
def capture():
    global pending_command
    if pending_command is None:
        pending_command = {"command": "capture"}
    return {"status": "queued"}


# ===========================
# ESP COMMAND CHECK
# ===========================
@app.get("/get-command")
def get_command():
    global pending_command
    if pending_command:
        cmd = pending_command
        pending_command = None
        return cmd
    return {"command": "none"}


# ===========================
# HEARTBEAT
# ===========================
@app.post("/esp-ping")
def esp_ping():
    global last_heartbeat
    last_heartbeat = datetime.utcnow()
    return {"status": "ok"}


@app.get("/esp-status")
def esp_status():
    global last_ping, last_heartbeat

    if not last_ping and not last_heartbeat:
        return {"status": "offline", "reason": "no data yet"}

    now = datetime.utcnow()
    ages = []

    if last_ping:
        ages.append((now - last_ping).total_seconds())
    if last_heartbeat:
        ages.append((now - last_heartbeat).total_seconds())

    last_seen = min(ages)

    # IMPORTANT: ensure this is a real '<', not HTML-escaped '&lt;'
    if last_seen < 20:
        return {"status": "online", "last_seen": last_seen}

    return {"status": "offline", "last_seen": last_seen}


# ===========================
# ADMIN / DEBUG TOOL
# ===========================
@app.post("/clear")
def clear_state():
    global latest_result, latest_image, latest_image_mime, pending_command, last_ping, last_heartbeat
    latest_result = None
    latest_image = None
    latest_image_mime = None
    pending_command = None
    last_ping = None
    last_heartbeat = None
    return {"status": "cleared"}


# ===========================
# HEALTH
# ===========================
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
