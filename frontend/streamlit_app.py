import streamlit as st
import requests
from model_utils_frontend import format_result
from streamlit_autorefresh import st_autorefresh


# ===========================================
# CONFIG
# ===========================================
BACKEND = st.secrets["BACKEND_URL"]

st.set_page_config(
    page_title="Plant Disease Dashboard",
    layout="wide",
)

st.title("🌿 Plant Disease Detection Dashboard")

# Auto-refresh every 5 seconds
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

st.header("ESP32 WiFi Status")

try:
    status = requests.get(f"{BACKEND}/esp-status", timeout=5).json()

    if status.get("status") == "online":
        last = status.get("last_seen", 0)
        st.success(f"🟢 ESP32 Connected — last activity {last:.1f}s ago")

    else:
        st.error("🔴 ESP32 NOT Connected (No recent ping or image upload)")

except:
    st.error("⚠️ Backend unreachable")


# ===========================================
# 2️⃣ SELECT MODE
# ===========================================
st.header("Latest Prediction")

mode = st.radio(
    "Choose prediction mode:",
    ["📡 ESP32 (Live)", "🖼️ Manual Upload"],
    horizontal=True
)

data = None
dose_ml = 0.0
img_bytes = None


# ===========================================
# A) ESP32 LIVE MODE
# ===========================================
if mode == "📡 ESP32 (Live)":

    if st.button("🔄 Refresh ESP Data"):
        st.rerun()

    try:
        latest_raw = requests.get(f"{BACKEND}/latest").json()
        img_bytes = requests.get(f"{BACKEND}/latest/image").content
    except Exception:
        st.error("⚠️ Could not fetch data from backend.")
        st.stop()

    if not latest_raw:
        st.warning("No prediction yet from ESP32.")
        st.stop()

    data = format_result(latest_raw)
    dose_ml = latest_raw.get("dose_ml", 0.0)


# ===========================================
# B) MANUAL UPLOAD MODE
# ===========================================
else:
    uploaded_file = st.file_uploader(
        "📂 Upload leaf image",
        type=["jpg", "jpeg", "png"]
    )

    if not uploaded_file:
        st.info("Upload a leaf image to start prediction.")
        st.stop()

    files = {"image": uploaded_file.getvalue()}
    resp = requests.post(f"{BACKEND}/predict/raw", files=files)

    # --- SAFE JSON HANDLING
    if resp.headers.get("Content-Type") != "application/json":
        st.error(f"Backend Response:\n{resp.text}")
        st.stop()

    try:
        latest_raw = resp.json()
    except Exception:
        st.error(f"Invalid JSON returned by backend:\n{resp.text}")
        st.stop()

    img_bytes = uploaded_file.getvalue()
    data = format_result(latest_raw)
    dose_ml = latest_raw.get("dose_ml", 0.0)


# ===========================================
# 3️⃣ DISPLAY RESULT
# ===========================================
col_img, col_info = st.columns([3, 2], gap="medium")

with col_img:
    st.markdown("<div class='img-box'>", unsafe_allow_html=True)
    st.image(img_bytes, caption="📷 Leaf Image", use_column_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


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

    # Spray button works for both
    if st.button("🚿 Send Spray Command", use_container_width=True):
        if dose_ml > 0:
            requests.post(f"{BACKEND}/spray", params={"volume_ml": dose_ml})
            st.success(f"Spray Command Sent: {dose_ml} mL!")
        else:
            st.warning("Dose is 0 mL. No infection detected.")

    st.markdown("</div>", unsafe_allow_html=True)
