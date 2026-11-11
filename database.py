import sqlite3
from pathlib import Path
from utils.auth import hash_password
from utils.maps_config import campus_login_admin_email, campus_login_admin_password

DB_NAME = Path(__file__).resolve().parent / "database" / "campus.db"

def connect():
    DB_NAME.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS buildings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        x REAL,
        y REAL
    )
    """)

    conn.commit()
    conn.close()

def add_default_data():

    admin_password = campus_login_admin_password()
    if not admin_password:
        return
    admin_email = campus_login_admin_email()

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=?", (admin_email,))

    if cur.fetchone() is None:

        cur.execute("""
        INSERT INTO users(name,email,password,role)
        VALUES(?,?,?,?)
        """,(
            "Administrator",
            admin_email,
            hash_password(admin_password),
            "Admin"
        ))

    conn.commit()
    conn.close()

create_tables()
add_default_data()
