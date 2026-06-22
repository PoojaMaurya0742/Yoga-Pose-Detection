import sys

with open("yoga_pose_updated.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the end of defaults loop (line 71)
start_idx = 0
for i, line in enumerate(lines):
    if "st.session_state[key] = value" in line:
        start_idx = i + 1
        break

# Find the VOICE section (line 496)
end_idx = 0
for i in range(start_idx, len(lines)):
    if "# VOICE" in lines[i]:
        end_idx = i - 1  # Keep the # --------- line above it
        break

new_content = """# ---------------------------------
# GLOBAL CSS & THEME
# ---------------------------------
def get_theme_css(theme: str) -> str:
    if theme == "light":
        return \"\"\"
<style>
div[data-baseweb="select"], div[data-baseweb="select"] * { cursor: pointer !important; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stAppViewContainer"], .stApp {
    background: radial-gradient(circle at top left, rgba(139, 92, 246, 0.1), transparent 28%),
                radial-gradient(circle at bottom right, rgba(6, 182, 212, 0.1), transparent 24%),
                linear-gradient(135deg, #f8fafc, #f1f5f9) !important;
    color: #0f172a !important;
}
.main { background: transparent !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
h1, h2, h3, h4, h5, h6 { color: #0f172a !important; }
p, li, label, span, div { color: inherit; }
.stMarkdown p, .stMarkdown li { color: #334155 !important; }
div.stButton > button {
    width: 100%; border-radius: 16px; border: none; padding: 12px 16px; font-weight: 700;
    color: white !important; background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    box-shadow: 0 8px 16px rgba(104, 92, 246, 0.2); cursor: pointer;
}
div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 12px 20px rgba(104, 92, 246, 0.25); }
.stSidebar { background: rgba(255,255,255,0.7) !important; border-right: 1px solid rgba(0,0,0,0.05); }
section[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, rgba(139,92,246,0.05), rgba(6,182,212,0.05)), rgba(255, 255, 255, 0.9);
}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p {
    color: #0f172a !important;
}
div[data-baseweb="select"] > div, .stTextInput > div > div > input, .stNumberInput input {
    background: #ffffff !important; color: #000000 !important;
    -webkit-text-fill-color: #000000 !important; caret-color: #000000 !important;
    border-radius: 14px !important; border: 1px solid rgba(0,0,0,0.15) !important;
}
.stTextInput input::placeholder { color: #94a3b8 !important; -webkit-text-fill-color: #94a3b8 !important; }
.stSlider > div[data-baseweb="slider"] { color: #8b5cf6 !important; }
.stProgress > div > div > div > div { background: linear-gradient(90deg, #8b5cf6, #06b6d4) !important; }
img { border-radius: 18px !important; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 12px 28px rgba(0,0,0,0.08); }
.title-box { padding: 20px 24px; border-radius: 24px; background: rgba(255,255,255,0.9); border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 8px 32px rgba(0,0,0,0.05); text-align: center; margin-bottom: 25px; }
.stat-card { background: rgba(255,255,255,0.9); border: 1px solid rgba(0,0,0,0.05); border-radius: 20px; padding: 20px; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,0.05); }
.stat-value { font-size: 36px; font-weight: 800; background: linear-gradient(135deg, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 5px 0; }
.stat-label { font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.camera-container { background: #ffffff; padding: 12px; border-radius: 24px; box-shadow: 0 16px 40px rgba(0,0,0,0.1); border: 1px solid rgba(0,0,0,0.05); margin-bottom: 20px; }
.login-shell { background: rgba(255,255,255,0.95); border-radius: 30px; box-shadow: 0 24px 50px rgba(0,0,0,0.1); border: 1px solid rgba(0,0,0,0.05); }
.login-heading { font-size: 42px; font-weight: 800; color: #0f172a; margin-bottom: 10px; }
.hero-title { font-size: 52px; font-weight: 800; line-height: 1.1; margin-bottom: 20px; background: linear-gradient(to right, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-subtitle { font-size: 20px; color: #475569; line-height: 1.6; margin-bottom: 30px; }
.feature-item { font-size: 16px; color: #334155; margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
.success-msg { color: #10b981; font-weight: 600; background: rgba(16, 185, 129, 0.1); padding: 10px 15px; border-radius: 10px; border-left: 4px solid #10b981; margin-top: 10px; }
.error-msg { color: #ef4444; font-weight: 600; background: rgba(239, 68, 68, 0.1); padding: 10px 15px; border-radius: 10px; border-left: 4px solid #ef4444; margin-top: 10px; }
.login-btn { width: 100%; border-radius: 12px; border: none; padding: 12px; font-weight: 700; color: white; background: linear-gradient(135deg, #1e293b, #334155); cursor: pointer; box-shadow: 0 4px 12px rgba(15,23,42,0.1); }
.info-box { background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 8px; color: #1e40af; margin-bottom: 15px; font-size: 15px; }
.warning-box { background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 8px; color: #92400e; margin-bottom: 15px; font-size: 15px; }
.success-box { background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 8px; color: #065f46; margin-bottom: 15px; font-size: 15px; }
.score-green { color: #10b981; font-weight: 800; font-size: 1.2em; }
.score-orange { color: #f59e0b; font-weight: 800; font-size: 1.2em; }
.score-red { color: #ef4444; font-weight: 800; font-size: 1.2em; }
div[data-testid="stExpander"] { background: rgba(255, 255, 255, 0.8) !important; border-radius: 12px !important; border: 1px solid rgba(0,0,0,0.1) !important; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
div[data-testid="stExpander"] summary { background: transparent !important; color: #0f172a !important; }
div[data-testid="stExpander"] summary:hover { background: rgba(0, 0, 0, 0.03) !important; color: #0f172a !important; }
div[data-testid="stExpander"] summary p { color: #0f172a !important; font-weight: 600 !important; }
div[data-testid="stExpanderDetails"] { color: #334155 !important; }
@media (max-width: 768px) {
    .login-shell { grid-template-columns: 1fr; }
    .hero-title { font-size: 38px; }
    .login-heading { font-size: 34px; }
    .feedback-row { grid-template-columns: 1fr; }
}
</style>\"\"\"
    else:
        return \"\"\"
<style>
div[data-baseweb="select"], div[data-baseweb="select"] * { cursor: pointer !important; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stAppViewContainer"], .stApp {
    background: radial-gradient(circle at top left, rgba(139, 92, 246, 0.28), transparent 28%),
                radial-gradient(circle at bottom right, rgba(6, 182, 212, 0.22), transparent 24%),
                linear-gradient(135deg, #0f172a, #111827) !important;
    color: #ffffff !important;
}
.main { background: transparent !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }
p, li, label, span, div { color: inherit; }
.stMarkdown p, .stMarkdown li { color: #e5e7eb !important; }
div.stButton > button {
    width: 100%; border-radius: 16px; border: none; padding: 12px 16px; font-weight: 700;
    color: white !important; background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    box-shadow: 0 14px 28px rgba(104, 92, 246, 0.32); cursor: pointer;
}
div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 18px 30px rgba(104, 92, 246, 0.38); }
.stSidebar { background: rgba(255,255,255,0.04) !important; border-right: 1px solid rgba(255,255,255,0.08); }
section[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, rgba(139,92,246,0.12), rgba(6,182,212,0.04)), rgba(15, 23, 42, 0.92);
}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p {
    color: #ffffff !important;
}
div[data-baseweb="select"] > div, .stTextInput > div > div > input, .stNumberInput input {
    background: rgba(255,255,255,0.95) !important; color: #000000 !important;
    -webkit-text-fill-color: #000000 !important; caret-color: #000000 !important;
    border-radius: 14px !important; border: 1px solid rgba(255,255,255,0.18) !important;
}
.stTextInput input::placeholder { color: #64748b !important; -webkit-text-fill-color: #64748b !important; }
.stTextInput label, .stTextInput p, label { color: #e5e7eb !important; }
.stSlider > div[data-baseweb="slider"] { color: #8b5cf6 !important; }
.stProgress > div > div > div > div { background: linear-gradient(90deg, #8b5cf6, #06b6d4) !important; }
img { border-radius: 18px !important; border: 1px solid rgba(255,255,255,0.10); box-shadow: 0 12px 28px rgba(0,0,0,0.22); }
.title-box { padding: 20px 24px; border-radius: 24px; background: rgba(255,255,255,0.08); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.12); box-shadow: 0 8px 32px rgba(0,0,0,0.15); text-align: center; margin-bottom: 25px; }
.stat-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 20px; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
.stat-value { font-size: 36px; font-weight: 800; background: linear-gradient(135deg, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 5px 0; }
.stat-label { font-size: 14px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.camera-container { background: #000000; padding: 12px; border-radius: 24px; box-shadow: 0 16px 40px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px; }
.login-shell { background: rgba(255,255,255,0.03); backdrop-filter: blur(16px); border-radius: 30px; box-shadow: 0 24px 50px rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); }
.login-heading { font-size: 42px; font-weight: 800; color: #ffffff; margin-bottom: 10px; }
.hero-title { font-size: 52px; font-weight: 800; line-height: 1.1; margin-bottom: 20px; background: linear-gradient(to right, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-subtitle { font-size: 20px; color: #cbd5e1; line-height: 1.6; margin-bottom: 30px; }
.feature-item { font-size: 16px; color: #94a3b8; margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
.success-msg { color: #10b981; font-weight: 600; background: rgba(16, 185, 129, 0.15); padding: 10px 15px; border-radius: 10px; border-left: 4px solid #10b981; margin-top: 10px; }
.error-msg { color: #ef4444; font-weight: 600; background: rgba(239, 68, 68, 0.15); padding: 10px 15px; border-radius: 10px; border-left: 4px solid #ef4444; margin-top: 10px; }
.login-btn { width: 100%; border-radius: 12px; border: none; padding: 12px; font-weight: 700; color: white; background: linear-gradient(135deg, #1e293b, #334155); cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.info-box { background: rgba(59, 130, 246, 0.15); border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 8px; color: #93c5fd; margin-bottom: 15px; font-size: 15px; }
.warning-box { background: rgba(245, 158, 11, 0.15); border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 8px; color: #fcd34d; margin-bottom: 15px; font-size: 15px; }
.success-box { background: rgba(16, 185, 129, 0.15); border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 8px; color: #6ee7b7; margin-bottom: 15px; font-size: 15px; }
.score-green { color: #10b981; font-weight: 800; font-size: 1.2em; }
.score-orange { color: #f59e0b; font-weight: 800; font-size: 1.2em; }
.score-red { color: #ef4444; font-weight: 800; font-size: 1.2em; }
div[data-testid="stExpander"] { background: rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
div[data-testid="stExpander"] summary { background: transparent !important; color: #ffffff !important; }
div[data-testid="stExpander"] summary:hover { background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; }
div[data-testid="stExpander"] summary p { color: #ffffff !important; font-weight: 600 !important; }
div[data-testid="stExpanderDetails"] { color: #e5e7eb !important; }
@media (max-width: 768px) {
    .login-shell { grid-template-columns: 1fr; }
    .hero-title { font-size: 38px; }
    .login-heading { font-size: 34px; }
    .feedback-row { grid-template-columns: 1fr; }
}
</style>\"\"\"

# Render Theme CSS
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# THEME TOGGLE BUTTON AT TOP RIGHT
t_col1, t_col2 = st.columns([0.88, 0.12])
with t_col2:
    btn_icon = "☀️ Light" if st.session_state.theme == "dark" else "🌙 Dark"
    if st.button(f"{btn_icon}", key="theme_toggle"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
"""

new_lines = lines[:start_idx] + [new_content + "\\n"] + lines[end_idx:]

with open("yoga_pose_updated.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("File successfully patched!")
