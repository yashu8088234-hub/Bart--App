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

gs = gspread.authorize(creds)
ws = gs.open_by_key("1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0").worksheet("StaffSchedule")

# =========================
# 2. CONFIG
# =========================
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

SHIFT_OPTIONS = ["Morning shift", "Mid shift", "Evening shift", "Night shift"]
TIME_OPTIONS = [f"{h}:00 AM" for h in range(1, 13)] + [f"{h}:00 PM" for h in range(1, 13)] + ["OFF"]

SHIFT_COLORS = {
    "Morning shift": "#FFF3B0",
    "Mid shift": "#BDE0FE",
    "Evening shift": "#CDB4DB",
    "Night shift": "#A2D2FF",
}

# =========================
# 3. UI
# =========================
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")

start_date = st.date_input("Week Start Date")
shift_mode = st.toggle("Enable Shift-wise Mode")

day_dates = [(start_date + timedelta(days=i)).strftime("%a %d/%m") for i in range(7)]

# =========================
# 4. LOAD DATA
# =========================
def load_data():
    df = pd.DataFrame(ws.get_all_records())

    if df.empty:
        df = pd.DataFrame(columns=["Branch", "Date", "Name", "Role"] + DAYS)

    return df[df["Branch"] == st.session_state.selected_branch].copy()


df = load_data()

# =========================
# 5. CLEAN STRUCTURE (NO GHOST COLUMNS)
# =========================
df_display = df.copy()

for day in DAYS:
    for col in [day, f"{day}: Start", f"{day}: End", f"{day}: Finish"]:
        if col in df_display.columns:
            df_display.drop(columns=[col], inplace=True)

for day in DAYS:
    if shift_mode:
        df_display[day] = df.get(day, "")
    else:
        df_display[f"{day}: Start"] = df.get(f"{day}: Start", "")
        df_display[f"{day}: End"] = df.get(f"{day}: End", df.get(f"{day}: Finish", ""))

# Ensure base columns
if "Role" not in df_display.columns:
    df_display["Role"] = ""
if "Name" not in df_display.columns:
    df_display["Name"] = ""

# =========================
# 6. CONFLICT DETECTION
# =========================
def detect_conflicts(data):
    conflicts = []

    for i, row in data.iterrows():
        for day in DAYS:
            val = row.get(day) if shift_mode else row.get(f"{day}: Start")

            if isinstance(val, str) and val.strip() == "":
                continue

            # simple rule: duplicate shift assignment check
            if val in SHIFT_OPTIONS and list(data[day].values).count(val) > 1:
                conflicts.append((i, day))

    return conflicts


conflicts = detect_conflicts(df_display)

if conflicts:
    st.warning("⚠ Some shifts are duplicated across staff (check assignments)")

# =========================
# 7. COLUMN CONFIG
# =========================
config = {
    "Name": st.column_config.TextColumn("Name"),
    "Role": st.column_config.SelectboxColumn("Role", options=[
        "Staff",
        "Supervisor",
        "Acting Supervisor",
        "Team Leader",
        "Acting Team Leader"
    ])
}

for i, day in enumerate(DAYS):

    label = f"({day_dates[i]})"

    if shift_mode:
        config[day] = st.column_config.SelectboxColumn(
            label,
            options=SHIFT_OPTIONS
        )
    else:
        config[f"{day}: Start"] = st.column_config.SelectboxColumn(
            f"{label} Start",
            options=TIME_OPTIONS
        )
        config[f"{day}: End"] = st.column_config.SelectboxColumn(
            f"{label} End",
            options=TIME_OPTIONS
        )

# =========================
# 8. UI TABLE
# =========================
edited_df = st.data_editor(
    df_display,
    column_config=config,
    use_container_width=True,
    num_rows="dynamic"
)

# =========================
# 9. SAVE (SAFE UPSERT)
# =========================
if st.button("💾 Save Schedule", type="primary"):

    all_data = pd.DataFrame(ws.get_all_records())

    # remove only this branch
    all_data = all_data[all_data["Branch"] != st.session_state.selected_branch]

    new_data = edited_df.copy()
    new_data["Branch"] = st.session_state.selected_branch
    new_data["Date"] = str(start_date)

    if "Name" in new_data.columns:
        new_data["Name"] = new_data["Name"].astype(str).str.upper()

    final = pd.concat([all_data, new_data], ignore_index=True)

    ws.clear()
    ws.update([final.columns.tolist()] + final.fillna("").values.tolist())

    st.success("✅ Schedule updated successfully")
    st.rerun()

# =========================
# 10. BACK
# =========================
if st.button("⬅ Back"):
    st.switch_page("app.py")
