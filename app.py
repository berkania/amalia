from auth import add_user, validate_user, list_users
import streamlit as st
import requests
from datetime import datetime
import html
import logging
from supabase import create_client, Client

# Configuration du logging pour les erreurs
logging.basicConfig(level=logging.ERROR)

# Configuration Supabase (réutilisez celle de auth.py)
url = "https://eyffbmbmwdhrzzcboawu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5ZmZibWJtd2Rocnp6Y2JvYXd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2Njc2NzksImV4cCI6MjA3NzI0MzY3OX0.iSfIDxTpdnwAdSSzjo6tFOZJs8ZQGY5DE50TIo2_79I"
supabase: Client = create_client(url, key)

# Fonctions de persistance avec Supabase
def save_chat(username, chat_data):
    try:
        res = supabase.table("chats").insert({
            "username": username,
            "name": chat_data["name"],
            "messages": chat_data["messages"],
            "created": chat_data["created"]
        }).execute()
        if res.data:
            return res.data[0]["id"]  # Retourne l'ID du chat créé
        else:
            logging.error("Erreur lors de la sauvegarde du chat : pas de données retournées")
            return None
    except Exception as e:
        logging.error(f"Erreur save_chat: {e}")
        return None

def load_chats(username):
    try:
        # Charger les chats depuis la table chats
        res_chats = supabase.table("chats").select("*").eq("username", username).execute()
        chats = {}
        for row in res_chats.data:
            chat_id = str(row["id"])
            chats[chat_id] = {
                "name": row["name"],
                "messages": [],  # Initialiser vide, on va charger les messages séparément
                "created": row["created"]
            }
        
        # Charger les messages depuis la table messages et les associer aux chats
        res_messages = supabase.table("messages").select("*").eq("chat_id", list(chats.keys())).execute()
        for msg in res_messages.data:
            chat_id = str(msg["chat_id"])
            if chat_id in chats:
                chats[chat_id]["messages"].append({
                    "role": msg["sender"],  # "user" ou "assistant"
                    "content": msg["content"]
                })
        
        # Trier les messages par timestamp si nécessaire (optionnel)
        for chat_id in chats:
            chats[chat_id]["messages"].sort(key=lambda x: x.get("timestamp", ""), reverse=False)
        
        return chats
    except Exception as e:
        logging.error(f"Erreur load_chats: {e}")
        return {}

def update_chat(chat_id, chat_data):
    try:
        supabase.table("chats").update({
            "messages": chat_data["messages"]
        }).eq("id", chat_id).execute()
    except Exception as e:
        logging.error(f"Erreur update_chat: {e}")

def delete_chat(chat_id):
    try:
        supabase.table("chats").delete().eq("id", chat_id).execute()
        supabase.table("messages").delete().eq("chat_id", chat_id).execute()  # Supprime aussi les messages
    except Exception as e:
        logging.error(f"Erreur delete_chat: {e}")

def save_message(chat_id, sender, content):
    try:
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "sender": sender,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        logging.error(f"Erreur save_message: {e}")

