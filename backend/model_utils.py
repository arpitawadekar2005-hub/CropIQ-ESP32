# backend/model_utils.py

import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
import os
import gdown

# =============================
# CONFIG
# =============================
MODEL_PATH = os.environ.get("MODEL_PATH", "plant_disease_model.h5")
CSV_PATH = os.environ.get("CSV_PATH", "pesticide_data.csv")

DRIVE_FILE_ID = "170lylylDDiePU_pj1bfXppef6li1VMqz"  # <-- replace

def download_model():
    """Download the model from Drive if missing."""
    if not os.path.exists(MODEL_PATH):
        url = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}"
        print("📥 Downloading model from Google Drive...")
        gdown.download(url, MODEL_PATH, quiet=False)
        print("✅ Model downloaded:", MODEL_PATH)
     
# =============================
# CLASS LABELS (must match model output)
# =============================
classes = [
 'Tomato___Bacterial_spot',
 'Tomato___Early_blight',
 'Tomato___healthy',
 'Tomato___Late_blight',
 'Tomato___Leaf_Mold',
 'Tomato___Septoria_leaf_spot',
 'Tomato___Spider_mites Two-spotted_spider_mite',
 'Tomato___Target_Spot',
 'Tomato___Tomato_mosaic_virus',
 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',

]

# =============================
# LOAD CSV DATA
# =============================
pesticide_df = pd.read_csv(CSV_PATH)

# =============================
# LOAD MODEL (lazy load once)
# =============================
_model = None

def load_cnn_model():
    """Load TensorFlow model exactly once."""
    global _model

    if _model is None:
        download_model()
        print("🚀 Loading CNN model...")
        _model = load_model(MODEL_PATH)
        print("✅ Model loaded!")

    return _model

# =============================
# LABEL CLEANING
# =============================

def extract_plant_and_disease(label: str):
    """
    Convert model label like 'Strawberry___Leaf_scorch' into:
    plant='strawberry', disease='leaf scorch'
    """

    parts = label.split("___")
    raw_plant = parts[0]
    raw_disease = parts[1] if len(parts) > 1 else "healthy"

    # clean plant name
    plant = (
        raw_plant.replace("_(including_sour)", "")
                 .replace("(including_sour)", "")
                 .replace("(maize)", "")
                 .replace(",", "")
                 .replace("_", " ")
                 .strip()
                 .lower()
    )

    # clean disease name
    disease = (
        raw_disease.replace("_", " ")
                   .replace("(Black Measles)", "")
                   .replace("(Black_Measles)", "")
                   .strip()
                   .lower()
    )

    return plant, disease

# =============================
# DOSE CALCULATION
# =============================

def confidence_to_infection(confidence: float) -> float:
    """Convert confidence (0–1) to infection percentage (0–100)."""
    return round(confidence * 100, 2)


def get_base_dose(plant: str, disease: str):
    """
    Match plant + disease to the CSV row.
    Returns: pesticide_name, base_ml_per_L
    """
    row = pesticide_df[
        (pesticide_df['plant'].str.lower() == plant.lower()) &
        (pesticide_df['disease'].str.lower() == disease.lower())
    ]

    if row.empty:
        return None, None

    pesticide = row.iloc[0]['pesticide']
    base_ml_per_L = float(row.iloc[0]['base_ml_per_L'])
    return pesticide, base_ml_per_L


def compute_final_dose(base_ml_per_L: float, infection_percent: float, water_volume_ml: int = 100) -> float:
    """
    Dose for a container of water_volume_ml (default 100ml).
    """
    base_for_container = base_ml_per_L * (water_volume_ml/1000.0 )
    final_dose = base_for_container * (infection_percent )
    return round(final_dose, 3)

# =============================
# MAIN INFERENCE FUNCTION
# (Used by FastAPI /predict endpoint)
# =============================

def run_inference_bgr(np_bgr_image):
    """
    Accepts: numpy BGR image directly from ESP32 (OpenCV format)
    Returns: dict with prediction + dose
    """

    import cv2

    model = load_cnn_model()
    input_shape = model.input_shape
    img_h = input_shape[1]
    img_w = input_shape[2]

    # Convert ESP32 BGR → RGB
    img_rgb = cv2.cvtColor(np_bgr_image, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (img_w, img_h))
    img_resized = img_resized.astype(np.float32) / 255.0
    img_resized = np.expand_dims(img_resized, axis=0)

    # Prediction
    pred = model.predict(img_resized)[0]
    idx = int(np.argmax(pred))
    confidence = float(pred[idx])

    label = classes[idx]
    plant, disease = extract_plant_and_disease(label)

    infection_percent = confidence_to_infection(confidence)

    pesticide, base_ml_per_L = get_base_dose(plant, disease)

    dose_ml = None
    if pesticide is not None:
        dose_ml = compute_final_dose(base_ml_per_L, infection_percent)

    # Final response
    return {
        "plant": plant,
        "disease": disease,
        "label": label,
        "confidence": confidence,
        "infection_percent": infection_percent,
        "pesticide": pesticide,
        "base_ml_per_L": base_ml_per_L,
        "dose_ml": dose_ml,
        "raw_pred": pred.tolist()
    }
