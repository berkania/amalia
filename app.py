import streamlit as st
import requests
import os

st.set_page_config(page_title="Amalia - Mon Assistant IA 🤖")

st.title("🤖 Amalia - Ton assistant IA")
st.write("Pose ta question et Amalia te répondra grâce à l'IA Groq !")

# Initialiser l'historique
if "history" not in st.session_state:
    st.session_state.history = []

# Zone de texte pour la question
user_input = st.text_input("Pose ta question ici:")

# Bouton d'envoi
if st.button("Envoyer") and user_input:
    api_key = st.secrets.get("GROQ_API_KEY", "")
    
    if not api_key:
        st.error("⚠️ Clé API Groq manquante ! Configure-la dans les secrets Streamlit.")
    else:
        with st.spinner("Amalia réfléchit..."):
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            # Construire l'historique des messages
            messages = [{"role": "system", "content": "Tu es Amalia, une assistante IA conviviale et créative."}]
            
            for msg in st.session_state.history:
                messages.append({"role": "user", "content": msg["user"]})
                messages.append({"role": "assistant", "content": msg["assistant"]})
            
            messages.append({"role": "user", "content": user_input})
            
            data = {
                "model": "llama3-70b-8192",
                "messages": messages
            }
            
            try:
                resp = requests.post(url, headers=headers, json=data)
                
                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"]
                    st.session_state.history.append({"user": user_input, "assistant": answer})
                else:
                    st.error(f"Erreur API : {resp.status_code} - {resp.text}")
            except Exception as e:
                st.error(f"Erreur : {str(e)}")

# Afficher l'historique
for msg in st.session_state.history:
    with st.chat_message("user"):
        st.write(msg["user"])
    with st.chat_message("assistant"):
        st.write(msg["assistant"])

