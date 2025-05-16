import sqlite3
from datetime import datetime
import csv
from openpyxl import Workbook

DB_NAME = "users.db"

# === Ініціалізація бази
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

# === Додати користувача
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

# === Всього юзерів
def get_total_users():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]

# === Останні юзери
def get_last_users(limit=5):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT telegram_id, username, first_name, joined_at
            FROM users ORDER BY id DESC LIMIT ?
        """, (limit,))
        return cursor.fetchall()

# === Усі ID для розсилки
def get_all_user_ids():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users")
        return [row[0] for row in cursor.fetchall()]

# === Експорт у .xlsx
def export_users_to_xlsx(filename="users.xlsx"):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, username, first_name, joined_at FROM users")
        rows = cursor.fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Users"
        ws.append(["telegram_id", "username", "first_name", "joined_at"])
        for row in rows:
            ws.append(row)

        wb.save(filename)
