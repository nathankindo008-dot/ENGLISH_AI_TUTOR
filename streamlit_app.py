import os
import tempfile
import requests
import base64
import streamlit as st
from streamlit_lottie import st_lottie

from modules.llm_client import ask_llm, LEARNING_MODES
from modules.feedback import extract_feedback
from modules.conversation import ConversationManager
from modules.analytics import ProgressTracker
from modules.stt import transcribe_audio_file
from modules.translator import translate_word
from modules.tts import VOICES, voice_settings, set_voice, get_voice
from config import tts_settings, TTS_RATE_MIN, TTS_RATE_MAX, TTS_RATE_DEFAULT


def autoplay_audio(audio_bytes):
    """Joue l'audio automatiquement sans clic."""
    if audio_bytes:
        b64 = base64.b64encode(audio_bytes).decode()
        # Utiliser JavaScript pour forcer l'autoplay
        audio_html = f"""
            <audio id="ai-audio" autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            <script>
                var audio = document.getElementById('ai-audio');
                audio.play().catch(function(error) {{
                    console.log('Autoplay blocked:', error);
                }});
            </script>
        """
        st.markdown(audio_html, unsafe_allow_html=True)


st.set_page_config(
    page_title="English AI Tutor by KINDO Nathan",
    page_icon="🎓",
    layout="wide",
)

@st.cache_data(show_spinner=False)
def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


# Avatars (tu peux remplacer par d'autres liens Lottie plus “humains”)
# Animations Lottie pour l'assistant (robot)
LOTTIE_IDLE = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_M9p23l.json")
LOTTIE_TALKING = load_lottie_url("https://assets3.lottiefiles.com/packages/lf20_kyu7xb1v.json")


