import streamlit as st
import requests

st.set_page_config(page_title="Amalia - Mon Assistant IA 🤖", page_icon="🤖")

st.title("🤖 Amalia - Ton assistant IA")
st.write("Pose ta question et Amalia te répondra grâce à l'IA Groq !")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.text_input("Pose ta question ici:", key="text_input")

def get_amalia_response(user_input):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    
    if not api_key:
        return "⚠️ Clé API Groq manquante !"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "system", "content": "Tu es Amalia, une assistante IA conviviale et créative."}]
    
    for msg in st.session_state.history:
        messages.append({"role": "user", "content": msg["user"]})
        messages.append({"role": "assistant", "content": msg["assistant"]})
    
    messages.append({"role": "user", "content": user_input})
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"Erreur API : {resp.status_code}"
    except Exception as e:
        return f"Erreur : {str(e)}"

if st.button("Envoyer ✨") and user_input:
    with st.spinner("Amalia réfléchit..."):
        answer = get_amalia_response(user_input)
        st.session_state.history.append({"user": user_input, "assistant": answer})

st.markdown("---")
st.markdown("### 💬 Conversation")

for msg in st.session_state.history:
    with st.chat_message("user"):
        st.write(msg["user"])
    with st.chat_message("assistant"):
        st.write(msg["assistant"])

if st.session_state.history:
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.history = []
        st.rerun()



