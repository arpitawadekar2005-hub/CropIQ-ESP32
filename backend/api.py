from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import numpy as np
import cv2
from model_utils import run_inference_bgr
from datetime import datetime

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
latest_result = None
latest_image = None
pending_command = None
last_ping = None
last_heartbeat = None


# ===========================
# IMAGE UPLOAD (ESP)
# ===========================
@app.post("/predict/raw")
async def predict_raw(request: Request):
    global latest_result, latest_image, last_ping

    content = await request.body()
    latest_image = content
    last_ping = datetime.utcnow()

    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = run_inference_bgr(img)
    latest_result = result

    return {"status": "ok", "result": result}


# ===========================
# IMAGE UPLOAD (Manual UI)
# ===========================
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    global latest_result, latest_image

    content = await file.read()
    latest_image = content

    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = run_inference_bgr(img)
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
        return Response(latest_image, media_type="image/jpeg")
    return {"status": "no_image"}


# ===========================
# SPRAY CONTROL
# ===========================
# @app.post("/spray")
# def spray(duration_ms: int = 2000):
#     global pending_command
#     pending_command = {"command": "start", "duration_ms": duration_ms}
#     return {"status": "queued"}

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

    if last_seen < 20:
        return {"status": "online", "last_seen": last_seen}

    return {"status": "offline", "last_seen": last_seen}


# ===========================
# ADMIN / DEBUG TOOL
# ===========================
@app.post("/clear")
def clear_state():
    global latest_result, latest_image, pending_command, last_ping, last_heartbeat
    latest_result = None
    latest_image = None
    pending_command = None
    last_ping = None
    last_heartbeat = None
    return {"status": "cleared"}
