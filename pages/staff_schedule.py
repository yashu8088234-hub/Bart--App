import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import timedelta

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# 1. AUTH & CONNECTION
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

# 2. CONFIG
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

ROLE_OPTIONS = ["Staff", "Supervisor", "Acting Supervisor", "Team Leader", "Acting Team Leader"]
SHIFT_OPTIONS = ["Morning shift", "Mid shift", "Evening shift", "Night shift"]
TIME_OPTIONS = [f"{h}:00 AM" for h in range(1, 13)] + [f"{h}:00 PM" for h in range(1, 13)] + ["OFF"]

# 3. UI
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

start_date = st.date_input("Week Start Date")
shift_mode = st.toggle("Enable Shift-wise Mode")

# ✅ FIXED DATE FORMAT (Sun 24/05)
day_dates = [
    (start_date + timedelta(days=i)).strftime("%a %d/%m")
    for i in range(7)
]

# 4. LOAD DATA
def get_filtered_data():
    ws = master_sheet.worksheet("StaffSchedule")
    all_data = ws.get_all_records()

    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

    return df[df["Branch"] == st.session_state.selected_branch]


df = get_filtered_data()

# 5. BUILD UI (UNCHANGED LOGIC)
st.subheader("Edit Roster")

config = {
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS)
}

df_display = df.copy()

for i, day in enumerate(DAYS):

    if shift_mode:
        # remove time columns if exist
        start_col = f"{day}: Start"
        end_col = f"{day}: Finish"

        if start_col in df_display.columns:
            cols_to_drop = [start_col]
            if end_col in df_display.columns:
                cols_to_drop.append(end_col)

            df_display.drop(columns=cols_to_drop, inplace=True)

        if day not in df_display.columns:
            df_display[day] = ""

        # SHIFT MODE CONFIG
        config[day] = st.column_config.SelectboxColumn(
            f"({day_dates[i]})",
            options=SHIFT_OPTIONS
        )

    else:
        # remove shift column if exists
        if day in df_display.columns:
            df_display.drop(columns=[day], inplace=True)

        start_col = f"{day}: Start"
        end_col = f"{day}: End"

        if start_col not in df_display.columns:
            df_display[start_col] = ""

        if end_col not in df_display.columns:
            df_display[end_col] = ""

# ==============================
# ✅ NORMAL MODE HEADER GROUPING
# ==============================

if not shift_mode:

    # Ensure base columns exist
    if "Name" not in df_display.columns:
        df_display["Name"] = ""

    if "Role" not in df_display.columns:
        df_display["Role"] = ""

    # Build ordered multi-index columns
    multi_columns = [
        ("Info", "Name"),
        ("Info", "Role")
    ]

    rename_map = {
        "Name": ("Info", "Name"),
        "Role": ("Info", "Role")
    }

    for i, day in enumerate(DAYS):

        day_label = day_dates[i]

        start_col = f"{day}: Start"
        end_col = f"{day}: End"

        # fallback support if old data has Finish
        if end_col not in df_display.columns:
            alt_end = f"{day}: Finish"

            if alt_end in df_display.columns:
                df_display.rename(columns={alt_end: end_col}, inplace=True)
            else:
                df_display[end_col] = ""

        if start_col not in df_display.columns:
            df_display[start_col] = ""

        rename_map[start_col] = (day_label, "Start")
        rename_map[end_col] = (day_label, "End")

        multi_columns.append((day_label, "Start"))
        multi_columns.append((day_label, "End"))

    # rename columns
    df_display = df_display.rename(columns=rename_map)

    # keep only needed columns in order
    existing_cols = [c for c in multi_columns if c in df_display.columns]

    df_display = df_display[existing_cols]

else:

    # SHIFT MODE (UNCHANGED)
    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True
    )

# ==============================
# ✅ NORMAL MODE DATA EDITOR
# ==============================

if not shift_mode:

    edited_df = st.data_editor(
        df_display,
        num_rows="dynamic",
        use_container_width=True
    )

# 6. SAVE LOGIC (UNCHANGED)
if st.button("💾 Save to Master Sheet", type="primary"):

    ws = master_sheet.worksheet("StaffSchedule")
    full_data = pd.DataFrame(ws.get_all_records())

    remaining_data = full_data[
        full_data["Branch"] != st.session_state.selected_branch
    ]

    new_data = edited_df.copy()

    # ==============================
    # ✅ FLATTEN MULTIINDEX COLUMNS
    # ==============================
    if not shift_mode and isinstance(new_data.columns, pd.MultiIndex):

        flat_columns = []

        for top, bottom in new_data.columns:

            if top == "Info":
                flat_columns.append(bottom)

            else:
                day_name = DAYS[day_dates.index(top)]

                flat_columns.append(f"{day_name}: {bottom}")

        new_data.columns = flat_columns

    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = str(start_date)

    if "Name" in new_data.columns:
        new_data["Name"] = (
            new_data["Name"]
            .astype(str)
            .str.upper()
        )

    final_df = pd.concat(
        [remaining_data, new_data],
        ignore_index=True
    )

    ws.clear()
    ws.update(
        [final_df.columns.values.tolist()] +
        final_df.fillna("").values.tolist()
    )

    st.success("✅ Saved Successfully!")
    st.rerun()

# 7. BACK BUTTON
if st.button("⬅ Back"):
    st.switch_page("app.py")
