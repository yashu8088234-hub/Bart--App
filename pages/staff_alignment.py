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
# LOAD DATA (CACHE 15 MIN)
# =========================
@st.cache_data(ttl=900)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

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
    return (start <= now_min < end) if start < end else (now_min >= start or now_min < end)

# =========================
# 🔥 SINGLE ENGINE (SOURCE OF TRUTH)
# =========================
def compute(df, branch, col, now_min, selected_date):

    branch_df = df[df["Branch"] == branch]

    u_act, u_inact = [], []
    b_act, b_inact = [], []

    # UNIVERSAL
    for _, row in df.iterrows():
        r = row.to_dict()
        r["Date"] = selected_date

        if is_active(row[col], now_min):
            u_act.append(r)
        else:
            u_inact.append(r)

    # BRANCH
    for _, row in branch_df.iterrows():
        r = row.to_dict()
        r["Date"] = selected_date

        if is_active(row[col], now_min):
            b_act.append(r)
        else:
            b_inact.append(r)

    return (
        pd.DataFrame(u_act),
        pd.DataFrame(u_inact),
        pd.DataFrame(b_act),
        pd.DataFrame(b_inact),
    )

# =========================
# LOAD DATA
# =========================
df = load_data()

# =========================
# UI CONTROLS
# =========================
branches = sorted(df["Branch"].dropna().unique().tolist())
shift_cols = [c for c in df.columns if c not in ["Branch", "Name", "Role"]]

c1, c2 = st.columns(2)

with c1:
    branch = st.selectbox("🏢 Branch", branches)

with c2:
    selected_date = st.date_input("📅 Date", value=date.today())

st.metric("📅 Selected Date", selected_date.strftime("%d-%m-%Y"))

selected_col = shift_cols[0]

# =========================
# TIME
# =========================
now = datetime.now()
now_min = now.hour * 60 + now.minute

# =========================
# RUN ENGINE
# =========================
u_act, u_inact, b_act, b_inact = compute(
    df, branch, selected_col, now_min, selected_date
)

# =========================
# 🌍 UNIVERSAL OVERVIEW (FIXED)
# =========================
st.subheader("🌍 Universal Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Total Branches", len(branches))

with c2:
    st.metric("👥 Total Staff", len(df))

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
    temp = df[df["Branch"] == b]

    a = 0
    i = 0

    for _, row in temp.iterrows():
        if is_active(row[selected_col], now_min):
            a += 1
        else:
            i += 1

    summary.append({
        "Branch": b,
        "Active": a,
        "Inactive": i
    })

st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

st.divider()

# =========================
# 🏢 BRANCH OVERVIEW
# =========================
st.subheader("🏢 Branch Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Branch", branch)

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

full = pd.concat([b_act, b_inact], ignore_index=True)

st.dataframe(full, use_container_width=True, hide_index=True)
