import streamlit as st
import requests
import base64 
from model_utils_frontend import format_result
from streamlit_autorefresh import st_autorefresh
# Import for explicit error handling
from requests.exceptions import RequestException 
import json 
from binascii import Error as BinasciiError 
import requests.exceptions

# ===========================================
# CONFIG
# ===========================================
# The backend URL is retrieved securely from Streamlit secrets
BACKEND = st.secrets["BACKEND_URL"]

st.set_page_config(
    page_title="Plant Disease Dashboard",
    layout="wide",
)

st.title("🌿 Plant Disease Detection Dashboard")

# Auto-refresh every 5s to check for new data
st_autorefresh(interval=5000, key="data_refresh")


# ===========================================
# STYLE
# ===========================================
st.markdown("""
<style>
/* Custom styling for the image container */
.img-box {
    border: 1px solid #444;
    border-radius: 10px;
    overflow: hidden;
    max-height: 420px;
}
/* Custom styling for the prediction result text */
.pred-box {
    text-align:center;
    font-size:18px;
    padding: 10px;
}

/* Customize Streamlit tabs */
div[data-baseweb="tab-list"] {
    gap: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ===========================================
# 1️⃣ ESP32 STATUS & CONTROL
# ===========================================
st.header("1. ESP32 Control and Status")

# Check connectivity to the backend and the ESP32 status endpoint
try:
    status = requests.get(f"{BACKEND}/esp-status", timeout=3).json()
    if status["status"] == "online":
        st.success(f"🟢 ESP32 Connected — last seen {status['last_seen']:.1f}s ago")
    else:
        st.error("🔴 ESP32 NOT Connected")
except:
    st.error("⚠️ Backend unreachable. Check if the server at BACKEND_URL is running.")


# Capture photo button sends a request to the backend to trigger the ESP32
if st.button("📸 Send Capture Command to ESP32", use_container_width=True):
    try:
        requests.post(f"{BACKEND}/capture")
        st.toast("📩 Capture Request Sent to ESP32")
    except RequestException:
        st.error("Could not send capture request. Backend is unreachable.")

st.markdown("---")

# ===========================================
# 2️⃣ PREDICTION MODES (TABS)
# ===========================================
st.header("2. Prediction Results")

# --- TAB SETUP ---
tab_live, tab_manual = st.tabs(["Live ESP32 Data", "Manual Upload / Test"])

# --- FETCH DATA WITH ROBUST ERROR HANDLING ---
# This function centralizes the data fetching logic to be used by the 'Live' tab
def fetch_latest_data():
    latest_raw = {}
    img_bytes = b''
    
    try:
        # 1. Attempt to fetch prediction data (JSON)
        pred_response = requests.get(f"{BACKEND}/latest")
        pred_response.raise_for_status() 
        latest_raw = pred_response.json()

        # 2. Attempt to fetch image content (Base64 bytes)
        img_response = requests.get(f"{BACKEND}/latest/image")
        img_response.raise_for_status() 
        base64_img_bytes = img_response.content 

        if not base64_img_bytes:
            img_bytes = b''
        else:
            # Decode the Base64 bytes into raw image bytes (JPEG/PNG)
            img_bytes = base64.b64decode(base64_img_bytes)

    except BinasciiError:
        st.warning("Image data received was corrupt or not valid Base64 format.")
        img_bytes = b''
    except json.JSONDecodeError:
        st.error("🛑 Error: Prediction data endpoint returned invalid JSON.")
        return None, None
    except requests.exceptions.HTTPError as e:
        st.error(f"🛑 Error Fetching Data: Backend endpoint returned a server error ({e.response.status_code}).")
        return None, None
    except RequestException:
        st.error(f"🛑 Error Fetching Data: Could not connect to the backend or request timed out.")
        return None, None
    except Exception as e:
        st.error(f"An unexpected system error occurred: {e}")
        return None, None
    
    return latest_raw, img_bytes

# --- LIVE ESP32 DATA TAB ---
with tab_live:
    st.subheader("Latest Result from ESP32/Backend")
    
    # Manual refresh button inside the tab
    if st.button("🔄 Refresh Data", key="refresh_live"):
        st.rerun()

    latest_raw, img_bytes = fetch_latest_data()
    
    if latest_raw is None:
        # This handles connection errors caught in fetch_latest_data
        st.warning("Waiting for data from backend...")
    elif not latest_raw:
        # This handles a successful connection, but the backend returned an empty payload
        st.info("No prediction data yet. Use the 'Capture' button above or the 'Manual Upload' tab to generate data.")
    else:
        # --- DISPLAY RESULTS (Reused Logic) ---
        dose_ml = latest_raw.get("dose_ml", 0.0)
        data = format_result(latest_raw)
        
        col_img, col_info = st.columns([3,2], gap="medium")
        
        # LEFT: IMAGE BOX
        with col_img:
            st.markdown("<div class='img-box'>", unsafe_allow_html=True)
            if img_bytes:
                st.image(img_bytes, caption="📷 Leaf Image from ESP32", use_column_width=True) 
            else:
                st.markdown(
                    "<div style='height:420px; display:flex; align-items:center; justify-content:center; background-color:#262730; color:#aaa; border-radius:10px;'>"
                    "<h3>🖼️ No Image Received</h3>"
                    "</div>", unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # RIGHT: PREDICTION
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
            
            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
            if st.button("🚿 Send Spray Command", use_container_width=True):
                if dose_ml > 0:
                    try:
                        requests.post(f"{BACKEND}/spray", params={"volume_ml": dose_ml})
                        st.success(f"Spray Command Sent: {dose_ml} mL!")
                    except RequestException:
                         st.error("Could not send spray command. Backend is unreachable.")
                else:
                    st.warning("Cannot spray: Calculated dose is 0 mL (Plant appears healthy).")
            st.markdown("</div>", unsafe_allow_html=True)

# --- MANUAL UPLOAD / TEST TAB ---
with tab_manual:
    st.subheader("Upload an Image for Immediate Prediction")
    st.info("Use this tab to upload a test image directly from your computer to the backend for processing.")
    
    uploaded_file = st.file_uploader(
        "Choose a leaf image (JPEG or PNG)", 
        type=['jpg', 'jpeg', 'png']
    )

    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        
        col_prev, col_up = st.columns([1, 2])
        with col_prev:
            st.image(image_bytes, caption="Local Preview", width=150)
            
        with col_up:
            if st.button("🚀 Upload & Process Image", key="manual_upload_btn", use_container_width=True):
                st.info("Uploading image and triggering backend prediction...")
                
                try:
                    # Send the raw bytes to the new backend endpoint
                    upload_response = requests.post(
                        f"{BACKEND}/upload-image", 
                        data=image_bytes,
                        headers={'Content-Type': uploaded_file.type}
                    )
                    upload_response.raise_for_status()
                    st.success("Image uploaded successfully! Switch to the 'Live ESP32 Data' tab to see the new prediction.")
                    # Note: We rely on the autorefresh or manual switch to show the new result.
                except requests.exceptions.HTTPError as e:
                    st.error(f"Upload failed: Backend returned error {e.response.status_code}. Response: {upload_response.text}")
                except RequestException:
                    st.error("Could not connect to the backend to upload the image.")

    else:
        st.markdown(
            """
            <div style='padding: 20px; background-color: #1e1e2d; border-radius: 8px; text-align: center; color: #ccc;'>
                A file uploader is active above. Please select a local image file to begin manual testing.
            </div>
            """,
            unsafe_allow_html=True
        )
