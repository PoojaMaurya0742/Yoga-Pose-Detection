import os
import time
import threading
import sqlite3
from dataclasses import dataclass
from typing import List, Dict, Tuple

import cv2
import mediapipe as mp
import numpy as np
import streamlit as st
from PIL import Image

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="Yoga Pose Detection Pro",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------
# DATABASE
# ---------------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL
)
""")
conn.commit()

cur.execute("""
CREATE TABLE IF NOT EXISTS pose_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    pose_name TEXT NOT NULL,
    accuracy REAL NOT NULL,
    grade TEXT NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

cur.execute("""
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def save_chat_message(email: str, role: str, content: str):
    cur.execute("INSERT INTO chat_messages (user_email, role, content) VALUES (?, ?, ?)", (email, role, content))
    conn.commit()

def get_chat_history(email: str, limit: int = 20):
    cur.execute("SELECT role, content FROM chat_messages WHERE user_email = ? ORDER BY created_at DESC LIMIT ?", (email, limit))
    rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


# ---------------------------------
# SESSION DEFAULTS
# ---------------------------------
defaults = {
    "logged_in": False,
    "current_user": "",
    "latest_confidence": 0.0,
    "latest_feedback": "Waiting for pose...",
    "latest_grade": "Not Ready",
    "saved_snapshots": [],
    "selected_pose_name": "Warrior II",
    "capture_interval": 10,
    "total_shots": 3,
    "snapshot_count": 0,
    "capturing_now": False,
    "login_error": "",
    "register_error": "",
    "register_success": "",
    "voice_language": "English",
    "chat_history": [],
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
# ---------------------------------
# GLOBAL CSS
# ---------------------------------
st.markdown("""
<style>
div[data-baseweb="select"],
div[data-baseweb="select"] * {
    cursor: pointer !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

header[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(139, 92, 246, 0.28), transparent 28%),
        radial-gradient(circle at bottom right, rgba(6, 182, 212, 0.22), transparent 24%),
        linear-gradient(135deg, #0f172a, #111827) !important;
}

[data-testid="stToolbar"] {
    right: 1rem !important;
    top: 0.5rem !important;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(139, 92, 246, 0.28), transparent 28%),
        radial-gradient(circle at bottom right, rgba(6, 182, 212, 0.22), transparent 24%),
        linear-gradient(135deg, #0f172a, #111827);
    color: #ffffff;
}

.main {
    background: transparent !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

p, li, label, span, div {
    color: inherit;
}

.stMarkdown p, .stMarkdown li {
    color: #e5e7eb !important;
}

div.stButton > button {
    width: 100%;
    border-radius: 16px;
    border: none;
    padding: 12px 16px;
    font-weight: 700;
    color: white !important;
    background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    box-shadow: 0 14px 28px rgba(104, 92, 246, 0.32);
    cursor: pointer;
}

div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 18px 30px rgba(104, 92, 246, 0.38);
}

.stSidebar {
    background: rgba(255,255,255,0.04) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] > div {
    background:
        linear-gradient(180deg, rgba(139,92,246,0.12), rgba(6,182,212,0.04)),
        rgba(15, 23, 42, 0.92);
}

section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p {
    color: #ffffff !important;
}

div[data-baseweb="select"] > div,
.stTextInput > div > div > input,
.stNumberInput input {
    background: rgba(255,255,255,0.95) !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
}

.stTextInput input {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
}

.stTextInput input::placeholder {
    color: #64748b !important;
    -webkit-text-fill-color: #64748b !important;
}

.stTextInput label,
.stTextInput p,
label {
    color: #e5e7eb !important;
}

.stSlider > div[data-baseweb="slider"] {
    color: #8b5cf6 !important;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #8b5cf6, #06b6d4) !important;
}

img {
    border-radius: 18px !important;
    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: 0 12px 28px rgba(0,0,0,0.22);
}

.title-box {
    padding: 20px 24px;
    border-radius: 24px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    box-shadow: 0 25px 50px rgba(0,0,0,0.35);
    backdrop-filter: blur(18px);
    margin-bottom: 18px;
}

.metric-box {
    background: rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 12px 28px rgba(0,0,0,0.24);
    border: 1px solid rgba(255,255,255,0.12);
    color: white;
    backdrop-filter: blur(16px);
    min-height: 138px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.small-card {
    background: rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    border: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 12px;
    color: #f8fafc;
}

.soft-info {
    background: rgba(30, 58, 95, 0.55);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 16px 18px;
    color: #f8fafc !important;
    margin-bottom: 14px;
    box-shadow: 0 12px 26px rgba(0,0,0,0.18);
}

.soft-success {
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.30);
    border-radius: 18px;
    padding: 16px 18px;
    color: #ecfdf5 !important;
    margin-bottom: 14px;
}

.soft-warning {
    background: rgba(245, 158, 11, 0.14);
    border: 1px solid rgba(245, 158, 11, 0.30);
    border-radius: 18px;
    padding: 16px 18px;
    color: #fffbeb !important;
    margin-bottom: 14px;
}

.soft-danger {
    background: rgba(239, 68, 68, 0.14);
    border: 1px solid rgba(239, 68, 68, 0.30);
    border-radius: 18px;
    padding: 16px 18px;
    color: #fef2f2 !important;
    margin-bottom: 14px;
}

.badge {
    display: inline-block;
    background: rgba(255,255,255,0.08);
    color: #e9d5ff;
    border: 1px solid rgba(139, 92, 246, 0.32);
    padding: 7px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    margin-right: 8px;
    margin-bottom: 8px;
    box-shadow: 0 8px 18px rgba(139, 92, 246, 0.15);
}

.section-title {
    font-size: 30px;
    font-weight: 800;
    margin-bottom: 6px;
    color: #ffffff;
}

.muted {
    color: #cbd5e1;
    font-size: 15px;
}

.footer-note {
    text-align: center;
    color: #cbd5e1;
    margin-top: 22px;
    font-size: 14px;
}

.spacer-12 { height: 12px; }
.spacer-18 { height: 18px; }

.login-shell {
    width: 100%;
    max-width: 1180px;
    display: grid;
    grid-template-columns: 1.02fr 0.98fr;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 28px;
    overflow: hidden;
    box-shadow: 0 25px 50px rgba(0,0,0,0.35);
    backdrop-filter: blur(20px);
}

.login-left {
    padding: 34px 34px 30px;
    background: linear-gradient(160deg, rgba(139,92,246,0.18), rgba(6,182,212,0.08));
}

.login-right {
    padding: 34px 34px 30px;
    background: rgba(8, 15, 33, 0.80);
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 22px;
    color: #ffffff;
}

.brand-badge {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    box-shadow: 0 10px 25px rgba(139, 92, 246, 0.35);
}

.yoga-visual {
    position: relative;
    width: 100%;
    max-width: 100%;
    margin-bottom: 28px;
}

.hero-yoga-img {
    width: 100%;
    height: 420px;
    object-fit: cover;
    border-radius: 28px;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
}

.floating-card {
    position: absolute;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 14px 20px;
    border-radius: 20px;
    background: rgba(15, 23, 42, 0.82);
    color: #f8fafc;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 16px 40px rgba(0,0,0,0.3);
    backdrop-filter: blur(16px);
    font-size: 15px;
    font-weight: 600;
}

.card-1 { top: 16px; left: 22px; }
.card-2 { right: 20px; bottom: 20px; }

.hero-small {
    color: #d8dfff;
    font-size: 16px;
    margin-top: 16px;
    margin-bottom: 14px;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    font-weight: 600;
}

.hero-title {
    font-size: 62px;
    line-height: 1.05;
    font-weight: 900;
    margin-bottom: 18px;
    color: #ffffff;
    letter-spacing: -1px;
}

.hero-desc {
    color: #cbd5e1;
    font-size: 18px;
    line-height: 1.7;
    max-width: 100%;
    margin-bottom: 28px;
    font-weight: 500;
}

.feature-item {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 18px;
    padding: 16px;
    min-height: 118px;
}

.feature-item strong {
    display: block;
    margin-bottom: 8px;
    font-size: 14px;
    color: #ffffff;
}

.feature-item span {
    color: #cbd5e1;
    font-size: 12px;
    line-height: 1.7;
}

.login-chip {
    display: inline-block;
    font-size: 12px;
    color: #dbeafe;
    padding: 8px 12px;
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    margin-bottom: 18px;
}

.login-heading {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 10px;
    color: #ffffff;
}

.login-sub {
    color: #cbd5e1;
    font-size: 15px;
    margin-bottom: 24px;
}

.row-between {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #dbeafe;
    font-size: 14px;
    margin-top: 6px;
    margin-bottom: 10px;
}

.fake-link {
    color: #c4b5fd;
    text-decoration: none;
    font-weight: 600;
}

.divider {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 16px 0 14px;
    color: #cbd5e1;
    font-size: 14px;
}

.divider::before,
.divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.12);
}

.login-help {
    color: #cbd5e1;
    font-size: 13px;
    text-align: center;
    margin-top: 14px;
}

.login-help span {
    color: #c4b5fd;
    font-weight: 700;
}

.feedback-glass {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 22px;
    padding: 18px;
    box-shadow: 0 18px 40px rgba(0,0,0,0.22);
}

.feedback-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 16px;
}

.feedback-mini {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 14px;
    text-align: center;
}

.feedback-mini h4 {
    margin: 0 0 6px 0;
    font-size: 14px;
    color: #cbd5e1 !important;
}

.feedback-mini p {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: #ffffff !important;
}

[data-testid="stTabs"] {
    gap: 0 !important;
    background: rgba(255,255,255,0.04) !important;
    border-radius: 20px !important;
    padding: 8px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    backdrop-filter: blur(12px) !important;
}

[data-testid="stTabs"] > div:first-child {
    gap: 4px !important;
}

button[data-testid="stTab"] {
    padding: 14px 28px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    background: transparent !important;
    color: #cbd5e1 !important;
    border: none !important;
    border-radius: 14px !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
    letter-spacing: 0.5px !important;
    text-transform: capitalize !important;
}

button[data-testid="stTab"]::before {
    content: "" !important;
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(6, 182, 212, 0.15)) !important;
    border-radius: 14px !important;
    opacity: 0 !important;
    transition: opacity 0.35s ease !important;
    z-index: -1 !important;
}

button[data-testid="stTab"]:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #e0e7ff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.15) !important;
}

button[data-testid="stTab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(6, 182, 212, 0.15)) !important;
    color: #c4b5fd !important;
    box-shadow: 0 8px 24px rgba(139, 92, 246, 0.25), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
}

@media (max-width: 960px) {
    .login-shell {
        grid-template-columns: 1fr;
    }
    .hero-title {
        font-size: 38px;
    }
    .login-heading {
        font-size: 34px;
    }
    .feedback-row {
        grid-template-columns: 1fr;
    }
}

/* Fix for Expander white strip issue */
div[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

div[data-testid="stExpander"] summary {
    background: transparent !important;
    color: #ffffff !important;
}

div[data-testid="stExpander"] summary:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
}

div[data-testid="stExpander"] summary p {
    color: #ffffff !important;
    font-weight: 600 !important;
}

