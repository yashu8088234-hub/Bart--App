# -----------------------------
# PASSWORDS FROM MASTER SHEET
# -----------------------------
def load_passwords_from_master(branch_data):
    """
    Converts master sheet into:
    { "B01 - Jeddah Branch": "pass123", "ADMIN": "admin123" }
    """
    passwords = {}

    for row in branch_data:
        key = row["BranchCode"]
        if row["BranchCode"] != "ADMIN":
            key = f"{row['BranchCode']} - {row['BranchName']}"

        passwords[key] = row.get("Password", "")

    return passwords


def get_admin_password(branch_data):
    for row in branch_data:
        if row["BranchCode"] == "ADMIN":
            return row.get("Password", "")
    return None
