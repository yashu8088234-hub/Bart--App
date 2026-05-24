import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from st_aggrid import AgGrid

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# =========================================
# 1. AUTH
# =========================================

if (
    "authenticated" not in st.session_state
    or not st.session_state.authenticated
):
    st.error("Please login first.")
    st.stop()

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
)

master_sheet = gspread.authorize(creds).open_by_key(
    "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
)

# =========================================
# 2. CONFIG
# =========================================

DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

ROLE_OPTIONS = [
    "Staff","Supervisor","Acting Supervisor",
    "Team Leader","Acting Team Leader"
]

SHIFT_OPTIONS = [
    "Morning shift",
    "Mid shift",
    "Evening shift",
    "Night shift",
    "OFF",
    "Custom Time"
]

# =========================================
# 3. STATE (POPUP CONTROL)
# =========================================

if "custom_time_open" not in st.session_state:
    st.session_state.custom_time_open = False

if "custom_time_target" not in st.session_state:
    st.session_state.custom_time_target = None


# =========================================
# 4. UI
# =========================================

st.title(f"🏢 Schedule: {st.session_state.selected_branch}")
edit_mode = st.toggle("Edit Mode Only")

# =========================================
# 5. LOAD DATA
# =========================================

def get_filtered_data():
    ws = master_sheet.worksheet("StaffSchedule")
    all_data = ws.get_all_records()
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

    return df[df["Branch"] == st.session_state.selected_branch]


df = get_filtered_data()

existing_names = df["Name"].dropna().unique().tolist()

# =========================================
# 6. EDIT MODE TABLE
# =========================================

config = {
    "Name": st.column_config.SelectboxColumn("Name", options=existing_names),
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS),
}

for day in DAYS:
    config[day] = st.column_config.SelectboxColumn(
        day,
        options=SHIFT_OPTIONS
    )

if edit_mode:
    df_display = pd.DataFrame(columns=["Name", "Role"] + DAYS)

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True
    )

    # =========================================
    # SMALL CONTROL PANEL (NO SPACE WASTE)
    # =========================================

    st.markdown("### ⚡ Quick Custom Time Setup")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_person = st.selectbox("Employee", edited_df["Name"].dropna().tolist() if not edited_df.empty else [])

    with col2:
        selected_day = st.selectbox("Day", DAYS)

    with col3:
        if st.button("⏰ Set Custom Time"):
            st.session_state.custom_time_open = True
            st.session_state.custom_time_target = {
                "name": selected_person,
                "day": selected_day
            }

# =========================================
# 7. MODAL POPUP (CLEAN CALENDAR STYLE)
# =========================================

@st.dialog("⏰ Custom Time Picker")
def custom_time_dialog():

    target = st.session_state.custom_time_target

    st.write(f"**Employee:** {target['name']}")
    st.write(f"**Day:** {target['day']}")

    col1, col2, col3 = st.columns(3)

    with col1:
        sh = st.selectbox("Start Hour", list(range(1, 13)))
    with col2:
        sm = st.selectbox("Min", ["00", "30"])
    with col3:
        sap = st.selectbox("AM/PM", ["AM", "PM"])

    col4, col5, col6 = st.columns(3)

    with col4:
        eh = st.selectbox("End Hour", list(range(1, 13)))
    with col5:
        em = st.selectbox("Min", ["00", "30"])
    with col6:
        eap = st.selectbox("AM/PM", ["AM", "PM"])

    apply_all = st.checkbox("Apply to all days")

    if st.button("Save Time"):
        time_value = f"{sh}:{sm} {sap} - {eh}:{em} {eap}"

        name = target["name"]
        day = target["day"]

        idx = edited_df[edited_df["Name"] == name].index

        if apply_all:
            for d in DAYS:
                edited_df.loc[idx, d] = time_value
        else:
            edited_df.loc[idx, day] = time_value

        st.session_state.custom_time_open = False
        st.success("Saved!")
        st.rerun()


if st.session_state.custom_time_open:
    custom_time_dialog()

# =========================================
# 8. SAVE
# =========================================

if edit_mode and st.button("💾 Save to Master Sheet", type="primary"):

    ws = master_sheet.worksheet("StaffSchedule")
    full_data = pd.DataFrame(ws.get_all_records())

    remaining = full_data[
        full_data["Branch"] != st.session_state.selected_branch
    ]

    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = datetime.now().strftime("%A %d %B")

    if "Name" in new_data.columns:
        new_data["Name"] = new_data["Name"].astype(str).str.upper()

    final_df = pd.concat([remaining, new_data], ignore_index=True)

    ws.clear()
    ws.update(
        [final_df.columns.tolist()] +
        final_df.fillna("").values.tolist()
    )

    st.success("✅ Saved Successfully!")
    st.rerun()

# =========================================
# 9. BACK
# =========================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
