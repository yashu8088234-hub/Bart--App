import streamlit as st
import pandas as pd
import psycopg2
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (PostgreSQL)")

# =========================================================
# DATABASE CONNECTION
# =========================================================

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        dbname="mydatabase",
        user="postgres",
        host="localhost",
        port=5432
    )

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=300)
def load_data(selected_date):
    conn = get_connection()

    query = """
        SELECT branch_name, item_name, sku, uom, stock_type, stock_date, quantity
        FROM stock_data
        WHERE stock_date = %s
    """

    df = pd.read_sql(query, conn, params=[selected_date])
    return df

# =========================================================
# PROCESS DATA (PIVOT LIKE YOUR OLD SYSTEM)
# =========================================================

def process_stock(df, stock_type):

    df = df[df["stock_type"] == stock_type]

    if df.empty:
        return pd.DataFrame()

    pivot = df.pivot_table(
        index=["item_name", "sku", "uom"],
        columns="branch_name",
        values="quantity",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    pivot.columns.name = None

    pivot = pivot.rename(columns={
        "item_name": "Item Name",
        "sku": "SKU",
        "uom": "UOM"
    })

    return pivot

# =========================================================
# UI - DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")

# =========================================================
# LOAD FROM DB
# =========================================================

df = load_data(selected_date)

# =========================================================
# BUILD TABLES
# =========================================================

daily_df = process_stock(df, "daily")
weekly_df = process_stock(df, "weekly")

# branch columns
branch_names = [c for c in daily_df.columns if c not in ["Item Name", "SKU", "UOM"]]

# =========================================================
# AGGRID
# =========================================================

def render_grid(df, title):

    st.subheader(title)

    if df.empty:
        st.warning("No Data Found")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item Name", pinned="left", minWidth=200)
    gb.configure_column("SKU", pinned="left", minWidth=120)
    gb.configure_column("UOM", pinned="left", minWidth=80)

    for col in branch_names:
        gb.configure_column(col, minWidth=120)

    gb.configure_default_column(resizable=True, sortable=True, filter=True)

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        fit_columns_on_grid_load=False
    )

# =========================================================
# DISPLAY
# =========================================================

render_grid(daily_df, "📦 Daily Items Stock")
render_grid(weekly_df, "📦 Weekly Items Stock")

# =========================================================
# EXCEL EXPORT
# =========================================================

def create_excel(daily_df, weekly_df):

    output = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock Report"

    header_font = Font(bold=True)
    center = Alignment(horizontal="center")

    def write_section(title, df, start_row):

        ws.cell(row=start_row, column=1, value=title).font = Font(bold=True, size=14)

        rows = dataframe_to_rows(df, index=False, header=True)

        r = start_row + 2

        for i, row in enumerate(rows):
            for j, val in enumerate(row, 1):
                cell = ws.cell(row=r + i, column=j, value=val)
                cell.alignment = center

                if i == 0:
                    cell.font = header_font

        return r + len(list(rows)) + 2

    next_row = write_section("DAILY STOCK", daily_df, 1)
    write_section("WEEKLY STOCK", weekly_df, next_row)

    wb.save(output)
    output.seek(0)
    return output

excel = create_excel(daily_df, weekly_df)

st.download_button(
    "📥 Download Excel Report",
    excel,
    file_name="stock_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
