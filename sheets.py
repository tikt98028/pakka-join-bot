import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Файл ключа сервісного акаунта (поклади в корінь проєкту)
CREDENTIALS_FILE = "pakka-sheets-sync-b080d6114c1f.json"  # <-- назви свій .json саме так
SPREADSHEET_NAME = "Pakka Users"

# Підключення до Google Sheets
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet

# Додає нового юзера
def add_user_to_sheet(telegram_id, username, first_name):
    sheet = get_sheet()
    joined_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    sheet.append_row([
        str(telegram_id),
        username if username else "",
        first_name if first_name else "",
        joined_at
    ])
