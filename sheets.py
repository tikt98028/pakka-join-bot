import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from pytz import timezone

# 🔐 Шлях до Google credentials
GOOGLE_CREDENTIALS_PATH = "/etc/secrets/google-credentials.json"

# 🔗 Права доступу
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔑 Авторизація
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
        print(f"[+] Додано в таблицю: {user_id}")
    except Exception as e:
        print(f"[!] Sheets помилка: {e}")

# 📬 Усі telegram_id
def get_all_user_ids():
    return [
        int(row["telegram_id"]) for row in sheet.get_all_records()
        if row.get("telegram_id", "").isdigit()
    ]

# 📊 Всі користувачі
def get_total_users():
    return len(sheet.get_all_records())

# 📋 Останні N користувачів
def get_last_users(limit=5):
    return sheet.get_all_records()[-limit:]

# 📅 Користувачі за СЬОГОДНІ (за Києвом)
def get_users_today():
    kyiv = timezone("Europe/Kyiv")
    today = datetime.now(kyiv).date()
    count = 0

    for row in sheet.get_all_records():
        try:
            dt = datetime.strptime(row["joined_at"], "%Y-%m-%d %H:%M:%S")
            dt = kyiv.localize(dt)
            if dt.date() == today:
                count += 1
        except:
            continue

    return count

# 📈 Джерела приєднання (всі)
def get_users_by_source():
    stats = {}
    for row in sheet.get_all_records():
        source = row.get("invite_source", "unknown")
        stats[source] = stats.get(source, 0) + 1
    return stats.items()

# 🔗 Кількість з одного джерела
def count_by_source(source_name: str) -> int:
    return sum(
        1 for row in sheet.get_all_records()
        if row.get("invite_source") == source_name
    )

# 📅 Джерела за СЬОГОДНІ (за Києвом)
def get_users_today_by_source():
    kyiv = timezone("Europe/Kyiv")
    today = datetime.now(kyiv).date()
    stats = {}

    for row in sheet.get_all_records():
        try:
            dt = datetime.strptime(row["joined_at"], "%Y-%m-%d %H:%M:%S")
            dt = kyiv.localize(dt)
            if dt.date() == today:
                source = row.get("invite_source", "unknown")
                stats[source] = stats.get(source, 0) + 1
        except:
            continue

    return stats.items()
