import streamlit as st
import time

# =========================================================
# SYSTEM CONFIG
# =========================================================
st.set_page_config(
    page_title="BART Portal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# CSS
# =========================================================
st.markdown("""<style>

/* ================= HIDE UI ================= */
[data-testid="stSidebar"] {
    display: none;
}

.stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
    background: transparent !important;
}

#MainMenu, footer, header {
    visibility: hidden;
}

/* ================= BACKGROUND ================= */
.background-layer {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    z-index: -9999;
    overflow: hidden;
    background-color: #F8FAFC;
}

/* ================= ORBIT ================= */
.orbit {
    position: absolute;
    border: 1px solid rgba(0,0,0,0.15);
    border-radius: 50%;
    animation: spin linear infinite;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
}

.o1 { width: 200px; height: 200px; animation-duration: 20s; }
.o2 { width: 350px; height: 350px; animation-duration: 30s; }
.o3 { width: 500px; height: 500px; animation-duration: 40s; }
.o4 { width: 650px; height: 650px; animation-duration: 50s; }
.o5 { width: 800px; height: 800px; animation-duration: 65s; }
.o6 { width: 950px; height: 950px; animation-duration: 85s; }
.o7 { width: 1100px; height: 1100px; animation-duration: 110s; }

@keyframes spin {
    from { transform: translate(-50%, -50%) rotate(0deg); }
    to { transform: translate(-50%, -50%) rotate(360deg); }
}

/* ================= BART LOGO ================= */
@keyframes bartGlow {
    0%, 100% {
        filter: drop-shadow(0 0 10px rgba(247, 93, 89, 0.3));
        transform: scale(1);
    }
    50% {
        filter: drop-shadow(0 0 30px rgba(247, 93, 89, 0.7));
        transform: scale(1.04);
    }
}

.bart-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    margin-top: 20px;
}

.bart-logo {
    font-size: 120px;
    font-weight: 900;
    letter-spacing: -8px;

    background: linear-gradient(180deg, #ff8a86, #F75D59, #d93b37);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    animation: bartGlow 2.5s infinite ease-in-out;
    position: relative;
}

/* REGISTERED SYMBOL */
.bart-logo::after {
    content: "®";
    position: absolute;
    top: 10px;
    right: -30px;

    font-size: 24px;
    color: #7C4DFF;

    text-shadow:
        0 0 10px rgba(124,77,255,0.8),
        0 0 20px rgba(124,77,255,0.5);
}

/* PURPLE LEAF */
.bart-leaf {
    width: 28px;
    height: 45px;
    margin-left: 8px;

    background: linear-gradient(180deg, #8B5CF6, #7C4DFF);
    border-radius: 70% 30% 70% 30%;

    transform: rotate(45deg) translateY(25px);

    box-shadow: 0 0 20px rgba(124,77,255,0.5);

    animation: floatLeaf 3s infinite ease-in-out;
}

@keyframes floatLeaf {
    0%, 100% { transform: rotate(45deg) translateY(25px); }
    50% { transform: rotate(45deg) translateY(18px); }
}

/* ================= TEXT ================= */
.title {
    text-align: center;
    font-size: 60px;
    font-weight: 800;
    margin-top: 10px;
}

.sub {
    text-align: center;
    font-size: 18px;
    color: #64748B;
}

/* ================= BUTTON ================= */
div.stButton > button {
    height: 54px !important;
    border-radius: 50px !important;

    background: #F75D59 !important;
    color: white !important;

    font-weight: 900 !important;
    letter-spacing: 2px !important;

    border: none !important;

    transition: 0.3s ease;
}

div.stButton > button:hover {
    transform: scale(1.05);
    background: #e64540 !important;
    box-shadow: 0 10px 25px rgba(247,93,89,0.35);
}

</style>""", unsafe_allow_html=True)

# =========================================================
# STATE
# =========================================================
st.session_state.authenticated = True

# =========================================================
# BACKGROUND
# =========================================================
st.markdown("""
<div class="background-layer">
    <div class="orbit o1"></div>
    <div class="orbit o2"></div>
    <div class="orbit o3"></div>
    <div class="orbit o4"></div>
    <div class="orbit o5"></div>
    <div class="orbit o6"></div>
    <div class="orbit o7"></div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="bart-wrap">
    <div class="bart-logo">BART</div>
    <div class="bart-leaf"></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<h1 class="title">Operations management</h1>
<h1 class="title" style="color:#F75D59; margin-top:-20px;">just got easier.</h1>
<p class="sub">
Welcome to the central command unit for BART. Manage branches, logs and operations seamlessly.
</p>
""", unsafe_allow_html=True)

# =========================================================
# CARDS
# =========================================================
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### Staff Control")
    st.write("Daily logs, stock checks, and reports.")
    if st.button("ACCESS STAFF CONTROL →"):
        st.switch_page("pages/staff_dashboard.py")

with col2:
    st.markdown("### HQ Administration")
    st.write("Secure configs and system management.")
    if st.button("UNLOCK ADMIN PANEL →"):
        st.switch_page("pages/management_dashboard.py")
