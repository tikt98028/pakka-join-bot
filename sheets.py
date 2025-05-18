import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# 🔐 Шлях до секретного ключа
GOOGLE_CREDENTIALS_PATH = "/etc/secrets/google-credentials.json"

# 🔗 Права доступу
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔄 Авторизація Google Sheets
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
            invite_source or ""
        ])
        print(f"[+] Added to sheet: {user_id}")
    except Exception as e:
        print(f"[!] Sheets error: {e}")

# 📬 Отримати всі telegram_id
def get_all_user_ids():
    ids = []
    for row in sheet.get_all_records():
        try:
            ids.append(int(row["telegram_id"]))
        except:
            continue
    return ids

# 📊 Кількість всіх користувачів
def get_total_users():
    return len(sheet.get_all_records())

# 📋 Останні N користувачів
def get_last_users(limit=5):
    rows = sheet.get_all_records()
    return rows[-limit:]

# ⏱ Користувачі за останні 24 години
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

# 📊 Джерела приєднання (всі)
def get_users_by_source():
    source_map = {}
    for row in sheet.get_all_records():
        source = row.get("invite_source", "unknown")
        source_map[source] = source_map.get(source, 0) + 1
    return source_map.items()

# 📍 Статистика по конкретному джерелу
def count_by_source(source_name: str) -> int:
    data = sheet.get_all_records()
    return sum(1 for row in data if row.get("invite_source") == source_name)

# 🕒 Статистика за добу по кожному джерелу
def get_users_last_24h_by_source():
    now = datetime.utcnow()
    stats = {}
    for row in sheet.get_all_records():
        try:
            source = row.get("invite_source", "unknown")
            joined_at = datetime.strptime(row["joined_at"], "%Y-%m-%d %H:%M:%S")
            if now - joined_at <= timedelta(hours=24):
                stats[source] = stats.get(source, 0) + 1
        except:
            continue
    return stats.items()
