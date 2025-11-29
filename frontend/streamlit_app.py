import streamlit as st
import requests
from model_utils_frontend import format_result
from streamlit_autorefresh import st_autorefresh

BACKEND = st.secrets["BACKEND_URL"]

# ================================
# UI CONFIG
# ================================
st.set_page_config(page_title="Plant Disease Dashboard", layout="wide")
st.title("🌿 Plant Disease Detection Dashboard")

# 🔄 Auto refresh every 5 seconds
st_autorefresh(interval=5000, limit=None, key="data_refresh")


# ================================
# ESP STATUS
# ================================
st.subheader("ESP32 Status")

try:
    status = requests.get(f"{BACKEND}/esp-status", timeout=2).json()
    if status.get("status") == "online":
        st.success(f"🟢 ESP32 Connected (last seen {status['last_seen']:.1f}s ago)")
    else:
        st.error("🔴 ESP32 NOT Connected")
except Exception:
    st.error("⚠️ Backend unreachable")

st.button("📸 Capture Leaf Image", on_click=lambda: requests.post(f"{BACKEND}/capture"))

# ================================
# LATEST IMAGE + PREDICTION
# ================================
st.header("Latest Prediction from ESP32")

# Manual refresh option
if st.button("Refresh"):
    st.rerun()

# ---- Get latest data ----
latest = requests.get(f"{BACKEND}/latest").json()
data = format_result(latest)

# ---- Get latest image ----
img_url = f"{BACKEND}/latest/image"
img_response = requests.get(img_url)

img_bytes = img_response.content if img_response.status_code == 200 else None

if not data:
    st.warning("No data yet — ESP32 has not uploaded an image")
else:
    st.success("Latest Data Received")

    # ---------- SHOW IMAGE ----------
    if img_bytes and img_bytes != b'{"status":"no_image"}':
        st.image(img_bytes, caption="Live Image from ESP32", use_column_width=True)
    else:
        st.info("Image not available")

    # ---------- SHOW PREDICTION ----------
    st.write(f"**🌱 Plant:** {data['plant']}")
    st.write(f"**🦠 Disease:** {data['disease']}")
    st.write(f"**📊 Confidence:** {data['confidence']}%")
    st.write(f"**🔥 Infection Level:** {data['infection']}%")
    st.write(f"**🧪 Pesticide:** {data['pesticide']}")
    st.write(f"**💧 Dose (per 100 ml):** {data['dose']} ml")

    if st.button("Send Spray Command"):
        requests.post(f"{BACKEND}/spray", params={"duration_ms": 2000})
        st.success("🌧️ Spray command sent to ESP32!")
