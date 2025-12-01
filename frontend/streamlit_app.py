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
# B) MANUAL UPLOAD MODE
# ===========================================
else:
    uploaded_file = st.file_uploader("📂 Upload leaf image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        files = {"image": uploaded_file.getvalue()}
        resp = requests.post(f"{BACKEND}/predict/raw", files=files)

        latest_raw = resp.json()
        img_bytes = uploaded_file.getvalue()
        data = format_result(latest_raw)
        dose_ml = latest_raw.get("dose_ml", 0.0)

    else:
        st.info("Upload a leaf image to start prediction.")
        st.stop()



# ===========================================
# A) ESP32 LIVE MODE
# ===========================================
if mode == "📡 ESP32 (Live)":

    if st.button("🔄 Refresh ESP Data"):
        st.rerun()

    try:
        latest_raw = requests.get(f"{BACKEND}/latest").json()
        img_bytes = requests.get(f"{BACKEND}/latest/image").content
    except:
        st.error("⚠️ Could not fetch data from backend")
        st.stop()

    if not latest_raw:
        st.warning("No prediction yet from ESP32")
        st.stop()

    # format for UI
    data = format_result(latest_raw)

    # raw spray dose
    dose_ml = latest_raw.get("dose_ml", 0.0)


# ===========================================
# B) MANUAL UPLOAD MODE
# ===========================================
else:
    uploaded_file = st.file_uploader("📂 Upload leaf image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        # send to backend
        files = {"image": uploaded_file.getvalue()}
        resp = requests.post(f"{BACKEND}/predict/raw", files=files)

        if resp.status_code == 200:
            latest_raw = resp.json()
            img_bytes = uploaded_file.getvalue()
            data = format_result(latest_raw)
            dose_ml = latest_raw.get("dose_ml", 0.0)
        else:
            st.error("❌ Prediction failed — backend e
