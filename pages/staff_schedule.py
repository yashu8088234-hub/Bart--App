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

ROLE_OPTIONS = [
    "Staff",
    "Supervisor",
    "Acting Supervisor",
    "Team Leader",
    "Acting Team Leader"
]

SHIFT_OPTIONS = [
    "Morning shift",
    "Mid shift",
    "Evening shift",
    "Night shift"
]

TIME_OPTIONS = (
    [f"{h}:00 AM" for h in range(1, 13)] +
    [f"{h}:00 PM" for h in range(1, 13)] +
    ["OFF"]
)

# 3. UI
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

start_date = st.date_input("Week Start Date")
shift_mode = st.toggle("Enable Shift-wise Mode")

# ✅ DATE FORMAT
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
        df = pd.DataFrame(
            columns=["Branch", "Date", "Name", "Role"] + DAYS
        )

    return df[df["Branch"] == st.session_state.selected_branch]


df = get_filtered_data()

# 5. BUILD UI
st.subheader("Edit Roster")

config = {
    "Role": st.column_config.SelectboxColumn(
        "Role",
        options=ROLE_OPTIONS
    )
}

df_display = df.copy()

for i, day in enumerate(DAYS):

    if shift_mode:

        # REMOVE TIME COLUMNS IF EXIST
        start_col = f"{day}: Start"
        end_col = f"{day}: Finish"

        if start_col in df_display.columns:

            cols_to_drop = [start_col]

            if end_col in df_display.columns:
                cols_to_drop.append(end_col)

            df_display.drop(columns=cols_to_drop, inplace=True)

        if day not in df_display.columns:
            df_display[day] = ""

        # SHIFT MODE COLUMN
        config[day] = st.column_config.SelectboxColumn(
            f"({day_dates[i]})",
            options=SHIFT_OPTIONS
        )

    else:

        # REMOVE SHIFT COLUMN IF EXISTS
        if day in df_display.columns:
            df_display.drop(columns=[day], inplace=True)

        start_col = f"{day}: Start"
        end_col = f"{day}: End"

        # SUPPORT OLD "Finish" COLUMNS
        alt_end_col = f"{day}: Finish"

        if end_col not in df_display.columns:

            if alt_end_col in df_display.columns:
                df_display.rename(
                    columns={alt_end_col: end_col},
                    inplace=True
                )
            else:
                df_display[end_col] = ""

        if start_col not in df_display.columns:
            df_display[start_col] = ""

# ==============================
# SHIFT MODE (UNCHANGED)
# ==============================

if shift_mode:

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True
    )

# ==============================
# NORMAL MODE WITH GROUPED HEADERS
# ==============================

else:

    # ORDER COLUMNS PROPERLY
    ordered_cols = ["Name", "Role"]

    for day in DAYS:
        ordered_cols.append(f"{day}: Start")
        ordered_cols.append(f"{day}: End")

    existing_cols = [
        col for col in ordered_cols
        if col in df_display.columns
    ]

    df_display = df_display[existing_cols]

    # ==============================
    # CUSTOM HEADER ROW
    # ==============================

    header_cols = st.columns(
        [1.8, 1.5] + [2.2] * 7
    )

    header_cols[0].markdown(
        "<div style='font-weight:bold; font-size:18px;'>Name</div>",
        unsafe_allow_html=True
    )

    header_cols[1].markdown(
        "<div style='font-weight:bold; font-size:18px;'>Role</div>",
        unsafe_allow_html=True
    )

    for i, day_label in enumerate(day_dates):

        header_cols[i + 2].markdown(
            f"""
            <div style="
                text-align:center;
                font-weight:bold;
                font-size:17px;
                margin-bottom:0px;
            ">
                {day_label}
            </div>

            <div style="
                display:flex;
                justify-content:space-between;
                padding:0 18px;
                font-size:13px;
                color:gray;
                margin-top:-5px;
            ">
                <span>Start</span>
                <span>End</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ==============================
    # DATA EDITOR
    # ==============================

    edited_df = st.data_editor(
        df_display,

        column_config={

            "Name": st.column_config.TextColumn(
                "",
                width="medium"
            ),

            "Role": st.column_config.SelectboxColumn(
                "",
                options=ROLE_OPTIONS,
                width="medium"
            ),

            **{
                f"{day}: Start": st.column_config.SelectboxColumn(
                    "",
                    options=TIME_OPTIONS,
                    width="small"
                )
                for day in DAYS
            },

            **{
                f"{day}: End": st.column_config.SelectboxColumn(
                    "",
                    options=TIME_OPTIONS,
                    width="small"
                )
                for day in DAYS
            }
        },

        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )

# 6. SAVE LOGIC (UNCHANGED)

if st.button("💾 Save to Master Sheet", type="primary"):

    ws = master_sheet.worksheet("StaffSchedule")
    full_data = pd.DataFrame(ws.get_all_records())

    remaining_data = full_data[
        full_data["Branch"] != st.session_state.selected_branch
    ]

    new_data = edited_df.copy()

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
