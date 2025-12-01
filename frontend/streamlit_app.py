import io
import requests
from PIL import Image, UnidentifiedImageError
import streamlit as st
from model_utils_frontend import format_result
from streamlit_autorefresh import st_autorefresh

# ============================
# CONFIG
# ============================
BACKEND = st.secrets.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Plant Disease Dashboard",
    layout="wide",
)

st.title("🌿 Plant Disease Detection Dashboard")

# Auto-refresh every 5s
st_autorefresh(interval=5000, key="data_refresh")

# ============================
# STYLE
# ============================
st.markdown(
    """
<style>
.img-box {
    border: 1px solid #444;
    border-radius: 10px;
    overflow: hidden;
    max-height: 420px;
}
.pred-box {
    text-align:center;
    font-size:18px;
    padding: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================
# ESP32 STATUS
# ============================
st.header("ESP32 Status")

try:
    resp = requests.get(f"{BACKEND}/esp-status", timeout=3)
    if resp.ok:
        status = resp.json()
        if status.get("status") == "online":
            last_seen = status.get("last_seen")
            try:
                last_seen_str = f" — last seen {float(last_seen):.1f}s ago" if last_seen is not None else ""
            except Exception:
                last_seen_str = ""
            st.success(f"🟢 ESP32 Connected{last_seen_str}")
        else:
            st.error("🔴 ESP32 NOT Connected")
    else:
        st.warning("⚠️ ESP32 status endpoint returned an error.")
except requests.RequestException:
    st.error("⚠️ Backend unreachable (could not fetch ESP32 status).")

# Capture photo button
if st.button("📸 Capture Leaf Image"):
    try:
        post = requests.post(f"{BACKEND}/capture", timeout=5)
        if post.ok:
            st.success("📩 Capture request sent to ESP32")
        else:
            st.warning("Capture request sent but backend responded with an error.")
    except requests.RequestException:
        st.error("⚠️ Failed to send capture request to backend.")

st.markdown("---")

# ============================
# REFRESH BUTTON
# ============================
if st.button("🔄 Refresh"):
    try:
        st.experimental_rerun()
    except Exception:
        pass

# ============================
# FETCH LATEST METADATA AND IMAGE (Robust)
# ============================
latest_raw = {}
dose_ml = 0.0
data = {}
pil_image = None

# Fetch latest metadata/result safely
try:
    latest_resp = requests.get(f"{BACKEND}/latest", timeout=5)
    if latest_resp.ok and latest_resp.content:
        try:
            latest_raw = latest_resp.json()
        except ValueError:
            latest_raw = {}
    else:
        latest_raw = {}
except requests.RequestException:
    latest_raw = {}

# Normalize dose
try:
    dose_ml = float(latest_raw.get("dose_ml", 0.0) or 0.0)
except Exception:
    dose_ml = 0.0

# Determine whether backend has a prediction-like payload (metadata only)
has_metadata_prediction = bool(
    latest_raw
    and any(k in latest_raw for k in ("plant", "disease", "confidence", "infection", "pesticide", "dose_ml"))
)

# Fetch image safely (we fetch image regardless so we can decide later)
try:
    img_resp = requests.get(f"{BACKEND}/latest/image", timeout=5)
    if img_resp.ok and img_resp.content:
        ctype = img_resp.headers.get("Content-Type", "")
        if ctype and ctype.startswith("image"):
            img_bytes = img_resp.content
            try:
                tmp = Image.open(io.BytesIO(img_bytes))
                tmp.verify()  # raises if corrupted
                tmp = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                pil_image = tmp
            except (UnidentifiedImageError, OSError):
                pil_image = None
        else:
            pil_image = None
    else:
        pil_image = None
except requests.RequestException:
    pil_image = None

# Only show prediction when BOTH metadata exists and a valid image was retrieved
show_prediction = bool(has_metadata_prediction and (pil_image is not None))

# Prepare formatted data only if we will show it (defensive)
if show_prediction:
    try:
        data = format_result(latest_raw) or {}
    except Exception:
        data = {
            "plant": latest_raw.get("plant", "Unknown"),
            "disease": latest_raw.get("disease", "Unknown"),
            "confidence": latest_raw.get("confidence", 0),
            "infection": latest_raw.get("infection", 0),
            "pesticide": latest_raw.get("pesticide", "Unknown"),
            "dose": latest_raw.get("dose", f"{dose_ml}"),
        }
else:
    # Ensure data defaults exist to avoid KeyError in UI (not used when show_prediction is False)
    data = {
        "plant": "Unknown",
        "disease": "Unknown",
        "confidence": 0,
        "infection": 0,
        "pesticide": "Unknown",
        "dose": f"{dose_ml}",
    }

# ============================
# RENDER LAYOUT
# ============================
col_img, col_info = st.columns([3, 2], gap="medium")

# LEFT: Image or placeholder
with col_img:
    st.markdown("<div class='img-box'>", unsafe_allow_html=True)
    if pil_image is not None:
        st.image(pil_image, caption="📷 Leaf Image from ESP32", use_column_width=True)
    else:
        st.markdown(
            """
            <div style='display:flex;align-items:center;justify-content:center;height:300px;padding:20px;'>
            <div style='text-align:center;color:#666;'>📷 <i>No image uploaded yet</i></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# RIGHT: Prediction info or friendly no-data message
with col_info:
    st.markdown("<h3 style='text-align:center;'>🧠 Prediction Result</h3>", unsafe_allow_html=True)

    if show_prediction:
        plant = data.get("plant", "Unknown")
        disease = data.get("disease", "Unknown")
        confidence = data.get("confidence", 0)
        infection = data.get("infection", 0)
        pesticide = data.get("pesticide", "Unknown")
        dose_display = data.get("dose", f"{dose_ml}")

        st.markdown(
            f"""
            <div class="pred-box">
            🌱 <b>Plant:</b> {plant}<br><br>
            🦠 <b>Disease:</b> {disease}<br><br>
            🎯 <b>Confidence:</b> {confidence}%<br><br>
            🔥 <b>Infection Level:</b> {infection}%<br><br>
            🧪 <b>Pesticide:</b> {pesticide}<br><br>
            💧 <b>Dose (per 100 ml):</b> {dose_display} ml
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="pred-box">
            No prediction available — a valid image must be uploaded by the ESP32 before predictions are shown.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='text-align:center;margin-top:10px;'>", unsafe_allow_html=True)
    # Spray button: guarded behavior
    if st.button("🚿 Send Spray Command", use_container_width=True):
        if not show_prediction:
            st.warning("Cannot spray: no valid image/prediction available.")
        elif dose_ml and dose_ml > 0:
            try:
                spray_resp = requests.post(f"{BACKEND}/spray", params={"volume_ml": dose_ml}, timeout=5)
                if spray_resp.ok:
                    st.success(f"Spray Command Sent: {dose_ml} mL!")
                else:
                    st.error("Spray request failed (backend error).")
            except requests.RequestException:
                st.error("Spray request failed (could not reach backend).")
        else:
            st.warning("Cannot spray: Calculated dose is 0 mL (Plant appears healthy).")
    st.markdown("</div>", unsafe_allow_html=True)
