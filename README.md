# Smart Classroom Attendance System

> Multi-Angle Face Recognition with Super-Resolution for Automated Classroom Attendance

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0+-black?style=for-the-badge&logo=flask)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?style=for-the-badge&logo=sqlite)
![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)


---

## About the Project

The **Smart Classroom Attendance System** is an AI-powered solution that automates student attendance using **multi-angle face recognition** combined with **super-resolution enhancement**. The system captures faces from multiple camera angles, enhances low-quality images using super-resolution techniques, and accurately marks attendance in real time — eliminating the need for manual roll calls.

---

## Features

- **Multi-Angle Face Detection** using MTCNN
- **Face Recognition** using dlib with 128-d face encodings
- **Super-Resolution Enhancement** for low-quality or distant face images
- **Web-based Dashboard** built with Flask
- **SQLite Database** for storing student records and attendance logs
- **Automated Attendance Marking** with timestamp
- **False Match Prevention** using tolerance threshold and ambiguity margin checks
- **Attendance Reports** viewable through the web interface

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.8+ |
| Web Framework | Flask |
| Face Detection | MTCNN |
| Face Recognition | dlib, face_recognition |
| Image Processing | OpenCV |
| Super Resolution | OpenCV DNN / ESPCN |
| Database | SQLite3 |
| Frontend | HTML, CSS, JavaScript |

---

## Project Structure

```
smart-classroom-attendance/
│
├── attendance system/       # Core attendance system module
├── data/                    # Student face data and encodings
├── scripts/                 # Utility and helper scripts
├── src/                     # Source code modules
│
├── face_attendance_system.py  # Main application entry point
├── requirements.txt           # Python dependencies
├── output_log.txt             # System output logs
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/niteshmishra-07/smart-classroom-attendance.git
cd smart-classroom-attendance
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python face_attendance_system.py
```

### 5. Open in browser
```
http://localhost:5000
```

---

## How It Works

1. **Student Registration** — Upload multiple face photos from different angles
2. **Face Encoding** — System generates 128-dimensional face encodings using dlib
3. **Super Resolution** — Low-quality images are enhanced before encoding
4. **Live Recognition** — Camera feed is processed in real time
5. **Attendance Marking** — Matched faces are marked present with timestamp in SQLite DB
6. **Dashboard** — View and export attendance records via web interface

---

## Team

| Name |
|------|
| Nitesh Mishra |
| Arnav Mhetre |

---

## Institution

**Vishwakarma Institute of Technology (VIT), Pune**
Academic Year: 2025–26

---

## Patent

A **Provisional Patent** has been filed for this system covering the multi-angle face fusion and super-resolution attendance methodology.

---

## Contact

**Nitesh Mishra**
GitHub: [@niteshmishra-07](https://github.com/niteshmishra-07)
Institution: VIT Pune,