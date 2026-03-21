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

bg_image = get_base64_image("barthome.png")  # Hero background

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
    background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("data:image/png;base64,{bg_image}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    font-family: 'Segoe UI', sans-serif;
}}

/* Hero Section */
.hero {{
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: white;
}}

.hero h1 {{
    font-size: 70px;
    font-weight: bold;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    margin-bottom: 10px;
    animation: fadeUp 1s forwards;
}}

.hero h2 {{
    font-size: 28px;
    margin-bottom: 20px;
    animation: fadeUp 1s forwards;
    animation-delay: 0.3s;
}}

.hero p {{
    max-width: 900px;
    font-size: 20px;
    margin: 10px auto 30px;
    line-height:1.6;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.7);
    animation: fadeUp 1s forwards;
    animation-delay: 0.6s;
}}

/* Hero CTA Buttons */
.cta-buttons {{
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
    margin-top: 20px;
}}

.cta-buttons button {{
    height: 65px;
    font-size: 20px;
    border-radius: 12px;
    padding: 0 25px;
    transition: 0.3s;
    font-weight: bold;
    cursor: pointer;
}}

.cta-buttons button:hover {{
    background-color: #ff4b4b;
    color: white;
}}

/* Section Cards */
.section {{
    padding: 60px 20px;
    text-align: center;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(4px);
    margin: 40px auto;
    border-radius: 12px;
    max-width: 1200px;
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
    line-height: 1.6;
}}

.card-container {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 20px;
}}

.card {{
    background: rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 20px;
    width: 250px;
    text-align: center;
    transition: transform 0.3s;
}}

.card:hover {{
    transform: scale(1.05);
}}

.card img {{
    max-width: 100%;
    border-radius: 8px;
    margin-bottom: 15px;
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
    .section h2 {{ font-size: 32px; }}
    .card {{ width: 90%; }}
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
        Enjoy quick, specialty coffee, desserts, and fresh snacks at BART. Popular items include 
        <b>Nutella/Kinder French Toast</b> and <b>Mango & Hibiscus Slush</b>.
    </p>
    <div class="cta-buttons">
        <button onclick="window.location.href='#'">Staff Login 👨‍💼</button>
        <button onclick="window.location.href='#'">Management 👩‍💼</button>
        <button onclick="window.location.href='#'">Manager 🏆</button>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- Section 1: Our Experience ----------------
st.markdown("""
<div class="section">
<h2>Our Experience</h2>
<p>Relax in a cozy environment with friends and family. Fast service, friendly staff, and a welcoming atmosphere await you at every BART location.</p>
</div>
""", unsafe_allow_html=True)

# ---------------- Section 2: Visit Us ----------------
st.markdown("""
<div class="section">
<h2>Visit Us</h2>
<p>Multiple locations in Jeddah. Check our website for branch info, opening hours, and latest offers: 
<a style='color:#ffcc00;' href="https://bart.sa" target="_blank">bart.sa</a></p>
</div>
""", unsafe_allow_html=True)

# ---------------- Section 3: Popular Items Carousel ----------------
st.markdown("""
<div class="section">
<h2>Popular Menu Items</h2>
<div class="card-container">
    <div class="card">
        <img src="https://i.imgur.com/2QpWQWa.jpg" alt="Nutella French Toast">
        <h3>Nutella French Toast</h3>
        <p>SAR 28</p>
    </div>
    <div class="card">
        <img src="https://i.imgur.com/A3o3rYy.jpg" alt="Mango Slush">
        <h3>Mango Slush</h3>
        <p>SAR 15</p>
    </div>
    <div class="card">
        <img src="https://i.imgur.com/3T9d7Dm.jpg" alt="Hibiscus Slush">
        <h3>Hibiscus Slush</h3>
        <p>SAR 15</p>
    </div>
    <div class="card">
        <img src="https://i.imgur.com/7vGQ9qX.jpg" alt="Dubai Chocolate Pudding">
        <h3>Dubai Chocolate Pudding</h3>
        <p>SAR 22</p>
    </div>
</div>
</div>
""", unsafe_allow_html=True)

# ---------------- Footer ----------------
st.markdown("""
<div class="section">
<p>© 2026 BART | Follow us on 
<a href="https://instagram.com/bart" target="_blank" style='color:#ffcc00;'>Instagram</a> | 
<a href="https://facebook.com/bart" target="_blank" style='color:#ffcc00;'>Facebook</a> | 
<a href="https://bart.sa" target="_blank" style='color:#ffcc00;'>Website</a></p>
</div>
""", unsafe_allow_html=True)