div[data-testid="stExpanderDetails"] {
    color: #e5e7eb !important;
}
</style>
""", unsafe_allow_html=True)
# ---------------------------------
# VOICE
# ---------------------------------
import threading

def get_voice_id(engine, language: str = "English"):
    try:
        voices = engine.getProperty("voices")
    except Exception:
        return None

    if not voices:
        return None

    if language == "Hindi":
        for voice in voices:
            meta = f"{voice.id} {voice.name}".lower()
            if "hindi" in meta or "india" in meta or "hi-in" in meta:
                return voice.id

    for voice in voices:
        meta = f"{voice.id} {voice.name}".lower()
        if "zira" in meta or "female" in meta or "hazel" in meta or "susan" in meta:
            return voice.id

    return voices[0].id

def build_voice_text(pose_name: str, language: str) -> str:
    english_data = {
        "Warrior II": [
            "You selected Warrior Two pose.",
            "Step 1. Stand in a wide stance and stretch both legs.",
            "Step 2. Turn one foot outward and keep the back foot slightly inward.",
            "Step 3. Bend the front knee until it aligns above the ankle.",
            "Step 4. Stretch both arms parallel to the floor.",
            "Step 5. Keep the chest open and look over the front hand."
        ],
        "Tree Pose": [
            "You selected Tree Pose.",
            "Step 1. Stand straight and shift weight onto one leg.",
            "Step 2. Lift the other foot and place it on inner calf or thigh.",
            "Step 3. Join palms near the chest or raise hands upward.",
            "Step 4. Keep your standing leg straight and steady.",
            "Step 5. Focus on one point in front to balance."
        ],
        "Butterfly Pose": [
            "You selected Butterfly Pose.",
            "Step 1. Sit down with your back straight.",
            "Step 2. Bring the soles of your feet together.",
            "Step 3. Hold your feet with both hands.",
            "Step 4. Let the knees relax toward the floor.",
            "Step 5. Keep breathing and stay upright."
        ],
        "Cobra Pose": [
            "You selected Cobra Pose.",
            "Step 1. Lie flat on your stomach.",
            "Step 2. Place palms beside the shoulders.",
            "Step 3. Press lightly through the palms.",
            "Step 4. Lift your chest slowly upward.",
            "Step 5. Keep shoulders relaxed and look forward."
        ],
        "Mountain Pose": [
            "You selected Mountain Pose.",
            "Step 1. Stand straight with feet together or slightly apart.",
            "Step 2. Keep arms relaxed by your sides.",
            "Step 3. Lengthen your spine and lift your chest gently.",
            "Step 4. Relax shoulders and keep chin level.",
            "Step 5. Look straight ahead and breathe calmly."
        ],
        "Padmasana": [
            "You selected Padmasana.",
            "Step 1. Sit on the floor with legs stretched out.",
            "Step 2. Bend the right knee and place the foot on left thigh.",
            "Step 3. Bend the left knee and place the foot on right thigh.",
            "Step 4. Keep your spine upright and place hands on knees.",
            "Step 5. Close your eyes and breathe deeply."
        ],
        "Swastikasana": [
            "You selected Swastikasana.",
            "Step 1. Sit on the floor with legs extended.",
            "Step 2. Bend the left leg and place the foot near right inner thigh.",
            "Step 3. Bend the right leg and lock the foot between left thigh and calf.",
            "Step 4. Keep the spine erect and open your chest.",
            "Step 5. Place hands on knees and focus."
        ],
        "Vajrasana": [
            "You selected Vajrasana.",
            "Step 1. Kneel down on the floor with knees close together.",
            "Step 2. Lower your hips so you are sitting on your heels.",
            "Step 3. Keep the big toes touching and heels slightly apart.",
            "Step 4. Place hands on your knees, palms facing down.",
            "Step 5. Keep your spine upright and look straight ahead."
        ],
        "Gomukhasana": [
            "You selected Gomukhasana.",
            "Step 1. Sit and stack your right knee over the left knee.",
            "Step 2. Bring left arm behind your back and up.",
            "Step 3. Raise right arm, bend elbow, and clasp hands behind your back.",
            "Step 4. Keep the chest open and look straight ahead.",
            "Step 5. Stay erect and breathe calmly."
        ],
        "Ardha Matsyendrasana": [
            "You selected Half Fish Pose.",
            "Step 1. Sit with legs straight. Place right foot outside left knee.",
            "Step 2. Bend left leg and tuck foot close to right hip.",
            "Step 3. Bring left arm over right knee to press against it.",
            "Step 4. Twist torso to the right and support with right hand.",
            "Step 5. Look over your right shoulder."
        ],
        "Janu Shirshasana": [
            "You selected Head to Knee pose.",
            "Step 1. Sit with legs straight in front.",
            "Step 2. Bend left knee, place sole against right inner thigh.",
            "Step 3. Inhale and raise both arms up to stretch spine.",
            "Step 4. Exhale and fold forward over the right leg.",
            "Step 5. Hold foot with hands and touch head to knee."
        ],
        "Paschimottanasana": [
            "You selected Seated Forward Bend.",
            "Step 1. Sit with legs straight in front, feet touching.",
            "Step 2. Stretch your arms up toward the sky.",
            "Step 3. Fold forward from the hips, keeping spine long.",
            "Step 4. Hold your feet with hands.",
            "Step 5. Lower your forehead toward your shins."
        ],
        "Tadasana": [
            "You selected Tadasana.",
            "Step 1. Stand straight with feet together.",
            "Step 2. Distribute weight evenly on both feet.",
            "Step 3. Align pelvis and lift your chest.",
            "Step 4. Relax shoulders and extend arms down.",
            "Step 5. Look forward and breathe calmly."
        ],
        "Trikonasana": [
            "You selected Trikonasana.",
            "Step 1. Stand in a wide stance, turn one foot outward.",
            "Step 2. Extend both arms parallel to the floor.",
            "Step 3. Fold sideways over your front leg.",
            "Step 4. Touch your ankle or shin with the lower hand.",
            "Step 5. Stretch upper arm towards the ceiling and look up."
        ],
        "Utkatasana": [
            "You selected Chair Pose.",
            "Step 1. Stand straight and raise arms above the head.",
            "Step 2. Bend knees and lower hips like sitting on a chair.",
            "Step 3. Keep thighs parallel to the floor.",
            "Step 4. Keep chest lifted and spine long.",
            "Step 5. Look forward and balance."
        ],
        "Virabhadrasana I": [
            "You selected Warrior One pose.",
            "Step 1. Step one foot back and square hips forward.",
            "Step 2. Bend your front knee over the ankle.",
            "Step 3. Stretch both arms up to the ceiling.",
            "Step 4. Keep back leg active and heel down.",
            "Step 5. Look up and breathe."
        ],
        "Virabhadrasana II": [
            "You selected Warrior Two pose.",
            "Step 1. Stand in a wide stance and stretch both legs.",
            "Step 2. Turn one foot outward and bend the knee.",
            "Step 3. Stretch arms wide parallel to the floor.",
            "Step 4. Keep your chest open.",
            "Step 5. Look over the front hand."
        ],
        "Vrikshasana": [
            "You selected Tree Pose.",
            "Step 1. Stand straight and shift weight onto one leg.",
            "Step 2. Lift the other foot onto inner calf or thigh.",
            "Step 3. Join palms near chest or raise hands up.",
            "Step 4. Keep standing leg stable.",
            "Step 5. Focus on a point in front to balance."
        ],
        "Malasana": [
            "You selected Garland Pose.",
            "Step 1. Stand with feet slightly wider than hips.",
            "Step 2. Bend knees and lower hips into a deep squat.",
            "Step 3. Press elbows against inner knees.",
            "Step 4. Bring palms together in namaste at your chest.",
            "Step 5. Keep spine erect and lift your chest."
        ],
        "Natarajasana": [
            "You selected Dancer Pose.",
            "Step 1. Stand straight on one leg.",
            "Step 2. Bend back leg and hold foot with hand.",
            "Step 3. Raise other arm straight up.",
            "Step 4. Kick foot back and lean slightly forward.",
            "Step 5. Look forward and hold balance."
        ]
    }

    hindi_data = {
        "Warrior II": [
            "Aapne Warrior Two pose select kiya hai.",
            "Step 1. Pairon ko door rakh kar seedhe khade ho jaiye.",
            "Step 2. Ek pair ko bahar ki taraf ghumaiye aur dusre pair ko halka andar rakhiye.",
            "Step 3. Aage wale ghutne ko modiye jab tak woh ankle ke upar aaye.",
            "Step 4. Dono haathon ko side mein failaiye.",
            "Step 5. Chest open rakhiye aur aage wale haath ki taraf dekhiye."
        ],
        "Tree Pose": [
            "Aapne Tree Pose select kiya hai.",
            "Step 1. Seedhe khade ho jaiye aur body ka weight ek pair par lijiye.",
            "Step 2. Dusre pair ko utha kar calf ya thigh par rakhiye.",
            "Step 3. Haathon ko namaste mein rakhiye ya upar uthaiye.",
            "Step 4. Standing leg ko stable rakhiye.",
            "Step 5. Balance ke liye saamne ek point par focus kijiye."
        ],
        "Butterfly Pose": [
            "Aapne Butterfly Pose select kiya hai.",
            "Step 1. Seedhe baith jaiye aur back ko straight rakhiye.",
            "Step 2. Dono pairon ke talwe aapas mein milaiye.",
            "Step 3. Dono haathon se pair pakdiye.",
            "Step 4. Ghutnon ko dheere se neeche relax hone dijiye.",
            "Step 5. Saans lete rahiye aur body ko upright rakhiye."
        ],
        "Cobra Pose": [
            "Aapne Cobra Pose select kiya hai.",
            "Step 1. Pet ke bal seedha let jaiye.",
            "Step 2. Haath kandhon ke paas rakhiye.",
            "Step 3. Palms se halka pressure dijiye.",
            "Step 4. Chest ko dheere dheere upar uthaiye.",
            "Step 5. Shoulders ko relax rakhiye aur saamne dekhiye."
        ],
        "Mountain Pose": [
            "Aapne Mountain Pose select kiya hai.",
            "Step 1. Seedhe khade ho jaiye, pair saath ya halka gap mein rakhiye.",
            "Step 2. Haath side mein relax rakhiye.",
            "Step 3. Spine ko lamba rakhiye aur chest ko halka upar uthaiye.",
            "Step 4. Shoulders relax rakhiye aur chin seedhi rakhiye.",
            "Step 5. Saamne dekhiye aur aaram se saans lijiye."
        ],
        "Padmasana": [
            "Aapne Padmasana select kiya hai.",
            "Step 1. Seedhe baithiye aur pair failaiye.",
            "Step 2. Ek pair ko mod kar opposite thigh par rakhiye.",
            "Step 3. Dusre pair ko mod kar dusri thigh par rakhiye.",
            "Step 4. Back ko ekdum straight rakhiye.",
            "Step 5. Aankhein band karke lambi saans lijiye."
        ],
        "Swastikasana": [
            "Aapne Swastikasana select kiya hai.",
            "Step 1. Floor par seedhe baith jaiye.",
            "Step 2. Ek pair ko mod kar opposite thigh ke paas rakhiye.",
            "Step 3. Dusre pair ko lock kijiye.",
            "Step 4. Spine ko bilkul straight rakhiye.",
            "Step 5. Haath ghutnon par rakh kar meditation kijiye."
        ],
        "Vajrasana": [
            "Aapne Vajrasana select kiya hai.",
            "Step 1. Ghutno ke bal khade ho jaiye.",
            "Step 2. Hips ko neeche karke heels par baithiye.",
            "Step 3. Dono pair ke anguthe aapas mein touch karein.",
            "Step 4. Haath ghutnon par rakhein.",
            "Step 5. Spine ko straight rakhiye."
        ],
        "Gomukhasana": [
            "Aapne Gomukhasana select kiya hai.",
            "Step 1. Baith kar dono ghutnon ko ek ke upar ek stack kijiye.",
            "Step 2. Ek haath peeth ke peeche se upar laiye.",
            "Step 3. Dusra haath kandhe ke upar se peeche le jaiye.",
            "Step 4. Dono haath peeth ke peeche clasp kijiye.",
            "Step 5. Chest open rakhiye aur seedha dekhiye."
        ],
        "Ardha Matsyendrasana": [
            "Aapne Half Fish Pose select kiya hai.",
            "Step 1. Dono pair seedhe karke baithiye.",
            "Step 2. Ek pair ko mod kar opposite knee ke bahar rakhiye.",
            "Step 3. Torso ko side mein twist kijiye.",
            "Step 4. Ek haath se knee ko press kijiye.",
            "Step 5. Shoulder ke peeche dekhiye."
        ],
        "Janu Shirshasana": [
            "Aapne Head to Knee pose select kiya hai.",
            "Step 1. Dono pair seedhe karke baithiye.",
            "Step 2. Ek pair ke talwe ko opposite thigh par rakhiye.",
            "Step 3. Dono haath upar karke body stretch kijiye.",
            "Step 4. Hips se aage jhukiye.",
            "Step 5. Foot ko pakdiye aur forehead ko knee par lagane ki koshish kijiye."
        ],
        "Paschimottanasana": [
            "Aapne Seated Forward Bend select kiya hai.",
            "Step 1. Dono pair seedhe aage faila kar baithiye.",
            "Step 2. Haathon ko upar stretch kijiye.",
            "Step 3. Hips se aage jhukiye.",
            "Step 4. Pairon ke anguthe pakdiye.",
            "Step 5. Forehead ko legs par rest kijiye."
        ],
        "Tadasana": [
            "Aapne Tadasana select kiya hai.",
            "Step 1. Seedhe khade ho jaiye, pair aapas mein milaiye.",
            "Step 2. Body ka weight dono pairon par barabar rakhiye.",
            "Step 3. Spine aur neck seedhi rakhiye aur chest ko lift kijiye.",
            "Step 4. Shoulders ko relax rakhiye aur arms ko side mein dheela chodiye.",
            "Step 5. Saamne dekhiye aur shaant saans lijiye."
        ],
        "Trikonasana": [
            "Aapne Trikonasana select kiya hai.",
            "Step 1. Pairon ko door failaiye aur ek foot ko 90 degree ghumaiye.",
            "Step 2. Dono arms ko shoulder level par failaiye.",
            "Step 3. Aage jate hue side mein jhukiye.",
            "Step 4. Neeche wale haath se pair ko chuiye.",
            "Step 5. Upper hand ko aakash ki taraf straight kijiye aur upar dekhiye."
        ],
        "Utkatasana": [
            "Aapne Chair Pose select kiya hai.",
            "Step 1. Seedhe khade hokar dono haathon ko upar uthaiye.",
            "Step 2. Ghutnon ko modte hue hips ko neeche kijiye, jaise chair par baithe hon.",
            "Step 3. Thighs ko floor ke parallel lane ki koshish kijiye.",
            "Step 4. Chest ko lift aur spine ko seedha rakhiye.",
            "Step 5. Saamne dekhiye aur balance banaye rakhein."
        ],
        "Virabhadrasana I": [
            "Aapne Warrior One pose select kiya hai.",
            "Step 1. Ek leg peeche le jaiye aur hips ko square rakhiye.",
            "Step 2. Aage wale knee ko ankle ke upar modiye.",
            "Step 3. Dono haathon ko aakash ki taraf straight uthaiye.",
            "Step 4. Back leg ko active rakhiye.",
            "Step 5. Dheere se upar dekhiye aur lambi saans lijiye."
        ],
        "Virabhadrasana II": [
            "Aapne Warrior Two pose select kiya hai.",
            "Step 1. Dono pair faila kar wide stance lijiye.",
            "Step 2. Ek pair ko side mein ghumaiye aur modiye.",
            "Step 3. Arms ko side mein stretch kijiye.",
            "Step 4. Chest ko open rakhiye.",
            "Step 5. Aage wale haath ki taraf dekhiye."
        ],
        "Vrikshasana": [
            "Aapne Tree Pose select kiya hai.",
            "Step 1. Seedhe khade hokar ek leg par weight lijiye.",
            "Step 2. Dusre foot ko thigh ya calf par rest kijiye.",
            "Step 3. Palms ko chest ke paas namaste mein laiye ya arms upar uthaiye.",
            "Step 4. Standing leg ko bilkul stable rakhiye.",
            "Step 5. Focus banaye rakhne ke liye saamne dekhiye."
        ],
        "Malasana": [
            "Aapne Garland Pose select kiya hai.",
            "Step 1. Feet ko hip-width se wide karke khade ho jaiye.",
            "Step 2. Knees ko bend kijiye aur deep squat posture mein hips neeche laiye.",
            "Step 3. Elbows se knee ko bahar press kijiye.",
            "Step 4. Palms ko chest ke paas namaste mein milaiye.",
            "Step 5. Spine ko straight aur chest ko lift rakhiye."
        ],
        "Natarajasana": [
            "Aapne Dancer Pose select kiya hai.",
            "Step 1. Ek pair par balance banakar seedhe khade ho jaiye.",
            "Step 2. Dusra pair peeche bend kijiye aur foot ko haath se pakdiye.",
            "Step 3. Haath aage failaiye.",
            "Step 4. Foot ko peeche kick kijiye aur torso aage bend kijiye.",
            "Step 5. Saamne dekhiye aur balance banaye rakhein."
        ]
    }

    if language == "Hindi":
        if pose_name in hindi_data:
            return " ".join(hindi_data[pose_name])
        else:
            extra_hindi = {
                "Phalakasana (Plank)": ["Aapne Plank pose select kiya hai.", "Step 1. Push-up position mein aaiye.", "Step 2. Kandho ko kalaiyo ke thik upar rakhiye.", "Step 3. Core ko tight rakhiye.", "Step 4. Body ko ek seedhi line mein rakhiye.", "Step 5. Posture hold kijiye."],
                "Chaturanga Dandasana": ["Aapne Chaturanga select kiya hai.", "Step 1. Plank pose se shuru karein.", "Step 2. Elbows ko 90 degree par modiye.", "Step 3. Body ko floor ke parallel rakhiye.", "Step 4. Core tight rakhiye.", "Step 5. Balance banaye rakhiye."],
                "Bakasana": ["Aapne Crow pose select kiya hai.", "Step 1. Squat position mein aaiye.", "Step 2. Hatho ko zameen par rakhiye.", "Step 3. Ghutno ko armpits ke paas rest karein.", "Step 4. Aage jhukiye aur pairo ko uthaiye.", "Step 5. Balance banaiye."],
                "Adho Mukha Svanasana": ["Aapne Downward Dog select kiya hai.", "Step 1. Hatho aur ghutno ke bal aaiye.", "Step 2. Hips ko upar uthaiye.", "Step 3. Pairo aur hatho ko seedha kijiye.", "Step 4. V-shape banaiye.", "Step 5. Edhiyo ko zameen ki taraf push kijiye."],
                "Vasisthasana": ["Aapne Side Plank select kiya hai.", "Step 1. Plank pose se shuru karein.", "Step 2. Ek hath par weight shift kijiye.", "Step 3. Dusre hath ko upar uthaiye.", "Step 4. Legs ko straight rakhiye.", "Step 5. Upar wale hath ki taraf dekhiye."],
                "Step 1: Pranamasana": ["Surya Namaskar Step 1.", "Namaste mudra mein khade ho jaiye."],
                "Step 2: Hasta Uttanasana": ["Surya Namaskar Step 2.", "Hatho ko upar uthaiye aur peechhe ki taraf jhukiye."],
                "Step 3: Padahastasana": ["Surya Namaskar Step 3.", "Aage jhukiye aur hatho ko zameen par rakhiye."],
                "Step 4: Ashwa Sanchalanasana": ["Surya Namaskar Step 4.", "Ek pair peeche le jaiye aur aage dekhiye."],
                "Step 5: Dandasana": ["Surya Namaskar Step 5.", "Dono pair peeche le jaiye aur push-up position mein aaiye."],
                "Step 6: Ashtanga Namaskara": ["Surya Namaskar Step 6.", "Ghutne, chest aur chin ko zameen par lagaiye."],
                "Step 7: Bhujangasana": ["Surya Namaskar Step 7.", "Chest ko upar uthaiye aur saamne dekhiye."],
                "Step 8: Adho Mukha Svanasana": ["Surya Namaskar Step 8.", "Hips ko upar uthakar V-shape banaiye."],
                "Step 9: Ashwa Sanchalanasana": ["Surya Namaskar Step 9.", "Dusre pair ko aage laiye."],
                "Step 10: Padahastasana": ["Surya Namaskar Step 10.", "Aage jhukiye aur hatho ko zameen par rakhiye."],
                "Step 11: Hasta Uttanasana": ["Surya Namaskar Step 11.", "Hatho ko upar uthaiye aur peechhe ki taraf jhukiye."],
                "Step 12: Pranamasana": ["Surya Namaskar Step 12.", "Wapas namaste mudra mein aaiye aur relax karein."]
            }
            if pose_name in extra_hindi:
                return " ".join(extra_hindi[pose_name])
            
            if pose_name in globals().get("POSES", {}):
                steps = globals()["POSES"][pose_name].steps
                return f"Aapne {pose_name} select kiya hai. " + " ".join(steps)
            return f"Aapne {pose_name} select kiya hai. Kripya screen par diye gaye steps ko dhyan se follow karein."
    else:
        if pose_name in english_data:
            return " ".join(english_data[pose_name])
        else:
            # Global POSES dictionary fallback
            if pose_name in globals().get("POSES", {}):
                steps = globals()["POSES"][pose_name].steps
                return f"You selected {pose_name}. " + " ".join(steps)
            return f"You selected {pose_name}. Please follow the steps on the screen."

def stop_voice():
    import streamlit as st
    if "speech_process" in st.session_state and st.session_state.speech_process is not None:
        try:
            st.session_state.speech_process.terminate()
            st.session_state.speech_process.wait(timeout=1)
        except Exception:
            pass
        st.session_state.speech_process = None

def speak_text(text: str, language: str = "English"):
    speak_async(text, language)

def speak_async(text: str, language: str = "English"):
    import subprocess
    import sys
    import os
    import glob
    import streamlit as st
    
    stop_voice()
    
    try:
        for f in glob.glob("temp_voice_*.mp3"):
            try:
                os.remove(f)
            except:
                pass
    except:
        pass
    
    script_content = """import sys
