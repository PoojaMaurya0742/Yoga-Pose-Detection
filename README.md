# 🧘‍♀️ Yoga Pose Detection

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-green?style=for-the-badge&logo=opencv" alt="OpenCV">
  <img src="https://img.shields.io/badge/MediaPipe-Pose%20Estimation-orange?style=for-the-badge" alt="MediaPipe">
  <img src="https://img.shields.io/badge/Streamlit-Web%20App-red?style=for-the-badge&logo=streamlit" alt="Streamlit">
</p>

<p align="center">
  <strong>AI-Powered Real-Time Yoga Pose Detection & Posture Correction</strong>
</p>

<p align="center">
  A Computer Vision based virtual yoga assistant that detects yoga poses through a webcam,
  analyzes body posture using joint angles, and provides real-time corrective feedback.
</p>

---

## 🏆 Achievement

> 🥈 **2nd Prize — ProjecTech 2025**

This project was presented at **ProjecTech 2025** and received **2nd Prize** for its implementation of real-time yoga pose detection and posture analysis using Computer Vision.

---

## 📌 About The Project

**Yoga Pose Detection** is an AI and Computer Vision based application developed as a **2nd-year academic mini project**.

The system uses a webcam to capture the user's movements and applies **MediaPipe Pose Estimation** to detect human body landmarks. These landmarks are analyzed using joint-angle calculations to identify yoga poses and provide posture correction feedback.

The application is designed as a **virtual yoga assistant**, helping users practice yoga while receiving real-time visual and voice-based guidance.

---

## ✨ Key Features

* 🧘 **Real-Time Yoga Pose Detection**
* 📷 **Webcam-Based Pose Estimation**
* 🦴 **Human Body Landmark Detection**
* 📐 **Joint Angle Calculation**
* ✅ **Posture Detection & Correction**
* 🔊 **English & Hindi Voice Feedback**
* 🤖 **AI-Powered Yoga Chatbot**
* 👤 **User Authentication**
* 📊 **Progress Tracking**
* 📸 **Pose Snapshots**
* 🌐 **Interactive Streamlit Web Interface**

---

## 🧠 How It Works

The application follows a computer vision pipeline to detect and analyze yoga poses:

```text
                    ┌──────────────────┐
                    │      Webcam      │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │  Video Capture   │
                    │     OpenCV       │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ MediaPipe Pose   │
                    │    Detection     │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Body Landmarks   │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Joint Angle      │
                    │   Calculation    │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Pose Analysis &  │
                    │ Classification   │
                    └────────┬─────────┘
                             ↓
              ┌──────────────┴──────────────┐
              ↓                             ↓
      ┌───────────────┐             ┌───────────────┐
      │ Correct Pose  │             │ Incorrect Pose│
      └───────┬───────┘             └───────┬───────┘
              ↓                             ↓
      Positive Feedback             Correction Feedback
```

---

## 🔬 Pose Detection

The application uses **MediaPipe Pose** to detect important human body landmarks such as:

* Shoulders
* Elbows
* Wrists
* Hips
* Knees
* Ankles

These landmarks provide the coordinates required for posture analysis.

### Joint Angle Calculation

The angle between three body landmarks can be calculated using their coordinates.

For example:

```text
        A
         \
          \
           B -------- C
```

The angle at point `B` can be calculated using the coordinates of `A`, `B`, and `C`.

These calculated angles are then used to determine whether the user's posture matches the expected posture for a particular yoga pose.

---

## 🧘 Supported Yoga Poses

The project contains reference images and configurations for multiple yoga poses, including:

* Tadasana
* Vrikshasana
* Trikonasana
* Virabhadrasana
* Bhujangasana
* Dhanurasana
* Dandasana
* Padmasana
* Paschimottanasana
* Malasana
* Bakasana
* Chaturanga Dandasana
* Phalakasana (Plank)
* Shavasana
* Setu Bandhasana
* Natarajasana
* Gomukhasana
* Janu Shirshasana
* Pavanamuktasana
* Vasisthasana
* Ashwa Sanchalanasana
* Adho Mukha Svanasana
* and other yoga poses

---

## 🔊 Voice Feedback

The application provides real-time voice feedback to guide the user during practice.

Feedback can be provided in:

* 🇬🇧 English
* 🇮🇳 Hindi

This allows the user to focus on their posture without continuously looking at the screen.

---

## 🤖 AI Yoga Chatbot

The application also includes an AI-based chatbot that can assist users with yoga-related queries.

Users can interact with the chatbot to ask questions related to:

* Yoga poses
* Exercise guidance
* Yoga practice
* General yoga-related information

---

## 👤 User Authentication & Progress

The application includes user-related functionality for managing individual practice sessions.

