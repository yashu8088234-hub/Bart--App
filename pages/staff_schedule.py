import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import timedelta

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# =========================
# 1. AUTH
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first.")
    st.stop()

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
)

master_sheet = gspread.authorize(creds).open_by_key(
    "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
)

ws = master_sheet.worksheet("StaffSchedule")

# =========================
# 2. CONFIG
# =========================
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

ROLE_OPTIONS = [
    "Staff",
    "Supervisor",
    "Acting Supervisor",
    "Team Leader",
    "Acting Team Leader"
]

SHIFT_OPTIONS = ["Morning shift", "Mid shift", "Evening shift", "Night shift"]

TIME_OPTIONS = (
    [f"{h}:00 AM" for h in range(1, 13)] +
    [f"{h}:00 PM" for h in range(1, 13)] +
    ["OFF"]
)

# =========================
# 3. UI
# =========================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

start_date = st.date_input("Week Start Date")
shift_mode = st.toggle("Enable Shift-wise Mode")

day_dates = [
    (start_date + timedelta(days=i)).strftime("%a %d/%m")
    for i in range(7)
]

# =========================
# 4. LOAD DATA
# =========================
def load_data():
    data = ws.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        df = pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

    return df[df["Branch"] == st.session_state.selected_branch]


df = load_data()

# =========================
# 5. BUILD CLEAN DISPLAY DF (IMPORTANT FIX)
# =========================
base_cols = ["Role"]

df_display = df.copy()

# FORCE CLEAN REBUILD (prevents ghost columns)
for day in DAYS:
    shift_col = day
    start_col = f"{day}: Start"
    end_col = f"{day}: Finish"

    # remove both schemas first
    for col in [shift_col, start_col, end_col]:
        if col in df_display.columns:
            df_display.drop(columns=[col], inplace=True)

# =========================
# REBUILD BASE STRUCTURE
# =========================
for day in DAYS:
    if shift_mode:
        df_display[day] = df.get(day, "")
    else:
        df_display[f"{day}: Start"] = df.get(f"{day}: Start", "")
        df_display[f"{day}: Finish"] = df.get(f"{day}: Finish", "")

# =========================
# 6. COLUMN CONFIG
# =========================
config = {
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS)
}

for i, day in enumerate(DAYS):

    if shift_mode:
        config[day] = st.column_config.SelectboxColumn(
            f"({day_dates[i]})",
            options=SHIFT_OPTIONS
        )
    else:
        start_col = f"{day}: Start"
        end_col = f"{day}: Finish"

        config[start_col] = st.column_config.SelectboxColumn(
            f"({day_dates[i]}) Start",
            options=TIME_OPTIONS
        )

        config[end_col] = st.column_config.SelectboxColumn(
            f"({day_dates[i]}) End",
            options=TIME_OPTIONS
        )

# =========================
# 7. EDITOR
# =========================
edited_df = st.data_editor(
    df_display,
    column_config=config,
    num_rows="dynamic",
    use_container_width=True
)

# =========================
# 8. SAVE (SAFE + CLEAN)
# =========================
if st.button("💾 Save to Master Sheet", type="primary"):

    full_data = pd.DataFrame(ws.get_all_records())

    # remove old branch data
    full_data = full_data[full_data["Branch"] != st.session_state.selected_branch]

    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = str(start_date)

    if "Name" in new_data.columns:
        new_data["Name"] = new_data["Name"].astype(str).str.upper()

    final_df = pd.concat([full_data, new_data], ignore_index=True)

    ws.clear()
    ws.update([final_df.columns.tolist()] + final_df.fillna("").values.tolist())

    st.success("✅ Saved Successfully!")
    st.rerun()

# =========================
# 9. BACK
# =========================
if st.button("⬅ Back"):
    st.switch_page("app.py")
