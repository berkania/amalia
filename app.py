from auth import add_user, validate_user, list_users, has_secret_journal, create_secret_journal, validate_journal_code, load_journal_content, save_journal_content
import streamlit as st
import requests
from datetime import datetime
import html
import logging
import os
import random
import time
from gtts import gTTS
from supabase import create_client, Client
from assistant import traiter_commande  # Import du fichier assistant.py pour l'assistant vocal

# Configuration du logging pour les erreurs
logging.basicConfig(level=logging.ERROR)

# Configuration Supabase
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

        if res.error:
            st.error(f"Erreur Supabase lors de la sauvegarde : {res.error}")
            return None

        if not res.data:
            logging.error("Erreur lors de la sauvegarde du chat : pas de données retournées")
            return None

        return res.data[0]["id"]
    except Exception as e:
        logging.error(f"Erreur save_chat: {e}")
        return None

def load_chats(username):
    try:
        res_chats = supabase.table("chats").select("*").eq("username", username).execute()
        chats = {}
        chat_ids = []

        for row in res_chats.data:
            chat_id = str(row["id"])
            chat_ids.append(chat_id)
            chats[chat_id] = {
                "name": row["name"],
                "messages": [],
                "created": row["created"]
            }

        if chat_ids:
            res_messages = supabase.table("messages").select("*").in_("chat_id", chat_ids).execute()

            for msg in res_messages.data:
                chat_id = str(msg["chat_id"])
                if chat_id in chats:
                    chats[chat_id]["messages"].append({
                        "role": msg["sender"],
                        "content": msg["content"],
                        "timestamp": msg.get("timestamp", "")
                    })

            for chat_id in chats:
                chats[chat_id]["messages"].sort(key=lambda x: x.get("timestamp", ""))

        return chats
    except Exception as e:
        logging.error(f"Erreur load_chats: {e}")
        return {}

def delete_chat(chat_id):
    try:
        supabase.table("chats").delete().eq("id", chat_id).execute()
        supabase.table("messages").delete().eq("chat_id", chat_id).execute()
    except Exception as e:
        logging.error(f"Erreur delete_chat: {e}")

def save_message(chat_id, sender, content):
    try:
        if not str(chat_id).isdigit():
            print(f"⚠️ Chat ID '{chat_id}' n’est pas valide, message non sauvegardé.")
            return

        chat_id = int(chat_id)
        timestamp = datetime.now().isoformat()
        response = supabase.table("messages").insert({
            "chat_id": chat_id,
            "sender": sender,
            "content": content,
            "timestamp": timestamp
        }).execute()

        if response.error:
            st.error(f"❌ Erreur Supabase lors de la sauvegarde du message : {response.error}")
        else:
            print("Message sauvegardé en DB !")
    except Exception as e:
        st.error(f"Erreur save_message: {e}")

def update_chat_name(chat_id, new_name):
    try:
        supabase.table("chats").update({"name": new_name}).eq("id", chat_id).execute()
    except Exception as e:
        logging.error(f"Erreur update_chat_name: {e}")

# Fonctions pour TTS et animation
def parle(text):
    print("🤖:", text)
    tts = gTTS(text=text, lang='fr')
    nom_fichier = f"reponse_{int(time.time())}.mp3"
    tts.save(nom_fichier)
    
    voyelles = [c for c in text.lower() if c in "aeioué"]
    duree = len(text) * 0.06
    
    return nom_fichier, voyelles, duree

def extraire_voyelles(text):
    return [c for c in text.lower() if c in "aeioué"]

# Nettoyage fichiers audio anciens
def nettoyage_audio():
    for f in os.listdir():
        if f.startswith("reponse_") and f.endswith(".mp3"):
            try:
                os.remove(f)
            except Exception:
                pass

nettoyage_audio()

# Configuration de la page
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
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "show_journal" not in st.session_state:
    st.session_state.show_journal = False
if "journal_accessed" not in st.session_state:
    st.session_state.journal_accessed = False
if "journal_data" not in st.session_state:
    st.session_state.journal_data = None
if "create_journal_step" not in st.session_state:
    st.session_state.create_journal_step = 0
if "journal_temp" not in st.session_state:
    st.session_state.journal_temp = {"color": "", "name": "", "code": "", "confirm_code": ""}