import os
import uuid

def run_voice():
    try:
        from gtts import gTTS
        import pygame
        import warnings
        warnings.filterwarnings("ignore")
        
        text = sys.argv[1]
        language = sys.argv[2]
        
        lang_code = 'hi' if language == 'Hindi' else 'en'
        tld = 'co.in' if language == 'Hindi' else 'us'
        
        tts = gTTS(text=text, lang=lang_code, tld=tld, slow=False)
        
        unique_id = uuid.uuid4().hex
        audio_file = f"temp_voice_{unique_id}.mp3"
        tts.save(audio_file)
        
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.quit()
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
    except Exception as e:
        pass

if __name__ == '__main__':
    run_voice()
"""
    try:
        with open("temp_voice_worker.py", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        st.session_state.speech_process = subprocess.Popen(
            [sys.executable, "temp_voice_worker.py", text, language]
        )
    except Exception as e:
        print("Speech process error:", e)
    
# ---------------------------------
# POSE DATA
# ---------------------------------
@dataclass
class PoseInfo:
    name: str
    description: str
    image_paths: List[str]
    confidence_threshold: float
    steps: List[str]
    benefits: List[str]
    tips: List[str]

POSES: Dict[str, PoseInfo] = {
    "Warrior II": PoseInfo(
        name="Warrior II",
        description="A strong standing pose where one knee bends, arms stretch wide, and the body stays balanced and open.",
        image_paths=["warrior2.jpg", "warrior2_alt.jpg"],
        confidence_threshold=0.68,
        steps=[
            "Stand in a wide stance and stretch both legs.",
            "Turn one foot outward and keep the back foot slightly inward.",
            "Bend the front knee until it aligns above the ankle.",
            "Stretch both arms parallel to the floor.",
            "Keep the chest open and look over the front hand."
        ],
        benefits=[
            "Strengthens legs and shoulders",
            "Improves stamina and body balance",
            "Opens hips and chest",
            "Builds focus and stability"
        ],
        tips=[
            "Keep your arms straight.",
            "Do not let the front knee go too far ahead.",
            "Maintain a wide stance.",
            "Keep your back leg active."
        ]
    ),
    "Tree Pose": PoseInfo(
        name="Tree Pose",
        description="A balancing pose where you stand on one leg while the other foot rests on the calf or inner thigh.",
        image_paths=["tree.jpg", "tree_alt.jpg"],
        confidence_threshold=0.64,
        steps=[
            "Stand straight and shift weight onto one leg.",
            "Lift the other foot and place it on inner calf or thigh.",
            "Join palms near the chest or raise hands upward.",
            "Keep your standing leg straight and steady.",
            "Focus on one point in front to balance."
        ],
        benefits=[
            "Improves concentration",
            "Builds balance and posture",
            "Strengthens legs and core",
            "Enhances body control"
        ],
        tips=[
            "Fix your gaze on one point.",
            "Keep the standing leg stable.",
            "Do not press the foot on the knee joint.",
            "Engage your core gently."
        ]
    ),
    "Butterfly Pose": PoseInfo(
        name="Butterfly Pose",
        description="A seated pose with feet together and knees moving out to the sides for hip opening.",
        image_paths=["butterfly.jpg", "butterfly_alt.jpg"],
        confidence_threshold=0.58,
        steps=[
            "Sit down with your back straight.",
            "Bring the soles of your feet together.",
            "Hold your feet with both hands.",
            "Let the knees relax toward the floor.",
            "Keep breathing and stay upright."
        ],
        benefits=[
            "Improves hip flexibility",
            "Stretches inner thighs",
            "Relaxes lower body",
            "Helps improve sitting posture"
        ],
        tips=[
            "Sit tall, do not round the back.",
            "Do not force the knees downward.",
            "Keep the feet close but comfortable.",
            "Relax your shoulders."
        ]
    ),
    "Cobra Pose": PoseInfo(
        name="Cobra Pose",
        description="A back-bending pose done lying on the stomach while lifting the chest upward.",
        image_paths=["cobra.jpg", "cobra_alt.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Lie flat on your stomach.",
            "Place palms beside the shoulders.",
            "Press lightly through the palms.",
            "Lift your chest slowly upward.",
            "Keep shoulders relaxed and look forward."
        ],
        benefits=[
            "Strengthens the back",
            "Opens chest and shoulders",
            "Improves spinal flexibility",
            "Helps posture awareness"
        ],
        tips=[
            "Do not over-compress the lower back.",
            "Lift gradually.",
            "Keep elbows soft, not locked.",
            "Relax the neck and shoulders."
        ]
    ),
    "Mountain Pose": PoseInfo(
        name="Mountain Pose",
        description="A simple standing posture where the body stays straight, tall, and balanced.",
        image_paths=["mountain.jpg", "mountain_alt.jpg"],
        confidence_threshold=0.65,
        steps=[
            "Stand straight with feet together or slightly apart.",
            "Keep arms relaxed by your sides.",
            "Lengthen your spine and lift your chest gently.",
            "Relax shoulders and keep chin level.",
            "Look straight ahead and breathe calmly."
        ],
        benefits=[
            "Improves posture",
            "Builds body awareness",
            "Creates alignment and stability",
            "Prepares the body for other poses"
        ],
        tips=[
            "Stand evenly on both feet.",
            "Keep the spine straight.",
            "Relax the jaw and shoulders.",
            "Avoid leaning forward or backward."
        ]
    ),
    "Padmasana": PoseInfo(
        name="Padmasana",
        description="A cross-legged meditation posture that helps calm the mind and prepare for deep meditation.",
        image_paths=["padmasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Sit on the floor with legs stretched out.",
            "Bend the right knee and place the right foot on the left thigh.",
            "Bend the left knee and place the left foot on the right thigh.",
            "Keep your spine upright and place hands on knees in Gyan Mudra.",
            "Close your eyes and breathe deeply."
        ],
        benefits=[
            "Calms the brain and increases awareness",
            "Keeps the spine straight and improves posture",
            "Stretches knees and ankles"
        ],
        tips=[
            "Do not force your feet if your hips are tight.",
            "Keep your spine tall and relaxed.",
            "Avoid if you have knee injuries."
        ]
    ),
    "Swastikasana": PoseInfo(
        name="Swastikasana",
        description="An ancient meditation posture where the legs are crossed in a stable and comfortable position.",
        image_paths=["swastikasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Sit on the floor with legs extended.",
            "Bend the left leg and place the foot near the right thigh groin.",
            "Bend the right leg and push the foot into the space between the left thigh and calf.",
            "Ensure feet are locked comfortably.",
            "Keep spine erect, chest open, and hands on knees."
        ],
        benefits=[
            "Improves concentration and focus",
            "Stretches leg muscles and ankle joints",
            "Quietens the mind"
        ],
        tips=[
            "Keep your weight centered on both sit bones.",
            "Keep your back erect.",
            "Relax the thighs."
        ]
    ),
    "Vajrasana": PoseInfo(
        name="Vajrasana",
        description="A kneeling pose that is excellent for digestion and meditation.",
        image_paths=["vajrasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Kneel down on the floor with knees close together.",
            "Lower your hips so you are sitting on your heels.",
            "Keep your big toes touching and heels slightly apart.",
            "Place hands on your knees, palms facing down.",
            "Keep your spine upright and look straight ahead."
        ],
        benefits=[
            "Improves digestion and relieves gas",
            "Strengthens thigh muscles",
            "Stabilizes the mind for meditation"
        ],
        tips=[
            "Keep knees together.",
            "Keep your weight centered.",
            "Avoid if you have acute knee pain."
        ]
    ),
    "Gomukhasana": PoseInfo(
        name="Gomukhasana",
        description="A seated pose that stretches the shoulders, chest, hips, and thighs.",
        image_paths=["Gomukhasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Sit down, cross your legs so the right knee is stacked directly on top of the left knee.",
            "Bring your left arm behind your back and up.",
            "Raise your right arm, bend the elbow, and reach down to clasp the left hand behind your back.",
            "Keep the chest open and lift your right elbow toward the ceiling.",
            "Stay erect and breathe calmly."
        ],
        benefits=[
            "Opens chest and shoulders, improving breathing",
            "Stretches hips and thighs deeply",
            "Relieves backache and stiffness"
        ],
        tips=[
            "If hands don't touch, use a yoga strap or hold your shirt.",
            "Keep the head upright, do not press it forward with the upper arm."
        ]
    ),
    "Ardha Matsyendrasana": PoseInfo(
        name="Ardha Matsyendrasana",
        description="A seated spinal twist that improves digestion, spine flexibility, and stimulates abdominal organs.",
        image_paths=["Ardha Matsyendrasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Sit with legs straight. Bend the right leg and place the foot outside the left knee.",
            "Bend the left leg and tuck the foot close to the right hip.",
            "Bring the left arm over the right knee to press against it and twist the torso right.",
            "Place the right hand on the floor behind you for support.",
            "Look over your right shoulder."
        ],
        benefits=[
            "Increases spine elasticity and relieves back pain",
            "Improves digestion and detoxifies internal organs",
            "Stretches shoulders and neck"
        ],
        tips=[
            "Keep both sit bones on the floor.",
            "Elongate the spine upwards before twisting."
        ]
    ),
    "Janu Shirshasana": PoseInfo(
        name="Janu Shirshasana",
        description="A seated forward fold where one leg is extended straight and the other knee is bent outward.",
        image_paths=["Janu Shirshasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Sit down with legs extended straight in front.",
            "Bend the left knee, placing the sole of the left foot against the right inner thigh.",
            "Inhale and raise both arms up, lengthening the spine.",
            "Exhale and fold forward from the hips over the right leg.",
            "Hold the right foot with hands and lower the head toward the knee."
        ],
        benefits=[
            "Stretches hamstrings, groin, and spine",
            "Calms the mind and helps relieve anxiety",
            "Stimulates liver and kidneys"
        ],
        tips=[
            "Do not round your upper back; lead with the chest.",
            "Keep the straight leg active with toes pointing up."
        ]
    ),
    "Paschimottanasana": PoseInfo(
        name="Paschimottanasana",
        description="A seated forward fold stretching the back of the entire body, especially the legs and calves.",
        image_paths=["Paschimottanasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Sit with legs straight in front, feet touching.",
            "Inhale and stretch your arms up toward the sky.",
            "Exhale and bend forward from the hips, keeping your spine long.",
            "Hold your shins, ankles, or toes with your hands.",
            "Lower your forehead toward your shins."
        ],
        benefits=[
            "Deep stretch for hamstrings, calves, and lower back",
            "Calms the nervous system and reduces fatigue",
            "Aids digestion and abdominal organ toning"
        ],
        tips=[
            "Keep your knees slightly bent if your hamstrings are tight.",
            "Avoid pulling yourself down forcefully; let gravity work."
        ]
    ),
    "Tadasana": PoseInfo(
        name="Tadasana",
        description="A basic standing posture that forms the foundation of all other standing poses.",
        image_paths=["Tadasana.jpg"],
        confidence_threshold=0.65,
        steps=[
            "Stand straight with feet together.",
            "Distribute weight evenly on both feet.",
            "Align pelvis, draw abdomen in, and lift the chest.",
            "Relax shoulders and hang arms down.",
            "Look forward and breathe calmly."
        ],
        benefits=[
            "Improves posture and body alignment",
            "Strengthens thighs, knees, and ankles",
            "Calms the nervous system"
        ],
        tips=[
            "Keep weight centered.",
            "Stand tall.",
            "Breathe naturally."
        ]
    ),
    "Trikonasana": PoseInfo(
        name="Trikonasana",
        description="A standing posture that stretches and strengthens the entire body, improving flexibility.",
        image_paths=["Trikonasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Stand in a wide stance, turn one foot outward 90 degrees.",
            "Extend both arms parallel to the floor.",
            "Reach sideways and fold from the hip over the front leg.",
            "Bring your lower hand down to your shin, ankle, or floor.",
            "Stretch your upper arm toward the ceiling and look up."
        ],
        benefits=[
            "Stretches spine, hips, hamstrings, and calves",
            "Stimulates abdominal organs and aids digestion",
            "Improves balance and core stability"
        ],
        tips=[
            "Keep both legs straight.",
            "Do not let the torso lean forward; keep the body in one plane."
        ]
    ),
    "Utkatasana": PoseInfo(
        name="Utkatasana",
        description="A powerful standing pose that mimics sitting on an imaginary chair, building lower body strength.",
        image_paths=["Utkatasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Stand straight, then inhale and raise arms above the head.",
            "Exhale and bend knees, lowering hips as if sitting in a chair.",
            "Keep thighs as parallel to the floor as possible.",
            "Keep your chest lifted and spine long.",
            "Look forward or up toward your hands."
        ],
        benefits=[
            "Strengthens thighs, calves, and spine",
            "Stretches shoulders and chest",
            "Stimulates heart and diaphragm"
        ],
        tips=[
            "Keep weight in your heels.",
            "Do not let knees go past your toes."
        ]
    ),
    "Virabhadrasana I": PoseInfo(
        name="Virabhadrasana I",
        description="A powerful standing posture that opens hips and chest while strengthening the legs.",
        image_paths=["Virabhadrasana I.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Step one foot back, turning the heel in 45 degrees.",
            "Bend the front knee until it is above the ankle.",
            "Square your hips toward the front.",
            "Inhale and raise both arms up towards the ceiling.",
            "Lift the chest and gaze gently upward."
        ],
        benefits=[
            "Strengthens shoulders, arms, legs, and back",
            "Opens hips, chest, and lungs",
            "Improves focus and balance"
        ],
        tips=[
            "Keep the back leg straight and active.",
            "Keep the hips squared forward."
        ]
    ),
    "Virabhadrasana II": PoseInfo(
        name="Virabhadrasana II",
        description="A strong standing pose where one knee bends, arms stretch wide, and chest stays open.",
        image_paths=["Virabhadrasana II.jpg"],
        confidence_threshold=0.68,
        steps=[
            "Stand in a wide stance and stretch both legs.",
            "Turn one foot outward and keep the back foot slightly inward.",
            "Bend the front knee until it aligns above the ankle.",
            "Stretch both arms parallel to the floor.",
            "Keep the chest open and look over the front hand."
        ],
        benefits=[
            "Strengthens legs and shoulders",
            "Improves stamina and body balance",
            "Opens hips and chest"
        ],
        tips=[
            "Keep your arms straight and parallel to the floor.",
            "Do not let the front knee go too far ahead."
        ]
    ),
    "Vrikshasana": PoseInfo(
        name="Vrikshasana",
        description="A balancing pose where you stand on one leg while the other foot rests on the calf or thigh.",
        image_paths=["Vrikshasana.jpg"],
        confidence_threshold=0.64,
        steps=[
            "Stand straight and shift weight onto one leg.",
            "Lift the other foot and place it on inner calf or thigh.",
            "Join palms near the chest or raise hands upward.",
            "Keep your standing leg straight and steady.",
            "Focus on one point in front to balance."
        ],
        benefits=[
            "Improves concentration and focus",
            "Builds balance and posture",
            "Strengthens legs and core"
        ],
        tips=[
            "Fix your gaze on one point.",
            "Keep the standing leg stable.",
            "Do not press the foot on the knee joint."
        ]
    ),
    "Malasana": PoseInfo(
        name="Malasana",
        description="A deep squatting pose that stretches the groin, lower back, and hips while strengthening the ankles.",
        image_paths=["Malasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Stand with feet slightly wider than hips.",
            "Bend knees and lower hips down into a deep squat.",
            "Press elbows against inner knees to open hips.",
            "Bring palms together in namaste at the heart center.",
            "Keep spine erect and lift chest."
        ],
        benefits=[
            "Stretches groin, hips, and ankles",
            "Improves posture and tones abdominal muscles",
            "Aids in digestive system stimulation"
        ],
        tips=[
            "If heels lift, place a folded blanket under them.",
            "Keep your spine upright."
        ]
    ),
    "Natarajasana": PoseInfo(
        name="Natarajasana",
        description="A graceful balancing standing pose that stretches shoulders and chest, improving balance and core strength.",
        image_paths=["Natarajasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Stand straight on one leg.",
            "Bend the other knee and reach back to grasp the inside of the foot.",
            "Inhale and raise the opposite arm straight up.",
            "Exhale, kick the back foot into your hand and tilt forward.",
            "Keep chest open and look at one spot for balance."
        ],
        benefits=[
            "Stretches chest, shoulders, and thighs",
            "Builds leg and ankle strength",
            "Enhances focus and balance"
        ],
        tips=[
            "Kick back firmly to lift the leg higher.",
            "Keep the standing leg strong and grounded."
        ]
    ),
    "Phalakasana (Plank)": PoseInfo(
        name="Phalakasana (Plank)",
        description="A core-strengthening push-up position that builds upper body stability and alignment.",
        image_paths=["Phalakasana (Plank).jpg"],
        confidence_threshold=0.65,
        steps=[
            "Start in a push-up position with hands shoulder-width apart.",
            "Keep your body in a straight line from head to heels.",
            "Engage your core, thighs, and glutes.",
            "Push the floor away to broaden the shoulders.",
            "Look slightly forward and breathe deeply."
        ],
        benefits=[
            "Strengthens wrists, arms, shoulders, and core",
            "Improves posture and full-body stability",
            "Tones the abdominal muscles"
        ],
        tips=[
            "Do not let your hips sag or lift too high.",
            "Press actively through the heels to engage legs."
        ]
    ),
    "Chaturanga Dandasana": PoseInfo(
        name="Chaturanga Dandasana",
        description="A low plank pose that builds intense arm, shoulder, and core strength, essential in sun salutations.",
        image_paths=["Chaturanga Dandasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "From plank pose, shift your weight slightly forward.",
            "Lower your body down until your elbows are bent at a 90-degree angle.",
            "Keep elbows tucked in close to your ribs.",
            "Maintain a straight line from head to toes.",
            "Gaze down and slightly forward."
        ],
        benefits=[
            "Strengthens arms, wrists, and shoulders",
            "Develops core and leg stability",
            "Prepares the body for arm balances"
        ],
        tips=[
            "Do not let your shoulders drop below elbow height.",
            "Keep the core fully engaged to support the spine."
        ]
    ),
    "Bakasana": PoseInfo(
        name="Bakasana",
        description="An advanced arm balance (Crow Pose) where the knees rest on the upper arms, lifting feet off the floor.",
        image_paths=["Bakasana.jpg"],
        confidence_threshold=0.55,
        steps=[
            "Squat down, place hands flat on the floor shoulder-width apart.",
            "Place knees high up against the back of your upper arms.",
            "Shift your weight forward onto your hands.",
            "Lift one foot, then the other, off the floor.",
            "Squeeze your inner thighs and look slightly forward."
        ],
        benefits=[
            "Significantly strengthens arms, wrists, and core",
            "Improves concentration and physical balance",
            "Stretches the upper back and groin"
        ],
        tips=[
            "Look forward, not down, to avoid rolling forward.",
            "Engage your abdominal muscles to lift your hips."
        ]
    ),
    "Adho Mukha Svanasana": PoseInfo(
        name="Adho Mukha Svanasana",
        description="Downward-Facing Dog, an inversion that stretches the hamstrings, calves, and spine while building arm strength.",
        image_paths=["Adho Mukha Svanasana.jpg"],
        confidence_threshold=0.65,
        steps=[
            "Start on all fours, hands slightly in front of shoulders.",
            "Exhale, tuck toes and lift knees, raising hips towards the ceiling.",
            "Push hips back to create an inverted V-shape.",
            "Press palms firmly into the mat, fingers spread wide.",
            "Relax your neck and let your heels reach down."
        ],
        benefits=[
            "Stretches hamstrings, calves, spine, and shoulders",
            "Strengthens arms, shoulders, and legs",
            "Improves blood circulation and relieves stress"
        ],
        tips=[
            "Micro-bend knees if your lower back rounds.",
            "Keep weight distributed evenly across your palms."
        ]
    ),
    "Vasisthasana": PoseInfo(
        name="Vasisthasana",
        description="Side Plank, a balancing pose that targets the obliques, shoulders, and arms.",
        image_paths=["Vasisthasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Start in a plank pose.",
            "Roll onto the outer edge of one foot and stack the other foot on top.",
            "Raise the opposite arm straight up towards the ceiling.",
            "Lift your hips to form a straight diagonal line.",
            "Look up toward the lifted hand if balance allows."
        ],
        benefits=[
            "Strengthens wrists, arms, shoulders, and obliques",
            "Improves balance and full-body concentration",
            "Tones the core and legs"
        ],
        tips=[
            "Keep the bottom hand slightly ahead of the shoulder to protect the joint.",
            "Engage the side waist to lift the hips high."
        ]
    ),
    "Step 1: Pranamasana": PoseInfo(
        name="Step 1: Pranamasana",
        description="Prayer Pose. Stand at the edge of your mat, bring hands together in a prayer position in front of chest.",
        image_paths=["Pranamasana.jpg"],
        confidence_threshold=0.65,
        steps=[
            "Stand at the edge of your mat with feet together.",
            "Bring palms together in front of your chest in prayer position.",
            "Relax your shoulders and look straight ahead."
        ],
        benefits=[
            "Promotes relaxation",
            "Centers the mind",
            "Improves posture"
        ],
        tips=[
            "Keep weight evenly balanced on both feet.",
            "Relax the face and shoulders."
        ]
    ),
    "Step 2: Hasta Uttanasana": PoseInfo(
        name="Step 2: Hasta Uttanasana",
        description="Raised Arms Pose. Inhale, lift arms up and slightly back, stretching the entire body.",
        image_paths=["hasta uttanasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Inhale and lift your arms up and back.",
            "Keep your biceps close to your ears.",
            "Stretch your whole body up from your heels."
        ],
        benefits=[
            "Stretches abdomen and chest",
            "Strengthens arms and shoulders",
            "Stimulates thyroid gland"
        ],
        tips=[
            "Do not over-arch the lower back.",
            "Keep arms straight."
        ]
    ),
    "Step 3: Padahastasana": PoseInfo(
        name="Step 3: Padahastasana",
        description="Hand to Foot Pose. Exhale, bend forward from the hips, keeping the spine straight, and bring hands to feet.",
        image_paths=["Padahastasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Exhale and bend forward from the hips.",
            "Keep your spine long and reach down toward the mat.",
            "Place hands on the floor next to feet or touch your toes."
        ],
        benefits=[
            "Stretches calves, hamstrings, and hips",
            "Improves digestion",
            "Calms the nervous system"
        ],
        tips=[
            "Bend knees slightly if hamstrings feel tight.",
            "Keep weight on the balls of your feet."
        ]
    ),
    "Step 4: Ashwa Sanchalanasana": PoseInfo(
        name="Step 4: Ashwa Sanchalanasana",
        description="Equestrian Pose. Inhale, push the right leg back, drop right knee to the floor, and look up.",
        image_paths=["Ashwa Sanchalanasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Inhale and push your right leg back as far as possible.",
            "Bring your right knee to the floor.",
            "Bend left knee, keeping left foot flat, and gaze upwards."
        ],
        benefits=[
            "Stretches quadriceps, psoas, and groin",
            "Strengthens hips and legs",
            "Improves flexibility of spine"
        ],
        tips=[
            "Ensure left knee is directly above left ankle.",
            "Keep chest lifted."
        ]
    ),
    "Step 5: Dandasana": PoseInfo(
        name="Step 5: Dandasana",
        description="Stick Pose / Plank Pose. Retain breath, bring left foot back to join right foot, keeping body in a straight line.",
        image_paths=["Dandasana.jpg"],
        confidence_threshold=0.65,
        steps=[
            "Bring your left leg back to join the right leg.",
            "Keep your hands shoulder-width apart and directly under shoulders.",
            "Maintain a straight line from head to heels."
        ],
        benefits=[
            "Strengthens arms, wrists, and core",
            "Improves posture",
            "Builds stamina"
        ],
        tips=[
            "Engage your core and do not let your hips sag."
        ]
    ),
    "Step 6: Ashtanga Namaskara": PoseInfo(
        name="Step 6: Ashtanga Namaskara",
        description="Salute With Eight Parts. Exhale, gently lower knees, chest, and chin to the floor while keeping hips elevated.",
        image_paths=["Ashtanga Namaskara.jpg"],
        confidence_threshold=0.55,
        steps=[
            "Exhale and gently bring your knees to the floor.",
            "Lower your chest and chin to the mat.",
            "Keep your hips slightly elevated so eight points of the body touch the ground."
        ],
        benefits=[
            "Strengthens chest, arms, and back",
            "Increases spinal flexibility",
            "Develops core stability"
        ],
        tips=[
            "Keep your elbows tucked in close to your chest."
        ]
    ),
    "Step 7: Bhujangasana": PoseInfo(
        name="Step 7: Bhujangasana",
        description="Cobra Pose. Inhale, slide forward and raise chest up, keeping elbows bent and shoulders back.",
        image_paths=["Bhujangasana.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Inhale, slide forward and lift your chest up.",
            "Keep your pelvis on the floor.",
            "Roll your shoulders back and look gently upward."
        ],
        benefits=[
            "Strengthens spine and shoulders",
            "Tones abdominal muscles",
            "Stretches chest and lungs"
        ],
        tips=[
            "Do not put too much weight in your hands; use back muscles.",
            "Keep neck long."
        ]
    ),
    "Step 8: Adho Mukha Svanasana": PoseInfo(
        name="Step 8: Adho Mukha Svanasana",
        description="Downward-Facing Dog. Exhale, lift hips up and push back, forming an inverted V-shape.",
        image_paths=["Adho Mukha Svanasana.jpg"],
        confidence_threshold=0.65,
        steps=[
            "Exhale, lift your hips and tailbone up.",
            "Push your body back into an inverted V-shape.",
            "Press your heels towards the floor and relax your neck."
        ],
        benefits=[
            "Stretches entire back of the body",
            "Calms the mind",
            "Strengthens arms and legs"
        ],
        tips=[
            "Keep fingers spread wide to protect wrists.",
            "Keep spine long."
        ]
    ),
    "Step 9: Ashwa Sanchalanasana": PoseInfo(
        name="Step 9: Ashwa Sanchalanasana",
        description="Equestrian Pose. Inhale, bring right foot forward between hands, drop left knee, and look up.",
        image_paths=["Ashwa Sanchalanasana 2.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Inhale and step your right foot forward between your hands.",
            "Lower your left knee to the mat.",
            "Look up and lift the chest."
        ],
        benefits=[
            "Stretches hip flexors and legs",
            "Relieves fatigue",
            "Improves balance"
        ],
        tips=[
            "Ensure the right knee is aligned above the ankle."
        ]
    ),
    "Step 10: Padahastasana": PoseInfo(
        name="Step 10: Padahastasana",
        description="Hand to Foot Pose. Exhale, bring left foot forward next to right, bend from the hips.",
        image_paths=["Padahastasana 2.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Exhale and bring your left foot forward next to your right foot.",
            "Bend forward from the hips and try to touch your toes.",
            "Relax your head and neck."
        ],
        benefits=[
            "Stretches hamstrings and calves",
            "Improves spinal flexibility",
            "Aids in digestion"
        ],
        tips=[
            "Let gravity pull your head and spine down."
        ]
    ),
    "Step 11: Hasta Uttanasana": PoseInfo(
        name="Step 11: Hasta Uttanasana",
        description="Raised Arms Pose. Inhale, raise arms up and stretch back.",
        image_paths=["Hasta Uttanasana 2.jpg"],
        confidence_threshold=0.60,
        steps=[
            "Inhale, raise your arms up, and tilt your body backward.",
            "Reach up from your hips.",
            "Look up at your hands."
        ],
        benefits=[
            "Stretches abdominal wall",
            "Expands lung capacity",
            "Strengthens shoulder joints"
        ],
        tips=[
            "Press your hips slightly forward as you lean back."
        ]
    ),
    "Step 12: Pranamasana": PoseInfo(
        name="Step 12: Pranamasana",
        description="Prayer Pose. Exhale, lower arms and return to prayer position at chest, then release.",
        image_paths=["Pranamasana 2.jpg"],
        confidence_threshold=0.65,
        steps=[
            "Exhale and lower your hands back to your chest in prayer position.",
            "Relax your body and stand straight.",
            "Take a few calm breaths to complete the cycle."
        ],
        benefits=[
            "Brings body and mind to balance",
            "Enhances state of concentration",
            "Restores normal breathing"
        ],
        tips=[
            "Close your eyes for a moment to feel the benefits of the cycle."
        ]
    ),
}
# ---------------------------------
# HELPERS
# ---------------------------------
def load_existing_images(paths: List[str], pose_name: str = "") -> List[Image.Image]:
    """Load images for a pose.

    1. First try the explicit ``paths`` supplied in ``PoseInfo``.
    2. If none are found, fall back to a category‑wide folder named
       ``Hand/Arm-Focused Asanas`` (or any folder matching the pose name).\n       The function searches for image files whose filenames contain the
       pose name (case‑insensitive) inside that folder.
    """
    loaded: List[Image.Image] = []
    # Primary paths from PoseInfo
    for path in paths:
        if os.path.exists(path):
            try:
                loaded.append(Image.open(path))
            except Exception:
                pass
    # Fallback: search a folder named after the pose (or the special category folder)
    if not loaded:
        base_dir = os.path.dirname(__file__)
        # Look for a generic folder that may hold images for this category
        fallback_folder = os.path.join(base_dir, "Hand/Arm-Focused Asanas")
        search_dirs = [fallback_folder]
        # Also try a pose‑specific folder
        pose_folder = os.path.join(base_dir, pose_name.replace(" ", "_"))
        search_dirs.append(pose_folder)
        # Also search the main base directory for images with matching names
        search_dirs.append(base_dir)
        for folder in search_dirs:
            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and pose_name.lower() in f.lower():
                        try:
                            loaded.append(Image.open(os.path.join(folder, f)))
                        except Exception:
                            pass
    return loaded

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180:
        angle = 360 - angle
    return angle

def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))

def get_xy(landmarks, landmark_enum):
    return [landmarks[landmark_enum.value].x, landmarks[landmark_enum.value].y]

def grade_label(score: float) -> str:
    if score >= 0.85:
        return "Excellent"
    if score >= 0.70:
        return "Good"
    if score >= 0.55:
        return "Average"
    return "Needs Improvement"

def render_soft_box(text: str, variant: str = "info"):
    klass = {
        "info": "soft-info",
        "success": "soft-success",
        "warning": "soft-warning",
        "danger": "soft-danger",
    }.get(variant, "soft-info")
    st.markdown(f'<div class="{klass}">{text}</div>', unsafe_allow_html=True)

def do_logout():
    st.session_state.logged_in = False
    st.session_state.current_user = ""
    st.session_state.capturing_now = False
    st.session_state.chat_history = []
    st.rerun()

def is_valid_email(email: str) -> bool:
    return "@" in email and "." in email and len(email) >= 6

def categorize_password(password: str) -> dict:
    """Categorize password by character types."""
    return {
        "has_uppercase": any(c.isupper() for c in password),
        "has_lowercase": any(c.islower() for c in password),
        "has_unique": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),
    }

def render_password_categories(password: str):
    """Display password character type categories with strength meter."""
    if not password:
        return
    
    cats = categorize_password(password)
    pwd_len = len(password)
    
    # Calculate strength score
    strength_score = 0
    if pwd_len >= 8:
        strength_score += 1
    if pwd_len >= 12:
        strength_score += 1
    if cats["has_uppercase"]:
        strength_score += 1
    if cats["has_lowercase"]:
        strength_score += 1
    if cats["has_unique"]:
        strength_score += 1
    
    # Determine strength level and color
    if strength_score <= 1:
        strength_level = "Weak"
        strength_color = "#ef4444"  # Red
        strength_width = "20%"
    elif strength_score == 2:
        strength_level = "Fair"
        strength_color = "#f97316"  # Orange-Red
        strength_width = "40%"
    elif strength_score == 3:
        strength_level = "Good"
        strength_color = "#eab308"  # Yellow
        strength_width = "60%"
    elif strength_score == 4:
        strength_level = "Strong"
        strength_color = "#84cc16"  # Green
        strength_width = "80%"
    else:
        strength_level = "Very Strong"
        strength_color = "#22c55e"  # Bright Green
        strength_width = "100%"
    
    # Strength meter bar with red gradient
    st.markdown(f"""
    <div style="margin-top: 12px; margin-bottom: 6px;">
        <div style="height: 8px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden; margin-bottom: 10px;">
            <div style="height: 100%; width: {strength_width}; background: linear-gradient(90deg, {strength_color}, {strength_color}); border-radius: 10px; transition: all 0.3s ease; box-shadow: 0 0 12px {strength_color}80;"></div>
        </div>
        <div style="color: #cbd5e1; font-size: 14px; font-weight: 700;">
            Password strength: <span style="color: {strength_color};">{strength_level}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Requirements list with real-time updates
    st.markdown(f"""
    <div style="margin-top: 10px; margin-bottom: 12px; font-size: 13px;">
        <div style="color: {'#22c55e' if pwd_len >= 8 else '#ef4444'}; margin-bottom: 8px; display: flex; align-items: center;">
            <span style="margin-right: 10px; font-weight: 700;">{'✓' if pwd_len >= 8 else '✗'}</span>
            <span>At least 8 characters ({pwd_len})</span>
        </div>
        <div style="color: {'#22c55e' if cats['has_uppercase'] else '#ef4444'}; margin-bottom: 8px; display: flex; align-items: center;">
            <span style="margin-right: 10px; font-weight: 700;">{'✓' if cats['has_uppercase'] else '✗'}</span>
            <span>One uppercase letter</span>
        </div>
        <div style="color: {'#22c55e' if cats['has_lowercase'] else '#ef4444'}; margin-bottom: 8px; display: flex; align-items: center;">
            <span style="margin-right: 10px; font-weight: 700;">{'✓' if cats['has_lowercase'] else '✗'}</span>
            <span>One lowercase letter</span>
        </div>
        <div style="color: {'#22c55e' if cats['has_unique'] else '#ef4444'}; display: flex; align-items: center;">
            <span style="margin-right: 10px; font-weight: 700;">{'✓' if cats['has_unique'] else '✗'}</span>
            <span>One unique character (!@#$%^&*)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def register_user(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if not is_valid_email(email):
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    cur.execute("SELECT email FROM users WHERE email=?", (email,))
    if cur.fetchone():
        return False, "Account already exists with this email."
    cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
    conn.commit()
    return True, "Account created successfully. Now login."

def login_user(email: str, password: str) -> bool:
    email = email.strip().lower()
    cur.execute("SELECT email FROM users WHERE email=? AND password=?", (email, password))
    return cur.fetchone() is not None

def save_pose_history(user_email: str, pose_name: str, accuracy: float, grade: str, feedback: str):
    if not user_email:
        return
    cur.execute("""
        INSERT INTO pose_history (user_email, pose_name, accuracy, grade, feedback)
        VALUES (?, ?, ?, ?, ?)
    """, (user_email, pose_name, accuracy, grade, feedback))
    conn.commit()

def get_user_history(user_email: str, limit: int = 10):
    if not user_email:
        return []
    cur.execute("""
        SELECT pose_name, accuracy, grade, feedback, created_at
        FROM pose_history
        WHERE user_email = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_email, limit))
    return cur.fetchall()

