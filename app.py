import streamlit as st


from ai_core import run_ai
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

bg_image = get_base64_image("barthome.png")

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
}}

.hero h2 {{
    font-size: 28px;
    text-shadow: 1px 1px 5px rgba(0,0,0,0.7);
    margin-bottom: 20px;
}}

.hero p {{
    max-width: 900px;
    font-size: 20px;
    margin: 10px auto;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.7);
    line-height:1.6;
}}

.login-buttons {{
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 40px;
    flex-wrap: wrap;
}}

div.stButton > button {{
    height: 65px;
    font-size: 20px;
    border-radius: 12px;
    width: 230px;
    transition: 0.3s;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
}}

div.stButton > button:hover {{
    background-color: #ff4b4b;
    color: white;
    transform: scale(1.05);
    box-shadow: 0px 8px 25px rgba(0,0,0,0.4);
}}

.section {{
    padding: 60px 20px;
    text-align: center;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(4px);
    margin: 40px 20px;
    border-radius: 12px;
    color: white;
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

@media only screen and (max-width:768px) {{
    .hero h1 {{ font-size: 50px; }}
    .hero h2 {{ font-size: 20px; }}
    .hero p {{ font-size: 16px; }}
    div.stButton > button {{ height:55px; font-size:18px; width:180px; }}
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
    <h2>Coffee, French Toast & Fresh Bites in Jeddah</h2>
    <p>
        A Saudi Arabian café chain specializing in <b>quick, on-the-go specialty coffee</b>, <b>desserts</b>, and <b>fresh snacks</b>.<br>
        Popular menu items include <b>Dubai Chocolate Pudding</b>, <b>Nutella/Kinder French Toast</b>, and various slush drinks.<br>
        📍 Locations: Jeddah – Al Rahman, Al-Safa <br>
        🌐 Website: <a href='https://bart.sa' target='_blank' style='color:#ffcc00;'>bart.sa</a>
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------- Login Buttons ----------------
st.markdown('<div class="login-buttons">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("Staff Login"):
        st.switch_page("pages/staff_dashboard.py")
with col2:
    if st.button("Management Login"):
        st.write("COMING SOON")
with col3:
    if st.button("Manager Login"):
        st.switch_page("pages/manager_dashboard.py")
st.markdown('</div>', unsafe_allow_html=True)



st.markdown("## 🤖 AI Assistant")

query = st.text_input("Ask AI...")

if query:
    context = {
        "revenue":  total_revenue_calc if "total_revenue_calc" in locals() else 0,
        "items": total_items_calc if "total_items_calc" in locals() else 0,
        "sales": st.session_state.get("pending_sales", [])
    }

    answer = run_ai(query, context)
    st.success(answer)







with st.sidebar:
    st.markdown("### 🤖 AI Assistant")
    query = st.text_input("Ask AI")

    if query:
        context = {
            "revenue": 0,
            "items": 0,
            "sales": []
        }
        st.success(run_ai(query, context))



st.markdown("## 🤖 AI Assistant")

if "chat" not in st.session_state:
    st.session_state.chat = []

user_input = st.text_input("Talk to AI...")

if user_input:
    context = {
        "revenue": total_revenue_calc if "total_revenue_calc" in locals() else 0,
        "items": total_items_calc if "total_items_calc" in locals() else 0,
        "sales": st.session_state.get("pending_sales", [])
    }

    response = run_ai(user_input, context)

    st.session_state.chat.append(("You", user_input))
    st.session_state.chat.append(("AI", response))

# DISPLAY CHAT
for sender, msg in st.session_state.chat[-10:]:
    st.write(f"**{sender}:** {msg}")
# ---------------- Info Sections ----------------
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
