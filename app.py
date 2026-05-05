import streamlit as st
from ai_core import run_ai

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- MODERN CAFE UI ----------------
st.markdown("""
<style>

/* Hide Streamlit UI */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

/* 🌟 Warm Café Background */
.stApp {
    background: linear-gradient(135deg, #fdf6f0, #f7e7dc, #f3d9c9);
    font-family: 'Segoe UI', sans-serif;
}

/* Layout */
.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1200px;
}

/* HERO */
.hero {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(10px);
    padding: 55px 30px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    margin-top: 20px;
}

.hero h1 {
    font-size: 58px;
    color: #c0392b;
    font-weight: 800;
}

.hero h2 {
    font-size: 22px;
    color: #333;
    margin-top: 5px;
}

.hero p {
    font-size: 16px;
    color: #555;
    max-width: 800px;
    margin: auto;
    line-height: 1.6;
}

/* Buttons */
div.stButton > button {
    height: 55px;
    width: 220px;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    background: #2c2a28;
    color: white;
    border: none;
    transition: 0.2s;
}

div.stButton > button:hover {
    background: #c0392b;
    transform: translateY(-2px);
}

/* login row */
.login-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 25px;
    flex-wrap: wrap;
}

/* SECTION */
.section {
    background: rgba(255,255,255,0.8);
    padding: 40px 25px;
    margin-top: 25px;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    text-align: center;
}

.section h2 {
    font-size: 28px;
    color: #c0392b;
}

.section p {
    font-size: 16px;
    color: #555;
    max-width: 750px;
    margin: auto;
    line-height: 1.6;
}

/* INPUT */
.stTextInput > div > div > input {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("""
<div class="hero">
    <h1>BART (بارت)</h1>
    <h2>Coffee, French Toast & Fresh Bites in Jeddah</h2>
    <p>
        A Saudi café brand specializing in specialty coffee, desserts, and fresh snacks.<br>
        Signature items: Dubai Chocolate Pudding, Nutella French Toast, signature drinks.<br><br>
        📍 Jeddah Branches: Al Rahman, Al-Safa<br>
        🌐 bart.sa
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------- LOGIN BUTTONS ----------------
st.markdown('<div class="login-buttons">', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard.py")

with col3:
    if st.button("Manager Login"):
        st.switch_page("pages/manager_dashboard.py")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- AI ----------------
st.sidebar.markdown("### 🤖 AI Assistant")
query = st.sidebar.text_input("Ask AI")

if query:
    context = {"revenue": 0, "items": 0, "sales": []}
    st.sidebar.success(run_ai(query, context))

# ---------------- CHAT ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

user_input = st.text_input("Talk to AI...")

if user_input:
    context = {
        "revenue": 0,
        "items": 0,
        "sales": st.session_state.get("pending_sales", [])
    }

    response = run_ai(user_input, context)

    st.session_state.chat.append(("You", user_input))
    st.session_state.chat.append(("AI", response))

for sender, msg in st.session_state.chat[-10:]:
    st.write(f"**{sender}:** {msg}")

# ---------------- INFO ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax in a cozy café environment with fast service and premium coffee experience.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="section">
<h2>Visit Us</h2>
<p>Find us in Jeddah or visit <a href="https://bart.sa" target="_blank">bart.sa</a></p>
</div>
""", unsafe_allow_html=True)