# ---------------------------------
# MEDIAPIPE
# ---------------------------------
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
# ---------------------------------
# POSE LOGIC
# ---------------------------------
def evaluate_pose(landmarks, pose_name: str) -> Tuple[float, str]:
    l_shoulder = get_xy(landmarks, mp_pose.PoseLandmark.LEFT_SHOULDER)
    r_shoulder = get_xy(landmarks, mp_pose.PoseLandmark.RIGHT_SHOULDER)
    l_elbow = get_xy(landmarks, mp_pose.PoseLandmark.LEFT_ELBOW)
    r_elbow = get_xy(landmarks, mp_pose.PoseLandmark.RIGHT_ELBOW)
    l_wrist = get_xy(landmarks, mp_pose.PoseLandmark.LEFT_WRIST)
    r_wrist = get_xy(landmarks, mp_pose.PoseLandmark.RIGHT_WRIST)
    l_hip = get_xy(landmarks, mp_pose.PoseLandmark.LEFT_HIP)
    r_hip = get_xy(landmarks, mp_pose.PoseLandmark.RIGHT_HIP)
    l_knee = get_xy(landmarks, mp_pose.PoseLandmark.LEFT_KNEE)
    r_knee = get_xy(landmarks, mp_pose.PoseLandmark.RIGHT_KNEE)
    l_ankle = get_xy(landmarks, mp_pose.PoseLandmark.LEFT_ANKLE)
    r_ankle = get_xy(landmarks, mp_pose.PoseLandmark.RIGHT_ANKLE)
    nose = get_xy(landmarks, mp_pose.PoseLandmark.NOSE)

    if pose_name == "Warrior II":
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)

        arm_score = (
            (1 - abs(180 - left_arm) / 180) +
            (1 - abs(180 - right_arm) / 180)
        ) / 2
        knee_score = max(
            1 - abs(95 - left_knee) / 95,
            1 - abs(95 - right_knee) / 95
        )
        shoulder_level = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(arm_score * 0.45 + knee_score * 0.40 + clamp_score(shoulder_level) * 0.15)

        if confidence > 0.8:
            feedback = "Excellent Warrior II. Arms and knee alignment are looking strong."
        elif confidence > 0.65:
            feedback = "Good pose. Make your front knee deeper and keep both arms fully straight."
        else:
            feedback = "Take a wider stance, bend one knee more, and stretch both arms strongly."
        return confidence, feedback

    if pose_name == "Tree Pose":
        left_leg = calculate_angle(l_hip, l_knee, l_ankle)
        right_leg = calculate_angle(r_hip, r_knee, r_ankle)
        straight_leg_score = max(1 - abs(180 - left_leg) / 180, 1 - abs(180 - right_leg) / 180)
        bent_leg_score = max(1 - abs(90 - left_leg) / 90, 1 - abs(90 - right_leg) / 90)
        symmetry = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(straight_leg_score * 0.45 + bent_leg_score * 0.35 + clamp_score(symmetry) * 0.20)

        if confidence > 0.8:
            feedback = "Excellent Tree Pose. Your balance looks stable."
        elif confidence > 0.63:
            feedback = "Good try. Keep one leg straighter and maintain balance."
        else:
            feedback = "Lift one foot higher and focus on balance. Keep the standing leg strong."
        return confidence, feedback

    if pose_name == "Butterfly Pose":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        knee_open_score = ((1 - abs(60 - left_knee) / 180) + (1 - abs(60 - right_knee) / 180)) / 2
        spine_mid_shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        spine_mid_hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]
        spine_angle = calculate_angle(nose, spine_mid_shoulder, spine_mid_hip)
        back_score = 1 - abs(180 - spine_angle) / 180
        confidence = clamp_score(knee_open_score * 0.60 + back_score * 0.40)

        if confidence > 0.75:
            feedback = "Very nice Butterfly Pose. Your posture is relaxed and aligned."
        elif confidence > 0.58:
            feedback = "Good pose. Sit taller and let the knees relax more."
        else:
            feedback = "Bring feet together and keep your back straighter."
        return confidence, feedback

    if pose_name == "Cobra Pose":
        left_back = calculate_angle(l_elbow, l_shoulder, l_hip)
        right_back = calculate_angle(r_elbow, r_shoulder, r_hip)
        chest_lift_score = ((1 - abs(140 - left_back) / 180) + (1 - abs(140 - right_back) / 180)) / 2
        shoulder_balance = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(chest_lift_score * 0.75 + clamp_score(shoulder_balance) * 0.25)

        if confidence > 0.78:
            feedback = "Excellent Cobra Pose. Chest lift looks smooth."
        elif confidence > 0.60:
            feedback = "Nice. Lift your chest a little more and relax shoulders."
        else:
            feedback = "Lie flat first, then lift the chest gently without straining."
        return confidence, feedback

    if pose_name == "Mountain Pose":
        left_body = calculate_angle(l_shoulder, l_hip, l_ankle)
        right_body = calculate_angle(r_shoulder, r_hip, r_ankle)
        left_score = 1 - abs(180 - left_body) / 180
        right_score = 1 - abs(180 - right_body) / 180
        symmetry = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(left_score * 0.35 + right_score * 0.35 + clamp_score(symmetry) * 0.30)

        if confidence > 0.82:
            feedback = "Excellent Mountain Pose. Body alignment looks straight."
        elif confidence > 0.65:
            feedback = "Good. Stand taller and relax the shoulders."
        else:
            feedback = "Keep your spine straight, feet grounded, and avoid leaning."
        return confidence, feedback

    if pose_name == "Padmasana":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        knee_score = ((1 - abs(45 - left_knee) / 180) + (1 - abs(45 - right_knee) / 180)) / 2
        spine_mid_shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        spine_mid_hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]
        spine_angle = calculate_angle(nose, spine_mid_shoulder, spine_mid_hip)
        back_score = 1 - abs(180 - spine_angle) / 180
        confidence = clamp_score(knee_score * 0.50 + back_score * 0.50)

        if confidence > 0.78:
            feedback = "Excellent Padmasana. Your spine is straight and knees are relaxed."
        elif confidence > 0.60:
            feedback = "Good posture. Try to keep your back straighter and relax your shoulders."
        else:
            feedback = "Sit with crossed legs, keep your spine tall, and rest your hands on your knees."
        return confidence, feedback

    if pose_name == "Swastikasana":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        knee_score = ((1 - abs(50 - left_knee) / 180) + (1 - abs(50 - right_knee) / 180)) / 2
        spine_mid_shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        spine_mid_hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]
        spine_angle = calculate_angle(nose, spine_mid_shoulder, spine_mid_hip)
        back_score = 1 - abs(180 - spine_angle) / 180
        confidence = clamp_score(knee_score * 0.50 + back_score * 0.50)

        if confidence > 0.78:
            feedback = "Excellent Swastikasana. Great balance and posture."
        elif confidence > 0.60:
            feedback = "Good try. Straighten your back slightly more."
        else:
            feedback = "Cross your legs comfortably and keep your upper body upright."
        return confidence, feedback

    if pose_name == "Vajrasana":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        knee_score = ((1 - abs(35 - left_knee) / 180) + (1 - abs(35 - right_knee) / 180)) / 2
        spine_mid_shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        spine_mid_hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]
        spine_angle = calculate_angle(nose, spine_mid_shoulder, spine_mid_hip)
        back_score = 1 - abs(180 - spine_angle) / 180
        confidence = clamp_score(knee_score * 0.50 + back_score * 0.50)

        if confidence > 0.78:
            feedback = "Excellent Vajrasana. Your spine is beautifully upright."
        elif confidence > 0.60:
            feedback = "Good form. Keep sitting on your heels and lengthen your back."
        else:
            feedback = "Kneel down, sit back on your heels, and keep your spine erect."
        return confidence, feedback

    if pose_name == "Gomukhasana":
        left_elbow_y = l_elbow[1]
        right_elbow_y = r_elbow[1]
        shoulder_diff = abs(left_elbow_y - right_elbow_y)
        elbow_score = clamp_score(shoulder_diff * 2)

        spine_mid_shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        spine_mid_hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]
        spine_angle = calculate_angle(nose, spine_mid_shoulder, spine_mid_hip)
        back_score = 1 - abs(180 - spine_angle) / 180

        confidence = clamp_score(elbow_score * 0.50 + back_score * 0.50)

        if confidence > 0.78:
            feedback = "Excellent Gomukhasana. Arms and spine are well aligned."
        elif confidence > 0.60:
            feedback = "Good. Try to stretch your shoulders more and open the chest."
        else:
            feedback = "Stack your knees, clasp your hands behind your back, and keep your spine upright."
        return confidence, feedback

    if pose_name == "Ardha Matsyendrasana":
        shoulder_width = abs(l_shoulder[0] - r_shoulder[0])
        twist_score = 1 - clamp_score(shoulder_width * 2)

        spine_mid_shoulder = [(l_shoulder[0] + r_shoulder[0]) / 2, (l_shoulder[1] + r_shoulder[1]) / 2]
        spine_mid_hip = [(l_hip[0] + r_hip[0]) / 2, (l_hip[1] + r_hip[1]) / 2]
        spine_angle = calculate_angle(nose, spine_mid_shoulder, spine_mid_hip)
        back_score = 1 - abs(180 - spine_angle) / 180

        confidence = clamp_score(twist_score * 0.40 + back_score * 0.60)

        if confidence > 0.78:
            feedback = "Excellent Ardha Matsyendrasana. Deep twist and tall spine."
        elif confidence > 0.60:
            feedback = "Good pose. Lengthen your spine before twisting."
        else:
            feedback = "Sit, bend your knee over the opposite thigh, twist your torso, and look back."
        return confidence, feedback

    if pose_name == "Janu Shirshasana":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        straight_leg = max(left_knee, right_knee)
        bent_leg = min(left_knee, right_knee)

        straight_score = 1 - abs(180 - straight_leg) / 180
        bent_score = 1 - abs(45 - bent_leg) / 90
        fold_score = 1 - clamp_score(abs(nose[1] - l_hip[1]) * 2)

        confidence = clamp_score(straight_score * 0.35 + bent_score * 0.35 + fold_score * 0.30)

        if confidence > 0.78:
            feedback = "Excellent Janu Shirshasana. Great hamstring stretch and back alignment."
        elif confidence > 0.60:
            feedback = "Good. Try to extend your chest forward instead of rounding your spine."
        else:
            feedback = "Place one foot on the opposite inner thigh, keep the other leg straight, and fold forward."
        return confidence, feedback

    if pose_name == "Paschimottanasana":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        leg_straight_score = ((1 - abs(180 - left_knee) / 180) + (1 - abs(180 - right_knee) / 180)) / 2
        fold_score = 1 - clamp_score(abs(nose[1] - l_hip[1]) * 2)

        confidence = clamp_score(leg_straight_score * 0.50 + fold_score * 0.50)

        if confidence > 0.78:
            feedback = "Excellent Paschimottanasana. Full stretch and deep forward fold."
        elif confidence > 0.60:
            feedback = "Good stretch. Try to bring your torso closer to your legs."
        else:
            feedback = "Keep both legs straight and extend your torso forward to reach your feet."
        return confidence, feedback

    if pose_name == "Tadasana":
        left_body = calculate_angle(l_shoulder, l_hip, l_ankle)
        right_body = calculate_angle(r_shoulder, r_hip, r_ankle)
        left_score = 1 - abs(180 - left_body) / 180
        right_score = 1 - abs(180 - right_body) / 180
        symmetry = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(left_score * 0.35 + right_score * 0.35 + clamp_score(symmetry) * 0.30)

        if confidence > 0.82:
            feedback = "Excellent Tadasana. Perfectly straight alignment."
        elif confidence > 0.65:
            feedback = "Good. Lengthen your spine and relax your shoulders."
        else:
            feedback = "Stand straight with feet grounded, look ahead, and keep body balanced."
        return confidence, feedback

    if pose_name == "Trikonasana":
        left_leg = calculate_angle(l_hip, l_knee, l_ankle)
        right_leg = calculate_angle(r_hip, r_knee, r_ankle)
        leg_score = ((1 - abs(180 - left_leg) / 180) + (1 - abs(180 - right_leg) / 180)) / 2
        arm_line = calculate_angle(l_wrist, l_shoulder, r_shoulder)
        arm_score = 1 - abs(180 - arm_line) / 180
        confidence = clamp_score(leg_score * 0.50 + clamp_score(arm_score) * 0.50)

        if confidence > 0.75:
            feedback = "Excellent Trikonasana. Great arm extension and leg alignment."
        elif confidence > 0.60:
            feedback = "Good try. Stretch your upper arm straight up."
        else:
            feedback = "Keep both legs straight, reach out sideways, fold over the leg, and look up."
        return confidence, feedback

    if pose_name == "Utkatasana":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        knee_score = ((1 - abs(115 - left_knee) / 90) + (1 - abs(115 - right_knee) / 90)) / 2
        left_shoulder_angle = calculate_angle(l_elbow, l_shoulder, l_hip)
        right_shoulder_angle = calculate_angle(r_elbow, r_shoulder, r_hip)
        arm_score = ((1 - abs(150 - left_shoulder_angle) / 180) + (1 - abs(150 - right_shoulder_angle) / 180)) / 2
        confidence = clamp_score(knee_score * 0.55 + arm_score * 0.45)

        if confidence > 0.76:
            feedback = "Excellent Utkatasana. Your hips are low and arms are strong."
        elif confidence > 0.60:
            feedback = "Good. Try to sink your hips slightly lower and lift your chest."
        else:
            feedback = "Bend your knees, push your hips back, and stretch your arms up."
        return confidence, feedback

    if pose_name == "Virabhadrasana I":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        front_knee = min(left_knee, right_knee)
        back_knee = max(left_knee, right_knee)
        front_score = 1 - abs(100 - front_knee) / 90
        back_score = 1 - abs(180 - back_knee) / 180
        left_shoulder_angle = calculate_angle(l_elbow, l_shoulder, l_hip)
        right_shoulder_angle = calculate_angle(r_elbow, r_shoulder, r_hip)
        arm_score = ((1 - abs(150 - left_shoulder_angle) / 180) + (1 - abs(150 - right_shoulder_angle) / 180)) / 2
        confidence = clamp_score(front_score * 0.40 + back_score * 0.35 + arm_score * 0.25)

        if confidence > 0.78:
            feedback = "Excellent Virabhadrasana I. Back leg is active and chest is lifted."
        elif confidence > 0.60:
            feedback = "Good. Stretch your arms higher and square your hips forward."
        else:
            feedback = "Step back with one leg straight, bend front knee, and raise arms up."
        return confidence, feedback

    if pose_name == "Virabhadrasana II":
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)

        arm_score = (
            (1 - abs(180 - left_arm) / 180) +
            (1 - abs(180 - right_arm) / 180)
        ) / 2
        knee_score = max(
            1 - abs(95 - left_knee) / 95,
            1 - abs(95 - right_knee) / 95
        )
        shoulder_level = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(arm_score * 0.45 + knee_score * 0.40 + clamp_score(shoulder_level) * 0.15)

        if confidence > 0.8:
            feedback = "Excellent Virabhadrasana II. Solid form."
        elif confidence > 0.65:
            feedback = "Good. Bend your front knee deeper."
        else:
            feedback = "Take a wide stance, bend one knee, and stretch arms wide."
        return confidence, feedback

    if pose_name == "Vrikshasana":
        left_leg = calculate_angle(l_hip, l_knee, l_ankle)
        right_leg = calculate_angle(r_hip, r_knee, r_ankle)
        straight_leg_score = max(1 - abs(180 - left_leg) / 180, 1 - abs(180 - right_leg) / 180)
        bent_leg_score = max(1 - abs(90 - left_leg) / 90, 1 - abs(90 - right_leg) / 90)
        symmetry = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(straight_leg_score * 0.45 + bent_leg_score * 0.35 + clamp_score(symmetry) * 0.20)

        if confidence > 0.8:
            feedback = "Excellent Vrikshasana. Very stable balance."
        elif confidence > 0.63:
            feedback = "Good. Try to hold your balance and stand tall."
        else:
            feedback = "Lift one foot onto your inner thigh/calf and join your hands."
        return confidence, feedback

    if pose_name == "Malasana":
        left_knee_angle = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
        # Ideal squat knee angle ~90 degrees
        squat_score = ((1 - abs(90 - left_knee_angle) / 90) + (1 - abs(90 - right_knee_angle) / 90)) / 2
        # Shoulder symmetry for upright spine
        symmetry = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(squat_score * 0.70 + clamp_score(symmetry) * 0.30)
        if confidence > 0.8:
            feedback = "Excellent Malasana. Deep, stable squat with good spine alignment."
        elif confidence > 0.6:
            feedback = "Good Malasana. Try to keep knees aligned and spine upright."
        else:
            feedback = "Work on lowering hips further and keeping heels down."
        return confidence, feedback

    if pose_name == "Natarajasana":
        # Check arm raise (should be near straight up ~180 degrees) and leg lift (hip‑knee‑ankle angle close to 180)
        arm_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
        leg_angle = calculate_angle(r_hip, r_knee, r_ankle)
        arm_score = 1 - abs(180 - arm_angle) / 180
        leg_score = 1 - abs(180 - leg_angle) / 180
        # Balance: shoulder level
        shoulder_level = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(arm_score * 0.40 + leg_score * 0.40 + clamp_score(shoulder_level) * 0.20)
        if confidence > 0.8:
            feedback = "Excellent Natarajasana. Strong balance and beautiful arm lift."
        elif confidence > 0.6:
            feedback = "Good Natarajasana. Keep the lifted leg and arm steady."
        else:
            feedback = "Focus on extending the lifted leg and raising the arm higher."
        return confidence, feedback

    if pose_name == "Phalakasana (Plank)":
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        left_torso = calculate_angle(l_shoulder, l_hip, l_knee)
        right_torso = calculate_angle(r_shoulder, r_hip, r_knee)
        
        arm_score = ((1 - abs(180 - left_arm) / 180) + (1 - abs(180 - right_arm) / 180)) / 2
        torso_score = ((1 - abs(180 - left_torso) / 180) + (1 - abs(180 - right_torso) / 180)) / 2
        confidence = clamp_score(arm_score * 0.40 + torso_score * 0.60)
        
        if confidence > 0.8:
            feedback = "Excellent Plank form! Flat back and straight arms."
        elif confidence > 0.65:
            feedback = "Good plank. Keep your body straight and avoid sagging your hips."
        else:
            feedback = "Keep a straight line from head to heels, and keep your elbows straight."
        return confidence, feedback

    if pose_name == "Chaturanga Dandasana":
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        left_torso = calculate_angle(l_shoulder, l_hip, l_knee)
        right_torso = calculate_angle(r_shoulder, r_hip, r_knee)
        
        arm_score = ((1 - abs(90 - left_arm) / 90) + (1 - abs(90 - right_arm) / 90)) / 2
        torso_score = ((1 - abs(180 - left_torso) / 180) + (1 - abs(180 - right_torso) / 180)) / 2
        confidence = clamp_score(arm_score * 0.50 + torso_score * 0.50)
        
        if confidence > 0.8:
            feedback = "Excellent Chaturanga! Solid 90-degree arm bend and flat body."
        elif confidence > 0.60:
            feedback = "Good Chaturanga. Try to keep elbows bent close to 90 degrees."
        else:
            feedback = "Lower your body, bend elbows to 90 degrees, and keep torso aligned."
        return confidence, feedback

    if pose_name == "Bakasana":
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        left_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        right_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee)
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        
        knee_flex_score = (clamp_score(1 - left_knee / 180) + clamp_score(1 - right_knee / 180)) / 2
        hip_flex_score = (clamp_score(1 - left_hip_angle / 180) + clamp_score(1 - right_hip_angle / 180)) / 2
        arm_score = ((1 - abs(120 - left_arm) / 120) + (1 - abs(120 - right_arm) / 120)) / 2
        
        confidence = clamp_score(knee_flex_score * 0.40 + hip_flex_score * 0.40 + clamp_score(arm_score) * 0.20)
        
        if confidence > 0.8:
            feedback = "Excellent Bakasana! High hips and knees placed well on upper arms."
        elif confidence > 0.55:
            feedback = "Good Bakasana. Bring your knees higher on your arms and engage core."
        else:
            feedback = "Lean forward on hands, bend elbows, and tuck knees against arms."
        return confidence, feedback

    if pose_name == "Adho Mukha Svanasana":
        left_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        right_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee)
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        
        hip_score = ((1 - abs(90 - left_hip_angle) / 90) + (1 - abs(90 - right_hip_angle) / 90)) / 2
        knee_score = ((1 - abs(180 - left_knee) / 180) + (1 - abs(180 - right_knee) / 180)) / 2
        arm_score = ((1 - abs(180 - left_arm) / 180) + (1 - abs(180 - right_arm) / 180)) / 2
        
        confidence = clamp_score(hip_score * 0.50 + knee_score * 0.25 + arm_score * 0.25)
        
        if confidence > 0.8:
            feedback = "Excellent Downward-Facing Dog! Great inverted V shape with straight back."
        elif confidence > 0.65:
            feedback = "Good form. Try to push hips higher and straighten legs more."
        else:
            feedback = "Press hands down, lift hips to ceiling to form an inverted V shape."
        return confidence, feedback

    if pose_name == "Vasisthasana":
        left_torso = calculate_angle(l_shoulder, l_hip, l_knee)
        right_torso = calculate_angle(r_shoulder, r_hip, r_knee)
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        
        torso_score = max(1 - abs(180 - left_torso) / 180, 1 - abs(180 - right_torso) / 180)
        arm_score = ((1 - abs(180 - left_arm) / 180) + (1 - abs(180 - right_arm) / 180)) / 2
        confidence = clamp_score(torso_score * 0.60 + arm_score * 0.40)
        
        if confidence > 0.8:
            feedback = "Excellent Vasisthasana! Hip raised and arm straight."
        elif confidence > 0.60:
            feedback = "Good side plank. Keep your hips lifted and body aligned."
        else:
            feedback = "Turn to side, balance on one hand/foot, and raise the other arm."
        return confidence, feedback

    if pose_name in ["Step 1: Pranamasana", "Step 12: Pranamasana"]:
        left_body = calculate_angle(l_shoulder, l_hip, l_ankle)
        right_body = calculate_angle(r_shoulder, r_hip, r_ankle)
        left_score = 1 - abs(180 - left_body) / 180
        right_score = 1 - abs(180 - right_body) / 180
        hand_dist = np.linalg.norm(np.array(l_wrist) - np.array(r_wrist))
        hand_score = clamp_score(1.0 - hand_dist * 4)
        confidence = clamp_score(left_score * 0.35 + right_score * 0.35 + hand_score * 0.30)
        
        if confidence > 0.8:
            feedback = f"Excellent {pose_name}. Standing tall with hands in prayer position."
        elif confidence > 0.65:
            feedback = "Good. Keep your shoulders relaxed and hands centered."
        else:
            feedback = "Stand straight and bring your palms together in front of your chest."
        return confidence, feedback

    if pose_name in ["Step 2: Hasta Uttanasana", "Step 11: Hasta Uttanasana"]:
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        left_up = l_wrist[1] < l_shoulder[1]
        right_up = r_wrist[1] < r_shoulder[1]
        arm_score = ((1 - abs(180 - left_arm) / 180) + (1 - abs(180 - right_arm) / 180)) / 2
        raise_score = 1.0 if (left_up and right_up) else 0.0
        confidence = clamp_score(arm_score * 0.50 + raise_score * 0.50)
        
        if confidence > 0.8:
            feedback = f"Excellent {pose_name}. Arms raised high and fully extended."
        elif confidence > 0.6:
            feedback = "Good. Try to raise your arms higher and reach back slightly."
        else:
            feedback = "Inhale, raise your arms up towards the ceiling, and stretch back."
        return confidence, feedback

    if pose_name in ["Step 3: Padahastasana", "Step 10: Padahastasana"]:
        left_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        right_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee)
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        
        hip_flex = ((1 - abs(60 - left_hip_angle) / 180) + (1 - abs(60 - right_hip_angle) / 180)) / 2
        knee_score = ((1 - abs(180 - left_knee) / 180) + (1 - abs(180 - right_knee) / 180)) / 2
        confidence = clamp_score(hip_flex * 0.60 + knee_score * 0.40)
        
        if confidence > 0.8:
            feedback = f"Excellent {pose_name}. Deep forward fold with straight legs."
        elif confidence > 0.6:
            feedback = "Good fold. Bring your torso closer to your legs."
        else:
            feedback = "Exhale, bend forward from the hips, and reach down to touch your toes."
        return confidence, feedback

    if pose_name in ["Step 4: Ashwa Sanchalanasana", "Step 9: Ashwa Sanchalanasana"]:
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        bent_knee = min(left_knee, right_knee)
        straight_knee = max(left_knee, right_knee)
        
        bent_score = 1 - abs(90 - bent_knee) / 90
        straight_score = 1 - abs(150 - straight_knee) / 150
        confidence = clamp_score(bent_score * 0.50 + straight_score * 0.50)
        
        if confidence > 0.8:
            feedback = f"Excellent {pose_name}. Nice deep lunge, chest open and looking up."
        elif confidence > 0.6:
            feedback = "Good. Try to extend the back leg further and lower your hips."
        else:
            feedback = "Step one foot back, lower the knee to the floor, and bend front knee to 90 degrees."
        return confidence, feedback

    if pose_name == "Step 5: Dandasana":
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        left_torso = calculate_angle(l_shoulder, l_hip, l_knee)
        right_torso = calculate_angle(r_shoulder, r_hip, r_knee)
        
        arm_score = ((1 - abs(180 - left_arm) / 180) + (1 - abs(180 - right_arm) / 180)) / 2
        torso_score = ((1 - abs(180 - left_torso) / 180) + (1 - abs(180 - right_torso) / 180)) / 2
        confidence = clamp_score(arm_score * 0.40 + torso_score * 0.60)
        
        if confidence > 0.8:
            feedback = "Excellent Dandasana plank form! Body is in a straight line."
        elif confidence > 0.65:
            feedback = "Good plank. Keep your core engaged and body straight."
        else:
            feedback = "Keep a straight line from head to heels, and keep your elbows straight."
        return confidence, feedback

    if pose_name == "Step 6: Ashtanga Namaskara":
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        arm_score = ((1 - abs(90 - left_arm) / 90) + (1 - abs(90 - right_arm) / 90)) / 2
        hip_elevated = (l_hip[1] < l_shoulder[1]) and (l_hip[1] < l_knee[1])
        elevation_score = 1.0 if hip_elevated else 0.5
        confidence = clamp_score(arm_score * 0.50 + elevation_score * 0.50)
        
        if confidence > 0.8:
            feedback = "Excellent Ashtanga Namaskara. Knees, chest, and chin are down, hips elevated."
        elif confidence > 0.55:
            feedback = "Good. Try to elevate your hips slightly more and keep elbows close."
        else:
            feedback = "Lower your knees, chest, and chin to the mat, keeping hips elevated."
        return confidence, feedback

    if pose_name == "Step 7: Bhujangasana":
        left_back = calculate_angle(l_elbow, l_shoulder, l_hip)
        right_back = calculate_angle(r_elbow, r_shoulder, r_hip)
        chest_lift_score = ((1 - abs(140 - left_back) / 180) + (1 - abs(140 - right_back) / 180)) / 2
        shoulder_balance = 1 - abs(l_shoulder[1] - r_shoulder[1]) * 3
        confidence = clamp_score(chest_lift_score * 0.75 + clamp_score(shoulder_balance) * 0.25)
        
        if confidence > 0.78:
            feedback = "Excellent Bhujangasana. Chest lift and cobra stretch look great."
        elif confidence > 0.60:
            feedback = "Good cobra stretch. Lift chest higher and roll shoulders back."
        else:
            feedback = "Slide forward, lift your chest, and look up while keeping pelvis on mat."
        return confidence, feedback

    if pose_name == "Step 8: Adho Mukha Svanasana":
        left_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        right_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee)
        left_knee = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee = calculate_angle(r_hip, r_knee, r_ankle)
        left_arm = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_arm = calculate_angle(r_shoulder, r_elbow, r_wrist)
        
        hip_score = ((1 - abs(90 - left_hip_angle) / 90) + (1 - abs(90 - right_hip_angle) / 90)) / 2
        knee_score = ((1 - abs(180 - left_knee) / 180) + (1 - abs(180 - right_knee) / 180)) / 2
        arm_score = ((1 - abs(180 - left_arm) / 180) + (1 - abs(180 - right_arm) / 180)) / 2
        confidence = clamp_score(hip_score * 0.50 + knee_score * 0.25 + arm_score * 0.25)
        
        if confidence > 0.8:
            feedback = "Excellent Downward Dog. Great inverted V shape with straight back."
        elif confidence > 0.65:
            feedback = "Good Downward Dog. Try to push hips higher and straighten legs."
        else:
            feedback = "Press hands down, lift hips to ceiling to form an inverted V shape."
        return confidence, feedback

    return 0.0, "Pose not recognized."

