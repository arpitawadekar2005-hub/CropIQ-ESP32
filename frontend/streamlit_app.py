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
# 2️⃣ LATEST PREDICTION
# ===========================================
st.header("Latest Prediction from ESP32")

# Refresh button
if st.button("🔄 Refresh"):
    st.rerun()

# Fetch data
latest_raw = requests.get(f"{BACKEND}/latest").json()

# 💡 FIX START: Extract the calculated dose from the backend response.
# The backend uses the key 'dose_ml' for the raw numeric value.
dose_ml = latest_raw.get("dose_ml") 
# Ensure it's treated as 0.0 or a safe number if the dose is None (e.g., if the plant is healthy)
if dose_ml is None or dose_ml == 0:
    dose_ml = 0.0
# 💡 FIX END

data = format_result(latest_raw)

img_bytes = requests.get(f"{BACKEND}/latest/image").content

if not data:
    st.warning("No data yet — ESP32 has not uploaded an image")
    st.stop()

# ===========================================
# Layout — IMAGE LEFT / DATA RIGHT
# ===========================================
col_img, col_info = st.columns([3,2], gap="medium")


# ─── LEFT: IMAGE BOX ─────────────────────
with col_img:
    st.markdown("<div class='img-box'>", unsafe_allow_html=True)
    st.image(img_bytes, caption="📷 Leaf Image from ESP32", use_column_width=True)
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

    # This line now works because dose_ml is defined above
    if st.button("🚿 Send Spray Command", use_container_width=True):
        if dose_ml > 0:
            requests.post(f"{BACKEND}/spray", params={"volume_ml": dose_ml})
            st.success(f"Spray Command Sent: {dose_ml} mL!")
        else:
            st.warning("Cannot spray: Calculated dose is 0 mL (Plant appears healthy).")

    st.markdown("</div>", unsafe_allow_html=True)
