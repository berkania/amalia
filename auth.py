import sqlite3
import bcrypt
import os
import logging

# Configuration du logging pour les erreurs
logging.basicConfig(level=logging.ERROR)

def connect_db():
    os.makedirs("db", exist_ok=True)  # Crée le dossier si nécessaire
    conn = sqlite3.connect("db/users.db", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")  # Active les foreign keys
    return conn

def create_tables():
    try:
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
        logging.info("Tables créées avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de la création des tables : {e}")
    finally:
        conn.close()

def add_user(username, password):
    if not username or not password:
        logging.error("Nom d'utilisateur ou mot de passe vide.")
        return False
    try:
        conn = connect_db()
        cursor = conn.cursor()
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        logging.error(f"L'utilisateur '{username}' existe déjà.")
        return False
    except Exception as e:
        logging.error(f"Erreur lors de l'ajout de l'utilisateur : {e}")
        return False
    finally:
        conn.close()

def validate_user(username, password):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username=?', (username,))
        row = cursor.fetchone()
        if row:
            stored_hash = row[0]
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        return False
    except Exception as e:
        logging.error(f"Erreur lors de la validation : {e}")
        return False
    finally:
        conn.close()

# Appel automatique pour créer les tables au démarrage
create_tables()


