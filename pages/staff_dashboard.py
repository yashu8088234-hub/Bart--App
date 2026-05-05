# ---------------- BRANCH SELECT (HTML + STREAMLIT SYNC) ----------------
st.subheader("Select Branch")

branch_options = ["-- Select Branch --"] + branches

# get from URL (this is how HTML talks to Streamlit safely)
query_params = st.query_params
url_branch = query_params.get("branch", st.session_state.selected_branch)

# update session state
st.session_state.selected_branch = url_branch

# build HTML dropdown
html = """
<select onchange="location = this.value;" style="
    width:100%;
    padding:14px;
    font-size:16px;
    border-radius:10px;
    border:1px solid #ccc;
    background:white;
">
"""

for b in branch_options:
    html += f'<option value="?branch={b}" {"selected" if b == url_branch else ""}>{b}</option>'

html += "</select>"

st.markdown(html, unsafe_allow_html=True)

selected_branch = st.session_state.selected_branch
