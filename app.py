import streamlit as st
import requests

st.set_page_config(
    page_title="Amalia - Assistant IA",
    page_icon="🤖",
    layout="centered"
)

# CSS professionnel
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stChatMessage {
        background: white;
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    h1 {
        color: white;
        text-align: center;
        padding: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Amalia - Ton Assistant IA")

# Initialisation
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False

# Fonction pour obtenir la réponse d'Amalia
def get_response(user_input):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    
    if not api_key:
        return "⚠️ Clé API manquante"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "system", "content": "Tu es Amalia, une assistante IA conviviale et professionnelle. Réponds de manière claire et concise."}]
    
    for msg in st.session_state.messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_input})
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
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

# Bouton micro en haut de l'input
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
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s;
            width: 50px;
            height: 50px;
        " title="Clique pour parler">🎤</button>
        <div id="status" style="font-size: 10px; text-align: center; margin-top: 4px; color: white;"></div>
    </div>

    <script>
    const micBtn = document.getElementById('micBtn');
    const status = document.getElementById('status');
    let isRecording = false;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'fr-FR';
        recognition.continuous = false;

        micBtn.onclick = function() {
            if (!isRecording) {
                recognition.start();
                isRecording = true;
                micBtn.style.background = 'linear-gradient(135deg, #ff4444 0%, #cc0000 100%)';
                micBtn.textContent = '⏺️';
                status.textContent = 'Écoute...';
            }
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            isRecording = false;
            micBtn.style.background = 'linear-gradient(135deg, #10a37f 0%, #0d8a6d 100%)';
            micBtn.textContent = '🎤';
            status.textContent = '✓';
            
            // Mettre à jour l'input Streamlit
            const chatInput = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (chatInput) {
                chatInput.value = transcript;
                chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Marquer comme mode vocal
                window.parent.sessionStorage.setItem('voiceMode', 'true');
            }
        };

        recognition.onerror = function() {
            status.textContent = '❌';
            isRecording = false;
            micBtn.style.background = 'linear-gradient(135deg, #10a37f 0%, #0d8a6d 100%)';
            micBtn.textContent = '🎤';
        };

        recognition.onend = function() {
            isRecording = false;
            micBtn.style.background = 'linear-gradient(135deg, #10a37f 0%, #0d8a6d 100%)';
            micBtn.textContent = '🎤';
        };
    } else {
        micBtn.disabled = true;
        micBtn.style.opacity = '0.5';
        status.textContent = 'Non supporté';
    }
    </script>
    """
    st.components.v1.html(mic_html, height=80)

with col2:
    # Input de chat
    if prompt := st.chat_input("Écris ton message ici..."):
        # Ajouter message utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Afficher message utilisateur
        with st.chat_message("user"):
            st.write(prompt)
        
        # Obtenir réponse
        with st.chat_message("assistant"):
            with st.spinner("Amalia réfléchit..."):
                response = get_response(prompt)
                st.write(response)
        
        # Ajouter réponse à l'historique
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Synthèse vocale automatique si mode vocal
        check_voice_html = """
        <script>
        const voiceMode = window.parent.sessionStorage.getItem('voiceMode');
        if (voiceMode === 'true') {
            window.parent.sessionStorage.removeItem('voiceMode');
            const response = document.querySelector('.stChatMessage:last-child p').textContent;
            const utterance = new SpeechSynthesisUtterance(response);
            utterance.lang = 'fr-FR';
            utterance.rate = 1.0;
            window.speechSynthesis.speak(utterance);
        }
        </script>
        """
        st.components.v1.html(check_voice_html, height=0)
        
        st.rerun()

# Sidebar avec options
with st.sidebar:
    st.markdown("### ⚙️ Options")
    
    if st.button("🗑️ Effacer l'historique", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Statistiques")
    st.metric("Messages échangés", len(st.session_state.messages))
    
    st.markdown("---")
    st.markdown("### ℹ️ Aide")
    st.info("""
    **🎤 Mode Vocal**
    Clique sur le micro, parle, et Amalia te répondra à l'oral !
    
    **✍️ Mode Texte**
    Écris ton message et Amalia te répondra par écrit.
    """)