if "show_character_chat" not in st.session_state:
    st.session_state.show_character_chat = False
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None
if "expression" not in st.session_state:
    st.session_state.expression = "neutre"
if "show_assistant" not in st.session_state:
    st.session_state.show_assistant = False
if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""

# Fonction pour obtenir la réponse du personnage
def get_character_response(user_input, character_prompt, chat_history):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        return "⚠️ Clé API manquante"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "system", "content": character_prompt}]
    for msg in chat_history:
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

# Fonction pour obtenir la réponse d'Amalia
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

# Logique de connexion/inscription
if not st.session_state.logged_in:
    st.sidebar.title("Connexion")
    
    if st.sidebar.button("Se connecter", key="show_login_btn"):
        st.session_state.show_login = True
        st.session_state.show_register = False
    
    if st.sidebar.button("Créer un compte", key="show_register_btn"):
        st.session_state.show_register = True
        st.session_state.show_login = False
    
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
                        local_id = "local_1"
                        st.session_state.chats[local_id] = chat_data
                        st.session_state.current_chat_id = local_id
                        st.warning("⚠️ Persistance désactivée : vérifiez vos tables Supabase. Les chats sont temporaires.")
                else:
                    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                st.rerun()
            else:
                st.sidebar.error("Nom d'utilisateur ou mot de passe incorrect")
    
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
    
    st.stop()

# Logique après connexion
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
        local_id = f"local_{len(st.session_state.chats) + 1}"
        st.session_state.chats[local_id] = chat_data
        st.session_state.current_chat_id = local_id
        st.warning("⚠️ Persistance désactivée : vérifiez vos tables Supabase")

# Sidebar après connexion
st.sidebar.success(f"Connecté en tant que {st.session_state.logged_user}")
if st.sidebar.button("Carnet Secret", key="journal_btn"):
    st.session_state.show_journal = True
    st.session_state.journal_accessed = False
    st.session_state.create_journal_step = 0
    st.session_state.show_character_chat = False
    st.session_state.show_assistant = False
    st.rerun()

if st.sidebar.button("Conversation avec Personnage", key="character_chat_btn"):
    st.session_state.show_character_chat = True
    st.session_state.show_journal = False
    st.session_state.show_assistant = False
    st.rerun()

if st.sidebar.button("Assistant Vocal", key="assistant_btn"):
    st.session_state.show_assistant = True
    st.session_state.show_journal = False
    st.session_state.show_character_chat = False
    st.rerun()

if st.sidebar.button("Déconnexion", key="logout_btn"):
    st.session_state.logged_user = None
    st.session_state.logged_in = False
    st.session_state.show_login = False
    st.session_state.show_register = False
    st.session_state.chats = {}
    st.session_state.current_chat_id = None
    st.session_state.show_journal = False
    st.session_state.journal_accessed = False
    st.session_state.journal_data = None
    st.session_state.create_journal_step = 0
    st.session_state.journal_temp = {"color": "", "name": "", "code": "", "confirm_code": ""}
    st.session_state.show_character_chat = False
    st.session_state.show_assistant = False
    st.rerun()

