import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

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

# ✅ ОНОВЛЕНА ФУНКЦІЯ:
def add_user_to_sheet(user_id: int, username: str, first_name: str, joined_at: str):
    try:
        sheet.append_row([str(user_id), username, first_name, joined_at])
        print(f"[+] User added to sheet: {user_id}")
    except Exception as e:
        print(f"[!] Failed to add user to sheet: {e}")
