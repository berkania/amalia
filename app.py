import streamlit as st
import requests
import base64
from io import BytesIO

st.set_page_config(page_title="Amalia - Assistant Vocal IA 🤖", page_icon="🤖", layout="wide")

st.title("🤖 Amalia - Ton assistant vocal IA")
st.write("🎤 Utilise le micro de ton navigateur ou écris ta question !")

# CSS personnalisé pour le style
st.markdown("""
    <style>
    .stButton button {
        background-color: #2ecc71;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

# Fonction pour obtenir la réponse d'Amalia
def get_amalia_response(user_input):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    
    if not api_key:
        return "⚠️ Clé API Groq manquante !"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "system", "content": "Tu es Amalia, une assistante IA conviviale et créative. Réponds de manière concise et claire."}]
    
    for msg in st.session_state.history:
        messages.append({"role": "user", "content": msg["user"]})
        messages.append({"role": "assistant", "content": msg["assistant"]})
    
    messages.append({"role": "user", "content": user_input})
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"Erreur API : {resp.status_code}"
    except Exception as e:
        return f"Erreur : {str(e)}"

# Zone de saisie avec reconnaissance vocale HTML5
st.markdown("### 💬 Parle ou écris ta question")

# HTML pour le bouton micro avec reconnaissance vocale native
audio_html = """
<div style="margin-bottom: 20px;">
    <button id="voiceBtn" style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 50px;
        font-size: 18px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
        🎤 Appuie pour parler
    </button>
    <div id="status" style="margin-top: 10px; font-size: 14px; color: #666;"></div>
    <textarea id="voiceInput" style="display:none;"></textarea>
</div>

<script>
const voiceBtn = document.getElementById('voiceBtn');
const status = document.getElementById('status');
const voiceInput = document.getElementById('voiceInput');

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'fr-FR';
    recognition.continuous = false;
    recognition.interimResults = false;

    voiceBtn.onclick = function() {
        recognition.start();
        status.textContent = '🎙️ Écoute en cours... Parle maintenant !';
        voiceBtn.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        voiceInput.value = transcript;
        status.textContent = '✅ Tu as dit : "' + transcript + '"';
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        
        // Trigger Streamlit rerun avec le texte
        const textInput = window.parent.document.querySelector('input[type="text"]');
        if (textInput) {
            textInput.value = transcript;
            textInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
    };

    recognition.onerror = function(event) {
        status.textContent = '❌ Erreur : ' + event.error;
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    };

    recognition.onend = function() {
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    };
} else {
    status.textContent = '❌ La reconnaissance vocale n\'est pas supportée sur ce navigateur. Utilise Chrome ou Edge.';
    voiceBtn.disabled = true;
}
</script>
"""

st.components.v1.html(audio_html, height=150)

# Zone de texte alternative
user_input = st.text_input("Ou écris ta question ici:", key="text_input", placeholder="Tape ta question ou utilise le micro ci-dessus")

# Bouton d'envoi
col1, col2 = st.columns([1, 5])
with col1:
    send_button = st.button("📤 Envoyer")

if send_button and user_input:
    with st.spinner("🤔 Amalia réfléchit..."):
        answer = get_amalia_response(user_input)
        st.session_state.history.append({"user": user_input, "assistant": answer})
        
        # Synthèse vocale avec API Groq TTS (si disponible) ou HTML5
        st.success("✨ Réponse d'Amalia :")
        st.info(answer)
        
        # Lecture vocale HTML5
        speech_html = f"""
        <script>
        const text = `{answer.replace('`', '').replace('"', '\\"')}`;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'fr-FR';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
        </script>
        """
        st.components.v1.html(speech_html, height=0)

# Affichage de l'historique
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📜 Historique des conversations")
    
    for idx, msg in enumerate(reversed(st.session_state.history[-5:])):
        with st.expander(f"💬 Conversation {len(st.session_state.history) - idx}"):
            st.markdown(f"**👤 Toi :** {msg['user']}")
            st.markdown(f"**🤖 Amalia :** {msg['assistant']}")
            
            # Bouton pour réécouter
            replay_html = f"""
            <button onclick="
                const text = `{msg['assistant'].replace('`', '').replace('"', '\\"')}`;
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'fr-FR';
                window.speechSynthesis.speak(utterance);
            " style="
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                cursor: pointer;
            ">🔊 Réécouter</button>
            """
            st.components.v1.html(replay_html, height=50)
    
    # Bouton pour effacer l'historique
    if st.button("🗑️ Effacer tout l'historique"):
        st.session_state.history = []
        st.rerun()