# Logique conditionnelle pour les modes
if st.session_state.show_journal and st.session_state.logged_in:
    st.title("🔒 Carnet Secret")
    
    if not has_secret_journal(st.session_state.logged_user):
        if st.session_state.create_journal_step == 0:
            if st.button("Créer un nouveau carnet secret", key="create_journal_btn"):
                st.session_state.create_journal_step = 1
                st.rerun()
        elif st.session_state.create_journal_step == 1:
            st.subheader("Étape 1 : Choisissez la couleur de votre espace")
            color = st.color_picker("Couleur", "#ff0000")
            if st.button("Suivant", key="journal_step1_next"):
                st.session_state.journal_temp["color"] = color
                st.session_state.create_journal_step = 2
                st.rerun()
        elif st.session_state.create_journal_step == 2:
            st.subheader("Étape 2 : Donnez un nom à votre carnet")
            name = st.text_input("Nom du carnet")
            if st.button("Suivant", key="journal_step2_next"):
                if name:
                    st.session_state.journal_temp["name"] = name
                    st.session_state.create_journal_step = 3
                    st.rerun()
                else:
                    st.error("Nom requis.")
        elif st.session_state.create_journal_step == 3:
            st.subheader("Étape 3 : Définissez un code (chiffres seulement)")
            code = st.text_input("Code (chiffres)", type="password")
            confirm_code = st.text_input("Confirmer le code", type="password")
            if st.button("Créer le carnet", key="create_journal_final"):
                if code == confirm_code and code.isdigit():
                    if create_secret_journal(st.session_state.logged_user, st.session_state.journal_temp["name"], st.session_state.journal_temp["color"], code):
                        st.session_state.journal_data = load_journal_content(st.session_state.logged_user)
                        st.session_state.journal_accessed = True
                        st.session_state.create_journal_step = 0
                        st.rerun()
                else:
                    st.error("Codes ne correspondent pas ou ne sont pas des chiffres.")
    else:
        if not st.session_state.journal_accessed:
            st.subheader("Entrez le code de votre carnet secret")
            code = st.text_input("Code (chiffres)", type="password")
            if st.button("Accéder", key="access_journal_btn"):
                if validate_journal_code(st.session_state.logged_user, code):
                    st.session_state.journal_data = load_journal_content(st.session_state.logged_user)
                    st.session_state.journal_accessed = True
                    st.rerun()
                else:
                    st.error("Code incorrect.")
        else:
            journal = st.session_state.journal_data
            st.markdown(f"<h2 style='color: {journal['color']};'>{journal['name']}</h2>", unsafe_allow_html=True)
            
            pages = journal["content"]["pages"]
            page_options = [f"Page {i+1}: {p['title']}" for i, p in enumerate(pages)]
            selected_page = st.selectbox("Sélectionnez une page", page_options)
            page_index = page_options.index(selected_page)
            
            title = st.text_input("Titre de la page", value=pages[page_index]["title"])
            content = st.text_area("Contenu", value=pages[page_index]["content"], height=300)
            
            if st.button("Sauvegarder la page", key="save_page_btn"):
                pages[page_index]["title"] = title
                pages[page_index]["content"] = content
                save_journal_content(st.session_state.logged_user, journal["content"])
                st.success("Page sauvegardée !")
            
            if st.button("Ajouter une nouvelle page", key="add_page_btn"):
                pages.append({"title": f"Nouvelle Page {len(pages)+1}", "content": ""})
                save_journal_content(st.session_state.logged_user, journal["content"])
                st.rerun()
    
        if st.button("Retour au chat", key="return_to_chat_from_journal"):
        st.session_state.show_journal = False
        st.rerun()

elif st.session_state.show_character_chat and st.session_state.logged_in:
    st.title("💬 Conversation avec ton Personnage")
    
    if "selected_character" not in st.session_state:
        st.session_state.selected_character = None
    if "character_chat_history" not in st.session_state:
        st.session_state.character_chat_history = []
    
    characters = {
        "AYKIA": {
            "name": "AYKIA",
            "description": "Une assistante IA espiègle et amicale, toujours prête à discuter et à aider !",
            "prompt": "Tu es AYKIA, une assistante IA conviviale, espiègle et professionnelle. Réponds de manière fun et engageante.",
            "image_folder": "characters/aykia/",
            "default_image": "neutral.png"
        }
    }
    
    if st.session_state.selected_character is None:
        st.subheader("Choisis ton personnage pour commencer la conversation !")
        cols = st.columns(len(characters))
        for i, (key, char) in enumerate(characters.items()):
            with cols[i]:
                image_path = os.path.join(char["image_folder"], char["default_image"])
                if os.path.exists(image_path):
                    st.image(image_path, width=150, caption=char["name"])
                else:
                    st.write(f"Image non trouvée pour {char['name']}")
                if st.button(f"Choisir {char['name']}", key=f"select_{key}"):
                    st.session_state.selected_character = key
                    st.session_state.character_chat_history = []
                    st.rerun()
    
    else:
        char = characters[st.session_state.selected_character]
        st.subheader(f"Conversation avec {char['name']}")
        st.write(char["description"])
        
        image_path = os.path.join(char["image_folder"], char["default_image"])
        if os.path.exists(image_path):
            st.image(image_path, width=200)
        
        for msg in st.session_state.character_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if prompt := st.chat_input(f"Parle à {char['name']}..."):
            st.session_state.character_chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            response = get_character_response(prompt, char["prompt"], st.session_state.character_chat_history[:-1])
            
            st.session_state.character_chat_history.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
            
            st.rerun()
        
        if st.button("Changer de personnage", key="change_character_btn"):
            st.session_state.selected_character = None
            st.session_state.character_chat_history = []
            st.rerun()
        
        if st.button("Retour au chat Amalia", key="return_to_amalia_from_character"):
            st.session_state.selected_character = None
            st.session_state.character_chat_history = []
            st.session_state.show_character_chat = False
            st.rerun()

