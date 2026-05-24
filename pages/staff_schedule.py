import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# =========================================
# AUTH
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
# CONFIG
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
    "➕ Custom Time"
]

# =========================================
# STATE
# =================================

if "popup" not in st.session_state:
    st.session_state.popup = False

if "popup_target" not in st.session_state:
    st.session_state.popup_target = None

if "popup_key" not in st.session_state:
    st.session_state.popup_key = 0

# =========================================
# UI
# =================================

st.title(f"🏢 Schedule: {st.session_state.selected_branch}")
edit_mode = st.toggle("Edit Mode Only")

# =========================================
# LOAD DATA
# =================================

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
# EDIT TABLE
# =================================

config = {
    "Name": st.column_config.SelectboxColumn("Name", options=existing_names),
    "Role": st.column_config.SelectboxColumn("Role", options=ROLE_OPTIONS),
}

for d in DAYS:
    config[d] = st.column_config.SelectboxColumn(d, options=SHIFT_OPTIONS)

if edit_mode:
    df_display = pd.DataFrame(columns=["Name", "Role"] + DAYS)

    edited_df = st.data_editor(
        df_display,
        column_config=config,
        num_rows="dynamic",
        use_container_width=True,
        key="editor"
    )

    # =========================================
    # AUTO DETECT CUSTOM TIME SELECTION
    # =========================================

    for i, row in edited_df.iterrows():
        for d in DAYS:
            if row.get(d) == "➕ Custom Time":

                st.session_state.popup = True
                st.session_state.popup_target = {
                    "row": i,
                    "day": d,
                    "name": row.get("Name", "")
                }

                # reset cell to avoid loop reopen
                edited_df.at[i, d] = ""

                st.rerun()

# =========================================
# POPUP (MODAL)
# =================================

@st.dialog("⏰ Custom Time Picker")
def time_popup():

    target = st.session_state.popup_target
    uid = st.session_state.popup_key

    st.write(f"👤 **Employee:** {target['name']}")
    st.write(f"📅 **Day:** {target['day']}")

    col1, col2, col3 = st.columns(3)

    with col1:
        sh = st.selectbox("Start Hour", list(range(1, 13)), key=f"sh_{uid}")
    with col2:
        sm = st.selectbox("Min", ["00", "30"], key=f"sm_{uid}")
    with col3:
        sap = st.selectbox("AM/PM", ["AM", "PM"], key=f"sap_{uid}")

    col4, col5, col6 = st.columns(3)

    with col4:
        eh = st.selectbox("End Hour", list(range(1, 13)), key=f"eh_{uid}")
    with col5:
        em = st.selectbox("Min", ["00", "30"], key=f"em_{uid}")
    with col6:
        eap = st.selectbox("AM/PM", ["AM", "PM"], key=f"eap_{uid}")

    apply_all = st.checkbox("Apply to all days", key=f"all_{uid}")

    if st.button("Save", key=f"save_{uid}"):

        value = f"{sh}:{sm} {sap} - {eh}:{em} {eap}"

        idx = edited_df[
            edited_df["Name"] == target["name"]
        ].index

        if apply_all:
            for d in DAYS:
                edited_df.loc[idx, d] = value
        else:
            edited_df.loc[idx, target["day"]] = value

        st.session_state.popup = False
        st.session_state.popup_target = None
        st.session_state.popup_key += 1

        st.rerun()


# trigger modal
if st.session_state.popup:
    time_popup()

# =========================================
# SAVE
# =================================

if edit_mode and st.button("💾 Save to Master Sheet", type="primary"):

    ws = master_sheet.worksheet("StaffSchedule")
    full = pd.DataFrame(ws.get_all_records())

    remaining = full[
        full["Branch"] != st.session_state.selected_branch
    ]

    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = datetime.now().strftime("%A %d %B")

    if "Name" in new_data.columns:
        new_data["Name"] = new_data["Name"].astype(str).str.upper()

    final = pd.concat([remaining, new_data], ignore_index=True)

    ws.clear()
    ws.update(
        [final.columns.tolist()] +
        final.fillna("").values.tolist()
    )

    st.success("✅ Saved Successfully!")
    st.rerun()

# =========================================
# BACK
# =================================

if st.button("⬅ Back"):
    st.switch_page("app.py")
