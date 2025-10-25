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
    
    messages = [{"role": "system", "content": "Tu es Amalia, une assistante IA conviviale et créative. Réponds de manière concise."}]
    
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
st.markdown("### 🎤 Mode Vocal")
st.markdown("Clique sur le bouton, **autorise le micro**, parle, et Amalia te répondra à l'oral !")

# HTML pour reconnaissance vocale + envoi automatique
voice_html = """
<div style="margin-bottom: 20px;">
    <button id="voiceBtn" style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 20px 40px;
        border-radius: 50px;
        font-size: 20px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
        🎤 Clique pour parler
    </button>
    <div id="status" style="margin-top: 15px; font-size: 16px; font-weight: bold;"></div>
    <input type="hidden" id="voiceResult" value="">
</div>

<script>
const voiceBtn = document.getElementById('voiceBtn');
const status = document.getElementById('status');
const voiceResult = document.getElementById('voiceResult');

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'fr-FR';
    recognition.continuous = false;
    recognition.interimResults = false;

    voiceBtn.onclick = function() {
        recognition.start();
        status.textContent = '🎙️ Écoute en cours... Parle maintenant !';
        status.style.color = '#e74c3c';
        voiceBtn.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        voiceResult.value = transcript;
        status.textContent = '✅ Tu as dit : "' + transcript + '"';
        status.style.color = '#27ae60';
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        
        // Déclencher le formulaire Streamlit
        const forms = window.parent.document.querySelectorAll('form');
        if (forms.length > 0) {
            const input = forms[0].querySelector('input[type="text"]');
            if (input) {
                input.value = transcript;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Simuler le clic sur le bouton vocal
                const buttons = window.parent.document.querySelectorAll('button');
                for (let btn of buttons) {
                    if (btn.textContent.includes('🎤 Envoyer en mode vocal')) {
                        btn.click();
                        break;
                    }
                }
            }
        }
    };

    recognition.onerror = function(event) {
        status.textContent = '❌ Erreur : Autorise le micro dans ton navigateur !';
        status.style.color = '#e74c3c';
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    };

    recognition.onend = function() {
        voiceBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    };
} else {
    status.textContent = '❌ Utilise Chrome, Edge ou Safari pour le micro !';
    status.style.color = '#e74c3c';
    voiceBtn.disabled = true;
}
</script>
"""

st.components.v1.html(voice_html, height=180)

# Zone de saisie partagée
user_input = st.text_input("", key="shared_input", placeholder="Tu peux aussi écrire ici...", label_visibility="collapsed")

# Deux boutons : un pour vocal, un pour texte
col1, col2 = st.columns(2)

with col1:
    voice_button = st.button("🎤 Envoyer en mode vocal")

with col2:
    text_button = st.button("✍️ Envoyer en mode texte")

# Traitement mode vocal
if voice_button and user_input:
    with st.spinner("🤔 Amalia réfléchit..."):
        answer = get_amalia_response(user_input)
        st.session_state.history.append({"user": user_input, "assistant": answer, "mode": "voice"})
        
        st.success(f"**🎤 Tu as dit :** {user_input}")
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

# Traitement mode texte
if text_button and user_input:
    with st.spinner("🤔 Amalia réfléchit..."):
        answer = get_amalia_response(user_input)
        st.session_state.history.append({"user": user_input, "assistant": answer, "mode": "text"})
        
        st.success("**✍️ Ta question :**")
        st.write(user_input)
        st.info("**🤖 Réponse d'Amalia :**")
        st.write(answer)

# Historique
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📜 Historique des conversations")
    
    for idx, msg in enumerate(reversed(st.session_state.history[-5:])):
        mode_icon = "🎤" if msg.get("mode") == "voice" else "✍️"
        with st.expander(f"{mode_icon} Conversation {len(st.session_state.history) - idx}"):
            st.markdown(f"**👤 Toi :** {msg['user']}")
            st.markdown(f"**🤖 Amalia :** {msg['assistant']}")
            
            # Bouton pour réécouter
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
            ">🔊 Réécouter</button>
            """
            st.components.v1.html(replay_html, height=50, key=f"replay_{idx}")
    
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.history = []
        st.rerun()








