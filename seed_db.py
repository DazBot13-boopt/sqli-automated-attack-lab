#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL
)
""")

cur.execute("""
CREATE TABLE secret_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note TEXT NOT NULL
)
""")

users = [
    ("admin", "S3cr3tAdm1nP@ss!", 1),
    ("alice", "alicepassword123", 0),
    ("bob", "bobpassword456", 0),
]
cur.executemany("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", users)

products = [
    ("Clavier mecanique", "Clavier gaming RGB", 59.99),
    ("Souris sans fil", "Souris ergonomique 2.4GHz", 29.99),
    ("Ecran 27 pouces", "Ecran 4K IPS", 249.99),
    ("Casque audio", "Casque filaire avec micro", 39.99),
    ("Webcam HD", "Webcam 1080p USB", 24.99),
]
cur.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)

cur.execute("INSERT INTO secret_notes (note) VALUES (?)", ("CTF{DEMO_FLAG_FOUND_VIA_AUTOMATED_SQLI}",))

conn.commit()
conn.close()
print(f"Database seeded at {DB_PATH}")
