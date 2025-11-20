import streamlit as st
import requests
from model_utils_frontend import format_result

# Load backend URL
BACKEND = st.secrets["BACKEND_URL"]

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="CropIQ Dashboard",
    page_icon="🌿",
    layout="wide"
)

# ---- TOP LOGO + TITLE ----
col_logo, col_title = st.columns([1, 5])

with col_logo:
    st.image("assets/cropiq_logo.png", width=120)

with col_title:
    st.markdown("""
        <h1 style="margin-bottom: -10px;">CropIQ – Smart Plant Health Dashboard</h1>
        <p style="color: #3c763d; font-size: 18px;">AI-powered leaf analysis & automated pesticide control</p>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---- LAYOUT ----
col1, col2 = st.columns([1, 1])

# =========================================================
# LEFT PANEL — ESP32 LATEST DATA
# =========================================================
with col1:
    st.markdown("### 🌱 ESP32 Latest Detection")

    with st.container():
        st.markdown("""
            <div style='padding:15px; border-radius:15px; background:#F3FFF3; border:1px solid #CDECCD;'>
        """, unsafe_allow_html=True)

        if st.button("🔄 Refresh Latest Data"):
            pass

        # Fetch latest result
        res = requests.get(f"{BACKEND}/latest").json()
        data = format_result(res)

        if not data:
            st.warning("No data yet — ESP32 has not uploaded an image.")
        else:
            st.success("Latest data received successfully!")

            st.write(f"**🌿 Plant Type:** {data['plant']}")
            st.write(f"**🦠 Disease:** {data['disease']}")
            st.write(f"**📊 Confidence:** {data['confidence']}%")
            st.write(f"**🔥 Infection Level:** {data['infection']}%")
            st.write(f"**🧪 Recommended Pesticide:** {data['pesticide']}")
            st.write(f"**💧 Dose for 100 ml:** `{data['dose']} ml`")

            if st.button("🧴 Send Spray Command"):
                requests.post(f"{BACKEND}/spray", params={"duration_ms": 2000})
                st.success("Spray command sent to ESP32!")

        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# RIGHT PANEL — MANUAL IMAGE TEST
# =========================================================
with col2:
    st.markdown("### 📷 Manual Leaf Test")

    with st.container():
        st.markdown("""
            <div style='padding:15px; border-radius:15px; background:#F7FAFF; border:1px solid #D6E3FF;'>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader("Upload a leaf image", type=["jpg", "jpeg", "png"])

        if uploaded:
            st.image(uploaded, width=250, caption="Uploaded Image Preview")

            files = {
                "file": (uploaded.name, uploaded.read(), uploaded.type)
            }

            result = requests.post(f"{BACKEND}/predict", files=files).json()

            st.markdown("### 🧠 Model Output")
            st.json(result)

        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<hr>
<center>
    <p style='color: gray;'>© 2025 CropIQ — Powered by AI & IoT</p>
</center>
""", unsafe_allow_html=True)
