import streamlit as st
import requests
from datetime import datetime
import sqlite3
import bcrypt
import html
import os
import logging

# Configuration du logging pour les erreurs
logging.basicConfig(level=logging.ERROR)

# Fonction pour obtenir la connexion DB
def get_db_connection():
    os.makedirs("db", exist_ok=True)  # Crée le dossier si nécessaire
    conn = sqlite3.connect('db/users.db', check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")  # Active les foreign keys
    c = conn.cursor()
    # Tables utilisateurs, chats, messages
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                created_at TEXT
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                sender TEXT,
                content TEXT,
                timestamp TEXT
            )''')
    conn.commit()
    return conn

# Fonctions pour la persistance des chats et messages
def save_chat(username, chat_data):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO chats (username, created_at) VALUES (?, ?)", (username, chat_data["created"]))
        chat_db_id = c.lastrowid
        conn.commit()
        return chat_db_id  # Retourne l'ID DB pour l'utiliser comme clé
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du chat : {e}")
        return None
    finally:
        conn.close()

def load_chats(username):
    chats = {}
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, created_at FROM chats WHERE username=?", (username,))
        chats_db = c.fetchall()
        for chat_db_id, created_at in chats_db:
            c.execute("SELECT sender, content, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp", (chat_db_id,))
            messages = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
            chats[str(chat_db_id)] = {  # Utilise l'ID DB comme clé
                "name": "Nouveau Chat" if not messages else messages[0]["content"][:30] + "..." if len(messages[0]["content"]) > 30 else messages[0]["content"],
                "messages": messages,
                "created": created_at
            }
    except Exception as e:
        logging.error(f"Erreur lors du chargement des chats : {e}")
    finally:
        conn.close()
    return chats

def delete_chat(chat_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        c.execute("DELETE FROM chats WHERE id=?", (chat_id,))
        conn.commit()
    except Exception as e:
        logging.error(f"Erreur lors de la suppression du chat : {e}")
    finally:
        conn.close()

def save_message(chat_id, sender, content):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO messages (chat_id, sender, content, timestamp) VALUES (?, ?, ?, ?)",
                  (chat_id, sender, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du message : {e}")
    finally:
        conn.close()

# Fonctions pour utilisateurs
def validate_user(username, password):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if row and bcrypt.checkpw(password.encode('utf-8'), row[0]):
            return True
        return False
    except Exception as e:
        logging.error(f"Erreur lors de la validation : {e}")
        return False
    finally:
        conn.close()

def add_user(username, password):
    if not username or not password:
        return False
    try:
        conn = get_db_connection()
        c = conn.cursor()
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
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

st.set_page_config(
    page_title="Amalia - Assistant IA",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialisation de la session
if "logged_user" not in st.session_state:
    st.session_state.logged_user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False

if not st.session_state.logged_in:
    st.sidebar.title("Connexion")
    
    # Boutons pour afficher les formulaires
    if st.sidebar.button("Se connecter"):
        st.session_state.show_login = True
        st.session_state.show_register = False
        st.rerun()
    
    if st.sidebar.button("Créer un compte"):
        st.session_state.show_register = True
        st.session_state.show_login = False
        st.rerun()
    
    # Formulaire de connexion (affiché seulement si bouton cliqué)
    if st.session_state.show_login:
        st.sidebar.subheader("Connexion")
        username = st.sidebar.text_input("Nom d'utilisateur", key="login_username")
        password = st.sidebar.text_input("Mot de passe", type="password", key="login_password")
        if st.sidebar.button("Valider Connexion"):
            if validate_user(username, password):
                st.session_state.logged_user = username
                st.session_state.logged_in = True
                st.session_state.show_login = False
                # Charger les chats depuis la DB
                st.session_state.chats = load_chats(username)
                if not st.session_state.chats:
                    # Créer un premier chat si aucun
                    chat_data = {
                        "name": "Nouveau Chat",
                        "messages": [],
                        "created": datetime.now().strftime("%d/%m/%Y %H:%M")
                    }
                    chat_db_id = save_chat(username, chat_data)
                    if chat_db_id:
                        st.session_state.chats[str(chat_db_id)] = chat_data
                        st.session_state.current_chat_id = str(chat_db_id)
                else:
                    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                st.rerun()
            else:
                st.sidebar.error("Nom d'utilisateur ou mot de passe incorrect")
    
    # Formulaire d'inscription (affiché seulement si bouton cliqué)
    if st.session_state.show_register:
        st.sidebar.subheader("Créer un compte")
        new_user = st.sidebar.text_input("Nouveau nom d'utilisateur", key="register_username")
        new_password = st.sidebar.text_input("Nouveau mot de passe", type="password", key="register_password")
        if st.sidebar.button("Valider Inscription"):
            if add_user(new_user, new_password):
                st.sidebar.success("Compte créé avec succès ! Cliquez sur 'Se connecter' pour vous connecter.")
                st.session_state.show_register = False
                st.rerun()
            else:
                st.sidebar.error("Erreur lors de la création du compte (utilisateur existe déjà ou champs vides).")
    
    st.stop()  # Stop le reste de l'app si pas connecté
else:
    st.sidebar.success(f"Connecté en tant que {st.session_state.logged_user}")
    if st.sidebar.button("Déconnexion"):
        st.session_state.logged_user = None
        st.session_state.logged_in = False
        st.session_state.show_login = False
        st.session_state.show_register = False
        st.rerun()

# CSS professionnel avec texte NOIR
st.markdown("""
<style>
    .main {
        background: #f7f7f8;
    }
    .stChatMessage {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        color: #000000 !important;
    }
    .stChatMessage p {
        color: #000000 !important;
    }
    h1 {
        color: #202123;
        text-align: center;
        padding: 20px;
    }
    .chat-item {
        padding: 12px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        background: #f7f7f8;
        border: 1px solid #e5e5e5;
        transition: all 0.2s;
    }
    .chat-item:hover {
        background: #ececf1;
    }
    .chat-item.active {
        background: #d1d5db;
        border-color: #10a37f;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Amalia")

# Initialisation de la session (chargée depuis DB si connecté)
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    # Créer un premier chat si aucun chargé
    chat_data = {
        "name": "Nouveau Chat",
        "messages": [],
        "created": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    chat_db_id = save_chat(st.session_state.logged_user, chat_data)
    if chat_db_id:
        st.session_state.chats[str(chat_db_id)] = chat_data
        st.session_state.current_chat_id = str(chat_db_id)

# Fonction pour obtenir la réponse
def get_response(user_input, chat_id):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    
    if not api_key:
        return "⚠️ Clé API manquante"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "system", "content": "Tu es Amalia, une assistante IA conviviale et professionnelle."}]
    
    for msg in st.session_state.chats[chat_id]["messages"]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_input})
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"Erreur {resp.status_code}"
    except Exception as e:
        return f"Erreur: {str(e)}"

# Sidebar avec historique des chats
with st.sidebar:
    st.markdown("### 💬 Historique")
    
    # Bouton + Nouveau Chat
    if st.button("➕ Nouveau Chat", use_container_width=True, type="primary"):
        chat_data = {
            "name": "Nouveau Chat",
            "messages": [],
            "created": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        chat_db_id = save_chat(st.session_state.logged_user, chat_data)
        if chat_db_id:
            st.session_state.chats[str(chat_db_id)] = chat_data
            st.session_state.current_chat_id = str(chat_db_id)
            st.rerun()
    
    st.markdown("---")
    
    # Liste des chats (les plus récents en premier)
    sorted_chats = sorted(
        st.session_state.chats.items(),
        key=lambda x: x[1]["created"],
        reverse=True
    )
    
    for chat_id, chat_data in sorted_chats:
        # Définir le nom du chat (premier message ou "Nouveau Chat")
        if len(chat_data["messages"]) > 0:
            first_msg = chat_data["messages"][0]["content"]
            chat_name = first_msg[:30] + "..." if len(first_msg) > 30 else first_msg
        else:
            chat_name = "Nouveau Chat"
        
        # Bouton pour sélectionner ce chat
        col1, col2 = st.columns([4, 1])
        
        with col1:
            is_active = chat_id == st.session_state.current_chat_id
            if st.button(
                f"{'📌' if is_active else '💬'} {chat_name}",
                key=f"chat_{chat_id}",
                use_container_width=True,
                type="secondary" if is_active else "tertiary"
            ):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        
        with col2:
            # Bouton supprimer
            if st.button("🗑️", key=f"del_{chat_id}"):
                if len(st.session_state.chats) > 1:
                    delete_chat(chat_id)  # Supprimer de la DB
                    del st.session_state.chats[chat_id]
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Total chats", len(st.session_state.chats))
    current_chat = st.session_state.chats[st.session_state.current_chat_id]
    st.metric("Messages", len(current_chat["messages"]))

# Afficher les messages du chat actuel
current_chat = st.session_state.chats[st.session_state.current_chat_id]

for message in current_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(f'<div style="color: #000000;">{message["content"]}</div>', unsafe_allow_html=True)

# Bouton micro
col1, col2 = st.columns([1, 10])

with col1:
    mic_html = """
    <div style="margin-top: 8px;">
        <button id="micBtn" style="
            background: linear-gradient(135deg, #10a37f 0%, #0d8a6d 100%);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            width: 50px;
            height: 50px;
        ">🎤</button>
        <div id="status" style="font-size: 10px; text-align: center; margin-top: 4px; color: #666;"></div>
    </div>

    <script>
    const micBtn = document.getElementById('micBtn');
    const status = document.getElementById('status');

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'fr-FR';

        micBtn.onclick = function() {
            recognition.start();
            micBtn.style.background = 'linear-gradient(135deg, #ff4444 0%, #cc0000 100%)';
            micBtn.textContent = '⏺️';
            status.textContent = 'Écoute...';
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            micBtn.style.background = 'linear-gradient(135deg, #10a37f 0%, #0d8a6d 100%)';
            micBtn.textContent = '🎤';
            status.textContent = '✓';
            
            const chatInput = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (chatInput) {
                chatInput.value = transcript;
                chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                window.parent.sessionStorage.setItem('voiceMode', 'true');
            }
        };

        recognition.onerror = function() {
            status.textContent = '❌';
            micBtn.style.background = 'linear-gradient(135deg, #10a37f 0%, #0d8a6d 100%)';
            micBtn.textContent = '🎤';
        };
    } else {
        status.textContent = 'Non supporté';
    }
    </script>
    """
    st.components.v1.html(mic_html, height=80)

with col2:
    # Input de chat
    if prompt := st.chat_input("Message Amalia..."):
        # Ajouter message utilisateur
        current_chat["messages"].append({"role": "user", "content": prompt})
        save_message(st.session_state.current_chat_id, "user", prompt)  # Sauvegarder dans DB
        
        # Afficher message utilisateur
        with st.chat_message("user"):
            st.markdown(f'<div style="color: #000000;">{prompt}</div>', unsafe_allow_html=True)
        
        # Obtenir réponse
        with st.chat_message("assistant"):
            with st.spinner("Amalia réfléchit..."):
                response = get_response(prompt, st.session_state.current_chat_id)
                st.markdown(f'<div style="color: #000000;">{response}</div>', unsafe_allow_html=True)
        
        # Ajouter réponse à l'historique et sauvegarder
        current_chat["messages"].append({"role": "assistant", "content": response})
        save_message(st.session_state.current_chat_id, "assistant", response)
        
        # Synthèse vocale si mode vocal
        escaped_response = html.escape(response)
        check_voice_html = f"""
        <script>
        const voiceMode = window.parent.sessionStorage.getItem('voiceMode');
        if (voiceMode === 'true') {{
            window.parent.sessionStorage.removeItem('voiceMode');
            const response = `{escaped_response}`;
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance(response);
                utterance.lang = 'fr-FR';
                window.speechSynthesis.speak(utterance);
            }}
        }}
        </script>
        """
        st.components.v1.html(check_voice_html, height=0)
        
        st.rer
