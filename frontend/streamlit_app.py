
import streamlit as st
import requests
from model_utils_frontend import format_result  # your normalizer

# ===========================================
# CONFIG
# ===========================================
BACKEND = st.secrets["BACKEND_URL"]

st.set_page_config(page_title="Plant Disease Dashboard", layout="wide")
st.title("🌿 Plant Disease Detection Dashboard")

# ===========================================
# GLOBAL STYLES (Plant-themed CSS with tokens)
# ===========================================
# 🎨 Palette — tweak these values to change the mood
st.markdown(
    """
    <style>
    /* =======================
       🎨 Color Tokens
       ======================= */
    :root {
      /* App backgrounds */
      --bg-main:            #eef7ee;  /* page background */
      --bg-sidebar:         #e9f3e9;  /* sidebar background */

      /* Card + item surfaces */
      --card-bg:            #f6fbf6;  /* prediction card background (slightly lighter) */
      --card-border:        #b9ddb9;  /* prediction card border */

      /* 👉 Item rows slightly DARKER than page background */
      --item-bg:            #e1f0e1;  /* plant/disease/pesticide/dose row background */
      --item-border:        #a9cea9;  /* row border */

      /* Text */
      --text-heading:       #1f3c1f;  /* headings */
      --text-body:          #173217;  /* body text */
      --text-muted:         #517a51;  /* captions */

      /* Accents / buttons / focus */
      --accent:             #2e7d32;  /* green accent */
      --accent-weak:        #95c89a;  /* soft accent for focus/hover outlines */

      /* Shadows */
      --shadow-100:         0 1px 2px rgba(16, 24, 40, 0.06);
    }

    /* =======================
       Base surfaces
       ======================= */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-main);
    }
    [data-testid="stSidebar"] > div {
        background-color: var(--bg-sidebar);
    }

    /* =======================
       Cards & Image containers
       ======================= */
    .img-box {
        border: 1px solid var(--card-border);
        border-radius: 12px;
        overflow: hidden;
        background: #ffffff;
        box-shadow: var(--shadow-100);
    }
    .pred-card {
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 16px;
        background: var(--card-bg);
        box-shadow: var(--shadow-100);
    }
    .pred-title {
        text-align:center;
        margin: 0 0 12px 0;
        font-weight: 800;
        color: var(--text-heading);
    }

    /* =======================
       Stacked item rows (darker than bg)
       ======================= */
    .stack {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .pred-item {
        background: var(--item-bg);
        border: 1px solid var(--item-border);
        border-radius: 12px;
        padding: 12px 14px;
        transition: border-color .15s ease, background-color .15s ease;
    }
    .pred-item:hover {
        border-color: var(--accent-weak);
        /* fallback for old browsers is same bg; color-mix supported in modern engines */
        background: color-mix(in oklab, var(--item-bg) 92%, black 8%);
    }
    .pred-item b {
        display: block;
        font-size: 0.92rem;
        color: var(--text-heading);
        margin-bottom: 6px;
    }
    .pred-item .v {
        font-size: 1.06rem;
        color: var(--text-body);
        word-break: break-word;
    }

    /* =======================
       Actions (spray button)
       ======================= */
    .actions { margin-top: 14px; }
    .actions .caption { color: var(--text-muted); font-size: 0.92rem; }

    .stButton>button {
        border-radius: 12px !important;
        border: 1px solid var(--card-border) !important;
        background-color: #ffffff !important;
        color: var(--text-body) !important;
        box-shadow: var(--shadow-100) !important;
    }
    .stButton>button:hover {
        border-color: var(--accent) !important;
    }
    .stButton>button:disabled,
    .stButton>button[disabled] {
        opacity: .65 !important;
        cursor: not-allowed !important;
    }

    /* =======================
       Headings
       ======================= */
    h1, h2, h3 { color: var(--text-heading); }

    /* =======================
       ESP Status badges
       ======================= */
    .status-row { display:flex; gap: 10px; align-items:center; margin-bottom: 10px; flex-wrap: wrap; }
    .badge {
      display:inline-flex; align-items:center; gap:6px;
      padding: 6px 10px; border-radius: 999px;
      border: 1px solid var(--item-border);
      background: var(--item-bg);
      color: var(--text-body);
      font-size: 0.92rem;
      box-shadow: var(--shadow-100);
    }
    .badge .dot { width:10px; height:10px; border-radius:50%; display:inline-block; }
    .dot-green { background:#22c55e; }
    .dot-red   { background:#ef4444; }
    .dot-gray  { background:#9ca3af; }
    .badge small { color: var(--text-muted); }
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
# ESP status helper (cached)
# ===========================================
@st.cache_data(ttl=5, show_spinner=False)
def get_esp_status():
    """
    Returns a dict with keys:
      - status: 'online' | 'offline' | 'unknown'
      - last_seen: float seconds (may be absent)
      - reason: string (optional)
    """
    try:
        resp = requests.get(f"{BACKEND}/esp-status", timeout=4)
        if resp.ok:
            return resp.json()
        return {"status": "unknown", "reason": f"http {resp.status_code}"}
    except Exception as e:
        return {"status": "unknown", "reason": str(e)}

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
        st.markdown("<div class='pred-card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='pred-title'>🧠 Prediction</h3>", unsafe_allow_html=True)

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

    # --- Status badges row ---
    status = get_esp_status()
    state = status.get("status", "unknown")
    last_seen = status.get("last_seen", None)
    reason = status.get("reason")

    st.markdown("<div class='status-row'>", unsafe_allow_html=True)
    if state == "online":
        st.markdown("<span class='badge'><span class='dot dot-green'></span> ESP32: Online</span>", unsafe_allow_html=True)
    elif state == "offline":
        st.markdown("<span class='badge'><span class='dot dot-red'></span> ESP32: Offline</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge'><span class='dot dot-gray'></span> ESP32: Unknown</span>", unsafe_allow_html=True)

    if isinstance(last_seen, (int, float)):
        st.markdown(f"<span class='badge'>⏱️ Last seen: {last_seen:.1f}s</span>", unsafe_allow_html=True)

    if reason:
        st.markdown(f"<span class='badge'>ℹ️ {reason}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Action buttons ---
    top_cols = st.columns(2)
    with top_cols[0]:
        if st.button("📸 Capture Leaf Image", use_container_width=True):
            try:
                requests.post(f"{BACKEND}/capture", timeout=6)
                st.toast("📩 Capture requested")
            except Exception as e:
                st.error(f"Failed to request capture: {e}")
    with top_cols[1]:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

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
        # If your camera images appear flipped, add rotate helper & apply here
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
