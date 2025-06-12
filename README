# 🌱 Smart Irrigation System

This project implements a smart irrigation system powered by a neural network. It integrates environmental sensor data from Raspberry Pi devices with weather forecast data to decide whether watering is needed.

---

## 🚀 Project Overview

The system consists of:
- 🌡️ **Raspberry Pi clients** that collect temperature and humidity readings
- ☁️ **Weather API integration** to get rain probability and sunshine duration
- 🧠 **A neural network** that decides whether to water or not
- 💧 **Watering control** via GPIO (for 1 hour per decision)
- 📡 **MQTT** protocol for communication
- 🧾 **InfluxDB** for data and log storage
- 📊 **Grafana** dashboards for visualization

Each Raspberry Pi may water **up to 3 times per day**, based on neural network predictions and environmental conditions.

---

## 👥 Team Members

| Name                      | Student Number |
|---------------------------|----------------|
| Kleidonaris Dimitrios     | 2850           |
| Kournianos Paraschos      | 3300           |
| Papaefthymiou Panagiotis  | 3429           |

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone http://github.com/dkleidonaris/iot-ece335.git
```

### 2. Configure .env
Both the client/ and server/ folders contain an .env.example file.
Rename each one to .env to set the MQTT broker address, InfluxDB settings, device ID, coordinates, and other necessary parameters.

⚠️ You must configure your .env files correctly for the system to work. These contain private MQTT and InfluxDB connection details.

## ▶️ Running the System

### Raspberry Pi Client:
```bash
cd client
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

### Server (neural network, weather, and decision logic):
```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

## 📊 Monitoring with Grafana
All sensor data, watering decisions, and logs are stored in InfluxDB and visualized through Grafana.

You can monitor:
- Real-time temperature and humidity
- Watering decisions per device
- Weather forecast inputs (rain & sun)
- Device-specific activity using dropdown filters

### 🌐 Grafana URL
Access the Grafana dashboard here: [Grafana Dashboard](https://ece335.odeit.gr/)

### 🔐 Credentials
| Username   | Password |
|------------|----------|
| ece335     | ece335   |