Features include:

* User registration/login
* User-specific sessions
* Progress tracking
* Pose snapshots
* Practice history

---

## 🛠️ Tech Stack

| Technology    | Purpose                                       |
| ------------- | --------------------------------------------- |
| **Python**    | Core application development                  |
| **OpenCV**    | Real-time webcam and image processing         |
| **MediaPipe** | Human pose and landmark detection             |
| **Streamlit** | Interactive web application                   |
| **NumPy**     | Numerical and mathematical operations         |
| **SQLite**    | Local user/data storage                       |
| **Supabase**  | Cloud-based authentication/data functionality |
| **AI / LLM**  | Yoga chatbot functionality                    |

---

## 📂 Project Structure

```text
Yoga-Pose-Detection/
│
├── yoga_pose_updated.py
├── requirements.txt
│
├── patch.py
├── temp_voice_worker.py
│
├── matches.txt
├── voices.txt
├── streamlit_version.txt
│
├── users.db
│
├── *.jpg
│
├── .gitignore
│
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/PoojaMaurya0742/Yoga-Pose-Detection.git
```

### 2. Navigate to the Project

```bash
cd Yoga-Pose-Detection
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Install Compatible MediaPipe Version

This project uses the `mp.solutions` API of MediaPipe.

Install the compatible version:

```bash
pip uninstall mediapipe -y
pip install mediapipe==0.10.21
```

---

## ▶️ Run the Application

Start the Streamlit application:

```bash
streamlit run yoga_pose_updated.py
```

The application will be available at:

```text
http://localhost:8501
```

---

## 💻 Requirements

### Software

* Python 3.9 or higher
* Git
* Modern web browser

### Hardware

* Webcam
* Laptop/Desktop capable of running Python and OpenCV

### Recommended

* Good lighting
* Stable camera position
* Full or upper-body visibility depending on the selected pose

---

## 🎯 Project Objectives

The major objectives of this project are:

1. Detect human body posture using Computer Vision.
2. Identify yoga poses in real time.
3. Calculate body joint angles.
4. Analyze posture against predefined conditions.
5. Provide real-time corrective feedback.
6. Provide voice-based yoga guidance.
7. Build an interactive AI-assisted yoga application.

---

## 🧩 Core Concepts Used

This project demonstrates practical implementation of:

* Computer Vision
* Human Pose Estimation
* Image Processing
* Real-Time Video Processing
* Coordinate Geometry
* Joint Angle Calculation
* Pose Classification
* Artificial Intelligence
* AI Chatbot Integration
* Web Application Development
* User Authentication
* Database Management

---

## 🚀 Future Enhancements

* [ ] Add more yoga poses
* [ ] Improve pose classification accuracy
* [ ] Add automatic repetition counting
* [ ] Add pose-hold timer
* [ ] Add personalized workout plans
* [ ] Add advanced posture scoring
* [ ] Add detailed progress analytics
* [ ] Improve voice interaction
* [ ] Build a mobile application
* [ ] Add cloud-based user dashboards
* [ ] Improve AI-based personalized recommendations

---

## ⚠️ Limitations

Pose detection performance may vary depending on:

* Camera quality
* Lighting conditions
* Camera angle
* User distance from the camera
* Body visibility
* Background conditions
* Pose complexity

The system is developed primarily for **academic, educational, and demonstration purposes**.

---

## 🎓 Academic Project

**Project Type:** Mini Project
**Year:** Second Year
**Domain:** Artificial Intelligence & Computer Vision
**Event:** ProjecTech 2025
**Achievement:** 🥈 **2nd Prize**

This project was developed as a **group academic mini project** to apply concepts of Python, Computer Vision, Artificial Intelligence, MediaPipe, OpenCV, and web application development in a practical system.

---

## 👩‍💻 Team Project

This project was developed as a **group project** during the second year of the B.E. Information Technology program.

The project involved collaborative work across development, Computer Vision, pose detection, testing, and application implementation.

---

## 👩‍💻 Author

### Pooja Maurya

**B.E. Information Technology**
Shree L. R. Tiwari College of Engineering

* GitHub: [PoojaMaurya0742](https://github.com/PoojaMaurya0742)
* LinkedIn: [Pooja Maurya](https://www.linkedin.com/in/pooja-maurya-9070b52b8/)

---

## 📜 Disclaimer

This project is intended for **educational and demonstration purposes**. The posture feedback provided by the application should not be considered a substitute for professional medical, physiotherapy, or fitness advice.

---

## ⭐ Support

If you find this project interesting, consider giving the repository a ⭐ on GitHub.

---

<p align="center">
  Made with Python, OpenCV, MediaPipe & Streamlit
</p>