def process_pose_frame(frame, selected_pose):
    image = frame.copy()
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pose_detector = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    results = pose_detector.process(rgb)

    confidence = 0.0
    feedback = "Waiting for full body detection..."

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )
        confidence, feedback = evaluate_pose(landmarks, selected_pose)

    pose_detector.close()
    return image, confidence, feedback
# ---------------------------------
# LOGIN + REGISTER PAGE
# ---------------------------------
def render_login_page():
    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown("""
        <div class="brand">
            <div class="brand-badge">🔐</div>
            <span>SecureUI</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="yoga-visual">
            <div class="floating-card card-1">🧘 Pose Analysis</div>
            <div class="floating-card card-2">✨ AI Guided Flow</div>
            <img class="hero-yoga-img" src="https://images.unsplash.com/photo-1545389336-cf090694435e?auto=format&fit=crop&w=900&q=80" alt="Yoga Pose Detection">
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="hero-small">Find balance within yourself.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">YOGA POSE DETECTION</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-desc">“Calm mind brings inner strength and self-confidence.”</div>', unsafe_allow_html=True)

        st.markdown('<div class="spacer-18"></div>', unsafe_allow_html=True)

        f1, f2, f3 = st.columns(3)
        with f1:
            st.markdown("""
            <div class="feature-item">
                <strong>Design</strong>
                <span>Yoga Pose Detection Preview.</span>
            </div>
            """, unsafe_allow_html=True)
        with f2:
            st.markdown("""
            <div class="feature-item">
                <strong>Create Account</strong>
                <span>Make your own account and login smoothly.</span>
            </div>
            """, unsafe_allow_html=True)
        with f3:
            st.markdown("""
            <div class="feature-item">
                <strong>Posture Accuracy</strong>
                <span>Helps maintain correct body alignment during yoga practice.</span>
            </div>
            """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="login-chip">LOGIN PAGE</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-heading">Welcome Back</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Create account first, then login to continue to your yoga dashboard.</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Create Account", "Sign In"])

        with tab1:
            new_email = st.text_input("Email Address", placeholder="Create email", key="register_email")
            
            # Email validation warning
            if new_email and not is_valid_email(new_email):
                if "@" not in new_email:
                    render_soft_box("⚠️ Enter a valid email address (must include @)", "warning")
                elif "." not in new_email:
                    render_soft_box("⚠️ Enter a valid email address (must include domain)", "warning")
                elif len(new_email) < 6:
                    render_soft_box("⚠️ Email address too short", "warning")
            
            new_password = st.text_input("Password", type="password", placeholder="Create password", key="register_password")
            render_password_categories(new_password)
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="register_confirm_password")

            if st.button("Create Account", use_container_width=True, key="create_account_btn"):
                if new_password != confirm_password:
                    st.session_state.register_error = "Passwords do not match."
                    st.session_state.register_success = ""
                else:
                    ok, msg = register_user(new_email, new_password)
                    if ok:
                        st.session_state.register_success = msg
                        st.session_state.register_error = ""
                    else:
                        st.session_state.register_error = msg
                        st.session_state.register_success = ""

            if st.session_state.register_error:
                render_soft_box(st.session_state.register_error, "danger")
            if st.session_state.register_success:
                render_soft_box(st.session_state.register_success, "success")

        with tab2:
            email = st.text_input("Email Address", placeholder="Enter your email", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

            st.markdown("""
            <div class="row-between">
                <div>Remember me</div>
                <a class="fake-link">Forgot Password?</a>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Sign In", use_container_width=True, key="signin_btn"):
                if login_user(email, password):
                    st.session_state.logged_in = True
                    st.session_state.current_user = email.strip().lower()
                    st.session_state.login_error = ""
                    st.session_state.chat_history = get_chat_history(st.session_state.current_user)
                    st.rerun()
                else:
                    st.session_state.login_error = "Invalid email or password."

            if st.session_state.login_error:
                render_soft_box(st.session_state.login_error, "danger")

        st.markdown('<div class="divider">or continue with</div>', unsafe_allow_html=True)

        social1, social2 = st.columns(2)
        with social1:
            st.button("Google", use_container_width=True, disabled=True, key="google_btn")
        with social2:
            st.button("GitHub", use_container_width=True, disabled=True, key="github_btn")

        st.markdown('<div class="login-help">Don’t have an account? <span>Create Account</span></div>', unsafe_allow_html=True)

# ---------------------------------
# YOGA APP PAGE
# ---------------------------------
def render_yoga_app():
    st.markdown("""
    <div class="title-box">
        <div class="section-title">🧘 Yoga Pose Detection Pro</div>
        <div class="muted">
            Calm mind. Strong posture. Smart guided yoga flow with automatic pose capture and analysis.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("## ✨ Yoga Control Panel")
    if st.session_state.current_user:
        st.sidebar.markdown(f"**Logged in:** {st.session_state.current_user}")
    st.sidebar.button("🚪 Logout", on_click=do_logout)

    CATEGORIES = {
        "Meditation": ["Padmasana", "Swastikasana", "Vajrasana"],
        "Sitting Asana": ["Butterfly Pose", "Cobra Pose", "Gomukhasana", "Ardha Matsyendrasana", "Janu Shirshasana", "Paschimottanasana"],
        "Standing asana / leg focused asana": ["Mountain Pose", "Tree Pose", "Warrior II", "Tadasana", "Trikonasana", "Utkatasana", "Virabhadrasana I", "Virabhadrasana II", "Vrikshasana", "Malasana", "Natarajasana"],
        "Hand/Arm-Focused Asanas": ["Phalakasana (Plank)", "Chaturanga Dandasana", "Bakasana", "Adho Mukha Svanasana", "Vasisthasana"],
        "Surya Namaskar (12 Steps)": [
            "Step 1: Pranamasana",
            "Step 2: Hasta Uttanasana",
            "Step 3: Padahastasana",
            "Step 4: Ashwa Sanchalanasana",
            "Step 5: Dandasana",
            "Step 6: Ashtanga Namaskara",
            "Step 7: Bhujangasana",
            "Step 8: Adho Mukha Svanasana",
            "Step 9: Ashwa Sanchalanasana",
            "Step 10: Padahastasana",
            "Step 11: Hasta Uttanasana",
            "Step 12: Pranamasana"
        ]
    }

    current_cat = list(CATEGORIES.keys())[0]
    for cat, poses_list in CATEGORIES.items():
        if st.session_state.selected_pose_name in poses_list:
            current_cat = cat
            break

    selected_category = st.sidebar.selectbox(
        "Select Category",
        list(CATEGORIES.keys()),
        index=list(CATEGORIES.keys()).index(current_cat)
    )

    available_poses = CATEGORIES[selected_category]
    default_pose_idx = 0
    if st.session_state.selected_pose_name in available_poses:
        default_pose_idx = available_poses.index(st.session_state.selected_pose_name)

    selected_pose_name = st.sidebar.selectbox(
        "Select Pose",
        available_poses,
        index=default_pose_idx
    )
    st.session_state.selected_pose_name = selected_pose_name

    capture_interval = st.sidebar.slider("Auto Capture Interval (sec)", 5, 60, st.session_state.capture_interval)
    st.session_state.capture_interval = capture_interval

    total_shots = st.sidebar.slider("Total Shots", 1, 30, st.session_state.total_shots)
    st.session_state.total_shots = total_shots

    st.sidebar.markdown("### 🔊 Voice Assistant")
    voice_tab_eng, voice_tab_hin = st.sidebar.tabs(["English 🇬🇧", "Hindi 🇮🇳"])
    
    with voice_tab_eng:
        col_eng_play, col_eng_stop = st.columns(2)
        if col_eng_play.button("🔊 Play (EN)", use_container_width=True, key="play_en_sidebar"):
            st.session_state.voice_language = "English"
            text = build_voice_text(selected_pose_name, "English")
            speak_async(text, "English")
        if col_eng_stop.button("⏹ Stop (EN)", use_container_width=True, key="stop_en_sidebar"):
            stop_voice()
            
    with voice_tab_hin:
        col_hin_play, col_hin_stop = st.columns(2)
        if col_hin_play.button("🔊 Play (HI)", use_container_width=True, key="play_hi_sidebar"):
            st.session_state.voice_language = "Hindi"
            text = build_voice_text(selected_pose_name, "Hindi")
            speak_async(text, "Hindi")
        if col_hin_stop.button("⏹ Stop (HI)", use_container_width=True, key="stop_hi_sidebar"):
            stop_voice()

    live_voice = st.sidebar.checkbox(
        "🗣 Real-time Voice Feedback",
        value=st.session_state.get("live_voice_enabled", False),
        key="live_voice_checkbox_sidebar"
    )
    st.session_state.live_voice_enabled = live_voice

    pose_info = POSES[selected_pose_name]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><h4>Selected Pose</h4><h3>{selected_pose_name}</h3></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><h4>Live Accuracy</h4><h3>{st.session_state.latest_confidence * 100:.1f}%</h3></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><h4>Pose Grade</h4><h3>{st.session_state.latest_grade}</h3></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-box"><h4>Snapshots</h4><h3>{st.session_state.snapshot_count}</h3></div>', unsafe_allow_html=True)

    st.markdown('<div class="spacer-18"></div>', unsafe_allow_html=True)

    left, right = st.columns([1.05, 1.25], gap="large")

    with left:
        st.markdown("## 📸 Reference Pose Gallery")
        images = load_existing_images(pose_info.image_paths, selected_pose_name)
        if images:
            cols = st.columns(min(len(images), 2))
            for i, img in enumerate(images[:2]):
                with cols[i % 2]:
                    st.image(img, use_container_width=True)
        else:
            render_soft_box("Reference images not found. Add the image files in the same folder as yoga_pose.py.", "warning")

        st.markdown(f"### {pose_info.name}")
        st.write(pose_info.description)

        with st.expander("🪜 Steps to Perform", expanded=False):
            for i, step in enumerate(pose_info.steps, start=1):
                st.markdown(f"""
                <div class="small-card">
                    <b>Step {i}</b><br>{step}
                </div>
                """, unsafe_allow_html=True)

        with st.expander("🌿 Benefits", expanded=False):
            for benefit in pose_info.benefits:
                st.markdown(f"- {benefit}")

        with st.expander("💡 Tips", expanded=False):
            for tip in pose_info.tips:
                st.markdown(f'<span class="badge">{tip}</span>', unsafe_allow_html=True)

    with right:
        st.markdown("## 🎥 Live Pose Detection")
        render_soft_box("Start auto capture below. Full body frame me rakho for better accuracy.", "info")

        preview_placeholder = st.empty()
        countdown_placeholder = st.empty()
        metric_placeholder = st.empty()

        col_btn1, col_btn2 = st.columns(2)
        start_capture = col_btn1.button("▶ Start Auto Capture", use_container_width=True)
        stop_capture = col_btn2.button("■ Stop", use_container_width=True)

        if stop_capture:
            st.session_state.capturing_now = False
            stop_voice()

        if start_capture:
            st.session_state.capturing_now = True
            st.session_state.saved_snapshots = []
            st.session_state.snapshot_count = 0

        if st.session_state.get("capturing_now", False):
            cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                render_soft_box("Webcam open nahi ho rahi.", "danger")
                st.session_state.capturing_now = False
            else:
                selected_pose = st.session_state.selected_pose_name
                total = st.session_state.total_shots
                interval = st.session_state.capture_interval

                for shot_num in range(total):
                    if not st.session_state.capturing_now:
                        break

                    for sec in range(interval, 0, -1):
                        ret, frame = cap.read()
                        if not ret:
                            render_soft_box("Camera frame read nahi ho raha.", "danger")
                            st.session_state.capturing_now = False
                            break

                        frame = cv2.flip(frame, 1)
                        frame = cv2.resize(frame, (640, 480))
                        display_frame = frame.copy()

                        cv2.rectangle(display_frame, (15, 15), (340, 90), (255, 255, 255), -1)
                        cv2.putText(
                            display_frame,
                            f"Capture in: {sec}s",
                            (30, 58),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 120, 255),
                            2
                        )

                        preview_placeholder.image(
                            cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB),
                            use_container_width=True
                        )
                        countdown_placeholder.markdown(
                            f'<div class="soft-warning">Shot {shot_num + 1}/{total} • Next capture in {sec} sec</div>',
                            unsafe_allow_html=True
                        )
                        time.sleep(1)

                    if not st.session_state.capturing_now:
                        break

                    ret, frame = cap.read()
                    if not ret:
                        render_soft_box("Capture image nahi ho paayi.", "danger")
                        break

                    frame = cv2.flip(frame, 1)
                    frame = cv2.resize(frame, (640, 480))

                    processed_frame, confidence, feedback = process_pose_frame(frame, selected_pose)

                    st.session_state.latest_confidence = confidence
                    st.session_state.latest_feedback = feedback
                    st.session_state.latest_grade = grade_label(confidence)

                    if st.session_state.get("live_voice_enabled", False) and feedback:
                        speak_async(feedback, st.session_state.voice_language)

                    save_pose_history(
                        st.session_state.current_user,
                        selected_pose,
                        float(confidence * 100),
                        st.session_state.latest_grade,
                        feedback
                    )

                    snapshot_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    st.session_state.saved_snapshots.append(snapshot_rgb)
                    st.session_state.saved_snapshots = st.session_state.saved_snapshots[-12:]
                    st.session_state.snapshot_count += 1

                    preview_placeholder.image(snapshot_rgb, use_container_width=True)
                    countdown_placeholder.markdown(
                        f'<div class="soft-success">Captured Shot {shot_num + 1}/{total}</div>',
                        unsafe_allow_html=True
                    )
                    with metric_placeholder.container():
                        st.progress(float(confidence))
                        st.write(f"**Accuracy:** {confidence * 100:.1f}%")
                        st.write(f"**Grade:** {st.session_state.latest_grade}")

                        if confidence >= pose_info.confidence_threshold:
                            render_soft_box(feedback, "success")
                        elif confidence > 0:
                            render_soft_box(feedback, "warning")
                        else:
                            render_soft_box("Pose detect nahi hua. Full body frame me lao.", "info")

                    time.sleep(1)

                cap.release()
                st.session_state.capturing_now = False

        if not st.session_state.capturing_now and st.session_state.snapshot_count == 0:
            st.caption(
                f"Interval: {st.session_state.capture_interval} sec • Total Shots: {st.session_state.total_shots}"
            )
            render_soft_box("Auto capture start karne ke liye button dabao.", "info")

        st.markdown('<div class="spacer-12"></div>', unsafe_allow_html=True)

        st.markdown("## 🧠 Smart Feedback Panel")
        progress_val = float(st.session_state.latest_confidence)
        accuracy_pct = st.session_state.latest_confidence * 100

        if accuracy_pct >= 80:
            acc_color = "#22c55e"
        elif accuracy_pct >= 60:
            acc_color = "#f59e0b"
        else:
            acc_color = "#ef4444"

        st.markdown(f"""
        <div class="feedback-glass">
            <div class="feedback-row">
                <div class="feedback-mini">
                    <h4>Accuracy</h4>
                    <p style="color:{acc_color} !important;">{accuracy_pct:.1f}%</p>
                </div>
                <div class="feedback-mini">
                    <h4>Grade</h4>
                    <p>{st.session_state.latest_grade}</p>
                </div>
                <div class="feedback-mini">
                    <h4>Pose</h4>
                    <p>{selected_pose_name}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if progress_val >= 0.8:
            st.markdown("""
            <div class="small-card">
                <b>Status:</b> Excellent form<br>
                <b>Advice:</b> Hold the pose steadily and breathe naturally.
            </div>
            """, unsafe_allow_html=True)
        elif progress_val >= 0.6:
            st.markdown("""
            <div class="small-card">
                <b>Status:</b> Good attempt<br>
                <b>Advice:</b> Minor corrections needed for stronger alignment.
            </div>
            """, unsafe_allow_html=True)
        elif progress_val > 0:
            st.markdown("""
            <div class="small-card">
                <b>Status:</b> Needs correction<br>
                <b>Advice:</b> Follow the steps carefully and align your posture with the reference image.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="small-card">
                <b>Status:</b> Waiting for detection<br>
                <b>Advice:</b> Press Start Auto Capture and keep your full body visible.
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="spacer-18"></div>', unsafe_allow_html=True)

    col_gal, col_clr = st.columns([3.5, 1])
    with col_gal:
        st.markdown("## 🖼 Auto Capture Gallery")
    with col_clr:
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        if st.button("🗑 Clear Snapshots", key="gallery_clear_btn", use_container_width=True):
            st.session_state.saved_snapshots = []
            st.session_state.snapshot_count = 0
            st.session_state.latest_confidence = 0.0
            st.session_state.latest_feedback = "Waiting for pose..."
            st.session_state.latest_grade = "Not Ready"
            st.rerun()
    if st.session_state.saved_snapshots:
        cols = st.columns(3)
        for i, snap in enumerate(reversed(st.session_state.saved_snapshots)):
            with cols[i % 3]:
                st.image(snap, use_container_width=True, caption=f"Snapshot {len(st.session_state.saved_snapshots) - i}")
    else:
        render_soft_box("No snapshots yet. Start auto capture to generate your pose gallery.", "info")

    st.markdown("## 📜 Previous Score History")
    history_rows = get_user_history(st.session_state.current_user, limit=8)

    if history_rows:
        for row in history_rows:
            pose_name, accuracy, grade, feedback, created_at = row
            st.markdown(f"""
            <div class="small-card">
                <b>{pose_name}</b><br>
                Accuracy: {accuracy:.1f}%<br>
                Grade: {grade}<br>
                Feedback: {feedback}<br>
                Time: {created_at}
            </div>
            """, unsafe_allow_html=True)
    else:
        render_soft_box("No previous history yet. Start capture to save your scores.", "info")

    st.markdown("""
    <div class="footer-note">
        Yoga Pose Detection Pro • Built with Streamlit, MediaPipe, OpenCV, and Python
    </div>
    """, unsafe_allow_html=True)
    
    render_chatbot()

def get_bot_response(user_input: str) -> str:
    user_input = user_input.lower()
    
    # 1. Dynamic search against the entire POSES database!
    # If the user asks about ANY pose we have in our code, the bot will teach them.
    for pose_name, pose_info in POSES.items():
        name_lower = pose_name.lower()
        keywords = [name_lower]
        
        # Split names with parentheses (e.g. "Phalakasana (Plank)")
        if "(" in name_lower:
            parts = name_lower.replace(")", "").split("(")
            for p in parts:
                k = p.strip()
                if k and not k.startswith("step"):
                    keywords.append(k)
        # Handle "Step 1: Pranamasana" format
        elif ":" in name_lower:
            keywords.append(name_lower.split(":")[1].strip())
            
        # Add version without the word "pose" (e.g., "Butterfly")
        for k in list(keywords):
            if k.endswith(" pose"):
                keywords.append(k.replace(" pose", "").strip())

        # Check if any keyword matches
        for k in keywords:
            if len(k) > 3 and k in user_input:
                response = f"### 🧘 **{pose_info.name}**\n\n"
                if pose_info.description:
                    response += f"*{pose_info.description}*\n\n"
                
                if pose_info.steps:
                    response += "**👣 Steps:**\n"
                    for i, step in enumerate(pose_info.steps, 1):
                        response += f"{i}. {step}\n"
                    response += "\n"
                    
                if pose_info.tips:
                    response += "**💡 Pro Tips:**\n"
                    for tip in pose_info.tips:
                        response += f"- {tip}\n"
                    response += "\n"
                    
                if pose_info.benefits:
                    response += "**✨ Benefits:**\n"
                    for benefit in pose_info.benefits:
                        response += f"- {benefit}\n"
                        
                return response.strip()

    # 2. General Fallback Rules
    if "surya" in user_input or "namaskar" in user_input or "sun salutation" in user_input:
        return "Surya Namaskar (Sun Salutation) is extremely helpful for full-body flexibility and energy! It is a powerful sequence of 12 yoga poses. You should aim to do it at least 5 to 6 times a day, ideally early in the morning facing the sun. You can ask me for the steps of any specific step, like 'Pranamasana' or 'Ashwa Sanchalanasana'!"
    elif "weight" in user_input or "fat" in user_input or "calories" in user_input:
        return "For weight loss and burning belly fat, active poses work best! Try Surya Namaskar (Sun Salutation) daily, along with Phalakasana (Plank), Chaturanga Dandasana, and Warrior poses (Virabhadrasana). Consistency is key!"
    elif "stress" in user_input or "anxiety" in user_input or "tension" in user_input or "relax" in user_input:
        return "For stress and anxiety, I highly recommend Balasana (Child's Pose), Shavasana (Corpse Pose), and simple Meditation (Padmasana). Deep breathing (Pranayama) while sitting calmly will instantly soothe your nervous system."
    elif "back pain" in user_input or "backache" in user_input or "back" in user_input or "spine" in user_input:
        return "To help with back pain, gentle stretching is best. Try Bhujangasana (Cobra Pose) for lower back strength, and Marjaryasana-Bitilasana (Cat-Cow). Important: avoid twisting too hard if the pain is severe!"
    elif "sleep" in user_input or "insomnia" in user_input or "night" in user_input:
        return "To improve sleep quality, practice relaxing poses right before bed. Viparita Karani (Legs-Up-The-Wall), Janu Shirshasana (Head-to-Knee Forward Bend), and a 5-minute Shavasana work wonders."
    elif "core" in user_input or "abs" in user_input or "belly" in user_input or "strength" in user_input:
        return "For building a rock-solid core, Phalakasana (Plank), Vasisthasana (Side Plank), and Navasana (Boat Pose) are highly effective. Hold them for 30-60 seconds for maximum benefit."
    elif "flexibility" in user_input or "stretch" in user_input or "stiff" in user_input:
        return "To improve flexibility and open up stiff muscles, practice Paschimottanasana (Seated Forward Bend), Trikonasana (Triangle Pose), and Adho Mukha Svanasana (Downward Dog) daily."
    elif "digestion" in user_input or "stomach" in user_input or "gas" in user_input or "bloat" in user_input:
        return "For better digestion, Vajrasana (Thunderbolt Pose) is excellent right after meals! Pavanamuktasana (Wind-Relieving Pose) is also great for releasing trapped gas and bloating."
    elif "hi" in user_input or "hello" in user_input or "hey" in user_input or "namaste" in user_input:
        return "Namaste! 🙏 I'm your Yoga Assistant. You can ask me for the **steps, tips, or benefits of ANY yoga pose** in the app! For example, try asking: 'How to do Plank pose?' or 'Steps for Downward Dog'."
    elif "thank" in user_input:
        return "You're very welcome! Keep practicing and stay healthy. Namaste. 🧘‍♀️"
    else:
        return "I'm your Yoga Assistant! Try asking me for the **steps to any pose** (e.g., 'How to do Warrior II' or 'Teach me Cobra Pose'), or ask about general topics like Stress, Back pain, or Flexibility!"

def render_chatbot():
    def submit_chat():
        val = st.session_state.get("chat_input_widget", "")
        if val:
            # 1. Add and save User msg
            st.session_state.chat_history.append({"role": "user", "content": val})
            if st.session_state.current_user:
                save_chat_message(st.session_state.current_user, "user", val)
                
            # 2. Get Bot reply
            bot_reply = get_bot_response(val)
            
            # 3. Add and save Bot msg
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
            if st.session_state.current_user:
                save_chat_message(st.session_state.current_user, "assistant", bot_reply)
                
            st.session_state.chat_input_widget = ""

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 Yoga Assistant")
        st.markdown("<p style='font-size:13px; color:#94a3b8; margin-top:-10px;'>Ask about poses, steps, tips, or benefits.</p>", unsafe_allow_html=True)
        
        # Create a container for the chat history
        chat_container = st.container(height=350)
        
        with chat_container:
            if not st.session_state.chat_history:
                st.info("Say hello to start chatting!")
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # Use a standard text input instead of chat_input so it renders reliably exactly here.
        st.text_input("Type your message and press Enter:", key="chat_input_widget", on_change=submit_chat, placeholder="e.g. 'How to do Plank?'")

# ---------------------------------
# ROUTER
# ---------------------------------
if st.session_state.logged_in:
    render_yoga_app()
else: 
    render_login_page()

