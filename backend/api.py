from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
from model_utils import run_inference_bgr

app = FastAPI()

# For Frontend + Mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_result = None
pending_command = None

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    global latest_result

    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = run_inference_bgr(img)
    latest_result = result

    return {"status": "ok", "result": result}

@app.get("/latest")
def get_latest():
    return latest_result or {"status": "no_data"}

@app.post("/spray")
def spray(duration_ms: int = 2000):
    global pending_command
    pending_command = {"command": "start", "duration_ms": duration_ms}
    return {"status": "queued"}

@app.get("/get-command")
def get_command():
    global pending_command
    if pending_command:
        cmd = pending_command
        pending_command = None
        return cmd
    return {"command": "none"}
