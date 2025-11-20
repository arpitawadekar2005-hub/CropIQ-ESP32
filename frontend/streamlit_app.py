import streamlit as st
import requests
from model_utils_frontend import format_result

BACKEND = st.secrets["BACKEND_URL"]

st.set_page_config(page_title="Plant Disease Dashboard", layout="wide")
st.title("🌿 Plant Disease Detection Dashboard")

col1, col2 = st.columns([1,1])

with col1:
    st.header("Latest Prediction from ESP32")

    if st.button("Refresh"):
        pass

    res = requests.get(f"{BACKEND}/latest").json()
    data = format_result(res)

    if not data:
        st.warning("No data yet — ESP32 has not uploaded an image")
    else:
        st.success("Latest Data Received")

        st.write(f"**Plant:** {data['plant']}")
        st.write(f"**Disease:** {data['disease']}")
        st.write(f"**Confidence:** {data['confidence']}%")
        st.write(f"**Infection:** {data['infection']}%")
        st.write(f"**Pesticide:** {data['pesticide']}")
        st.write(f"**Dose for 100 ml:** {data['dose']} ml")

        if st.button("Send Spray Command"):
            requests.post(f"{BACKEND}/spray", params={"duration_ms": 2000})
            st.success("Spray command sent to ESP32!")

with col2:
    st.header("Manual Image Test")

    uploaded = st.file_uploader("Upload leaf image", type=["jpg","png","jpeg"])
    if uploaded:
        files = {"file": (uploaded.name, uploaded.read(), uploaded.type)}
        result = requests.post(f"{BACKEND}/predict", files=files).json()
        st.json(result)
