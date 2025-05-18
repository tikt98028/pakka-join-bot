import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIG ===
GOOGLE_CREDENTIALS_PATH = "/etc/secrets/google-credentials.json"
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# === LOAD CREDS ===
try:
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_CREDENTIALS_PATH, SCOPE
    )
    client = gspread.authorize(credentials)
except Exception as e:
    raise RuntimeError(f"❌ Failed to authorize Google Sheets client: {e}")

# === LOAD SHEET ===
SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    raise ValueError("❌ SHEET_ID is not set in environment variables")

try:
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    raise RuntimeError(f"❌ Failed to open Google Sheet: {e}")

# === FUNCTION: Add user to sheet ===
def add_user_to_sheet(user_id: int, username: str, first_name: str = ""):
    username = username or "no_username"
    first_name = first_name or ""
    try:
        sheet.append_row([str(user_id), username, first_name])
        print(f"✅ [SHEET] User added: {user_id} | {username}")
    except Exception as e:
        print(f"⚠️ [SHEET] Failed to add user: {e}")
