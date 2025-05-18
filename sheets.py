import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

GOOGLE_CREDENTIALS_PATH = "/etc/secrets/google-credentials.json"
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    GOOGLE_CREDENTIALS_PATH, SCOPE
)
client = gspread.authorize(credentials)
SHEET_ID = os.getenv("SHEET_ID")
sheet = client.open_by_key(SHEET_ID).sheet1

# ➕ Додати користувача
def add_user_to_sheet(user_id: int, username: str, first_name: str, joined_at: str, invite_source: str):
    try:
        sheet.append_row([
            str(user_id),
            username or "",
            first_name or "",
            joined_at,
            invite_source
        ])
        print(f"[+] Added to sheet: {user_id}")
    except Exception as e:
        print(f"[!] Sheets error: {e}")

# 📊 Всього користувачів
def get_total_users():
    return len(sheet.get_all_records())

# 📋 Останні N користувачів
def get_last_users(limit=5):
    rows = sheet.get_all_records()
    return rows[-limit:]

# ⏱ За останні 24 години
def get_users_last_24h():
    now = datetime.utcnow()
    count = 0
    for row in sheet.get_all_records():
        try:
            joined_at = datetime.strptime(row["joined_at"], "%Y-%m-%d %H:%M:%S")
            if now - joined_at <= timedelta(hours=24):
                count += 1
        except:
            continue
    return count

# 📊 Джерела приєднання
def get_users_by_source():
    source_map = {}
    for row in sheet.get_all_records():
        source = row.get("invite_source", "unknown")
        source_map[source] = source_map.get(source, 0) + 1
    return source_map.items()
