import streamlit as st
from ai_core import run_ai

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- MODERN BRAND UI ----------------
st.markdown("""
<style>

/* Hide Streamlit default UI */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

/* Background */
.stApp {
    background: linear-gradient(135deg, #F7F1EA, #FFFFFF);
    font-family: 'Segoe UI', sans-serif;
}

/* Layout */
.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1200px;
}

/* HERO */
.hero {
    background: linear-gradient(135deg, #FFFFFF, #F7F1EA);
    padding: 70px 35px;
    border-radius: 28px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
    margin-top: 20px;
    position: relative;
    overflow: hidden;
}

/* glow effects */
.hero::before {
    content: "";
    position: absolute;
    width: 320px;
    height: 320px;
    background: rgba(192,57,43,0.08);
    border-radius: 50%;
    top: -100px;
    left: -100px;
    filter: blur(20px);
}

.hero::after {
    content: "";
    position: absolute;
    width: 280px;
    height: 280px;
    background: rgba(230,177,126,0.08);
    border-radius: 50%;
    bottom: -100px;
    right: -100px;
    filter: blur(25px);
}

/* BART title */
.hero h1 {
    font-size: 74px;
    font-weight: 900;
    letter-spacing: 10px;
    color: #C0392B;
    margin-bottom: 10px;
}

/* subtitle */
.hero h2 {
    font-size: 22px;
    color: #2C2A28;
    font-weight: 600;
    margin-bottom: 15px;
}

/* paragraph */
.hero p {
    font-size: 16px;
    color: #555;
    max-width: 800px;
    margin: auto;
    line-height: 1.7;
}

/* LOGIN BUTTON ROW */
.login-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 30px;
    flex-wrap: wrap;
}

/* BUTTON STYLE */
div.stButton > button {
    height: 55px;
    width: 220px;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    background: #2C2A28;
    color: white;
    border: none;
    transition: 0.2s;
}

div.stButton > button:hover {
    background: #C0392B;
    transform: translateY(-2px);
}

/* SECTION BOX */
.section {
    background: rgba(255,255,255,0.85);
    padding: 40px 25px;
    margin-top: 25px;
    border-radius: 18px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.06);
    text-align: center;
}

.section h2 {
    font-size: 28px;
    color: #C0392B;
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

# ---------------- HERO SECTION ----------------
st.markdown("""
<div class="hero">
    <h1>BART</h1>
    <h2>Coffee • French Toast • Fresh Bites</h2>
    <p>
        A modern Saudi café experience built for speed, quality, and taste.<br>
        Signature items: Dubai Chocolate Pudding, Nutella French Toast, specialty drinks.<br><br>
        📍 Jeddah Branches: Al Rahman • Al-Safa<br>
        🌐 <b style="color:#C0392B;">bart.sa</b>
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------- LOGIN BUTTONS ----------------
st.markdown('<div class="login-buttons">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    if st.button("Management Login"):
        st.switch_page("pages/management_dashboard.py")



st.markdown('</div>', unsafe_allow_html=True)

# ---------------- AI SIDEBAR ----------------
st.sidebar.markdown("### 🤖 AI Assistant")
query = st.sidebar.text_input("Ask AI")

if query:
    context = {
        "revenue": 0,
        "items": 0,
        "sales": []
    }
    st.sidebar.success(run_ai(query, context))

# ---------------- CHAT ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

# Chat input (clean ChatGPT-style, no button, arrow send)
user_input = st.chat_input("Message...")

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

# ---------------- INFO SECTIONS ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax in a cozy café environment with fast service and premium coffee experience.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="section">
<h2>Visit Us</h2>
<p>Find us in Jeddah branches or visit <b>bart.sa</b> for more information.</p>
</div>
""", unsafe_allow_html=True)
