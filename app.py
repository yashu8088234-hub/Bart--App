import streamlit as st
from ai_core import run_ai

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="BART",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- MODERN BRAND UI ----------------


if "chat" not in st.session_state:
    st.session_state.chat = []

# input row inside chat section
col1, col2 = st.columns([10, 1])

with col1:
    user_input = st.text_input("Message...", label_visibility="collapsed")

with col2:
    send = st.button("➤")

if send and user_input:
    context = {
        "revenue": 0,
        "items": 0,
        "sales": st.session_state.get("pending_sales", [])
    }

    response = run_ai(user_input, context)

    st.session_state.chat.append(("You", user_input))
    st.session_state.chat.append(("AI", response))

# chat history
for sender, msg in st.session_state.chat[-10:]:
    if sender == "You":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**AI:** {msg}")

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
<p>Find us in Jeddah branches or visit bart.sa for more information.</p>
</div>
""", unsafe_allow_html=True)
