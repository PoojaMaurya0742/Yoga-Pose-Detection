🧘‍♀️ Yoga Pose Detection

An AI-powered Yoga Pose Detection and Posture Correction system developed as a 2nd-year academic mini project.

The application uses Computer Vision, MediaPipe, OpenCV, and Streamlit to detect yoga poses through a webcam, analyze body posture using joint angles, and provide real-time feedback to help users perform poses correctly.

📌 Project Overview

Yoga Pose Detection is a real-time computer vision application that acts as a virtual yoga assistant.

The system captures the user's pose through a webcam and uses MediaPipe Pose Estimation to identify body landmarks. These landmarks are then used to calculate joint angles and analyze whether the user is performing a yoga pose correctly.

The application also provides:

🧘 Real-time yoga pose detection
📐 Joint-angle based posture analysis
💬 Real-time posture correction feedback
🔊 English and Hindi voice feedback
🤖 AI chatbot assistance
👤 User authentication
📊 Progress tracking
📸 Pose snapshots
🌐 Streamlit-based interactive interface
✨ Features
🧘 Real-Time Pose Detection

Detects body landmarks from the webcam using MediaPipe Pose.

The system tracks important body points such as:

Shoulders
Elbows
Wrists
Hips
Knees
Ankles
📐 Joint Angle Calculation

The application calculates angles between body joints to evaluate posture.

For example:

Shoulder
    |
    |
   Elbow
     \
      \
      Wrist

The angle between these points can be calculated using their coordinates.

✅ Posture Correction

The system compares detected joint angles with predefined posture conditions and provides feedback such as:

Correct posture
Adjust your knee
Straighten your arm
Raise your hand
Adjust your position
🔊 Bilingual Voice Feedback

The application supports voice feedback in:

English
Hindi

This makes the application more accessible for different users.

🤖 AI Chatbot

An integrated chatbot allows users to ask questions related to:

Yoga
Exercises
Yoga poses
General guidance
👤 User Authentication

The application includes user login/signup functionality for managing individual user sessions and progress.

📊 Progress Tracking

Users can track their yoga practice and pose-related progress.

📸 Pose Snapshots

The application can store snapshots associated with yoga practice and user progress.

🛠️ Tech Stack
Technology	Purpose
Python	Core programming
OpenCV	Webcam and image processing
MediaPipe	Human pose estimation
Streamlit	Web application interface
NumPy	Numerical operations
SQLite	Local data management
Supabase	Cloud authentication/data functionality
AI/LLM	Chatbot functionality
🧠 How It Works

The overall workflow is:

        Webcam
           ↓
    Video Frame Capture
           ↓
        OpenCV
           ↓
   MediaPipe Pose Detection
           ↓
     Body Landmarks
           ↓
    Joint Angle Calculation
           ↓
      Pose Analysis
           ↓
 ┌─────────┴─────────┐
 ↓                   ↓
Correct          Incorrect
Posture           Posture
 ↓                   ↓
Positive        Correction
Feedback         Feedback
🔬 Pose Detection Pipeline
Step 1 — Capture Video

The webcam continuously captures frames from the user.

Step 2 — Process Frame

OpenCV processes the captured image frame.

Step 3 — Detect Landmarks

MediaPipe identifies human body landmarks.

For example:

        Head
         ●
         |
    ●────●────●
 Shoulder  Shoulder
         |
        ●
        Hip
       /  \
      ●    ●
    Knee  Knee
Step 4 — Calculate Angles

The coordinates of three landmarks are used to calculate joint angles.

For example:

A -------- B
            \
             \
              C

The angle at B is calculated using the coordinates of A, B, and C.

Step 5 — Analyze Pose

The calculated angles are compared with predefined conditions for the selected yoga pose.

Step 6 — Provide Feedback

The system provides visual and voice feedback based on the detected posture.

🧘 Supported Yoga Poses

The application contains multiple yoga poses, including examples such as:

Tadasana
Tree Pose
Warrior Pose
Chair Pose
Downward Dog
Cobra Pose
Plank
Trikonasana

The exact supported poses depend on the pose configurations implemented in the application.

📂 Project Structure
Yoga-Pose-Detection/
│
├── yoga_pose_updated.py
│
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
⚙️ Installation
1. Clone the Repository
git clone https://github.com/PoojaMaurya0742/Yoga-Pose-Detection.git

Move into the project directory:

cd Yoga-Pose-Detection
2. Create a Virtual Environment
python -m venv venv

Activate it on Windows:

venv\Scripts\activate
3. Install Dependencies
pip install -r requirements.txt
MediaPipe Compatibility

This project uses the MediaPipe API containing:

mp.solutions.pose

Therefore, use:

pip install mediapipe==0.10.21

If another MediaPipe version causes:

AttributeError: module 'mediapipe' has no attribute 'solutions'

install the compatible version:

pip uninstall mediapipe -y
pip install mediapipe==0.10.21
▶️ Running the Application

Start the Streamlit application:

streamlit run yoga_pose_updated.py

The application will open in your browser at:

http://localhost:8501
💻 System Requirements

Recommended environment:

Python 3.9+
Webcam
Windows/Linux/macOS
Working internet connection for cloud/AI functionality
Modern web browser
🔐 Security

If deploying this application publicly:

Do not commit API keys.
Do not commit passwords.
Do not expose authentication credentials.
Store secrets using environment variables.
Avoid committing databases containing real user information.

Example:

API_KEY=your_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

Add sensitive files to .gitignore.

📚 Concepts Used

This project demonstrates practical implementation of:

Computer Vision
Human Pose Estimation
Machine Learning concepts
Image Processing
Coordinate Geometry
Joint Angle Calculation
Real-Time Video Processing
AI Chatbot Integration
Web Application Development
User Authentication
Database Management
Cloud Integration
🎯 Project Objective

The main objective of this project is to develop an accessible virtual yoga assistant that can:

Detect human body posture.
Identify yoga poses.
Analyze body alignment.
Provide real-time correction.
Give voice-based guidance.
Help users practice yoga using a webcam.
🚀 Future Enhancements

Possible future improvements include:

 More yoga poses
 Improved pose classification
 Personalized workout plans
 Advanced posture scoring
 Rep counting
 Pose-hold timer
 Improved voice interaction
 Mobile application
 Cloud-based user dashboard
 Historical performance analytics
 Improved AI-based posture recommendations
⚠️ Limitations

The accuracy of pose detection can depend on:

Camera quality
Lighting conditions
Camera angle
User distance from camera
Body visibility
Occlusion
Pose complexity

The application is intended for educational and demonstration purposes and should not replace professional medical or fitness advice.

🎓 Academic Project

Project Type: Mini Project
Academic Year: Second Year
Domain: Artificial Intelligence / Computer Vision
Application: Yoga Pose Detection & Posture Correction

This project was developed as part of an academic group project to gain practical experience in Python, Computer Vision, MediaPipe, OpenCV, AI, and Streamlit application development.

👩‍💻 Author

Pooja Maurya

B.E. Information Technology
Shree L. R. Tiwari College of Engineering

GitHub:
https://github.com/PoojaMaurya0742

LinkedIn:
https://www.linkedin.com/in/pooja-maurya-9070b52b8/

📜 Disclaimer

This project is developed for academic and educational purposes. Yoga posture feedback generated by the application should not be considered professional medical or fitness advice.

⭐ Project

If you find this project useful, consider giving the repository a ⭐ on GitHub.