# Configuration de la page (une seule fois au début)
st.set_page_config(
    page_title="Amalia - Assistant IA",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialisation de la session (une seule fois)
if "logged_user" not in st.session_state:
    st.session_state.logged_user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# Logique de connexion/inscription
if not st.session_state.logged_in:
    st.sidebar.title("Connexion")
    
    # Boutons pour afficher les formulaires (avec clés uniques)
    if st.sidebar.button("Se connecter", key="show_login_btn"):
        st.session_state.show_login = True
        st.session_state.show_register = False
    
    if st.sidebar.button("Créer un compte", key="show_register_btn"):
        st.session_state.show_register = True
        st.session_state.show_login = False
    
    # Formulaire de connexion
    if st.session_state.show_login:
        st.sidebar.subheader("Connexion")
        username = st.sidebar.text_input("Nom d'utilisateur", key="login_username")
        password = st.sidebar.text_input("Mot de passe", type="password", key="login_password")
        if st.sidebar.button("Valider Connexion", key="validate_login_btn"):
            if validate_user(username, password):
                st.session_state.logged_user = username
                st.session_state.logged_in = True
                st.session_state.show_login = False
                st.session_state.chats = load_chats(username)
                if not st.session_state.chats:
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
                        # Fallback local si DB échoue
                        local_id = "local_1"
                        st.session_state.chats[local_id] = chat_data
                        st.session_state.current_chat_id = local_id
                        st.warning("⚠️ Persistance désactivée : vérifiez vos tables Supabase. Les chats sont temporaires.")
                else:
                    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
            else:
                st.sidebar.error("Nom d'utilisateur ou mot de passe incorrect")
    
    # Formulaire d'inscription
    if st.session_state.show_register:
        st.sidebar.subheader("Créer un compte")
        new_user = st.sidebar.text_input("Nouveau nom d'utilisateur", key="register_username")
        new_password = st.sidebar.text_input("Nouveau mot de passe", type="password", key="register_password")
        if st.sidebar.button("Valider Inscription", key="validate_register_btn"):
            if add_user(new_user, new_password):
                st.sidebar.success("Compte créé avec succès ! Cliquez sur 'Se connecter' pour vous connecter.")
                st.session_state.show_register = False
            else:
                st.sidebar.error("Erreur lors de la création du compte (utilisateur existe déjà ou champs vides).")
    
    st.stop()  # Arrête l'app si pas connecté

# Logique après connexion : Vérifier et créer un chat par défaut si nécessaire
if not st.session_state.chats or st.session_state.current_chat_id not in st.session_state.chats:
    chat_data = {
        "name": "Nouveau Chat",
        "messages": [],
        "created": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    chat_db_id = save_chat(st.session_state.logged_user, chat_data)
    if chat_db_id:
        st.session_state.chats[str(chat_db_id)] = chat_data
        st.session_state.current_chat_id = str(chat_db_id)
    else:
        # Fallback local
        local_id = f"local_{len(st.session_state.chats) + 1}"
        st.session_state.chats[local_id] = chat_data
        st.session_state.current_chat_id = local_id
        st.warning("⚠️ Persistance désactivée : vérifiez vos tables Supabase. Les chats sont temporaires.")

st.sidebar.success(f"Connecté en tant que {st.session_state.logged_user}")
if st.sidebar.button("Déconnexion", key="logout_btn"):
    st.session_state.logged_user = None
    st.session_state.logged_in = False
    st.session_state.show_login = False
    st.session_state.show_register = False
    st.session_state.chats = {}
    st.session_state.current_chat_id = None

# CSS
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
    
    if st.button("➕ Nouveau Chat", key="new_chat_btn", use_container_width=True, type="primary"):
        chat_data = {
            "name": "Nouveau Chat",
            "messages": [],
            "created": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        chat_db_id = save_chat(st.session_state.logged_user, chat_data)
        if chat_db_id:
            st.session_state.chats[str(chat_db_id)] = chat_data
            st.session_state.current_chat_id = str(chat_db_id)
        else:
            # Fallback local
            local_id = f"local_{len(st.session_state.chats) + 1}"
            st.session_state.chats[local_id] = chat_data
            st.session_state.current_chat_id = local_id
    
    st.markdown("---")
    
    sorted_chats = sorted(
        st.session_state.chats.items(),
        key=lambda x: x[1]["created"],
        reverse=True
    )
    
    for chat_id, chat_data in sorted_chats:
        if len(chat_data["messages"]) > 0:
            first_msg = chat_data["messages"][0]["content"]
            chat_name = first_msg[:30] + "..." if len(first_msg) > 30 else first_msg
        else:
            chat_name = "Nouveau Chat"
        
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
        
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                if len(st.session_state.chats) > 1:
                    delete_chat(chat_id)
                    del st.session_state.chats[chat_id]
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Total chats", len(st.session_state.chats))
    # Vérification de sécurité avant d'accéder à current_chat
    if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chats:
        current_chat = st.session_state.chats[st.session_state.current_chat_id]
        st.metric("Messages", len(current_chat["messages"]))
    else:
        st.metric("Messages", 0)

# Afficher les messages (avec vérification de sécurité)
if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chats:
    current_chat = st.session_state.chats[st.session_state.current_chat_id]
    
    for message in current_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(f'<div style="color: #000000;">{message["content"]}</div>', unsafe_allow_html=True)
else:
    st.error("Erreur : Aucun chat actif trouvé. Rechargez la page.")

# Bouton micro et input
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
        # Vérifier que le chat existe avant d'ajouter
        if st.session_state.current_chat_id and st.session_state.current_chat_id in st.session_state.chats:
            current_chat = st.session_state.chats[st.session_state.current_chat_id]
            
            # Ajouter message utilisateur
            current_chat["messages"].append({"role": "user", "content": prompt})
            save_message(st.session_state.current_chat_id, "user", prompt)  # Sauvegarder dans DB
            
            # Afficher message utilisateur
            with st.chat_message("user"):
                st.markdown(f'<div style="color




