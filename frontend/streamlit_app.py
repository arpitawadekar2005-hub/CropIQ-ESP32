import streamlit as st
import requests
from model_utils_frontend import format_result

# ===========================================
# CONFIG
# ===========================================
BACKEND = st.secrets["BACKEND_URL"]

st.set_page_config(
    page_title="Plant Disease Dashboard",
    layout="wide",
)

st.title("🌿 Plant Disease Detection Dashboard")

# ===========================================
# STYLE
# ===========================================
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
    unsafe_allow_html=True
)

# ===========================================
# SESSION STATE
# ===========================================
for key, default in [
    ("esp_result", None),
    ("esp_image", None),
    ("manual_result", None),
    ("manual_image", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------------
# Helper: render prediction UI (shared)
# -------------------------
def render_prediction_ui(image_bytes, result_raw, btn_key: str):
    """Render image + prediction panel + spray button."""
    try:
        dose_ml = 0.0
        if isinstance(result_raw, dict):
            # Backend may provide dose_ml (numeric), otherwise it will be 0.0
            dose_ml = float(result_raw.get("dose_ml") or 0.0)

        data = format_result(result_raw)  # normalized fields dict
        if not data:
            st.warning("No data available for this image / response")
            return

        col_img, col_info = st.columns([3, 2], gap="medium")

        with col_img:
            st.markdown("<div class='img-box'>", unsafe_allow_html=True)
            st.image(image_bytes, caption="📷 Leaf Image", use_column_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_info:
            st.markdown(
                "<h3 style='text-align:center;'>🧠 Prediction Result</h3>",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="pred-box">
                🌱 <b>Plant:</b> {data.get('plant', '—')}<br><br>
                🦠 <b>Disease:</b> {data.get('disease', '—')}<br><br>
                🎯 <b>Confidence:</b> {data.get('confidence', '—')}%<br><br>
                🔥 <b>Infection Level:</b> {data.get('infection', '—')}%<br><br>
                🧪 <b>Pesticide:</b> {data.get('pesticide', '—')}<br><br>
                💧 <b>Dose (per 100 ml):</b> {data.get('dose', '0')} ml
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")
            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)

            if st.button("🚿 Send Spray Command", key=btn_key, use_container_width=True):
                try:
                    vol = max(0.0, float(dose_ml))
                    if vol > 0:
                        requests.post(f"{BACKEND}/spray", params={"volume_ml": vol}, timeout=6)
                        st.success(f"Spray Command Sent: {vol:.1f} mL!")
                    else:
                        st.warning("Cannot spray: Calculated dose is 0 mL (Plant appears healthy).")
                except Exception as e:
                    st.error(f"Failed to send spray command: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Failed to render prediction UI: {e}")

# ===========================================
# TABS: ESP32 | Manual Upload
# ===========================================
tab_esp, tab_manual = st.tabs(["ESP32", "Manual Upload"])

# ===========================================
# TAB: ESP32
# ===========================================
with tab_esp:
    st.header("ESP32 Status & Latest Prediction")

    # Status
    try:
        status_resp = requests.get(f"{BACKEND}/esp-status", timeout=3)
        status = status_resp.json() if status_resp.ok else {"status": "unknown"}
        if status.get("status") == "online":
            last_seen = status.get("last_seen")
            if isinstance(last_seen, (int, float)):
                st.success(f"🟢 ESP32 Connected — last seen {last_seen:.1f}s ago")
            else:
                st.success("🟢 ESP32 Connected")
        else:
            st.error("🔴 ESP32 NOT Connected")
    except Exception:
        st.error("⚠️ Backend unreachable")

    st.write("")

    colA, colB = st.columns(2)
    with colA:
        if st.button("📸 Capture Leaf Image", use_container_width=True):
            try:
                requests.post(f"{BACKEND}/capture", timeout=5)
                st.toast("📩 Capture Request Sent to ESP32")
            except Exception as e:
                st.error(f"Failed to request capture: {e}")

    with colB:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Latest prediction & image from ESP
    try:
        latest_resp = requests.get(f"{BACKEND}/latest", timeout=5)
        latest_raw = latest_resp.json() if latest_resp.ok else None

        if latest_raw:
            img_resp = requests.get(f"{BACKEND}/latest/image", timeout=5)
            if img_resp.ok:
                st.session_state.esp_image = img_resp.content
                st.session_state.esp_result = latest_raw
                render_prediction_ui(st.session_state.esp_image, st.session_state.esp_result, btn_key="spray_esp")
            else:
                st.warning(f"Could not fetch latest image (status: {img_resp.status_code})")
        else:
            # If previously had a result, show cached while waiting
            if st.session_state.esp_image and st.session_state.esp_result:
                render_prediction_ui(st.session_state.esp_image, st.session_state.esp_result, btn_key="spray_esp_cached")
            else:
                st.info("Waiting for image from ESP32 device...")
    except Exception as e:
        # Fallback to cached if available
        if st.session_state.esp_image and st.session_state.esp_result:
            st.warning(f"Live fetch error, showing last cached: {e}")
            render_prediction_ui(st.session_state.esp_image, st.session_state.esp_result, btn_key="spray_esp_cached_err")
        else:
            st.warning(f"Could not fetch latest data: {e}")

# ===========================================
# TAB: MANUAL UPLOAD
# ===========================================
with tab_manual:
    st.header("Upload an Image (Manual)")

    # Use a form to control submission and avoid rerun side effects
    with st.form("manual_predict_form", clear_on_submit=False):
        # NOTE: st.camera_input shows the camera preview by design.
        # We will NOT call st.image() ourselves to avoid duplicates.
        uploaded_file = st.camera_input("Take a picture")
        submitted = st.form_submit_button("🔎 Predict from Uploaded Image")

    # If a new image was captured, store it; DO NOT show extra preview
    if uploaded_file is not None:
        st.session_state.manual_image = uploaded_file.getvalue()
        # Reset result only when a new image arrives
        st.session_state.manual_result = None

    # Predict only when the button is pressed
    if submitted:
        if st.session_state.manual_image is None:
            st.warning("Please capture an image first.")
        else:
            with st.spinner("Processing prediction..."):
                try:
                    file_name = getattr(uploaded_file, "name", "camera.jpg") if uploaded_file else "camera.jpg"
                    file_type = getattr(uploaded_file, "type", "image/jpeg") if uploaded_file else "image/jpeg"
                    files = {"file": (file_name, st.session_state.manual_image, file_type)}

                    resp = requests.post(f"{BACKEND}/predict", files=files, timeout=30)
                    if resp.ok:
                        resp_json = resp.json()
                        st.session_state.manual_result = resp_json.get("result", {})
                        st.success("Prediction successful!")
                    else:
                        st.error(f"Prediction failed. Status code: {resp.status_code}")
                        st.session_state.manual_result = None
                except Exception as e:
                    st.error(f"Failed to send request or unexpected error: {e}")
                    st.session_state.manual_result = None

    # Render prediction result (only once, no extra manual preview)
    if st.session_state.manual_result and st.session_state.manual_image:
        st.markdown("---")
        render_prediction_ui(
            st.session_state.manual_image,
            st.session_state.manual_result,
            btn_key="spray_manual",
        )
