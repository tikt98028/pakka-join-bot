import sqlite3
from datetime import datetime, timedelta
import pytz
import csv

DB_NAME = "users.db"
KYIV_TZ = pytz.timezone("Europe/Kyiv")

def get_kyiv_time():
    return datetime.now(KYIV_TZ).strftime('%Y-%m-%d %H:%M:%S')

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                username TEXT,
                first_name TEXT,
                joined_at TEXT,
                invite_source TEXT
            )
        """)
        conn.commit()

def add_user(telegram_id, username, first_name, invite_source="unknown"):
    joined_at = get_kyiv_time()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (telegram_id, username, first_name, joined_at, invite_source)
            VALUES (?, ?, ?, ?, ?)
        """, (
            telegram_id,
            username,
            first_name,
            joined_at,
            invite_source
        ))
        conn.commit()

def get_total_users():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]

def get_last_users(limit=5):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT telegram_id, username, first_name, joined_at
            FROM users ORDER BY id DESC LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def get_all_user_ids():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users")
        return [row[0] for row in cursor.fetchall()]

def export_users_to_csv(filename="users.csv"):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, username, first_name, joined_at, invite_source FROM users")
        rows = cursor.fetchall()
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["telegram_id", "username", "first_name", "joined_at", "invite_source"])
            writer.writerows(rows)

def get_users_by_source():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT invite_source, COUNT(*) FROM users
            GROUP BY invite_source
        """)
        return cursor.fetchall()

def get_users_last_24h():
    since = (datetime.now(KYIV_TZ) - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM users
            WHERE joined_at >= ?
        """, (since,))
        return cursor.fetchone()[0]
