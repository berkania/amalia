import streamlit as st
import requests

st.set_page_config(page_title="Amalia - Assistant Vocal IA 🤖", page_icon="🤖", layout="wide")

st.title("🤖 Amalia - Ton assistant vocal IA")
st.markdown("**🎤 Parle au micro** = Réponse vocale | **✍️ Écris** = Réponse écrite")

# CSS personnalisé
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
if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False
if "voice_transcript" not in st.session_state:
    st.session_state.voice_transcript = ""

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

# Interface avec micro vocal
st.markdown("### 🎤 Reconnaissance vocale")

# HTML pour le bouton micro avec reconnaissance vocale
voice_html = """
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
        🎤 Clique et parle
    </button>
    <div id="status" style="margin-top: 15px; font-size: 16px; font-weight: bold; color: #333;"></div>
</div>

<script>
const voiceBtn = document.getElementById('voiceBtn');
const status = document.getElementById('status');

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'fr-FR';
    recognition.continuous = false;
    recognition.interimResults = false;

    let isListening = false;

    voiceBtn.onclick = function() {
        if (!isListening) {
            recognition.start();
            isListening = true;
            status.textContent = '🎙️ Écoute en cours... Parle maintenant !';
            status.style.color = '#e74c3c';
            voiceBtn.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
            voiceBtn.textContent = '⏹️ Arrêter';
        } else {
            recognition.stop();
            isListening = false;
            voiceBtn.textContent = '🎤 Clique et parle';
            voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        }
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        status.textContent = '✅ Tu as dit : "' + transcript + '"';
        status.style.color = '#27ae60';
        isListening = false;
        voiceBtn.textContent = '🎤 Clique et parle';
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        
        // Envoyer à Streamlit via query params
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            data: {transcript: transcript, voice_mode: true}
        }, '*');
    };

    recognition.onerror = function(event) {
        status.textContent = '❌ Erreur : Assure-toi d\'autoriser le micro !';
        status.style.color = '#e74c3c';
        isListening = false;
        voiceBtn.textContent = '🎤 Clique et parle';
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    };

    recognition.onend = function() {
        isListening = false;
        voiceBtn.textContent = '🎤 Clique et parle';
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    };
} else {
    status.textContent = '❌ Utilise Chrome, Edge ou Safari pour le micro !';
    status.style.color = '#e74c3c';
    voiceBtn.disabled = true;
}
</script>
"""

voice_component = st.components.v1.html(voice_html, height=150)

# Capturer la transcription vocale
if voice_component:
    if "transcript" in voice_component:
        st.session_state.voice_transcript = voice_component["transcript"]
        st.session_state.voice_mode = voice_component.get("voice_mode", False)

# Traiter automatiquement la transcription vocale
if st.session_state.voice_transcript and st.session_state.voice_mode:
    user_voice_input = st.session_state.voice_transcript
    
    with st.spinner("🤔 Amalia réfléchit..."):
        answer = get_amalia_response(user_voice_input)
        st.session_state.history.append({"user": user_voice_input, "assistant": answer, "mode": "voice"})
        
        # Afficher la réponse
        st.success(f"**Tu as dit :** {user_voice_input}")
        st.info(f"**🤖 Amalia répond :** {answer}")
        
        # Lecture vocale automatique
        speech_html = f"""
        <script>
        const text = `{answer.replace('`', '').replace('"', '\\"').replace("'", "\\'")}`;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'fr-FR';
        utterance.rate = 1.0;
        utterance.pitch = 1.1;
        window.speechSynthesis.speak(utterance);
        </script>
        """
        st.components.v1.html(speech_html, height=0)
    
    # Réinitialiser
    st.session_state.voice_transcript = ""
    st.session_state.voice_mode = False

# Mode texte
st.markdown("---")
st.markdown("### ✍️ Ou écris ta question")

user_text_input = st.text_input("Tape ta question ici:", key="text_input", placeholder="Écris ta question...")

if st.button("📤 Envoyer (mode texte)"):
    if user_text_input:
        with st.spinner("🤔 Amalia réfléchit..."):
            answer = get_amalia_response(user_text_input)
            st.session_state.history.append({"user": user_text_input, "assistant": answer, "mode": "text"})
            
            # Afficher la réponse (texte seulement)
            st.success("**✨ Réponse d'Amalia :**")
            st.write(answer)

# Historique
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📜 Historique")
    
    for idx, msg in enumerate(reversed(st.session_state.history[-5:])):
        mode_icon = "🎤" if msg.get("mode") == "voice" else "✍️"
        with st.expander(f"{mode_icon} Conversation {len(st.session_state.history) - idx}"):
            st.markdown(f"**👤 Toi :** {msg['user']}")
            st.markdown(f"**🤖 Amalia :** {msg['assistant']}")
            
            # Bouton réécouter
            replay_key = f"replay_{idx}"
            replay_html = f"""
            <button onclick="
                const text = `{msg['assistant'].replace('`', '').replace('"', '\\"').replace("'", "\\'")}`;
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
            ">🔊 Réécouter cette réponse</button>
            """
            st.components.v1.html(replay_html, height=50, key=replay_key)
    
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.history = []
        st.rerun()







