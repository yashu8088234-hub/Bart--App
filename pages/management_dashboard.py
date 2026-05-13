import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from gspread.exceptions import APIError
import time

# =========================================================
# PAGE CONFIG (UNCHANGED STYLE)
# =========================================================
st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# LIVE TIMER (SAFE INTERVAL)
# =========================================================
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60000, key="live_timer")  # 1 min (IMPORTANT FIX)

# =========================================================
# ERROR HANDLER
# =========================================================
def show_api_error(e):
    st.error("🚨 Google Sheets API Error")
    st.exception(e)
    st.stop()

# =========================================================
# GOOGLE AUTH
# =========================================================
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )
    return gspread.authorize(creds)

try:
    client = get_client()
except Exception as e:
    show_api_error(e)

# =========================================================
# MASTER SHEET ID
# =========================================================
MASTER_ID = "1KYNCls3HWWj_DFY2Q27JRDRJpolSVcxiSH7f4rNDOlM"

# =========================================================
# LOAD MASTER DATA ONLY (NO 28 SHEETS ANYMORE)
# =========================================================
@st.cache_data(ttl=600)
def load_data():
    try:
        sheet = client.open_by_key(MASTER_ID).worksheet("STOCKS")

        data = sheet.get_all_values()
        headers = data[0]
        rows = data[1:]

        df = pd.DataFrame(rows, columns=headers)

        # FIX TYPES
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # convert numeric branch columns safely
        for col in df.columns:
            if col.startswith("Branch"):
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df

    except Exception as e:
        raise e

# =========================================================
# LOAD DATA
# =========================================================
try:
    df = load_data()
except APIError as e:
    show_api_error(e)
except Exception as e:
    show_api_error(e)

if df.empty:
    st.warning("No Data Found in Master Sheet")
    st.stop()

# =========================================================
# REFRESH CONTROL (SAFE)
# =========================================================
if "last_force_refresh" not in st.session_state:
    st.session_state.last_force_refresh = 0

REFRESH_COOLDOWN = 40

now = time.time()
remaining = REFRESH_COOLDOWN - (now - st.session_state.last_force_refresh)
remaining = max(0, int(remaining))
can_force_refresh = remaining <= 0

# =========================================================
# FILTERS (DATE + ITEM + SKU)
# =========================================================
st.sidebar.header("🔎 Filters")

dates = sorted(df["Date"].dropna().unique())
selected_date = st.sidebar.selectbox("Select Date", dates)

items = ["All"] + sorted(df["Item"].dropna().unique().tolist())
selected_item = st.sidebar.selectbox("Select Item", items)

skus = ["All"] + sorted(df["SKU"].dropna().unique().tolist())
selected_sku = st.sidebar.selectbox("Select SKU", skus)

# =========================================================
# BUTTONS (UNCHANGED UI)
# =========================================================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Date Only"):
        st.rerun()

with col2:
    refresh_text = (
        "🔴 Refresh Data From Sheets"
        if can_force_refresh
        else f"⏳ Wait {remaining} sec"
    )

    if st.button(refresh_text, disabled=not can_force_refresh):
        try:
            st.cache_data.clear()
            st.session_state.last_force_refresh = time.time()
            st.success("Updated")
            st.rerun()
        except Exception as e:
            st.error(e)
            st.stop()

with col3:
    if st.button("🔙 Back"):
        st.switch_page("app.py")

# =========================================================
# TIMER DISPLAY
# =========================================================
st.info(f"⏳ Refresh available in: {remaining} seconds")

# =========================================================
# FILTER LOGIC (FAST LOCAL FILTERING)
# =========================================================
filtered = df[df["Date"] == selected_date]

if selected_item != "All":
    filtered = filtered[filtered["Item"] == selected_item]

if selected_sku != "All":
    filtered = filtered[filtered["SKU"] == selected_sku]

# =========================================================
# GRID WIDTH HELPER
# =========================================================
def get_width(series, min_width):
    try:
        series = series.fillna("").astype(str)
        max_len = series.map(len).max()
        return max(int(max_len * 5 + 25), min_width)
    except:
        return min_width

# =========================================================
# GRID RENDER (UNCHANGED STYLE)
# =========================================================
def render_grid(df, title):

    st.subheader(title)

    if df is None or df.empty:
        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item", pinned="left", minWidth=140)
    gb.configure_column("SKU", pinned="left", minWidth=80)
    gb.configure_column("UOM", pinned="left", minWidth=70)

    # dynamic branch column widths
    for col in df.columns:
        if col.startswith("Branch"):
            gb.configure_column(col, minWidth=get_width(df[col], 120))

    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_grid_options(domLayout='normal', suppressHorizontalScroll=False)

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        key=title
    )

# =========================================================
# DISPLAY DATA (SAME DESIGN)
# =========================================================
render_grid(filtered, "📦 Daily Items Stock")

# placeholder (kept for your old UI compatibility)
render_grid(pd.DataFrame(), "📦 Weekly Items Stock")

# =========================================================
# DOWNLOAD (SIMPLE EXPORT)
# =========================================================
st.download_button(
    "📥 Download Stock Report",
    filtered.to_csv(index=False),
    file_name="stock_report.csv"
)
