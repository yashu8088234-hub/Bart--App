import streamlit as st
import gspread
import pandas as pd
import datetime
from oauth2client.service_account import ServiceAccountCredentials

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Weekly Scheduler")

if "branch_info" not in st.session_state:
    st.warning("Session expired")
    st.stop()

branch_info = st.session_state.branch_info

# =========================================================
# GOOGLE SHEETS
# =========================================================

@st.cache_resource
def connect():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["GOOGLE_CREDS_JSON"],
        ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

client = connect()
sheet = client.open_by_key(branch_info["SheetID"])

# =========================================================
# WEEK
# =========================================================

st.title("📅 Weekly Scheduler")

from_date = st.date_input("Week Start", datetime.date.today())

worksheet_name = f"Weekly_{from_date}"

days = ["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday"]

columns = ["EmployeeName","Role",*days,"Notes"]

ROLE_OPTIONS = [
    "Staff",
    "Supervisor",
    "Acting Supervisor",
    "Team Leader",
    "Acting Team Leader"
]

# =========================================================
# LOAD DATA (SINGLE DATAFRAME ONLY)
# =========================================================

@st.cache_data(ttl=60)
def load():
    try:
        ws = sheet.worksheet(worksheet_name)
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame(columns=columns)

df = load()

for c in columns:
    if c not in df.columns:
        df[c] = ""

df = df[columns]

# =========================================================
# 🎨 COLOR TOOL (ICON STYLE ONLY)
# =========================================================

st.subheader("🧩 Tools")

col1, col2, col3 = st.columns([1,1,8])

with col1:
    paint_mode = st.toggle("🎨")

with col2:
    st.markdown("🖌️")

if "selected_color" not in st.session_state:
    st.session_state.selected_color = "#ffffff"

if paint_mode:
    st.session_state.selected_color = st.color_picker(
        "Pick Color",
        value=st.session_state.selected_color,
        label_visibility="collapsed"
    )

    st.success(f"Active Color Selected")

# =========================================================
# CELL COLOR STORAGE
# =========================================================

if "cell_colors" not in st.session_state:
    st.session_state.cell_colors = {}

# =========================================================
# EXCEL EDITOR (ONLY ONE DATAFRAME)
# =========================================================

st.subheader("📊 Weekly Schedule (Single Sheet)")

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    column_config={
        "Role": st.column_config.SelectboxColumn(
            "Role",
            options=ROLE_OPTIONS
        )
    }
)

# =========================================================
# 🖱️ CELL SELECTOR (NO EXTRA TABLE)
# =========================================================

if paint_mode:

    st.markdown("### 🖱️ Select Cell to Apply Color")

    row_index = st.number_input("Row Index", min_value=0, step=1)
    column_name = st.selectbox("Column", columns)

    if st.button("Apply Selected Color"):
        key = f"{row_index}_{column_name}"
        st.session_state.cell_colors[key] = st.session_state.selected_color
        st.success("Cell colored")

# =========================================================
# STYLE SINGLE DATAFRAME ONLY
# =========================================================

def style_table(df):

    def apply(row):

        styles = [""] * len(row)

        for i, col in enumerate(df.columns):

            key = f"{row.name}_{col}"

            if key in st.session_state.cell_colors:
                styles[i] = f"background-color: {st.session_state.cell_colors[key]}"

        return styles

    return df.style.apply(apply, axis=1)

st.dataframe(style_table(edited_df), use_container_width=True)

# =========================================================
# SAVE (ONLY ONE DATAFRAME USED)
# =========================================================

colA, colB = st.columns(2)

with colA:

    if st.button("💾 SAVE", type="primary"):

        ws = sheet.worksheet(worksheet_name)

        edited_df = edited_df.fillna("")
        edited_df = edited_df[columns]

        final = [columns] + edited_df.values.tolist()

        ws.clear()
        ws.update(final)

        st.success("Saved successfully")
        st.rerun()

# =========================================================
# DOWNLOAD
# =========================================================

with colB:

    csv = edited_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ DOWNLOAD",
        csv,
        file_name=f"{branch_info['BranchCode']}_weekly_{from_date}.csv",
        mime="text/csv"
    )
