# 🌱 CropIQ – AI-Powered Precision Spraying System

<p align="center">
  <img src="images/cropiq-prototype.jpg" alt="CropIQ Prototype" width="700">
</p>

<p align="center">
  <b>AI + IoT based precision agriculture system for crop disease detection and targeted spraying.</b>
</p>

---

## 📌 Overview

**CropIQ** is an AI-powered precision spraying system developed to detect crop diseases from leaf images and deliver targeted pesticide spraying based on the detected disease.

The system combines:

- 📷 ESP32-CAM for image acquisition
- 🤖 Machine Learning for crop disease detection
- ☁️ Cloud-based backend for AI processing
- 💧 Flow-controlled precision spraying
- 📡 IoT-based communication
- 🖥️ Streamlit dashboard for monitoring and control

The objective is to reduce unnecessary pesticide usage, improve disease detection and automate the spraying process.

---

## 🎯 Objectives

- Detect crop diseases using real-time leaf images.
- Generate appropriate spray dosage based on the detected disease.
- Automate pesticide spraying using sensors and actuators.
- Establish wireless communication between the hardware and cloud backend.
- Provide a user-friendly dashboard for monitoring and control.
- Reduce chemical wastage and manual intervention.
- Support sustainable and precision agriculture.

---

## 🏗️ System Architecture

<p align="center">
  <img src="images/block-diagram.png" alt="CropIQ System Block Diagram" width="800">
</p>

### System Flow

```text
              ┌────────────────────┐
              │     ESP32-CAM      │
              │   Image Capture   │
              └─────────┬──────────┘
                        │
                        │ Wi-Fi
                        ▼
              ┌────────────────────┐
              │   FastAPI Backend  │
              │      Render        │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │  EfficientNet-B0   │
              │   ML Prediction    │
              └─────────┬──────────┘
                        │
                 Disease + Dosage
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
     ┌────────────────┐   ┌────────────────┐
     │    Streamlit   │   │    ESP32-CAM   │
     │    Dashboard   │   │  Spray Control │
     └────────────────┘   └───────┬────────┘
                                  │
                                  ▼
                         ┌────────────────┐
                         │ Relay Module   │
                         └───────┬────────┘
                                 │
                                 ▼
                         ┌────────────────┐
                         │    DC Pump     │
                         └───────┬────────┘
                                 │
                                 ▼
                         ┌────────────────┐
                         │  YF-S401 Flow  │
                         │     Sensor     │
                         └───────┬────────┘
                                 │
                                 ▼
                          Precision Spray