elif st.session_state.show_assistant and st.session_state.logged_in:
    st.title("🎤 Assistant Vocal")
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 400px;">
        <svg width="200" height="200">
            <circle cx="100" cy="100" r="90" fill="#10a37f" stroke="#0d8a6d" stroke-width="10"/>
            <text x="100" y="110" text-anchor="middle" fill="white" font-size="20" font-family="Arial">Assistant</text>
        </svg>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("Appuie sur le micro pour parler à l'assistant vocal.")
    
    # Bouton micro pour capturer la voix
    mic_html = """
    <div style="margin-top: 20px; text-align: center;">
        <button id="micBtn" style="
            background: linear-gradient(135deg, #10a37f 0%, #0d8a6d 100%);
            color: white;
            border: none;
            padding: 15px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            width: 60px;
            height: 60px;
        ">🎤</button>
        <div id="status" style="font-size: 12px; margin-top: 8px; color: #666;"></div>
    </div>

    <script>
    const micBtn = document.getElementById('micBtn');
    const status = document.getElementById('status');

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'fr-FR';
        recognition.continuous = false;

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
            status.textContent = '✓ Commande reçue';
            
            // Envoyer la transcription à Streamlit
            fetch(window.location.href, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({voice_input: transcript})
            }).then(() => window.location.reload());
        };

        recognition.onerror = function() {
            status.textContent = '❌ Erreur';
            micBtn.style.background = 'linear-gradient(135deg, #10a37f 0%, #0d8a6d 100%)';
            micBtn.textContent = '🎤';
        };
    } else {
        status.textContent = 'Non supporté';
    }
    </script>
    """
    st.components.v1.html(mic_html, height=100)
    
    if st.session_state.voice_input:
        traiter_commande(st.session_state.voice_input)
        st.session_state.voice_input = ""
    
    if st.button("Retour au chat Amalia", key="return_to_amalia_from_assistant"):
        st.session_state.show_assistant = False
        st.rerun()

else:
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
            transition: all 0.2s ease;
        }
        .chat-item:hover {
            background: #e2e2e5;
        }
        .chat-item.active {
            background: #10a37f;
            color: white;
        }
    </style>
    """ , unsafe_allow_html=True)

    # Affichage du chat principal Amalia
    st.title("💬 Chat Amalia")

    chat_ids = list(st.session_state.chats.keys())
    cols = st.columns([3, 7])

    # Liste des chats à gauche
    with cols[0]:
        st.subheader("Chats")
        for chat_id in chat_ids:
            chat_name = st.session_state.chats[chat_id]["name"]
            if st.button(chat_name, key=f"select_chat_{chat_id}"):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        if st.button("Nouveau chat", key="new_chat_btn"):
            chat_data = {
                "name": f"Nouveau Chat {len(st.session_state.chats)+1}",
                "messages": [],
                "created": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            chat_db_id = save_chat(st.session_state.logged_user, chat_data)
            if chat_db_id:
                st.session_state.chats[str(chat_db_id)] = chat_data
                st.session_state.current_chat_id = str(chat_db_id)
            else:
                local_id = f"local_{len(st.session_state.chats)+1}"
                st.session_state.chats[local_id] = chat_data
                st.session_state.current_chat_id = local_id
                st.warning("⚠️ Persistance désactivée : vérifiez vos tables Supabase")
            st.rerun()

    # Messages du chat sélectionné à droite
    with cols[1]:
        if st.session_state.current_chat_id:
            chat_data = st.session_state.chats[st.session_state.current_chat_id]
            for msg in chat_data["messages"]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            if prompt := st.chat_input("Écris un message..."):
                chat_data["messages"].append({"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()})
                save_message(st.session_state.current_chat_id, "user", prompt)

                # Générer une réponse simple pour Amalia
                response = f"Amalia répond : {prompt[::-1]}"  # Exemple de réponse inversée pour test
                chat_data["messages"].append({"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})
                save_message(st.session_state.current_chat_id, "assistant", response)
                st.rerun()




