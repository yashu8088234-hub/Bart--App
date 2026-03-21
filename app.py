import streamlit as st
import base64

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- Encode Local Image ----------------
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_image = get_base64_image("barthome.png")  # Your background image

# ---------------- Custom CSS ----------------
custom_css = f"""
<style>
#MainMenu {{visibility:hidden;}}
footer {{visibility:hidden;}}
header {{visibility:hidden;}}
[data-testid="stToolbar"] {{display:none;}}
[data-testid="stSidebar"] {{display:none;}}
.block-container {{
    padding:0 !important;
    margin:0 auto !important;
    max-width: 100% !important;
}}
.stApp {{
    min-height: 100vh;
    background-image: linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35)), url("data:image/png;base64,{bg_image}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

/* Hero Section */
.hero {{
    min-height: 90vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: white;
    padding: 20px;
}}

.hero h1 {{
    font-size: 70px;
    color: #ff0000;
    font-weight: bold;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    margin-bottom: 10px;
    animation: fadeUp 1s forwards;
}}

.hero h2 {{
    font-size: 28px;
    text-shadow: 1px 1px 5px rgba(0,0,0,0.7);
    margin-bottom: 20px;
    animation: fadeUp 1.2s forwards;
}}

.hero p {{
    max-width: 900px;
    font-size: 20px;
    margin: 10px auto;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.7);
    line-height:1.6;
    animation: fadeUp 1.4s forwards;
}}

/* Feature Cards */
.features {{
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 20px;
    flex-wrap: wrap;
}}

.feature-card {{
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(5px);
    border-radius: 12px;
    padding: 20px 30px;
    font-size: 20px;
    text-align: center;
    min-width: 160px;
    transition: all 0.3s ease;
    cursor: default;
}}

.feature-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}}

/* Login Cards */
.login-cards {{
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 40px;
    flex-wrap: wrap;
}}

.login-card {{
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(5px);
    border-radius: 12px;
    padding: 25px 30px;
    text-align: center;
    width: 230px;
    transition: all 0.3s ease;
    cursor: pointer;
    font-size: 20px;
    font-weight: bold;
}}

.login-card:hover {{
    transform: scale(1.05);
    background-color: #ff4b4b;
    color: white;
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}}

/* Section Cards */
.section {{
    padding: 60px 20px;
    text-align: center;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(4px);
    margin: 40px 20px;
    border-radius: 12px;
    color: white;
    animation: fadeUp 1s forwards;
}}

.section h2 {{
    font-size: 40px;
    color: #ff4b4b;
    margin-bottom: 30px;
}}

.section p {{
    font-size: 18px;
    max-width: 800px;
    margin: 0 auto;
    line-height:1.6;
}}

/* Animations */
@keyframes fadeUp {{
    0% {{opacity:0; transform: translateY(30px);}}
    100% {{opacity:1; transform: translateY(0);}}
}}

@media only screen and (max-width:768px) {{
    .hero h1 {{ font-size: 50px; }}
    .hero h2 {{ font-size: 20px; }}
    .hero p {{ font-size: 16px; }}
    .feature-card, .login-card {{ width: 160px; font-size:16px; padding:15px 20px; }}
    .section h2 {{ font-size: 32px; }}
    .section p {{ font-size:16px; }}
}}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# ---------------- Hero Section ----------------
st.markdown(f"""
<div class="hero">
    <h1>BART (بارت)</h1>
    <h2>Coffee. French Toast. Fresh Bites.</h2>
    <div class="features">
        <div class="feature-card">☕ Specialty Coffee</div>
        <div class="feature-card">🍞 French Toast</div>
        <div class="feature-card">🥤 Slush Drinks</div>
    </div>
    <p>
        Enjoy fresh snacks and specialty drinks at multiple locations in Jeddah. Fast service, friendly staff, and cozy environment.
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------- Login Cards ----------------
st.markdown('<div class="login-cards">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("👩 Staff Login"):
        st.switch_page("pages/staff_dashboard.py")
with col2:
    if st.button("🛠 Management Login"):
        st.write("COMING SOON")
with col3:
    if st.button("🧑 Manager Login"):
        st.switch_page("pages/manager_dashboard.py")
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Sections ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax in a cozy environment with friends and family. Fast service, friendly staff, and a welcoming atmosphere await you at every BART location.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="section">
<h2>Visit Us</h2>
<p>Multiple locations in Jeddah. Check our website for branch info, opening hours, and latest offers: <a style='color:#ffcc00;' href="https://bart.sa" target="_blank">bart.sa</a></p>
</div>
""", unsafe_allow_html=True)
