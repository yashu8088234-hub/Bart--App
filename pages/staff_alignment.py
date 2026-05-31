import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# =========================
# APP CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Ops Control Center")
st.title("⚡ Ops Control Center")

# =========================
# SHEET CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

# =========================
# GOOGLE CLIENT
# =========================
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["GOOGLE_CREDS_JSON"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds)

client = get_client()
sheet = client.open_by_key(SHEET_ID)

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=900)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df_full = load_data()

# =========================
# SHIFT PARSER
# =========================
def clean(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_shift(cell):
    if not cell:
        return None

    text = clean(cell)
    matches = re.findall(r"\d{1,2}\s*(?:AM|PM)", text, re.I)

    if len(matches) < 2:
        return None

    def convert(t):
        t = t.upper().replace(" ", "")
        h = int(re.findall(r"\d{1,2}", t)[0])

        if "AM" in t:
            if h == 12:
                h = 0
        else:
            if h != 12:
                h += 12

        return h * 60

    return convert(matches[0]), convert(matches[1])

def is_active(cell, now_min):
    shift = get_shift(cell)
    if not shift:
        return False

    start, end = shift

    if start < end:
        return start <= now_min < end
    else:
        return now_min >= start or now_min < end

# =========================
# SHIFT COLUMN
# =========================
meta_cols = ["Branch", "Name", "Role"]
shift_cols = [c for c in df_full.columns if c not in meta_cols]

shift_col = st.selectbox("⏰ Shift Column", shift_cols)

df_full = df_full.rename(columns={shift_col: "Shift"})

# =========================
# FILTER CONTROLS (TOGETHER)
# =========================
col1, col2 = st.columns(2)

with col1:
    branches = sorted(df_full["Branch"].dropna().unique().tolist())
    selected_branch = st.selectbox("🏢 Branch", branches)

with col2:
    selected_date = st.date_input("📅 Date", value=date.today())

st.divider()

# =========================
# FILTERED DATA
# =========================
df_branch = df_full[df_full["Branch"] == selected_branch]

now_min = datetime.now().hour * 60 + datetime.now().minute

# =========================
# ENGINE
# =========================
def compute(df):
    active, inactive = [], []

    for _, row in df.iterrows():
        r = row.to_dict()
        r["Date"] = selected_date

        if is_active(row["Shift"], now_min):
            active.append(r)
        else:
            inactive.append(r)

    return pd.DataFrame(active), pd.DataFrame(inactive)

u_act, u_inact = compute(df_full)
b_act, b_inact = compute(df_branch)

# =========================
# 🌍 UNIVERSAL OVERVIEW
# =========================
st.subheader("🌍 Universal Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Total Branches", len(branches))

with c2:
    st.metric("👥 Total Staff", len(df_full))

with c3:
    st.metric("🟢 Active (All)", len(u_act))

with c4:
    st.metric("⚪ Inactive (All)", len(u_inact))

st.divider()

# =========================
# 🪟 BRANCH STATUS
# =========================
st.subheader("🪟 Branch Status")

summary = []

for b in branches:
    temp = df_full[df_full["Branch"] == b]
    a, i = compute(temp)

    summary.append({
        "Branch": b,
        "Active": len(a),
        "Inactive": len(i)
    })

st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

st.divider()

# =========================
# 🏢 BRANCH OVERVIEW
# =========================
st.subheader("🏢 Branch Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Branch", selected_branch)

with c2:
    st.metric("📅 Date", selected_date.strftime("%d-%m-%Y"))

with c3:
    st.metric("🟢 Active", len(b_act))

with c4:
    st.metric("⚪ Inactive", len(b_inact))

st.divider()

# =========================
# 🔥 ACTIVE STAFF
# =========================
st.subheader("🔥 Active Staff")
st.dataframe(b_act, use_container_width=True, hide_index=True)

# =========================
# 📊 FULL VIEW
# =========================
st.subheader("📊 Full View")
st.dataframe(pd.concat([b_act, b_inact]), use_container_width=True, hide_index=True)
