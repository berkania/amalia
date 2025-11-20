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

        if res.error:
            st.error(f"Erreur Supabase lors de la sauvegarde : {res.error}")
            return None

        if not res.data:
            logging.error("Erreur lors de la sauvegarde du chat : pas de données retournées")
            return None

        return res.data[0]["id"]  # Retourne l'ID du chat créé si succès

    except Exception as e:
        logging.error(f"Erreur save_chat: {e}")
        return None

def load_chats(username):
    try:
        # Charger tous les chats de l'utilisateur
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

        # Charger les messages associés à ces chats
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

            # Trier les messages par ordre chronologique
            for chat_id in chats:
                chats[chat_id]["messages"].sort(key=lambda x: x.get("timestamp", ""))

        return chats
    except Exception as e:
        logging.error(f"Erreur load_chats: {e}")
        return {}

def delete_chat(chat_id):
    try:
        supabase.table("chats").delete().eq("id", chat_id).execute()
        supabase.table("messages").delete().eq("chat_id", chat_id).execute()  # Supprime aussi les messages
    except Exception as e:
        logging.error(f"Erreur delete_chat: {e}")

def save_message(chat_id, sender, content):
    try:
        # Si c’est un chat local (pas enregistré en DB), on ignore
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
            print("Message sauvegardé en DB !")  # Pour déboguer, peut être retiré en prod

    except Exception as e:
        st.error(f"Erreur save_message: {e}")

# Nouvelle fonction pour mettre à jour le nom du chat dans la DB
def update_chat_name(chat_id, new_name):
    try:
        supabase.table("chats").update({"name": new_name}).eq("id", chat_id).execute()
    except Exception as e:
        logging.error(f"Erreur update_chat_name: {e}")

# Fonctions pour TTS et animation (inspirées de votre code AYKIA)
def parle(text):
    """Synthèse vocale avec gTTS et animation de l'image."""
    print("🤖:", text)
    tts = gTTS(text=text, lang='fr')
    nom_fichier = f"reponse_{int(time.time())}.mp3"
    tts.save(nom_fichier)
    
    # Animation basée sur les voyelles (simulée via JS)
    voyelles = [c for c in text.lower() if c in "aeioué"]
    duree = len(text) * 0.06  # Durée approximative
    
    # Retourner les données pour JS
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
# Nouveaux états pour le carnet secret
if "show_journal" not in st.session_state:
    st.session_state.show_journal = False
if "journal_accessed" not in st.session_state:
    st.session_state.journal_accessed = False
if "journal_data" not in st.session_state:
    st.session_state.journal_data = None
if "create_journal_step" not in st.session_state:
    st.session_state.create_journal_step = 0  # 0: rien, 1: couleur, 2: nom, 3: code
if "journal_temp" not in st.session_state:
    st.session_state.journal_temp = {"color": "", "name": "", "code": "", "confirm_code": ""}
# Nouveaux états pour le chat avec personnages
if "show_character_chat" not in st.session_state:
    st.session_state.show_character_chat = False
# États pour l'animation et TTS
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None
if "expression" not in st.session_state:
    st.session_state.expression = "neutre"

# Fonction pour obtenir la réponse du personnage (déplacée ici pour éviter NameError)
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
                st.rerun()  # Force rerun pour afficher le chat
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
        st.warning("⚠️ Persistance désactivée : vérifiez vos tables Supabase")

# Suite du code pour app.py (continuation après la logique de connexion/inscription)

# Sidebar après connexion
st.sidebar.success(f"Connecté en tant que {st.session_state.logged_user}")
if st.sidebar.button("Carnet Secret", key="journal_btn"):
    st.session_state.show_journal = True
    st.session_state.journal_accessed = False
    st.session_state.create_journal_step = 0
    st.session_state.show_character_chat = False  # Désactiver les autres modes
    st.rerun()

if st.sidebar.button("Conversation avec Personnage", key="character_chat_btn"):
    st.session_state.show_character_chat = True
    st.session_state.show_journal = False  # Désactiver les autres modes
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
    st.rerun()

