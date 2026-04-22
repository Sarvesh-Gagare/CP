# 🚦 Traffic Violation Explainable System

A **rule-based Explainable AI system** that detects traffic violations using **Prolog logic** and provides **human-readable explanations** through a **Python GUI dashboard**.

---

## 📌 Overview

This project combines **Artificial Intelligence (logic programming)** with a **modern GUI interface** to simulate real-world traffic monitoring systems.

Instead of just detecting violations, the system explains:

> ❓ *Why was this violation detected?*

This makes it an **Explainable AI (XAI)** system — highly useful for domains like:

* Smart traffic systems 🚗
* Law enforcement 🚓
* Autonomous driving 🚘

---

## ✨ Key Features

### 🧠 AI-Based Logic Engine (Prolog)

* Rule-based reasoning using First-Order Logic
* Supports multiple traffic violations
* Efficient inference using tabling

### 📊 Explainable Output

* Generates human-readable explanations
* Shows reasoning behind each violation
* Helps in transparency & debugging

### 🖥️ Interactive GUI (Python + Tkinter)

* Clean dashboard interface
* Input vehicle details manually
* View results instantly

### 🔎 Manual Query Console

* Run custom Prolog queries directly
* Example:

```prolog
check_violation(car_101, red_light).
```

### 📋 Supported Violations

* 🚦 Red Light Violation
* ⚡ Speeding
* 🛣️ Wrong Lane
* ⛑️ No Helmet
* ↩️ Wrong Direction
* 🔄 Illegal U-Turn
* 🪑 No Seatbelt
* 📱 Phone Usage
* 👥 Overloading
* 🚫 No Parking
* 🐢 Speed Breaker Violation

---

## 🏗️ System Architecture

```text
        +----------------------+
        |   Python GUI (UI)    |
        |  Tkinter Dashboard   |
        +----------+-----------+
                   |
                   ▼
        +----------------------+
        |  PySwip Interface    |
        |  (Python ↔ Prolog)   |
        +----------+-----------+
                   |
                   ▼
        +----------------------+
        |  Prolog Engine       |
        |  Rule-based Logic    |
        +----------------------+
```

---

## ⚙️ Tech Stack

| Component     | Technology            |
| ------------- | --------------------- |
| Programming   | Python, Prolog        |
| GUI           | Tkinter               |
| Logic Engine  | SWI-Prolog            |
| Integration   | PySwip                |
| Visualization | Matplotlib (optional) |

---

## 📂 Project Structure

```text
traffic-violation-system/
│
├── traffic_violations.pl      # Prolog rules (AI engine)
├── gui.py                     # Python GUI
├── README.md                  # Documentation
├── requirements.txt           # Dependencies
└── assets/                    # Screenshots (optional)
```

---

## 🚀 How to Run

### 1️⃣ Install Dependencies

```bash
pip install pyswip matplotlib
```

### 2️⃣ Install SWI-Prolog

Download from: https://www.swi-prolog.org/

### 3️⃣ Run the Application

```bash
python gui.py
```

---

## 🧪 Example Usage

### Input:

* Vehicle ID: `car_101`
* Violation: `red_light`

### Output:

```
Result: TRUE

[VIOLATION DETECTED] Vehicle car_101 committed red_light violation because:
traffic light was RED AND vehicle crossed the stop line AND vehicle is NOT an emergency vehicle.
```

---

## 🧠 Key Concepts Used

* First-Order Logic (FOL)
* Rule-Based Systems
* Explainable AI (XAI)
* Knowledge Representation
* Inference Engines
* Human-Computer Interaction (GUI)

---

## 🎯 Applications

* Smart Traffic Monitoring Systems
* AI-based Law Enforcement
* Autonomous Vehicle Decision Systems
* Educational AI Demonstrations

---

## 🔮 Future Enhancements

* 🎥 Live traffic detection using OpenCV
* 🌐 Web-based dashboard (Flask/React)
* 📊 Advanced analytics (charts & trends)
* 🤖 Machine Learning integration

---

## 👨‍💻 Author
Sarvesh Gagare
Chirag Gandhi
Tejas Gandhi
Pragati Gupta

Vishwakarma Institute of Technology (VIT), Pune

---

## 📜 License

This project is for **academic and educational purposes**.

---

## ⭐ Acknowledgment

Built as part of an academic project demonstrating the integration of:

* AI logic systems
* Explainable reasoning
* Interactive user interfaces

---

> 💡 *"Not just detecting violations, but explaining them — that's the power of Explainable AI."*
