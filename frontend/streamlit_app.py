
import streamlit as st
import requests
from model_utils_frontend import format_result

# ===========================================
# CONFIG
# ===========================================
BACKEND = st.secrets["BACKEND_URL"]

st.set_page_config(page_title="Plant Disease Dashboard", layout="wide")
st.title("🌿 Plant Disease Detection Dashboard")

# ===========================================
# STYLE
# ===========================================
st.markdown(
    """
    <style>
    .app-toolbar {
        display:flex; align-items:center; justify-content:space-between;
        padding: 0.25rem 0;
        border-bottom: 1px solid #e8e8e8;
        margin-bottom: 0.75rem;
    }
    .kpi {
        border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 14px;
        background: #fafafa;
    }
    .kpi h4 { margin: 0 0 2px 0; font-size: 0.95rem; color: #666; }
    .kpi .v { font-size: 1.1rem; font-weight: 700; color: #111; }
    .img-box {
        border: 1px solid #dadde1;
        border-radius: 10px;
        overflow: hidden;
        background: #fff;
    }
    .pred-card {
        border: 1px solid #dadde1;
        border-radius: 12px;
        padding: 16px;
        background: #fff;
    }
    .pred-title {
        text-align:center; margin: 0 0 12px 0;
    }
    .pred-grid { display:grid; grid-template-columns: 1fr 1fr; gap: 8px 12px; }
    .pred-item { background:#f8fafc; border:1px solid #e5e7eb; border-radius:8px; padding:10px; }
    .pred-item b { display:block; font-size: 0.9rem; color:#555; margin-bottom: 6px;}
    .pred-item .v { font-size: 1.05rem; }
    .actions { margin-top: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===========================================
# SESSION STATE
# ===========================================
defaults = {
    "esp_result": None,
    "esp_image": None,
    "manual_result": None,
    "manual_image": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===========================================
# UI HELPERS
# ===========================================
def kpi_card(title: str, value: str):
    st.markdown(f"""
    <div class="kpi">
      <h4>{title}</h4>
      <div class="v">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_prediction_ui(image_bytes, result_raw, btn_key: str):
    """
    Renders: image (left), prediction summary and spray action (right).
    Image is shown ONLY here to avoid duplicates.
    """
    dose_ml = 0.0
    if isinstance(result_raw, dict):
        try:
            dose_ml = float(result_raw.get("dose_ml") or 0.0)
        except Exception:
            dose_ml = 0.0

    data = format_result(result_raw)  # Expect keys: plant, disease, confidence, infection, pesticide, dose
    if not data:
        st.warning("No data available for this image / response.")
        return

    col_img, col_info = st.columns([3, 2], gap="large")

    with col_img:
        st.markdown("<div class='img-box'>", unsafe_allow_html=True)
        st.image(image_bytes, caption="📷 Leaf Image", use_column_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown("<div class='pred-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='pred-title'>🧠 Prediction</h3>", unsafe_allow_html=True)

        # KPI quick glance
        # k1, k2 = st.columns(2)
        # with k1:
        #     kpi_card("🎯 Confidence", f"{data.get('confidence', '—')}%")
        # with k2:
        #     kpi_card("🔥 Infection Level", f"{data.get('infection', '—')}%")

        st.markdown("")
        # Details grid
        st.markdown("<div class='pred-grid'>", unsafe_allow_html=True)
        colA, colB = st.columns(2)
        with colA:
            st.markdown(
                f"<div class='pred-item'><b>🌱 Plant</b><div class='v'>{data.get('plant', '—')}</div></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='pred-item'><b>🧪 Pesticide</b><div class='v'>{data.get('pesticide', '—')}</div></div>",
                unsafe_allow_html=True,
            )
        with colB:
            st.markdown(
                f"<div class='pred-item'><b>🦠 Disease</b><div class='v'>{data.get('disease', '—')}</div></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='pred-item'><b>💧 Dose (per 100 ml)</b><div class='v'>{data.get('dose', '0')} ml</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='actions'>", unsafe_allow_html=True)
        can_spray = dose_ml and dose_ml > 0
        spray_disabled = not can_spray

        if st.button("🚿 Send Spray Command", key=btn_key, use_container_width=True, disabled=spray_disabled):
            try:
                requests.post(f"{BACKEND}/spray", params={"volume_ml": float(dose_ml)}, timeout=8)
                st.success(f"Spray command sent: {float(dose_ml):.1f} mL")
                st.toast("✅ Spray queued")
            except Exception as e:
                st.error(f"Failed to send spray command: {e}")

        if spray_disabled:
            st.caption("Spray disabled because recommended dose is 0 mL.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)  # pred-card


# ===========================================
# TABS
# ===========================================
tab_esp, tab_manual = st.tabs(["ESP32", "Manual Upload"])

# ---------------------------
# TAB: ESP32
# ---------------------------
with tab_esp:
    # Toolbar
    with st.container():
        left, right = st.columns([4, 3])
        with left:
            st.subheader("ESP32 Status & Latest Prediction", divider="gray")
        with right:
            action_cols = st.columns(2)
            with action_cols[0]:
                if st.button("📸 Capture Leaf Image", use_container_width=True):
                    try:
                        requests.post(f"{BACKEND}/capture", timeout=6)
                        st.toast("📩 Capture requested")
                    except Exception as e:
                        st.error(f"Failed to request capture: {e}")
            with action_cols[1]:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()

    # Status card
    status_cols = st.columns(3)
    try:
        status_resp = requests.get(f"{BACKEND}/esp-status", timeout=4)
        status = status_resp.json() if status_resp.ok else {"status": "unknown"}
        state = status.get("status", "unknown")
        last_seen = status.get("last_seen", None)

        with status_cols[0]:
            kpi_card("ESP32", "🟢 Online" if state == "online" else "🔴 Offline")
        with status_cols[1]:
            kpi_card("Last Seen", f"{last_seen:.1f}s" if isinstance(last_seen, (int, float)) else "—")
        with status_cols[2]:
            kpi_card("Backend", f"{status_resp.status_code if status_resp else '—'} /esp-status")
    except Exception:
        with status_cols[0]:
            kpi_card("ESP32", "⚠️ Unreachable")
        with status_cols[1]:
            kpi_card("Last Seen", "—")
        with status_cols[2]:
            kpi_card("Backend", "—")

    st.markdown("---")

    # Fetch and show latest
    try:
        latest_resp = requests.get(f"{BACKEND}/latest", timeout=6)
        latest_raw = latest_resp.json() if latest_resp.ok else None

        if latest_raw and isinstance(latest_raw, dict) and latest_raw.get("status") != "no_data":
            img_resp = requests.get(f"{BACKEND}/latest/image", timeout=6)
            if img_resp.ok:
                st.session_state.esp_image = img_resp.content
                st.session_state.esp_result = latest_raw
                render_prediction_ui(st.session_state.esp_image, st.session_state.esp_result, btn_key="spray_esp")
            else:
                st.warning(f"Could not fetch latest image (status: {img_resp.status_code})")
        else:
            # Show cached if present
            if st.session_state.esp_image and st.session_state.esp_result:
                st.info("Showing cached ESP32 result")
                render_prediction_ui(st.session_state.esp_image, st.session_state.esp_result, btn_key="spray_esp_cached")
            else:
                st.info("Waiting for image from ESP32 device...")
    except Exception as e:
        if st.session_state.esp_image and st.session_state.esp_result:
            st.warning(f"Live fetch error, showing cached: {e}")
            render_prediction_ui(st.session_state.esp_image, st.session_state.esp_result, btn_key="spray_esp_cached_err")
        else:
            st.error(f"Could not fetch latest data: {e}")

# ---------------------------
# TAB: MANUAL
# ---------------------------
with tab_manual:
    st.subheader("Upload an Image (Manual)", divider="gray")

    # Use a form to stabilize interactions
    with st.form("manual_predict_form", clear_on_submit=False):
        uploaded_file = st.camera_input("Take a picture")
        submitted = st.form_submit_button("🔎 Predict from Uploaded Image")

    # Store image ONLY when a new one is captured.
    if uploaded_file is not None:
        st.session_state.manual_image = uploaded_file.getvalue()
        st.session_state.manual_result = None  # Reset only when new image arrives

    # Predict action
    if submitted:
        if not st.session_state.manual_image:
            st.warning("Please capture an image first.")
        else:
            with st.spinner("Processing prediction..."):
                try:
                    file_name = getattr(uploaded_file, "name", "camera.jpg") if uploaded_file else "camera.jpg"
                    file_type = getattr(uploaded_file, "type", "image/jpeg") if uploaded_file else "image/jpeg"
                    files = {"file": (file_name, st.session_state.manual_image, file_type)}
                    resp = requests.post(f"{BACKEND}/predict", files=files, timeout=45)
                    if resp.ok:
                        result = resp.json().get("result", {})
                        st.session_state.manual_result = result
                        st.success("Prediction successful!")
                        st.toast("✅ Prediction ready")
                    else:
                        st.error(f"Prediction failed (status {resp.status_code}).")
                        # Optional: show server message if provided
                        try:
                            err_detail = resp.json().get("detail")
                            if err_detail:
                                with st.expander("Details"):
                                    st.code(str(err_detail))
                        except Exception:
                            pass
                        st.session_state.manual_result = None
                except Exception as e:
                    st.error(f"Failed to send request: {e}")
                    st.session_state.manual_result = None

    # Render result (single display: no extra preview)
    if st.session_state.manual_result and st.session_state.manual_image:
        st.markdown("---")
        render_prediction_ui(
            st.session_state.manual_image,
            st.session_state.manual_result,
            btn_key="spray_manual",
        )
