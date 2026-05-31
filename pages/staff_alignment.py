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
    df = pd.DataFrame(raw[1:], columns=raw[0]).fillna("")
    return df

df_full = load_data()

# remove duplicate columns safety
df_full = df_full.loc[:, ~df_full.columns.duplicated()].copy()

# =========================
# SHIFT PARSER
# =========================
def clean(text):
    text = str(text).replace("–", "-").replace("—", "-")
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
# 🔥 TOP TOOLBAR (FIXED ALIGNMENT + BIGGER UI)
# =========================
meta_cols = ["Branch", "Name", "Role"]
shift_cols = [c for c in df_full.columns if c not in meta_cols]

toolbar1, toolbar2, toolbar3 = st.columns([3, 4, 2], vertical_alignment="center")

with toolbar1:
    st.markdown("### ⏰ Shift Control")

with toolbar2:
    shift_col = st.selectbox(
        "Select Shift Column",
        shift_cols,
        label_visibility="visible"
    )

with toolbar3:
    refresh = st.button("🔄 Refresh Data", use_container_width=True)

# refresh logic
if refresh:
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# =========================
# SHIFT COLUMN APPLY
# =========================
if "Shift" in df_full.columns:
    df_full = df_full.drop(columns=["Shift"])

df_full["Shift"] = df_full[shift_col]

# =========================
# TIME + BRANCHES
# =========================
now_min = datetime.now().hour * 60 + datetime.now().minute
branches = sorted(df_full["Branch"].dropna().unique().tolist())

# =========================
# SAFE DF
# =========================
def safe_df(df):
    df = df.copy()
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# =========================
# ENGINE
# =========================
def compute(df):
    active, inactive = [], []

    for _, row in df.iterrows():
        r = row.to_dict()

        if is_active(row["Shift"], now_min):
            active.append(r)
        else:
            inactive.append(r)

    cols = df.columns.tolist()

    return (
        pd.DataFrame(active, columns=cols),
        pd.DataFrame(inactive, columns=cols)
    )

u_act, u_inact = compute(df_full)

# =========================
# OVERVIEW
# =========================
st.subheader("🌍 Universal Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Branches", len(branches))

with c2:
    st.metric("👥 Staff", len(df_full))

with c3:
    st.metric("🟢 Active", len(u_act))

with c4:
    st.metric("⚪ Inactive", len(u_inact))

st.divider()

# =========================
# BRANCH STATUS
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

st.dataframe(safe_df(pd.DataFrame(summary)), use_container_width=True, hide_index=True)

st.divider()

# =========================
# BRANCH FILTER
# =========================
col1, col2 = st.columns(2)

with col1:
    selected_branch = st.selectbox("🏢 Branch", branches)

with col2:
    selected_date = st.date_input("📅 Date", value=date.today())

df_branch = df_full[df_full["Branch"] == selected_branch]
b_act, b_inact = compute(df_branch)

# =========================
# BRANCH OVERVIEW
# =========================
st.subheader("🏢 Branch Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Branch", selected_branch)

with c2:
    st.metric("Date", selected_date.strftime("%d-%m-%Y"))

with c3:
    st.metric("Active", len(b_act))

with c4:
    st.metric("Inactive", len(b_inact))

st.divider()

# =========================
# ACTIVE STAFF
# =========================
st.subheader("🔥 Active Staff")
st.dataframe(safe_df(b_act), use_container_width=True, hide_index=True)

# =========================
# FULL VIEW
# =========================
st.subheader("📊 Full View")

full_view = pd.concat([b_act, b_inact], ignore_index=True)
full_view = full_view[df_branch.columns]

st.dataframe(safe_df(full_view), use_container_width=True, hide_index=True)
