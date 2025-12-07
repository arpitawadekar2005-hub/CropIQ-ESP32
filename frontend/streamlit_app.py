
import streamlit as st
import requests
from model_utils_frontend import format_result  # your normalizer

# ===========================================
# CONFIG
# ===========================================
BACKEND = st.secrets["BACKEND_URL"]

# st.set_page_config(page_title="Plant Disease Dashboard", layout="wide")
st.title("🌿 CROPIQ - Plant Disease Detection")

# ===========================================
# GLOBAL STYLES (Plant-themed CSS)
# ===========================================
# 🎨 Palette — tweak these values to change the mood
BG_MAIN = "#eef7ee"             # soft mint/green background
BG_SIDEBAR = "#e9f3e9"          # sidebar background
CARD_BG = "#52796f"             # card background
CARD_BORDER = "#cfe6cf"         # card border
ITEM_BG = "#84a98c"             # item row background
ITEM_BORDER = "#d9ead9"         # item row border
TEXT_HEADING = "#1b4332"        # dark green headings
TEXT_BODY = "#FFFFFF"           # body text
ACCENT = "#354f52"              # accent for hover/borders (matches config.toml)

st.markdown(
    f"""
    <style>
    /* ----- App Background & Base ----- */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {BG_MAIN};
    }}
    [data-testid="stSidebar"] > div {{
        background-color: {BG_SIDEBAR};
    }}

    /* ----- Cards and Image ----- */
    .img-box {{
        border: 1px solid {CARD_BORDER};
        border-radius: 12px;
        overflow: hidden;
        background: {CARD_BG};
    }}
    .pred-card {{
        border: 1px solid {CARD_BORDER};
        border-radius: 12px;
        padding: 16px;
        background: {CARD_BG};
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.06);
    }}
    .pred-title {{
        text-align:center;
        margin: 0 0 12px 0;
        font-weight: 700;
        color: {TEXT_HEADING};
    }}

    /* ----- Single stacked details inside one card ----- */
    .stack {{
        display: flex;
        flex-direction: column;
        gap: 10px;
    }}
    .pred-item {{
        background: {ITEM_BG};
        border: 1px solid {ITEM_BORDER};
        border-radius: 10px;
        padding: 10px 12px;
    }}
    .pred-item b {{
        display: block;
        font-size: 0.9rem;
        color: #355f35;
        margin-bottom: 6px;
    }}
    .pred-item .v {{
        font-size: 1.05rem;
        color: {TEXT_BODY};
        word-break: break-word;
    }}

    /* ----- Actions ----- */
    .actions {{ margin-top: 12px; }}
    .actions .caption {{ color: #517a51; font-size: 0.9rem; }}

    /* ----- Buttons & headings ----- */
    .stButton>button {{
        border-radius: 10px;
        border: 1px solid {CARD_BORDER};
        background-color: {CARD_BG};
        color: {TEXT_BODY};
    }}
    .stButton>button:hover {{
        border-color: {ACCENT};
    }}
    h1, h2, h3 {{ color: {TEXT_HEADING}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===========================================
# SESSION STATE (kept separate per tab)
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
# OPTIONAL: rotate helper if your camera images appear upside-down
# Uncomment and use if needed
# from io import BytesIO
# from PIL import Image
# def rotate_bytes_180(img_bytes: bytes) -> bytes:
#     try:
#         im = Image.open(BytesIO(img_bytes))
#         im = im.rotate(180, expand=True)
#         out = BytesIO()
#         im.save(out, format="JPEG", quality=90)
#         return out.getvalue()
#     except Exception:
#         return img_bytes  # fallback

# ===========================================
# SHARED RENDERER: STACKED SINGLE CARD
# ===========================================
def render_prediction_ui(image_bytes, result_raw, btn_key: str):
    """
    Renders image (left) and a single stacked prediction card (right).
    Details shown: Plant, Disease, Pesticide, Dose (per 100 ml).
    Confidence/Infection are intentionally omitted.
    """
    # dose_ml used to enable/disable spray button
    dose_ml = 0.0
    if isinstance(result_raw, dict):
        try:
            dose_ml = float(result_raw.get("dose_ml") or 0.0)
        except Exception:
            dose_ml = 0.0

    data = format_result(result_raw)  # Expect keys: plant, disease, pesticide, dose
    if not data:
        st.warning("No data available for this image / response.")
        return

    col_img, col_info = st.columns([3, 2], gap="large")

    # Left: image
    with col_img:
        st.markdown("<div class='img-box'>", unsafe_allow_html=True)
        st.image(image_bytes, caption="📷 Leaf Image", use_column_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Right: single prediction card (stacked vertically)
    with col_info:
        # st.markdown("<div class='pred-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='pred-title'>Prediction</h3>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="stack">
                <div class="pred-item">
                    <b>🌱 Plant</b>
                    <div class="v">{data.get('plant', '—')}</div>
                </div>
                <div class="pred-item">
                    <b>🦠 Disease</b>
                    <div class="v">{data.get('disease', '—')}</div>
                </div>
                <div class="pred-item">
                    <b>🧪 Pesticide</b>
                    <div class="v">{data.get('pesticide', '—')}</div>
                </div>
                <div class="pred-item">
                    <b>💧 Dose (per 100 ml)</b>
                    <div class="v">{data.get('dose', '0')} ml</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Actions
        st.markdown("<div class='actions'>", unsafe_allow_html=True)
        can_spray = dose_ml > 0
        if st.button("🚿 Send Spray Command", key=btn_key, use_container_width=True, disabled=not can_spray):
            try:
                requests.post(f"{BACKEND}/spray", params={"volume_ml": float(dose_ml)}, timeout=8)
                st.success(f"Spray command sent: {float(dose_ml):.1f} mL")
                st.toast("✅ Spray queued")
            except Exception as e:
                st.error(f"Failed to send spray command: {e}")

        if not can_spray:
            st.caption("Spray disabled because recommended dose is 0 mL.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # end pred-card

# ===========================================
# TABS
# ===========================================
tab_esp, tab_manual = st.tabs(["ESP32", "Manual Upload"])

# ---------------------------
# TAB: ESP32
# ---------------------------
with tab_esp:
    st.header("ESP32 Status & Latest Prediction")
    try:
        status_resp = requests.get(f"{BACKEND}/esp-status", timeout=3)
        status = status_resp.json() if status_resp.ok else {"status": "unknown"}

        if status.get("status") == "online":
            last_seen = status.get("last_seen")
            if isinstance(last_seen, (int, float)):
                st.markdown(f"**ESP32 Status:** 🟢 Online (last seen {last_seen:.1f}s ago)")
            else:
                st.markdown("**ESP32 Status:** 🟢 Online")
        else:
            st.markdown("**ESP32 Status:** 🔴 Offline")

    except Exception:
        st.markdown("**ESP32 Status:** ⚠️ Backend unreachable")

    top_cols = st.columns(1)
    with top_cols[0]:
        if st.button("📸 Capture Leaf Image", use_container_width=True):
            try:
                requests.post(f"{BACKEND}/capture", timeout=6)
                st.toast("📩 Capture requested")
            except Exception as e:
                st.error(f"Failed to request capture: {e}")

    # with top_cols[1]:
    #     if st.button("🔄 Refresh", use_container_width=True):
    #         st.rerun()

    st.markdown("---")

    # Fetch and show latest ESP result
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
# TAB: MANUAL UPLOAD
# ---------------------------
with tab_manual:
    st.header("Upload an Image (Manual)")

    # Form stabilizes interactions and avoids rerun side-effects
    with st.form("manual_predict_form", clear_on_submit=False):
        uploaded_file = st.camera_input("Take a picture")
        submitted = st.form_submit_button("🔎 Predict from Uploaded Image")

    # Store image ONLY when a new one is captured (no extra preview here)
    if uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        # If you need rotation due to upside-down camera, uncomment:
        # raw_bytes = rotate_bytes_180(raw_bytes)
        st.session_state.manual_image = raw_bytes
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
                        # Optional: show server-provided error detail
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

    # Render result (single display in stacked card)
    if st.session_state.manual_result and st.session_state.manual_image:
        st.markdown("---")
        render_prediction_ui(
            st.session_state.manual_image,
            st.session_state.manual_result,
            btn_key="spray_manual",
        )

