# 🌱 CropIQ – AI-Powered Precision Spraying System

<p align="center">
  <img src="images/cropiq-prototype.jpg" alt="CropIQ Prototype" width="700">
</p>

<p align="center">
  <b>AI + IoT based precision agriculture system for crop disease detection and targeted spraying.</b>
</p>

---

##  Overview

**CropIQ** is an AI-powered precision spraying system developed to detect crop diseases from leaf images and deliver targeted pesticide spraying based on the detected disease.

The system combines:

- ESP32-CAM for image acquisition
- Machine Learning for crop disease detection
- Cloud-based backend for AI processing
- Flow-controlled precision spraying
- IoT-based communication
- Streamlit dashboard for monitoring and control

The objective is to reduce unnecessary pesticide usage, improve disease detection and automate the spraying process.

---

##  Objectives

- Detect crop diseases using real-time leaf images.
- Generate appropriate spray dosage based on the detected disease.
- Automate pesticide spraying using sensors and actuators.
- Establish wireless communication between the hardware and cloud backend.
- Provide a user-friendly dashboard for monitoring and control.
- Reduce chemical wastage and manual intervention.
- Support sustainable and precision agriculture.

---

##  System Architecture

<p align="center">
  <img src="images/block-diagram.png" alt="CropIQ System Block Diagram" width="800">
</p>

## Hardware Components
| Component               | Purpose                                                      |
| ----------------------- | ------------------------------------------------------------ |
| **ESP32-CAM**           | Captures crop/leaf images and provides Wi-Fi communication   |
| **Level Shifter**       | Provides voltage-level conversion between connected circuits |
| **Relay Module**        | Controls the DC pump using the ESP32 control signal          |
| **Mini DC Pump**        | Pumps the spraying liquid                                    |
| **YF-S401 Flow Sensor** | Measures liquid flow and helps control spray volume          |
| **3.7V Li-ion Battery** | Portable power source                                        |
| **IC 7805**             | Provides regulated 5V supply                                 |
| **Heat Sink**           | Helps dissipate heat from electronic components              |
| **Sprayer/Container**   | Stores and delivers the spraying liquid                      |

## Software Tools & Frameworks
| Technology          | Purpose                        |
| ------------------- | ------------------------------ |
| **Arduino IDE**     | ESP32-CAM firmware development |
| **Python**          | Backend and ML development     |
| **FastAPI**         | Backend API                    |
| **Uvicorn**         | ASGI server                    |
| **Streamlit**       | Web dashboard                  |
| **EfficientNet-B0** | Crop disease classification    |
| **Render**          | Backend cloud deployment       |
| **Streamlit Cloud** | Dashboard deployment           |
| **GitHub**          | Version control                |
| **Google Drive**    | Model storage                  |
| **HTTPS + JSON**    | API communication              |

## Machine Learning Model

CropIQ uses a fine-tuned EfficientNet-B0 image classification model for tomato leaf disease detection.

# Dataset
- Approximately 12,000 tomato leaf images
- 10 classes
- Images resized to 224 × 224
- Separate 1,000-image test set
# Model Performance
- Validation accuracy: 93.5%
- Final test accuracy: 94.4%
- F1 score for difficult classes such as Early Blight and Target Spot: 86–88%
- The model was fine-tuned using AdamW, weight decay and MixUp augmentation.

## ## Working Principle

The complete system operates in the following sequence:

1. **Image Capture** — ESP32-CAM captures an image of the crop leaf.
2. **Image Upload** — The image is sent to the cloud backend through Wi-Fi.
3. **AI Processing** — The backend processes the image using the trained EfficientNet-B0 model.
4. **Disease Detection** — The AI model identifies the detected crop disease.
5. **Dosage Calculation** — The backend calculates the required spray dosage.
6. **Spray Command** — The spray command is sent back to the ESP32.
7. **Pump Activation** — The ESP32 activates the relay to switch ON the DC pump.
8. **Flow Measurement** — The YF-S401 flow sensor measures the liquid flow.
9. **Precision Spraying** — The pump operates according to the calculated dosage.
10. **Monitoring** — Prediction and spraying information are displayed on the Streamlit dashboard.

## Web Dashboard

The CropIQ dashboard is developed using Streamlit.

It provides:

- Crop leaf image
- Disease prediction
- Prediction confidence
- Recommended pesticide
- Spray dosage
- ESP32 status
- Spraying status
- Manual image upload for testing
## Results

The complete CropIQ prototype was tested under controlled and semi-field conditions.

###  AI Disease Detection

- Crop leaf images were successfully captured using the **ESP32-CAM**.
- Images were processed using a **cloud-based AI model**.
- Disease predictions were obtained within approximately **1–3 seconds**, depending on network conditions.

### Precision Spraying

- A **relay-controlled pump** was successfully integrated into the system.
- The **YF-S401 flow sensor** provided real-time flow feedback.
- The system enabled controlled and repeatable spray volume.

### Chemical Usage

Small-scale testing indicated approximately:

**30–40% reduction in pesticide consumption**

This reduction was achieved through **selective spraying**, where pesticide is applied only when a crop disease is detected.

### Connectivity

- ESP32-CAM successfully connected to the backend system.
- Captured images were uploaded for cloud-based processing.
- AI responses were received successfully.
- The AI prediction was used to control the pesticide spraying mechanism.

### Summary of Results

| Parameter | Result |
|---|---|
| Image Capture | Successfully tested |
| AI Disease Detection | Successfully tested |
| Prediction Time | Approximately 1–3 seconds |
| Precision Spraying | Successfully integrated |
| Flow Feedback | YF-S401 sensor |
| Pump Control | Relay-controlled |
| Cloud Connectivity | Successfully tested |

> **Note:** These results are based on controlled and small-scale testing of the prototype. They are intended to demonstrate the feasibility of the system and should not be considered a universal performance guarantee under all field conditions.

## Advantages

- Reduced pesticide wastage through selective spraying.
- Automated AI-based disease detection.
- Precision spraying based on disease detection.
- Reduced manual intervention and labour requirement.
- Real-time monitoring through IoT connectivity.
- Supports sustainable agriculture.
- 
## Conclusion

CropIQ demonstrates the integration of Artificial Intelligence, IoT, embedded systems, computer vision and precision control for smart agriculture.
The prototype combines AI-based disease detection with automated, flow-controlled spraying to reduce unnecessary chemical usage and improve the efficiency of crop protection.

## Project Team

- **Arpita Wadekar** — Electronics & Communication Engineering
- **Akash Dukare** — Electronics & Communication Engineering
- **Nitin Patil** — Electronics & Communication Engineering
- **Aditya Jahagirdar** — Electronics & Communication Engineering

**Jain College of Engineering, Belagavi**
