import streamlit as st
import requests
import os

st.set_page_config(page_title="Amalia - Mon Assistant IA 🤖")

st.title("🤖 Amalia - Ton assistant IA")
st.write("Pose ta question et Amalia te répondra grâce à l’IA Groq !")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.text_input("Pose ta question ici:")

if st.button("Envoyer") and user_input:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        st.error("Aucune clé API Groq trouvée, configure ton secret !")
    else:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        url = "https://api.groq.com/openai/v1/chat/completions"
        data = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "Tu es Amalia, une assistante IA conviviale et créative."},
                *(
                    [
                        {"role": "user", "content": msg["user"]},
                        {"role": "assistant", "content": msg["assistant"]}
                    ] for msg in st.session_state.history
                ),
                {"role": "user", "content": user_input}
            ]
        }
        # Flatten list of lists
        messages = [item for sublist in data["messages"] if isinstance(sublist, list) for item in sublist] + \
                   [item for item in data["messages"] if not isinstance(item, list)]
        data["messages"] = messages
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            answer = resp.json()["choices"][0]["message"]["content"]
            st.session_state.history.append({"user": user_input, "assistant": answer})
            st.chat_message("user").write(user_input)
            st.chat_message("assistant").write(answer)
        else:
            st.error(resp.text)
else:
    for msg in st.session_state.history:
        st.chat_message("user").write(msg["user"])
        st.chat_message("assistant").write(msg["assistant"])
