import os
import requests
import hashlib
import time
from dotenv import load_dotenv

load_dotenv()

PIXEL_ID = os.getenv("PIXEL_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
API_URL = f"https://graph.facebook.com/v18.0/{PIXEL_ID}/events"

def hash_user_data(value):
    if value:
        return hashlib.sha256(value.strip().lower().encode()).hexdigest()
    return None

def send_facebook_event(event_id: str, user_data: dict, test_event_code: str = None):
    payload = {
        "data": [{
            "event_name": "LeadComplete",
            "event_time": int(time.time()),
            "event_id": event_id,
            "action_source": "system_generated",
            "user_data": {
                "em": hash_user_data(user_data.get("email")),
                "ph": hash_user_data(user_data.get("phone")),
                "fn": hash_user_data(user_data.get("first_name")),
                "ln": hash_user_data(user_data.get("last_name")),
            }
        }],
        "access_token": ACCESS_TOKEN
    }

    if test_event_code:
        payload["test_event_code"] = test_event_code

    response = requests.post(API_URL, json=payload)
    return response.status_code, response.text
