import sqlite3
import bcrypt

def connect_db():
    conn = sqlite3.connect("db/users.db", check_same_thread=False)
    return conn

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            chat_name TEXT,
            created_at TEXT,
            FOREIGN KEY (user) REFERENCES users(username)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY (chat_id) REFERENCES chats(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cursor.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, hashed))
    conn.commit()
    conn.close()

def validate_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username=?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        stored_hash = row[0]
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    return False

