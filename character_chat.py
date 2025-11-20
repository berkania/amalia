import streamlit as st
import requests
from datetime import datetime
import os

# Fonction pour obtenir la réponse du personnage (réutilise ta logique Groq)
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

# Définition des personnages (ajoute-en plus tard)
characters = {
    "AYKIA": {
        "name": "AYKIA",
        "description": "Une assistante IA espiègle et amicale, toujours prête à discuter et à aider !",
        "prompt": "Tu es AYKIA, une assistante IA conviviale, espiègle et professionnelle. Réponds de manière fun et engageante.",
        "image_folder": "characters/aykia/",
        "default_image": "neutral.png"  # Image par défaut
    },
    # Ajoute d'autres personnages ici, e.g.,
    # "Robot Sage": {
    #     "name": "Robot Sage",
    #     "description": "Un robot sage et réfléchi, expert en philosophie.",
    #     "prompt": "Tu es un robot sage, réponds de manière réfléchie et profonde.",
    #     "image_folder": "characters/robot_sage/",
    #     "default_image": "thinking.gif"
    # }
}

# Fonction principale pour la conversation avec le personnage
def run_character_chat():
    st.title("💬 Conversation avec ton Personnage")
    
    # Initialisation des états de session pour ce module
    if "selected_character" not in st.session_state:
        st.session_state.selected_character = None
    if "character_chat_history" not in st.session_state:
        st.session_state.character_chat_history = []
    
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
            response = get_character_response(prompt, char["prompt"], st.session_state.character_chat_history[:-1])  # Exclure le dernier message pour éviter la duplication
            
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
            st.rerun()
