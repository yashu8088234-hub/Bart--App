import streamlit as st
import base64

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- Encode Local Image to Base64 ----------------
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

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
    background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url("data:image/png;base64,{bg_image}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}
.hero {{
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: white;
}}
.hero h1, .hero h2, .hero p {{
    opacity: 0;
    transform: translateY(30px);
    animation: fadeUp 1s forwards;
}}
.hero h1 {{
    color: #ff0000;
    font-size: 70px;
    font-weight: bold;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    margin-bottom: 10px;
    animation-delay: 0.2s;
}}
.hero h2 {{
    font-size: 24px;
    text-shadow: 1px 1px 5px rgba(0,0,0,0.7);
    margin-bottom: 20px;
    animation-delay: 0.4s;
}}
.hero p {{
    max-width: 900px;
    font-size: 20px;
    margin: 10px auto;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.7);
    line-height:1.6;
    animation-delay: 0.6s;
}}
div.stButton > button {{
    height: 65px;
    font-size: 20px;
    border-radius: 12px;
    margin: 8px;
    width: 230px;
    transition: 0.3s;
}}
div.stButton > button:hover {{
    background-color: #ff4b4b;
    color: white;
}}
@keyframes fadeUp {{
    0% {{opacity:0; transform: translateY(30px);}}
    100% {{opacity:1; transform: translateY(0);}}
}}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# ---------------- Hero Section ----------------
st.markdown(f"""
<div class="hero">
    <h1>BART (بارت)</h1>
    <h2>Coffee, French Toast & Fresh Bites in Jeddah</h2>
    <p>
        A Saudi café chain with <b>quick, specialty coffee</b> and <b>fresh snacks</b>.<br>
        Popular items: Dubai Chocolate Pudding, Nutella/Kinder French Toast, Mango & Hibiscus Slush.<br>
        📍 Locations: Jeddah – Al Rahman, Al-Safa<br>
        📱 Ordering: HungerStation, Keeta<br>
        💰 Frequent promotions & offers<br>
        🌐 Website: <a href='https://bart.sa' target='_blank' style='color:#ffcc00;'>bart.sa</a>
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------- Staff / Management Buttons ----------------
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("Staff Login"):
        st.session_state["user_role"] = "staff"
        st.switch_page("pages/staff_dashboard.py")  # Connect to working staff page
with col2:
    if st.button("Management Login"):
        st.session_state["user_role"] = "management"
        st.write("Coming soon...")  # Placeholder
with col3:
    if st.button("Manager Login"):
        st.session_state["user_role"] = "manager"
        st.switch_page("pages/manager_dashboard.py")  # Connect to working manager page

# ---------------- Section: Our Experience ----------------
st.markdown("""
<div style="padding:60px; text-align:center; background: rgba(255,255,255,0.05); border-radius:12px; color:white;">
<h2>Our Experience</h2>
<p>Relax in a cozy environment with friends and family. Fast service, friendly staff, and a welcoming atmosphere at every BART location.</p>
</div>
""", unsafe_allow_html=True)

# ---------------- Section: Visit Us ----------------
st.markdown("""
<div style="padding:60px; text-align:center; background: rgba(255,255,255,0.05); border-radius:12px; color:white;">
<h2>Visit Us</h2>
<p>Multiple locations in Jeddah. Check our website for branch info, opening hours, and latest offers: 
<a style='color:#ffcc00;' href="https://bart.sa" target="_blank">bart.sa</a></p>
</div>
""", unsafe_allow_html=True)
