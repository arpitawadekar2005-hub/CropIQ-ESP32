import streamlit as st
import requests
import base64 
from model_utils_frontend import format_result
from streamlit_autorefresh import st_autorefresh
# Import for explicit error handling
from requests.exceptions import RequestException 
import json # Import for JSONDecodeError
from binascii import Error as BinasciiError # Import for specific Base64 decode errors

# ===========================================
# CONFIG
# ===========================================
BACKEND = st.secrets["BACKEND_URL"]

st.set_page_config(
    page_title="Plant Disease Dashboard",
    layout="wide",
)

st.title("🌿 Plant Disease Detection Dashboard")

# Auto-refresh every 5s
st_autorefresh(interval=5000, key="data_refresh")


# ===========================================
# STYLE
# ===========================================
st.markdown("""
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
""", unsafe_allow_html=True)


# ===========================================
# 1️⃣ ESP32 STATUS
# ===========================================
st.header("ESP32 Status")

try:
    status = requests.get(f"{BACKEND}/esp-status", timeout=3).json()
    if status["status"] == "online":
        st.success(f"🟢 ESP32 Connected — last seen {status['last_seen']:.1f}s ago")
    else:
        st.error("🔴 ESP32 NOT Connected")
except:
    st.error("⚠️ Backend unreachable")


# Capture photo button
if st.button("📸 Capture Leaf Image"):
    r = requests.post(f"{BACKEND}/capture")
    st.toast("📩 Capture Request Sent to ESP32")


st.markdown("---")


# ===========================================
# 2️⃣ LATEST PREDICTION
# ===========================================
st.header("Latest Prediction from ESP32")

# Refresh button
if st.button("🔄 Refresh"):
    st.rerun()

# --- FETCH DATA - ROBUSTNESS AGAINST BACKEND FAILURE ---
latest_raw = {}
img_bytes = b''
data_fetch_error = False

# 1. Fetch latest prediction data (JSON)
try:
    response = requests.get(f"{BACKEND}/latest")
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    latest_raw = response.json()
except (RequestException, json.JSONDecodeError) as e:
    st.error(f"🛑 Error Fetching Prediction Data: Could not connect to the backend or received invalid JSON.")
    data_fetch_error = True

# 2. Fetch and Decode Image content
try:
    base64_img_string = requests.get(f"{BACKEND}/latest/image").text
    
    if not base64_img_string:
        # Explicitly handle case where backend returns an empty string for the image
        img_bytes = b''
    else:
        # Attempt to decode the Base64 string
        img_bytes = base64.b64decode(base64_img_string)
        
except BinasciiError:
    # This happens if the backend returned non-Base64 text (like an error message)
    st.warning("Image data received was corrupt or not valid Base64.")
    img_bytes = b''
except RequestException:
    # This happens if the image endpoint is unreachable or gives a connection error
    st.warning("Could not reach the image endpoint (`/latest/image`).")
    img_bytes = b''
except Exception as e:
    # Catch any other unexpected error during image handling
    st.error(f"An unexpected error occurred while handling the image data: {e}")
    img_bytes = b''


# If prediction data fetching failed, stop the app execution here
if data_fetch_error:
    st.stop()

# 💡 Extract the calculated dose from the backend response.
dose_ml = latest_raw.get("dose_ml") 
if dose_ml is None:
    dose_ml = 0.0

# Ensure prediction data is not empty before proceeding
if not latest_raw:
    st.warning("No prediction data yet — ESP32 has not uploaded a valid result.")
    st.stop()

# We only format if we successfully fetched data
data = format_result(latest_raw)

# ===========================================
# Layout — IMAGE LEFT / DATA RIGHT
# ===========================================
col_img, col_info = st.columns([3,2], gap="medium")


# ─── LEFT: IMAGE BOX ─────────────────────
with col_img:
    st.markdown("<div class='img-box'>", unsafe_allow_html=True)
    if img_bytes:
        # Show the image if we have valid decoded bytes
        st.image(img_bytes, caption="📷 Leaf Image from ESP32", use_column_width=True) 
    else:
        # Show a placeholder message if img_bytes is empty or invalid
        st.markdown(
            "<div style='height:420px; display:flex; align-items:center; justify-content:center; background-color:#262730; color:#aaa; border-radius:10px;'>"
            "<h3>🖼️ No Image Received</h3>"
            "</div>", unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ─── RIGHT: PREDICTION ───────────────────
with col_info:
    st.markdown(
        "<h3 style='text-align:center;'>🧠 Prediction Result</h3>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="pred-box">
        🌱 <b>Plant:</b> {data['plant']}<br><br>
        🦠 <b>Disease:</b> {data['disease']}<br><br>
        🎯 <b>Confidence:</b> {data['confidence']}%<br><br>
        🔥 <b>Infection Level:</b> {data['infection']}%<br><br>
        🧪 <b>Pesticide:</b> {data['pesticide']}<br><br>
        💧 <b>Dose (per 100 ml):</b> {data['dose']} ml
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)

    # Use the dose_ml variable, ensuring it's not None
    if st.button("🚿 Send Spray Command", use_container_width=True):
        # We ensure dose_ml is at least 0.0 earlier in the script
        if dose_ml > 0:
            requests.post(f"{BACKEND}/spray", params={"volume_ml": dose_ml})
            st.success(f"Spray Command Sent: {dose_ml} mL!")
        else:
            st.warning("Cannot spray: Calculated dose is 0 mL (Plant appears healthy).")

    st.markdown("</div>", unsafe_allow_html=True)
