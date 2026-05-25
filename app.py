import streamlit as st

st.set_page_config(
    page_title="BART Portal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# GLOBAL STYLE
# =========================
st.markdown("""
<style>

/* REMOVE STREAMLIT DEFAULT MARGINS */
.block-container {
    padding-top: 2rem !important;
    max-width: 1050px !important;
    margin: auto;
}

.stApp {
    background: #F8FAFC;
}

/* ================= BACKGROUND ================= */
.bg {
    position: fixed;
    inset: 0;
    z-index: -1;
    background: radial-gradient(circle at top, #ffffff, #f1f5f9);
}

/* soft ring */
.bg::before {
    content: "";
    position: absolute;
    width: 900px;
    height: 900px;
    border-radius: 50%;
    border: 1px solid rgba(0,0,0,0.05);
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

/* ================= HERO ================= */
.hero {
    text-align: center;
    margin-top: 10px;
}

/* LOGO */
.logo {
    font-size: 110px;
    font-weight: 900;
    letter-spacing: -6px;
    position: relative;
    display: inline-block;

    background: linear-gradient(180deg, #ff6f6b, #F75D59);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* REGISTERED SYMBOL (fixed small glow, not blinking) */
.logo::after {
    content: "®";
    position: absolute;
    top: 18px;
    right: -28px;
    font-size: 22px;
    color: #6C5CE7;
    text-shadow: 0 0 6px rgba(108,92,231,0.3);
}

/* SMALL STATIC PURPLE DOT (like image accent) */
.logo::before {
    content: "";
    position: absolute;
    width: 12px;
    height: 12px;
    background: #6C5CE7;
    border-radius: 50%;
    bottom: 20px;
    right: -16px;
    box-shadow: 0 0 8px rgba(108,92,231,0.35);
}

/* ================= TITLE ================= */
.title {
    font-size: 54px;
    font-weight: 800;
    margin-top: 8px;
    color: #111;
}

.title span {
    color: #F75D59;
}

/* ================= SUB TEXT ================= */
.subtext {
    max-width: 620px;
    margin: auto;
    margin-top: 12px;
    font-size: 15px;
    line-height: 1.6;
    color: #64748B;
}

/* ================= CARDS ================= */
.cards {
    display: flex;
    justify-content: center;
    gap: 22px;
    margin-top: 42px;
}

/* CARD STYLE */
.card {
    flex: 1;
    background: white;
    border-radius: 18px;
    padding: 28px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    text-align: center;
}

/* CARD TITLE */
.card h3 {
    margin-bottom: 10px;
}

/* CARD TEXT */
.card p {
    color: #64748B;
    font-size: 14px;
}

/* ================= BUTTON ================= */
button[kind="primary"] {
    background: #F75D59 !important;
    border-radius: 50px !important;
    height: 52px !important;
    font-weight: 800 !important;
    letter-spacing: 1px !important;
    border: none !important;
}

button[kind="primary"]:hover {
    background: #e64a45 !important;
}

</style>
""", unsafe_allow_html=True)

# ================= BACKGROUND =================
st.markdown('<div class="bg"></div>', unsafe_allow_html=True)

# ================= HERO =================
st.markdown("""
<div class="hero">
    <div class="logo">BART</div>

    <div class="title">
        Operations management <span>just got easier.</span>
    </div>

    <div class="subtext">
        Welcome to the central command unit for BART. Seamlessly organize branch metrics,
        manage shift requirements, and deploy localized branch parameters.
    </div>
</div>
""", unsafe_allow_html=True)

# ================= CARDS =================
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("""
    <div class="card">
        <h3>Staff Control</h3>
        <p>Log daily updates, run checks and manage operations.</p>
    </div>
    """, unsafe_allow_html=True)

    st.button("ACCESS STAFF CONTROL →")

with col2:
    st.markdown("""
    <div class="card">
        <h3>HQ Administration</h3>
        <p>Secure logs, configs and global system settings.</p>
    </div>
    """, unsafe_allow_html=True)

    st.button("UNLOCK ADMIN PANEL →")