# Logique conditionnelle pour les modes
if st.session_state.show_journal and st.session_state.logged_in:
    # Interface du Carnet Secret
    st.title("🔒 Carnet Secret")
    
    if not has_secret_journal(st.session_state.logged_user):
        # Pas de carnet : proposer de créer
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
        # Carnet existe : demander le code ou afficher l'interface
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
            # Interface du carnet : éditeur avec pages
            journal = st.session_state.journal_data
            st.markdown(f"<h2 style='color: {journal['color']};'>{journal['name']}</h2>", unsafe_allow_html=True)
            
            pages = journal["content"]["pages"]
            page_options = [f"Page {i+1}: {p['title']}" for i, p in enumerate(pages)]
            selected_page = st.selectbox("Sélectionnez une page", page_options)
            page_index = page_options.index(selected_page)
            
            # Éditeur de la page
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
    # Interface du Chat avec Personnages (intégrée directement)
    st.title("💬 Conversation avec ton Personnage")
    
    # Initialisation des états de session pour ce module
    if "selected_character" not in st.session_state:
        st.session_state.selected_character = None
    if "character_chat_history" not in st.session_state:
        st.session_state.character_chat_history = []
    
    # Définition des personnages (ajoute-en plus tard)
    characters = {
        "AYKIA": {
            "name": "AYKIA",
            "description": "Une assistante IA espiègle et amicale, toujours prête à discuter et à aider !",
            "prompt": "Tu es AYKIA, une assistante IA conviviale, espiègle et professionnelle. Réponds de manière fun et engageante.",
            
            "default_image": "neutral.png"  # Image par défaut
        },
        # Ajoute d'autres personnages ici
    }
    
    # Étape 1 : Sélection du personnage
    if st.session_state.selected_character is None:
        st.subheader("Choisis ton personnage pour commencer la conversation !")
        cols = st.columns(len(characters))
        for i, (key, char) in enumerate(characters.items()):
            with cols[i]:
                # Afficher l'image du personnage
                image_path = os.path.join(char["image_folder"], char["default_image"])
                if os.path.exists(image_path):
                    st.image(image_path, width=150, caption=char["name"])
                else:
                    st.write(f"Image non trouvée pour {char['name']}")
                if st.button(f"Choisir {char['name']}", key=f"select_{key}"):
                    st.session_state.selected_character = key
                    st.session_state.character_chat_history = []  # Reset l'historique
                    st.rerun()
    
    # Étape 2 : Conversation avec le personnage sélectionné
    else:
        char = characters[st.session_state.selected_character]
        st.subheader(f"Conversation avec {char['name']}")
        st.write(char["description"])
        
        # Afficher l'image animée du personnage (si GIF, elle s'anime automatiquement)
        image_path = os.path.join(char["image_folder"], char["default_image"])
        if os.path.exists(image_path):
            st.image(image_path, width=200)
        
        # Afficher l'historique des messages
        for msg in st.session_state.character_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Input pour le message utilisateur
        if prompt := st.chat_input(f"Parle à {char['name']}..."):
            # Ajouter le message utilisateur
            st.session_state.character_chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Obtenir la réponse du personnage
            response = get_character_response(prompt, char["prompt"], st.session_state.character_chat_history[:-1])
            
            # Ajouter la réponse
            st.session_state.character_chat_history.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
            
            st.rerun()
        
        # Bouton pour changer de personnage
        if st.button("Changer de personnage", key="change_character_btn"):
            st.session_state.selected_character = None
            st.session_state.character_chat_history = []
            st.rerun()
        
        # Bouton pour retourner au chat normal
        if st.button("Retour au chat Amalia", key="return_to_amalia_from_character"):
            st.session_state.selected_character = None
            st.session_state.character_chat_history = []
            st.session_state.show_character_chat = False
            st.rerun()

else:
    # Interface de chat normale (Amalia)
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
            st.rerun()
        
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
            
            is_active = chat_id == st.session_state.current_chat_id
            if st.button(
                f"{'📌' if is_active else '💬'} {chat_name}",
                key=f"chat_{chat_id}",
                use_container_width=True,
                type="secondary" if is_active else "tertiary"
            ):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        
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
                current_chat["messages"].append({"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()})
                save_message(st.session_state.current_chat_id, "user", prompt)
                
                # Afficher message utilisateur
                with st.chat_message("user"):
                    st.markdown(f'<div style="color: #000000;">{prompt}</div>', unsafe_allow_html=True)
                
                # Obtenir la réponse de l'IA
                response = get_response(prompt, st.session_state.current_chat_id)
                
                # Ajouter le message de l'assistante
                current_chat["messages"].append({"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})
                save_message(st.session_state.current_chat_id, "assistant", response)
                
                # Afficher le message de l'assistante
                with st.chat_message("assistant"):
                    st.markdown(f'<div style="color: #000000;">{response}</div>', unsafe_allow_html=True)
                
                st.rerun()  # Recharger la page pour mettre à jour l'affichage

       




