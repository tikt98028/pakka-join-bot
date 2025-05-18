import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

def add_user_to_sheet(user_id: int, username: str, first_name: str, joined_at: str, invite_source: str):
    try:
        sheet.append_row([
            str(user_id),
            username,
            first_name,
            joined_at,
            invite_source
        ])
        print(f"[+] Added to Google Sheet: {user_id} from {invite_source}")
    except Exception as e:
        print(f"[!] Sheets error: {e}")