# ---------- CSS (bleu clair + moins d'espace en haut + micro gros) ----------
st.markdown(
    """
<style>
/* Fond bleu clair fixe */
.stApp {
    background: linear-gradient(180deg, #d7efff 0%, #f4fbff 65%, #ffffff 100%);
}

/* Réduit l'espace vide en haut */
header.stAppHeader { background: transparent; }
section.stMain .block-container{
  padding-top: 0.6rem !important;
  padding-bottom: 1rem !important;
}

/* Sidebar légère */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.70);
    backdrop-filter: blur(8px);
}

/* Cards */
.card {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid rgba(10, 80, 140, 0.12);
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 10px 24px rgba(10, 80, 140, 0.08);
    margin: 10px 0;
}

/* Titre */
.h-title {
    font-size: 2.0rem;
    font-weight: 800;
    color: #0b3558;
    margin: 0.2rem 0 0.2rem 0;
}
.signature {
    color: #0b3558;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

/* Chat bubbles */
.user-bubble {
    background: #0f62fe;
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 6px 18px;
    margin: 10px 0;
    max-width: 95%;
}
.ai-bubble {
    background: #1a73e8;
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 6px;
    margin: 10px 0;
    max-width: 95%;
}

/* Micro gros (styling du bouton du widget st.audio_input) */
div[data-testid="stAudioInput"] {
    width: 100%;
    display: flex;
    justify-content: flex-start; /* haut-gauche */
}
div[data-testid="stAudioInput"] button {
    width: 92px !important;
    height: 92px !important;
    border-radius: 999px !important;
    background: radial-gradient(circle at 30% 30%, #4aa3ff, #0f62fe) !important;
    border: 0 !important;
    box-shadow: 0 14px 30px rgba(15, 98, 254, 0.28) !important;
    transform: translateY(0);
    transition: transform .15s ease, box-shadow .15s ease;
}
div[data-testid="stAudioInput"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 40px rgba(15, 98, 254, 0.36) !important;
}

/* Petits textes */
.small-hint {
    color: #0b3558;
    font-weight: 600;
    margin-top: 6px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- SESSION ----------
if "manager" not in st.session_state:
    st.session_state.manager = ConversationManager()
if "history" not in st.session_state:
    st.session_state.history = []
if "turns" not in st.session_state:
    st.session_state.turns = []
if "role" not in st.session_state:
    st.session_state.role = "tutor"
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "avatar_state" not in st.session_state:
    st.session_state.avatar_state = "idle"  # idle | speaking
if "last_ai_audio_bytes" not in st.session_state:
    st.session_state.last_ai_audio_bytes = None
if "speech_speed" not in st.session_state:
    st.session_state.speech_speed = TTS_RATE_DEFAULT
if "learning_mode" not in st.session_state:
    st.session_state.learning_mode = "general"
if "selected_voice" not in st.session_state:
    st.session_state.selected_voice = "male_us"

# ---------- NAV ----------
st.sidebar.title("English AI Tutor")
st.sidebar.markdown("**Created by KINDO Nathan**")

# Afficher le mode actuel
current_mode = LEARNING_MODES.get(st.session_state.learning_mode, LEARNING_MODES["general"])
st.sidebar.markdown(f"**Mode:** {current_mode['icon']} {current_mode['name']}")

page = st.sidebar.radio("Navigation", ["Talk", "Progress", "Vocab", "Settings"])

# ---------- SPEECH SPEED CONTROL ----------
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔊 Speech Speed")
speech_speed = st.sidebar.slider(
    "Speed",
    min_value=TTS_RATE_MIN,
    max_value=TTS_RATE_MAX,
    value=st.session_state.speech_speed,
    step=10,
    help="Adjust how fast the AI speaks (80=slow, 250=fast)"
)
st.session_state.speech_speed = speech_speed
tts_settings["rate"] = speech_speed

# Visual indicator
if speech_speed < 120:
    st.sidebar.caption(f"🐢 Slow: {speech_speed}")
elif speech_speed > 200:
    st.sidebar.caption(f"⚡ Fast: {speech_speed}")
else:
    st.sidebar.caption(f"🎯 Normal: {speech_speed}")

# ---------- VOICE SELECTION ----------
st.sidebar.markdown("### 🎙️ Voice")
voice_options = {key: info["name"] for key, info in VOICES.items()}
selected_voice = st.sidebar.selectbox(
    "Voice",
    options=list(voice_options.keys()),
    format_func=lambda x: voice_options[x],
    index=list(voice_options.keys()).index(st.session_state.selected_voice),
    label_visibility="collapsed"
)
if selected_voice != st.session_state.selected_voice:
    st.session_state.selected_voice = selected_voice
    set_voice(selected_voice)
else:
    set_voice(st.session_state.selected_voice)

# ---------- TRANSLATOR ----------
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔤 Quick Translator")

# Choix de la direction de traduction
trans_direction = st.sidebar.radio(
    "Direction",
    ["🇫🇷 → 🇬🇧 FR to EN", "🇬🇧 → 🇫🇷 EN to FR"],
    horizontal=True,
    label_visibility="collapsed"
)

# Champ de saisie
word_to_translate = st.sidebar.text_input(
    "Enter word",
    placeholder="Tapez un mot...",
    label_visibility="collapsed"
)

# Bouton traduire
if st.sidebar.button("🔍 Translate", use_container_width=True):
    if word_to_translate.strip():
        with st.sidebar:
            with st.spinner("Translating..."):
                if "FR to EN" in trans_direction:
                    result = translate_word(word_to_translate, "French", "English")
                else:
                    result = translate_word(word_to_translate, "English", "French")
                
                if result:
                    st.sidebar.markdown(f"""
                    <div style="background: rgba(39, 174, 96, 0.1); padding: 10px; border-radius: 10px; margin-top: 10px; border-left: 4px solid #27ae60;">
                        {result}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.sidebar.warning("Enter a word first!")


# =========================
# PAGE: TALK
# =========================
if page == "Talk":
    # 2 colonnes: gauche (micro + chat), droite (avatar) [st.columns]
    col_left, col_right = st.columns([1.35, 1], vertical_alignment="top")

    with col_left:
        st.markdown('<div class="h-title">English AI Tutor</div>', unsafe_allow_html=True)
        st.markdown('<div class="signature">Created by KINDO Nathan</div>', unsafe_allow_html=True)

        # MICRO tout en haut à gauche
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Speak")
        audio_data = st.audio_input("Record", label_visibility="collapsed")
        st.markdown('<div class="small-hint">Clique sur le micro, parle, puis stop.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Mode
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Mode")
        role_select = st.radio("Role", ["Tutor", "Friend"], horizontal=True, label_visibility="collapsed")
        st.session_state.role = role_select.lower()
        st.markdown("</div>", unsafe_allow_html=True)

        # Traitement du son
        if audio_data is not None:
            audio_hash = hash(audio_data.getbuffer().tobytes())
            if audio_hash != st.session_state.last_audio_hash:
                st.session_state.last_audio_hash = audio_hash

                # nouveau tour => reset état
                st.session_state.avatar_state = "idle"
                st.session_state.last_ai_audio_bytes = None

                with st.spinner("Transcription…"):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(audio_data.getbuffer())
                        temp_path = f.name
                    try:
                        user_text = transcribe_audio_file(temp_path)
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

                if not user_text:
                    st.error("Je n’ai pas bien entendu. Réessaie en parlant plus clairement.")
                else:
                    st.markdown(f'<div class="user-bubble"><b>You:</b> {user_text}</div>', unsafe_allow_html=True)

                    with st.spinner("Réponse IA…"):
                        response, st.session_state.history = ask_llm(
                            st.session_state.history,
                            user_text,
                            role=st.session_state.role,
                            learning_mode=st.session_state.learning_mode,
                        )
                    feedback = extract_feedback(response)

                    turn = {"user": user_text, "feedback": feedback}
                    st.session_state.turns.append(turn)
                    st.session_state.manager.add_turn(user_text, response, feedback)

                    with st.spinner("Voix…"):
                        from modules.tts import speak
                        audio_file = speak(feedback["response"])
                        audio_bytes = None
                        if audio_file and os.path.exists(audio_file):
                            with open(audio_file, "rb") as f:
                                audio_bytes = f.read()

                    st.session_state.last_ai_audio_bytes = audio_bytes
                    st.session_state.avatar_state = "speaking"

                    st.markdown(
                        f'<div class="ai-bubble"><b>AI:</b> {feedback["response"]}</div>',
                        unsafe_allow_html=True,
                    )
                    
                    # Jouer l'audio automatiquement (une seule méthode pour éviter la superposition)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        # Historique (replié pour éviter de scroller)
        with st.expander("History", expanded=False):
            for t in st.session_state.turns[::-1][:12]:
                st.markdown(f'<div class="user-bubble"><b>You:</b> {t["user"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-bubble"><b>AI:</b> {t["feedback"]["response"]}</div>', unsafe_allow_html=True)

        # Actions
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save conversation"):
                st.session_state.manager.save()
                st.success("Saved.")
        with c2:
            if st.button("Reset"):
                st.session_state.history = []
                st.session_state.turns = []
                st.session_state.manager = ConversationManager()
                st.session_state.last_audio_hash = None
                st.session_state.avatar_state = "idle"
                st.session_state.last_ai_audio_bytes = None
                st.rerun()

    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Assistant")

        if st.session_state.avatar_state == "speaking":
            st.caption("🔊 Speaking…")
            # Avatar professeur qui parle
            st.markdown('''
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 100px; animation: pulse 1s infinite;">👨‍🏫</div>
                <div style="font-size: 24px; margin-top: 10px;">🇬🇧 🗣️ 🇺🇸</div>
            </div>
            <style>
                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                }
            </style>
            ''', unsafe_allow_html=True)
        else:
            st.caption("✅ Ready to listen")
            # Avatar professeur en attente
            st.markdown('''
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 100px;">👨‍🏫</div>
                <div style="font-size: 24px; margin-top: 10px;">🇬🇧 📚 🇺🇸</div>
                <div style="color: #666; margin-top: 10px;">Your English Tutor</div>
            </div>
            ''', unsafe_allow_html=True)

        # Player audio (à droite, sous l’avatar)
        if st.session_state.last_ai_audio_bytes:
            st.audio(st.session_state.last_ai_audio_bytes, format="audio/mp3")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Stats")
        total = len(st.session_state.turns)
        st.metric("Turns", total)
        if total:
            words = sum(len(t["user"].split()) for t in st.session_state.turns)
            st.metric("Words spoken", words)
        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# PAGE: PROGRESS
# =========================
elif page == "Progress":
    st.markdown('<div class="h-title">📊 Progress Dashboard</div>', unsafe_allow_html=True)
    
    tracker = ProgressTracker()
    
    # Statistiques principales en cartes
    col1, col2, col3, col4 = st.columns(4)
    
    total_turns = tracker.get_total_turns()
    total_words = tracker.get_total_words_spoken()
    avg_words = tracker.get_average_words_per_turn()
    perfect_turns = tracker.get_correction_free_turns()
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.metric("🎯 Total Conversations", total_turns)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.metric("💬 Words Spoken", total_words)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.metric("📈 Avg Words/Turn", avg_words)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        accuracy = round(perfect_turns/total_turns*100, 1) if total_turns > 0 else 0
        st.metric("✅ Accuracy", f"{accuracy}%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Graphique de progression quotidienne
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📅 Daily Activity")
    
    daily_stats = tracker.get_daily_progress()
    if daily_stats:
        import pandas as pd
        df = pd.DataFrame([
            {"Date": date, "Turns": data["turns"], "Words": data["words"]}
            for date, data in sorted(daily_stats.items())
        ])
        
        tab1, tab2 = st.tabs(["Conversations", "Words"])
        with tab1:
            st.bar_chart(df.set_index("Date")["Turns"], color="#0f62fe")
        with tab2:
            st.bar_chart(df.set_index("Date")["Words"], color="#27ae60")
    else:
        st.info("Start practicing to see your daily progress!")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Erreurs récurrentes
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🔴 Common Mistakes")
        recurring = tracker.get_recurring_errors(top_n=5)
        if recurring:
            for i, (error, count) in enumerate(recurring, 1):
                st.markdown(f"""
                <div style="background: rgba(231, 76, 60, 0.1); padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 4px solid #e74c3c;">
                    <b>{i}.</b> <span style="color: #e74c3c;">[{count}x]</span> {error}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No recurring errors - excellent work! 🎉")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📖 Grammar Tips Learned")
        tips = list(tracker.get_grammar_tips())[:5]
        if tips:
            for tip in tips:
                st.markdown(f"""
                <div style="background: rgba(39, 174, 96, 0.1); padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 4px solid #27ae60;">
                    💡 {tip}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Grammar tips will appear as you practice!")
        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# PAGE: VOCAB
# =========================
elif page == "Vocab":
    st.markdown('<div class="h-title">📚 Vocabulary Bank</div>', unsafe_allow_html=True)
    
    tracker = ProgressTracker()
    vocab = sorted(tracker.get_vocabulary_learned())
    
    # Stats
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📖 Total Words Learned", len(vocab))
    with col2:
        st.metric("🎯 Learning Mode", LEARNING_MODES.get(st.session_state.learning_mode, {}).get("name", "General"))
    st.markdown("</div>", unsafe_allow_html=True)
    
    if not vocab:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.info("🎯 Start practicing to build your vocabulary bank!")
        st.markdown("""
        **Tips to learn vocabulary:**
        - Practice conversations regularly
        - Pay attention to new words suggested by the AI
        - Try to use new words in your next responses
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Filtrer le vocabulaire
        search = st.text_input("🔍 Search vocabulary", placeholder="Type to filter...")
        
        filtered_vocab = [v for v in vocab if search.lower() in v.lower()] if search else vocab
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader(f"📝 Your Words ({len(filtered_vocab)})")
        
        # Afficher en grille avec style
        cols = st.columns(2)
        for i, word in enumerate(filtered_vocab):
            with cols[i % 2]:
                # Extraire le mot et sa définition si format "word (definition)"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(15, 98, 254, 0.1), rgba(26, 115, 232, 0.05)); 
                            padding: 12px 16px; border-radius: 12px; margin: 6px 0;
                            border-left: 4px solid #0f62fe;">
                    <span style="font-size: 1.1em;">📌</span> {word}
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Export option
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📥 Export")
        vocab_text = "\n".join([f"• {v}" for v in vocab])
        st.download_button(
            label="Download Vocabulary List",
            data=vocab_text,
            file_name="my_vocabulary.txt",
            mime="text/plain"
        )
        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# PAGE: SETTINGS
# =========================
else:
    st.markdown('<div class="h-title">⚙️ Settings</div>', unsafe_allow_html=True)
    
    # Mode d'apprentissage
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎯 Learning Mode")
    st.markdown("Choose your learning focus. The AI will adapt its vocabulary and topics accordingly.")
    
    # Afficher les modes en grille
    mode_cols = st.columns(3)
    
    for i, (mode_key, mode_info) in enumerate(LEARNING_MODES.items()):
        with mode_cols[i % 3]:
            is_selected = st.session_state.learning_mode == mode_key
            border_color = "#0f62fe" if is_selected else "transparent"
            bg_color = "rgba(15, 98, 254, 0.15)" if is_selected else "rgba(255,255,255,0.5)"
            
            st.markdown(f"""
            <div style="background: {bg_color}; padding: 15px; border-radius: 12px; 
                        border: 2px solid {border_color}; margin: 5px 0; text-align: center;
                        min-height: 120px;">
                <div style="font-size: 2em;">{mode_info['icon']}</div>
                <div style="font-weight: bold; margin: 5px 0;">{mode_info['name']}</div>
                <div style="font-size: 0.85em; color: #666;">{mode_info['description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select", key=f"mode_{mode_key}", use_container_width=True):
                st.session_state.learning_mode = mode_key
                # Reset history pour appliquer le nouveau mode
                st.session_state.history = []
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mode actuel
    current_mode = LEARNING_MODES.get(st.session_state.learning_mode, LEARNING_MODES["general"])
    st.success(f"**Current mode:** {current_mode['icon']} {current_mode['name']}")
    
    # Paramètres de conversation
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("💬 Conversation Style")
    
    role_options = {
        "tutor": "👨‍🏫 Tutor - Formal corrections & feedback",
        "friend": "👋 Friend - Casual conversation style"
    }
    
    selected_role = st.radio(
        "How should the AI interact with you?",
        options=list(role_options.keys()),
        format_func=lambda x: role_options[x],
        index=0 if st.session_state.role == "tutor" else 1
    )
    st.session_state.role = selected_role
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Paramètres de voix
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎙️ Voice Settings")
    st.markdown("Choose the AI's voice for speaking responses.")
    
    # Afficher les voix en grille
    voice_cols = st.columns(2)
    
    for i, (voice_key, voice_info) in enumerate(VOICES.items()):
        with voice_cols[i % 2]:
            is_selected = st.session_state.selected_voice == voice_key
            border_color = "#0f62fe" if is_selected else "transparent"
            bg_color = "rgba(15, 98, 254, 0.15)" if is_selected else "rgba(255,255,255,0.5)"
            gender_icon = "👨" if voice_info["gender"] == "male" else "👩"
            
            st.markdown(f"""
            <div style="background: {bg_color}; padding: 15px; border-radius: 12px; 
                        border: 2px solid {border_color}; margin: 5px 0; text-align: center;">
                <div style="font-size: 1.8em;">{voice_info['flag']} {gender_icon}</div>
                <div style="font-weight: bold; margin: 5px 0;">{voice_info['name'].split('(')[1].replace(')', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select", key=f"voice_{voice_key}", use_container_width=True):
                st.session_state.selected_voice = voice_key
                set_voice(voice_key)
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Infos sur l'application
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("ℹ️ About")
    st.markdown("""
    **English AI Tutor** helps you practice English conversation with AI-powered feedback.
    
    **Features:**
    - 🎤 Voice-based conversation
    - 📝 Grammar corrections
    - 📚 Vocabulary suggestions
    - 📊 Progress tracking
    - 🎯 Multiple learning modes
    
    ---
    **Created by KINDO Nathan**  
    Student at ENSEA, Abidjan
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Reset all data
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🗑️ Data Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset Current Session", use_container_width=True):
            st.session_state.history = []
            st.session_state.turns = []
            st.session_state.last_audio_hash = None
            st.session_state.avatar_state = "idle"
            st.session_state.last_ai_audio_bytes = None
            st.success("Session reset!")
            st.rerun()
    
    with col2:
        st.warning("⚠️ This will clear your current conversation only.")
    st.markdown("</div>", unsafe_allow_html=True)
