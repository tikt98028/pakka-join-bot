import sqlite3
from datetime import datetime
import csv

DB_NAME = "users.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                username TEXT,
                first_name TEXT,
                joined_at TEXT
            )
        """)
        conn.commit()

def add_user(telegram_id, username, first_name):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (telegram_id, username, first_name, joined_at)
            VALUES (?, ?, ?, ?)
        """, (
            telegram_id,
            username,
            first_name,
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
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
        cursor.execute("SELECT telegram_id, username, first_name, joined_at FROM users")
        rows = cursor.fetchall()
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["telegram_id", "username", "first_name", "joined_at"])
            writer.writerows(rows)
