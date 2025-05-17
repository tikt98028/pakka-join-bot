import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Параметри ===
SHEET_ID = "1fppuW2FtrJ7hXGkypgz52xZuMiMYr8zsZ2TeSnqutyA"
SHEET_NAME = "Лист1"  # або "Sheet1", якщо англійська версія

# === Авторизація Google API ===
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    return sheet

# === Додати рядок
def append_user_to_sheet(telegram_id, username, first_name, joined_at):
    sheet = get_sheet()
    sheet.append_row([telegram_id, username or "", first_name or "", joined_at])
