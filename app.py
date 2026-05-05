import streamlit as st
from ai_core import run_ai

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- Clean Modern UI ----------------
st.markdown("""
<style>

/* Hide default Streamlit UI */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

/* App background */
.stApp {
    background: #f6f8fb;
    font-family: 'Segoe UI', sans-serif;
}

/* Remove padding chaos */
.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1200px;
}

/* HERO CARD */
.hero {
    background: white;
    padding: 50px 30px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    margin-top: 20px;
}

/* Title */
.hero h1 {
    font-size: 56px;
    color: #e63946;
    margin-bottom: 10px;
    font-weight: 800;
}

/* Subtitle */
.hero h2 {
    font-size: 22px;
    color: #333;
    margin-bottom: 15px;
    font-weight: 500;
}

/* Paragraph */
.hero p {
    font-size: 16px;
    color: #666;
    max-width: 800px;
    margin: auto;
    line-height: 1.6;
}

/* Login buttons row */
.login-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 30px;
    flex-wrap: wrap;
}

/* Buttons */
div.stButton > button {
    height: 55px;
    width: 220px;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    background: #1f2937;
    color: white;
    border: none;
    transition: 0.2s;
}

div.stButton > button:hover {
    background: #e63946;
    transform: translateY(-2px);
}

/* Section cards */
.section {
    background: white;
    padding: 40px 25px;
    margin-top: 25px;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    text-align: center;
}

/* Section title */
.section h2 {
    font-size: 28px;
    color: #e63946;
    margin-bottom: 15px;
}

/* Section text */
.section p {
    font-size: 16px;
    color: #555;
    max-width: 750px;
    margin: auto;
    line-height: 1.6;
}

/* Chat input */
.stTextInput > div > div > input {
    border-radius: 10px;
}

/* Sidebar AI */
[data-testid="stSidebar"] {
    background: #ffffff;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HERO SECTION ----------------
st.markdown("""
<div class="hero">
    <h1>BART (بارت)</h1>
    <h2>Coffee, French Toast & Fresh Bites in Jeddah</h2>
    <p>
        A Saudi café brand specializing in specialty coffee, desserts, and quick bites.<br>
        Popular items include Dubai Chocolate Pudding, Nutella French Toast, and signature drinks.<br><br>
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

# ---------------- CHAT SECTION ----------------
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

# display chat
for sender, msg in st.session_state.chat[-10:]:
    st.write(f"**{sender}:** {msg}")

# ---------------- INFO SECTIONS ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax in a cozy environment with fast service and friendly staff. Perfect for coffee lovers and dessert fans.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="section">
<h2>Visit Us</h2>
<p>Find us in Jeddah branches or visit <a href="https://bart.sa" target="_blank">bart.sa</a> for more info.</p>
</div>
""", unsafe_allow_html=True)
