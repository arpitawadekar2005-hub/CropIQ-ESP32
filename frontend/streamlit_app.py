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

# Auto-refresh every 5s (keeps ESP tab up-to-date)
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
# TABS: ESP32 | Manual Upload
# ===========================================
tab_esp, tab_manual = st.tabs(["ESP32", "Manual Upload"])


# -------------------------
# Helper: render prediction UI (shared)
# -------------------------
def render_prediction_ui(image_bytes, result_raw):
    """Render image + prediction panel + spray button.
    result_raw is the raw backend response (dict) that format_result can consume.
    Returns nothing.
    """
    # Extract numeric dose value (backend may provide dose_ml)
    dose_ml = result_raw.get("dose_ml") if isinstance(result_raw, dict) else None
    if dose_ml is None:
        # fall back to 0.0 if missing or zero-like
        dose_ml = 0.0

    data = format_result(result_raw)

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
            🌱 <b>Plant:</b> {data['plant']}<br><br>
            🦠 <b>Disease:</b> {data['disease']}<br><br>
            🎯 <b>Confidence:</b> {data['confidence']}%<br><br>
            🔥 <b>Infection Level:</b> {data['infection']}%<br><br>
            🧪 <b>Pesticide:</b> {data['pesticide']}<br><br>
            💧 <b>Dose (per 100 ml):</b> {data['dose']} ml
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)

        # Spray button behaviour is identical for both tabs
        if st.button("🚿 Send Spray Command", use_container_width=True):
            if dose_ml and float(dose_ml) > 0:
                try:
                    requests.post(f"{BACKEND}/spray", params={"volume_ml": float(dose_ml)})
                    st.success(f"Spray Command Sent: {float(dose_ml)} mL!")
                except Exception as e:
                    st.error(f"Failed to send spray command: {e}")
            else:
                st.warning("Cannot spray: Calculated dose is 0 mL (Plant appears healthy).")

        st.markdown("</div>", unsafe_allow_html=True)


# ===========================================
# TAB: ESP32 (keeps original behaviour)
# ===========================================
with tab_esp:
    st.header("ESP32 Status & Latest Prediction")

    # ESP32 status check
    try:
        status = requests.get(f"{BACKEND}/esp-status", timeout=3).json()
        if status.get("status") == "online":
            st.success(f"🟢 ESP32 Connected — last seen {status.get('last_seen', 0):.1f}s ago")
        else:
            st.error("🔴 ESP32 NOT Connected")
    except Exception:
        st.error("⚠️ Backend unreachable")

    st.write("")

    # Capture photo button (same as before)
    if st.button("📸 Capture Leaf Image"):
        try:
            requests.post(f"{BACKEND}/capture")
            st.toast("📩 Capture Request Sent to ESP32")
        except Exception as e:
            st.error(f"Failed to request capture: {e}")

    st.markdown("---")

    # Refresh control
    if st.button("🔄 Refresh"):
        st.rerun()

    # Fetch latest prediction from backend
    try:
        latest_raw = requests.get(f"{BACKEND}/latest", timeout=4).json()
        # image bytes come from a specific endpoint
        img_bytes = requests.get(f"{BACKEND}/latest/image", timeout=4).content
        render_prediction_ui(img_bytes, latest_raw)
    except Exception as e:
        st.warning(f"Could not fetch latest data: {e}")


# ===========================================
# TAB: MANUAL UPLOAD
# ===========================================
with tab_manual:
    st.header("Upload an Image (Manual)")

    uploaded_file = st.file_uploader("Choose a leaf image", type=["png", "jpg", "jpeg"], accept_multiple_files=False)

    # Optional: allow the user to provide a confidence override or extra metadata in the future
    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        st.image(image_bytes, caption="Uploaded Image Preview", use_column_width=False)

        if st.button("🔎 Predict from Uploaded Image"):
            try:
                # <- IMPORTANT: backend expects field name "file"
                files = {"file": (uploaded_file.name, image_bytes, uploaded_file.type)}
                resp = requests.post(f"{BACKEND}/predict", files=files, timeout=15)
            except Exception as e:
                st.error(f"Failed to send request: {e}")
            else:
                st.write("Status code:", resp.status_code)
                st.write("Response headers:", dict(resp.headers))
                st.code(resp.text, language="json")

                if not resp.ok:
                    st.error(f"Backend returned {resp.status_code}. See raw response above.")
                else:
                    # Backend returns {"status":"ok","result": <your result dict>}
                    try:
                        resp_json = resp.json()
                    except Exception as e:
                        st.error(f"Response is not valid JSON: {e}")
                        st.stop()

                    if resp_json.get("status") != "ok" or "result" not in resp_json:
                        st.error("Unexpected response shape from backend; see raw response above.")
                    else:
                        result_raw = resp_json["result"]
                        # render the same UI as ESP tab using the unwrapped result
                        render_prediction_ui(image_bytes, result_raw)



# ===========================================
# FOOTER / NOTES
# ===========================================
st.markdown("---")
st.caption("Tabs: ESP32 (live device) | Manual Upload (send your own image to model). Spray command behavior is identical in both tabs.")
