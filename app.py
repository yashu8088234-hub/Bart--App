import streamlit as st
from ai_core import run_ai

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="BART Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS — CORPORATE PRO DESIGN
# =========================================================
st.markdown("""
<style>

/* -------------------------------------------------
GLOBAL
------------------------------------------------- */

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}

html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

.stApp {
    background-color: #F4F6F8;
}

/* Main Layout */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1500px;
}

/* -------------------------------------------------
SIDEBAR
------------------------------------------------- */

section[data-testid="stSidebar"] {
    background: #1F2937;
    width: 260px !important;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Sidebar Title */
.sidebar-title {
    font-size: 28px;
    font-weight: 800;
    color: white;
    text-align: center;
    margin-bottom: 30px;
    letter-spacing: 2px;
}

/* -------------------------------------------------
TOP HERO
------------------------------------------------- */

.hero {
    background: white;
    border-radius: 24px;
    padding: 40px;
    margin-bottom: 25px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}

.hero h1 {
    font-size: 52px;
    font-weight: 800;
    color: #1F2937;
    margin-bottom: 10px;
}

.hero p {
    font-size: 18px;
    color: #6B7280;
}

/* -------------------------------------------------
KPI CARDS
------------------------------------------------- */

.kpi-card {
    background: white;
    padding: 24px;
    border-radius: 20px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
    transition: 0.3s ease;
    border-left: 6px solid #2563EB;
}

.kpi-card:hover {
    transform: translateY(-4px);
}

.kpi-title {
    color: #6B7280;
    font-size: 15px;
    margin-bottom: 10px;
}

.kpi-value {
    color: #111827;
    font-size: 34px;
    font-weight: 700;
}

/* -------------------------------------------------
SECTION CONTAINERS
------------------------------------------------- */

.section-box {
    background: white;
    border-radius: 20px;
    padding: 28px;
    margin-top: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.05);
}

.section-title {
    font-size: 24px;
    font-weight: 700;
    color: #1F2937;
    margin-bottom: 20px;
}

/* -------------------------------------------------
BUTTONS
------------------------------------------------- */

div.stButton > button {
    width: 100%;
    height: 50px;
    border-radius: 14px;
    border: none;
    background: #2563EB;
    color: white;
    font-size: 15px;
    font-weight: 600;
    transition: 0.3s ease;
}

div.stButton > button:hover {
    background: #1D4ED8;
    transform: translateY(-2px);
}

/* -------------------------------------------------
CHAT
------------------------------------------------- */

.chat-user {
    background: #DBEAFE;
    padding: 14px 18px;
    border-radius: 14px;
    margin-bottom: 10px;
    color: #1E3A8A;
}

.chat-ai {
    background: #F3F4F6;
    padding: 14px 18px;
    border-radius: 14px;
    margin-bottom: 15px;
    color: #111827;
}

/* -------------------------------------------------
INPUT
------------------------------------------------- */

.stTextInput > div > div > input {
    border-radius: 12px;
    border: 1px solid #D1D5DB;
    padding: 12px;
}

/* -------------------------------------------------
TABLES
------------------------------------------------- */

[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
}

/* -------------------------------------------------
METRIC
------------------------------------------------- */

[data-testid="metric-container"] {
    background: white;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown('<div class="sidebar-title">BART</div>', unsafe_allow_html=True)

    st.button("🏠 Dashboard")
    st.button("☕ Orders")
    st.button("📦 Inventory")
    st.button("👨‍🍳 Staff")
    st.button("📊 Analytics")
    st.button("🤖 AI Assistant")
    st.button("⚙️ Settings")

# =========================================================
# HERO SECTION
# =========================================================

st.markdown("""
<div class="hero">
    <h1>BART Management Dashboard</h1>
    <p>
        Monitor café performance, manage staff operations,
        track revenue, and interact with BART AI Assistant.
    </p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# KPI SECTION
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-title">Today's Revenue</div>
        <div class="kpi-value">SAR 12,450</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-title">Orders</div>
        <div class="kpi-value">328</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-title">Staff Active</div>
        <div class="kpi-value">18</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-title">Avg Ticket</div>
        <div class="kpi-value">SAR 38</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# MAIN GRID
# =========================================================

left, right = st.columns([2,1])

# =========================================================
# LEFT SIDE
# =========================================================

with left:

    st.markdown("""
    <div class="section-box">
        <div class="section-title">Live Operations</div>
    </div>
    """, unsafe_allow_html=True)

    orders = [
        {"Order ID": "#1021", "Item": "Spanish Latte", "Status": "Preparing"},
        {"Order ID": "#1022", "Item": "French Toast", "Status": "Ready"},
        {"Order ID": "#1023", "Item": "Cappuccino", "Status": "Pending"},
        {"Order ID": "#1024", "Item": "Iced Americano", "Status": "Completed"},
    ]

    st.dataframe(orders, use_container_width=True)

    st.markdown("""
    <div class="section-box">
        <div class="section-title">Branch Notes</div>
        Team performance is stable today. Peak hour expected at 7PM.
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# RIGHT SIDE
# =========================================================

with right:

    st.markdown("""
    <div class="section-box">
        <div class="section-title">Quick Actions</div>
    </div>
    """, unsafe_allow_html=True)

    st.button("➕ New Order")
    st.button("📦 Update Inventory")
    st.button("👥 Manage Staff")
    st.button("📊 View Reports")

# =========================================================
# AI ASSISTANT
# =========================================================

st.markdown("""
<div class="section-box">
    <div class="section-title">BART AI Assistant</div>
</div>
""", unsafe_allow_html=True)

if "chat" not in st.session_state:
    st.session_state.chat = []

with st.form("chat_form", clear_on_submit=True):

    user_input = st.text_input(
        "",
        placeholder="Ask BART AI anything..."
    )

    send = st.form_submit_button("Send")

if send and user_input:

    context = {
        "revenue": 12450,
        "orders": 328,
        "staff_active": 18,
        "sales": st.session_state.get("pending_sales", [])
    }

    response = run_ai(user_input, context)

    st.session_state.chat.append(("You", user_input))
    st.session_state.chat.append(("AI", response))

# =========================================================
# CHAT DISPLAY
# =========================================================

for sender, msg in st.session_state.chat[-8:]:

    if sender == "You":
        st.markdown(
            f'<div class="chat-user"><b>You:</b> {msg}</div>',
            unsafe_allow_html=True
        )

    else:
        st.markdown(
            f'<div class="chat-ai"><b>BART AI:</b> {msg}</div>',
            unsafe_allow_html=True
        )

# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<br><br>
<center style='color:#9CA3AF; font-size:14px;'>
BART © 2026 • Corporate Management System
</center>
""", unsafe_allow_html=True)
