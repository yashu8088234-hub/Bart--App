import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from gspread.exceptions import APIError
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
import time

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="Stock Overview"
)

st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# LIVE TIMER
# =========================================================
from streamlit_autorefresh import st_autorefresh

st_autorefresh(
    interval=60000,
    key="live_timer"
)

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
# MASTER SHEET
# =========================================================
MASTER_ID = "1KYNCls3HWWj_DFY2Q27JRDRJpolSVcxiSH7f4rNDOlM"

# =========================================================
# LOAD MASTER DATA
# =========================================================
@st.cache_data(ttl=600)
def load_data():

    try:

        sheet = client.open_by_key(
            MASTER_ID
        ).worksheet("STOCKS")

        data = sheet.get_all_values()

        if not data or len(data) < 2:
            return pd.DataFrame()

        headers = data[0]
        rows = data[1:]

        df = pd.DataFrame(
            rows,
            columns=headers
        )

        # =============================================
        # DATE FIX
        # =============================================
        if "Date" in df.columns:

            df["Date"] = pd.to_datetime(
                df["Date"],
                errors="coerce"
            )

        # =============================================
        # NUMERIC FIX
        # =============================================
        fixed_cols = [
            "Date",
            "Item",
            "SKU",
            "UOM"
        ]

        for col in df.columns:

            if col not in fixed_cols:

                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                ).fillna(0)

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

    st.warning("No Data Found")
    st.stop()

# =========================================================
# REFRESH CONTROL
# =========================================================
if "last_force_refresh" not in st.session_state:
    st.session_state.last_force_refresh = 0

REFRESH_COOLDOWN = 40

now = time.time()

remaining = REFRESH_COOLDOWN - (
    now - st.session_state.last_force_refresh
)

remaining = max(0, int(remaining))

can_force_refresh = remaining <= 0

# =========================================================
# DATE SECTION
# =========================================================
available_dates = sorted(
    df["Date"].dropna().dt.date.unique(),
    reverse=True
)

selected_date = st.date_input(
    "📅 Select Date",
    value=available_dates[0]
    if available_dates else None
)

# =========================================================
# BUTTONS
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

    if st.button(
        refresh_text,
        disabled=not can_force_refresh
    ):

        try:

            st.cache_data.clear()

            st.session_state.last_force_refresh = time.time()

            st.success(
                "✅ Latest stock data loaded successfully"
            )

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
st.info(
    f"⏳ Refresh available in: {remaining} seconds"
)

# =========================================================
# FILTER BY DATE
# =========================================================
filtered = df[
    df["Date"].dt.date == selected_date
]

# =========================================================
# DAILY / WEEKLY LOGIC
# =========================================================
daily_rows = []
weekly_rows = []

current_section = None

for _, row in filtered.iterrows():

    row_text = " ".join(
        [str(x) for x in row.values]
    ).lower()

    # =============================================
    # SECTION DETECTION
    # =============================================
    if "daily item" in row_text:

        current_section = "daily"
        continue

    if "weekly item" in row_text:

        current_section = "weekly"
        continue

    # =============================================
    # SKIP EMPTY ITEMS
    # =============================================
    item = str(
        row.get("Item", "")
    ).strip()

    if item == "":
        continue

    # =============================================
    # STORE ROWS
    # =============================================
    if current_section == "daily":

        daily_rows.append(row)

    elif current_section == "weekly":

        weekly_rows.append(row)

# =========================================================
# DATAFRAMES
# =========================================================
daily_df = pd.DataFrame(daily_rows)

weekly_df = pd.DataFrame(weekly_rows)

# =========================================================
# GRID WIDTH
# =========================================================
def get_width(series, min_width):

    try:

        series = series.fillna("").astype(str)

        max_len = series.map(len).max()

        return max(
            int(max_len * 5 + 25),
            min_width
        )

    except:
        return min_width

# =========================================================
# GRID RENDER
# =========================================================
def render_grid(df, title):

    st.subheader(title)

    if df is None or df.empty:

        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    # =============================================
    # PINNED COLUMNS
    # =============================================
    if "Item" in df.columns:

        gb.configure_column(
            "Item",
            pinned="left",
            minWidth=180
        )

    if "SKU" in df.columns:

        gb.configure_column(
            "SKU",
            pinned="left",
            minWidth=100
        )

    if "UOM" in df.columns:

        gb.configure_column(
            "UOM",
            pinned="left",
            minWidth=80
        )

    # =============================================
    # DYNAMIC WIDTHS
    # =============================================
    fixed_cols = [
        "Date",
        "Item",
        "SKU",
        "UOM"
    ]

    for col in df.columns:

        if col not in fixed_cols:

            gb.configure_column(
                col,
                minWidth=get_width(
                    df[col],
                    120
                )
            )

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True
    )

    gb.configure_grid_options(
        domLayout='normal',
        suppressHorizontalScroll=False
    )

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        key=title
    )

# =========================================================
# DISPLAY
# =========================================================
render_grid(
    daily_df,
    "📦 Daily Items Stock"
)

render_grid(
    weekly_df,
    "📦 Weekly Items Stock"
)

# =========================================================
# EXCEL EXPORT
# =========================================================
def create_excel(
    daily_df,
    weekly_df
):

    output = BytesIO()

    wb = Workbook()

    ws = wb.active

    ws.title = "Stock Dashboard"

    def write_section(
        title,
        df,
        start_row
    ):

        rows = list(
            dataframe_to_rows(
                df,
                index=False,
                header=True
            )
        )

        if not rows:
            return start_row + 2

        total_cols = len(rows[0])

        ws.merge_cells(
            start_row=start_row,
            start_column=1,
            end_row=start_row,
            end_column=total_cols
        )

        ws.cell(
            row=start_row,
            column=1,
            value=title
        ).font = Font(bold=True)

        r0 = start_row + 2

        for r_i, row in enumerate(rows):

            for c_i, val in enumerate(row, 1):

                ws.cell(
                    row=r0 + r_i,
                    column=c_i,
                    value=val
                )

        return r0 + len(rows) + 3

    next_row = write_section(
        "DAILY STOCK",
        daily_df,
        1
    )

    write_section(
        "WEEKLY STOCK",
        weekly_df,
        next_row
    )

    wb.save(output)

    output.seek(0)

    return output

# =========================================================
# DOWNLOAD
# =========================================================
excel_file = create_excel(
    daily_df,
    weekly_df
)

st.download_button(
    "📥 Download Stock Report",
    excel_file,
    file_name="stock_report.xlsx"
)
