import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime

# 🔐 Шлях до секретного файла на Render
GOOGLE_CREDENTIALS_PATH = "/etc/secrets/google-credentials.json"

# 📡 Права доступу до Google Sheets + Drive API
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔑 Завантаження облікових даних
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    GOOGLE_CREDENTIALS_PATH, SCOPE
)

# 🚀 Авторизація клієнта Google Sheets
client = gspread.authorize(credentials)

# 📄 Ідентифікатор таблиці з env
SHEET_ID = os.getenv("SHEET_ID")

# 📑 Відкриваємо таблицю
sheet = client.open_by_key(SHEET_ID).sheet1

# ⚡ Функція: додати нового користувача
def add_user_to_sheet(user_id: int, username: str, first_name: str):
    try:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([str(user_id), username, first_name, timestamp])
        print(f"[+] User added to sheet: {user_id} - {username}")
    except Exception as e:
        print(f"[!] Failed to add user to sheet: {e}")
