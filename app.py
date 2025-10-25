import streamlit as st
import requests

st.set_page_config(page_title="Amalia 🤖", page_icon="🤖", layout="centered")

# CSS pour style ChatGPT
st.markdown("""
<style>
    .main > div {
        padding-bottom: 100px;
    }
    .stChatInput {
        position: fixed;
        bottom: 0;
        background: white;
        padding: 20px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Amalia")

# Initialisation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Fonction pour obtenir la réponse d'Amalia
def get_amalia_response(user_input):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    
    if not api_key:
        return "⚠️ Clé API manquante"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "system", "content": "Tu es Amalia, une assistante IA conviviale."}]
    
    for msg in st.session_state.messages:
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

# Afficher l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Interface de chat avec micro intégré
chat_container = st.container()

with chat_container:
    # HTML pour la barre de chat style ChatGPT avec micro
    chat_html = """
    <div style="position: fixed; bottom: 0; left: 0; right: 0; background: white; padding: 20px; border-top: 1px solid #ddd; z-index: 1000;">
        <div style="max-width: 800px; margin: 0 auto; display: flex; gap: 10px; align-items: center;">
            <button id="micBtn" style="
                background: #f0f0f0;
                border: none;
                padding: 12px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 20px;
                transition: all 0.2s;
            " title="Appuie pour parler">🎤</button>
            
            <input type="text" id="chatInput" placeholder="Écris ton message..." style="
                flex: 1;
                padding: 12px 16px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                outline: none;
            ">
            
            <button id="sendBtn" style="
                background: #10a37f;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 18px;
            ">➤</button>
        </div>
        <div id="status" style="text-align: center; margin-top: 10px; font-size: 14px; color: #666;"></div>
    </div>

    <script>
    const micBtn = document.getElementById('micBtn');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const status = document.getElementById('status');
    
    let isRecording = false;
    let recognition = null;

    // Configuration de la reconnaissance vocale
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'fr-FR';
        recognition.continuous = false;

        micBtn.onclick = function() {
            if (!isRecording) {
                recognition.start();
                isRecording = true;
                micBtn.style.background = '#ff4444';
                micBtn.textContent = '⏺️';
                status.textContent = '🎙️ Écoute en cours...';
            } else {
                recognition.stop();
                isRecording = false;
                micBtn.style.background = '#f0f0f0';
                micBtn.textContent = '🎤';
                status.textContent = '';
            }
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            status.textContent = '✅ "' + transcript + '"';
            isRecording = false;
            micBtn.style.background = '#f0f0f0';
            micBtn.textContent = '🎤';
        };

        recognition.onerror = function() {
            status.textContent = '❌ Autorise le micro !';
            isRecording = false;
            micBtn.style.background = '#f0f0f0';
            micBtn.textContent = '🎤';
        };
    } else {
        micBtn.disabled = true;
        micBtn.style.opacity = '0.5';
    }

    // Envoyer avec la flèche
    sendBtn.onclick = function() {
        if (chatInput.value.trim()) {
            const streamlitInput = window.parent.document.querySelector('input[data-testid="stChatInput"]');
            if (streamlitInput) {
                streamlitInput.value = chatInput.value;
                streamlitInput.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Simuler Enter
                const enterEvent = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    bubbles: true
                });
                streamlitInput.dispatchEvent(enterEvent);
            }
            chatInput.value = '';
        }
    };

    // Envoyer avec Enter
    chatInput.onkeydown = function(e) {
        if (e.key === 'Enter') {
            sendBtn.click();
        }
    };
    </script>
    """
    
    st.components.v1.html(chat_html, height=120)

# Input Streamlit caché (pour récupérer le message)
if prompt := st.chat_input("Message...", key="hidden_input"):
    # Ajouter le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # Obtenir et afficher la réponse
    with st.chat_message("assistant"):
        with st.spinner("Réflexion..."):
            response = get_amalia_response(prompt)
            st.write(response)
            
            # Réponse vocale si le message vient du micro
            speech_html = f"""
            <script>
            const text = `{response.replace('`', '').replace('"', '\\"').replace("'", "\\'")}`;
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'fr-FR';
            window.speechSynthesis.speak(utterance);
            </script>
            """
            st.components.v1.html(speech_html, height=0)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()









