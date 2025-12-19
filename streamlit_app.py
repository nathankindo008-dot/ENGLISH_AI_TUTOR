import os
import tempfile
import requests
import streamlit as st
from streamlit_lottie import st_lottie

from modules.llm_client import ask_llm
from modules.feedback import extract_feedback
from modules.conversation import ConversationManager
from modules.analytics import ProgressTracker
from modules.stt import transcribe_audio_file


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
LOTTIE_IDLE = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_obhph3sh.json")
LOTTIE_TALKING = load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_khtt8whi.json")


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

# ---------- NAV ----------
st.sidebar.title("English AI Tutor")
st.sidebar.markdown("**Created by KINDO Nathan**")
page = st.sidebar.radio("Navigation", ["Talk", "Progress", "Vocab", "Settings"])

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
            st.caption("Speaking…")
            if LOTTIE_TALKING:
                st_lottie(LOTTIE_TALKING, height=260, key="avatar_talking")
        else:
            st.caption("Ready")
            if LOTTIE_IDLE:
                st_lottie(LOTTIE_IDLE, height=260, key="avatar_idle")

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
    st.markdown('<div class="h-title">Progress</div>', unsafe_allow_html=True)
    tracker = ProgressTracker()
    st.write(tracker.get_report())


# =========================
# PAGE: VOCAB
# =========================
elif page == "Vocab":
    st.markdown('<div class="h-title">Vocabulary</div>', unsafe_allow_html=True)
    tracker = ProgressTracker()
    vocab = sorted(tracker.get_vocabulary_learned())
    if not vocab:
        st.info("No vocabulary yet.")
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, w in enumerate(vocab):
            with cols[i % 3]:
                st.write(f"- {w}")
        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# PAGE: SETTINGS
# =========================
else:
    st.markdown('<div class="h-title">Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("Created by KINDO Nathan.")
    st.markdown("</div>", unsafe_allow_html=True)
