import streamlit as st
import os
import tempfile
from modules.llm_client import ask_llm
from modules.feedback import extract_feedback
from modules.conversation import ConversationManager
from modules.analytics import ProgressTracker
from modules.stt import transcribe_audio_file

st.set_page_config(page_title="English AI Tutor by KINDO Nathan", page_icon="🎓", layout="wide")

# ULTRA WAOUH CSS
st.markdown("""
<style>
    /* Background gradient animé */
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Cards avec glassmorphism */
    .glass-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Stat box moderne */
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.5);
        transition: transform 0.3s ease;
        margin: 10px 0;
    }
    
    .stat-box:hover {
        transform: translateY(-10px) scale(1.05);
        box-shadow: 0 15px 50px rgba(102, 126, 234, 0.7);
    }
    
    /* Chat bubbles */
    .user-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        max-width: 70%;
        float: right;
        clear: both;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        animation: fadeIn 0.5s ease;
    }
    
    .ai-bubble {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        max-width: 70%;
        float: left;
        clear: both;
        box-shadow: 0 5px 15px rgba(245, 87, 108, 0.3);
        animation: fadeIn 0.5s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Avatar qui pulse */
    .avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        box-shadow: 0 0 30px rgba(102, 126, 234, 0.6);
        animation: pulse 2s infinite;
        margin: 20px auto;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); box-shadow: 0 0 30px rgba(102, 126, 234, 0.6); }
        50% { transform: scale(1.1); box-shadow: 0 0 50px rgba(102, 126, 234, 0.9); }
    }
    
    .avatar.speaking {
        animation: speaking 0.5s infinite;
        box-shadow: 0 0 50px rgba(245, 87, 108, 0.9) !important;
    }
    
    @keyframes speaking {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    
    /* Titre avec glow */
    .glow-title {
        text-align: center;
        font-size: 3em;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
        margin-bottom: 20px;
        animation: glow 3s ease-in-out infinite;
    }
    
    @keyframes glow {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.3); }
    }
    
    /* Button moderne */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: bold;
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.6);
    }
    
    /* Credit box stylé */
    .credit-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
        box-shadow: 0 5px 20px rgba(245, 87, 108, 0.4);
        animation: fadeIn 1s ease;
    }
    
    /* Corrections/Vocab boxes */
    .correction-box {
        background: rgba(220, 53, 69, 0.2);
        border-left: 4px solid #dc3545;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        backdrop-filter: blur(5px);
    }
    
    .vocab-box {
        background: rgba(0, 123, 255, 0.2);
        border-left: 4px solid #007bff;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        backdrop-filter: blur(5px);
    }
    
    .perfect-box {
        background: rgba(40, 167, 69, 0.2);
        border-left: 4px solid #28a745;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        backdrop-filter: blur(5px);
    }
    
    /* Sidebar moderne */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Radio buttons stylés */
    .stRadio > label {
        background: rgba(255, 255, 255, 0.2);
        padding: 10px 20px;
        border-radius: 20px;
        backdrop-filter: blur(5px);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown('<div class="glow-title">🎓</div>', unsafe_allow_html=True)
st.sidebar.title("English AI Tutor")
st.sidebar.markdown('<div class="credit-box">✨ Created by KINDO Nathan ✨</div>', unsafe_allow_html=True)

page = st.sidebar.radio("", ["💬 Talk", "📊 Progress", "📚 Vocab", "⚙️ Settings"])

# Session
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
if "is_speaking" not in st.session_state:
    st.session_state.is_speaking = False

# ==================== PAGE 1: TALK ====================
if page == "💬 Talk":
    st.markdown('<div class="glow-title">🎓 English AI Tutor</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: white; font-size: 1.2em;">Created by KINDO Nathan ✨</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Avatar animé
        avatar_class = "avatar speaking" if st.session_state.is_speaking else "avatar"
        st.markdown(f'<div class="{avatar_class}">🤖</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        role_select = st.radio("Choose tutor role:", ["Tutor", "Friend"], horizontal=True)
        st.session_state.role = role_select.lower()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🎤 Speak to Your AI Tutor")
        
        audio_data = st.audio_input("Click to record your voice:", label_visibility="collapsed")
        
        if audio_data is not None:
            audio_hash = hash(audio_data.getbuffer().tobytes())
            
            if audio_hash != st.session_state.last_audio_hash:
                st.session_state.last_audio_hash = audio_hash
                st.session_state.is_speaking = False
                
                with st.spinner("🔄 Processing your voice..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(audio_data.getbuffer())
                        temp_path = f.name
                    
                    try:
                        user_text = transcribe_audio_file(temp_path)
                        
                        if user_text:
                            st.markdown(f'<div class="user-bubble">🎤 <b>You:</b> {user_text}</div>', unsafe_allow_html=True)
                            
                            with st.spinner("💭 AI is thinking..."):
                                response, st.session_state.history = ask_llm(
                                    st.session_state.history,
                                    user_text,
                                    role=st.session_state.role
                                )
                            
                            feedback = extract_feedback(response)
                            turn = {"user": user_text, "feedback": feedback}
                            st.session_state.turns.append(turn)
                            st.session_state.manager.add_turn(user_text, response, feedback)
                            
                            st.session_state.is_speaking = True
                            
                            with st.spinner("🔊 AI is speaking..."):
                                from modules.tts import speak
                                audio_file = speak(feedback['response'])
                                
                                if audio_file and os.path.exists(audio_file):
                                    with open(audio_file, 'rb') as f:
                                        audio_bytes = f.read()
                                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                                
                                st.markdown(f'<div class="ai-bubble">🤖 <b>AI:</b> {feedback["response"]}</div>', unsafe_allow_html=True)
                            
                            st.session_state.is_speaking = False
                            st.rerun()
                        else:
                            st.error("❌ Could not understand. Try speaking more clearly.")
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # History avec chat bubbles
        if st.session_state.turns:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("💬 Conversation History")
            
            for i, turn in enumerate(st.session_state.turns, 1):
                st.markdown(f'<div class="user-bubble">🎤 {turn["user"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-bubble">🤖 {turn["feedback"]["response"]}</div>', unsafe_allow_html=True)
                
                if turn['feedback']['corrections'] and turn['feedback']['corrections'] != ["None - well done!"]:
                    corrections_text = ", ".join(turn['feedback']['corrections'])
                    st.markdown(f'<div class="correction-box">❌ <b>Corrections:</b> {corrections_text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="perfect-box">✅ <b>Perfect! No corrections needed.</b></div>', unsafe_allow_html=True)
                
                if turn['feedback']['vocabulary']:
                    vocab_text = ", ".join(turn['feedback']['vocabulary'])
                    st.markdown(f'<div class="vocab-box">📚 <b>New Vocabulary:</b> {vocab_text}</div>', unsafe_allow_html=True)
                
                st.write("---")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Buttons
        col_s, col_r = st.columns(2)
        with col_s:
            if st.button("💾 Save Conversation"):
                st.session_state.manager.save()
                st.success("✅ Conversation saved!")
        with col_r:
            if st.button("🔄 Reset Conversation"):
                st.session_state.history = []
                st.session_state.turns = []
                st.session_state.manager = ConversationManager()
                st.session_state.last_audio_hash = None
                st.rerun()
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📊 Live Stats")
        
        if st.session_state.turns:
            total = len(st.session_state.turns)
            perfect = sum(1 for t in st.session_state.turns 
                         if not t['feedback']['corrections'] or t['feedback']['corrections'] == ["None - well done!"])
            words = sum(len(t['user'].split()) for t in st.session_state.turns)
            
            st.markdown(f'<div class="stat-box"><h2>{total}</h2><p>Total Turns</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-box"><h2>{perfect}/{total}</h2><p>Perfect Turns</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-box"><h2>{words}</h2><p>Words Spoken</p></div>', unsafe_allow_html=True)
            
            if total > 0:
                accuracy = round(perfect/total*100, 1)
                st.markdown(f'<div class="stat-box"><h2>{accuracy}%</h2><p>Accuracy</p></div>', unsafe_allow_html=True)
        else:
            st.info("🎤 Start talking to see your stats!")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== PAGE 2: PROGRESS ====================
elif page == "📊 Progress":
    st.markdown('<div class="glow-title">📊 Your Learning Progress</div>', unsafe_allow_html=True)
    
    tracker = ProgressTracker()
    
    if tracker.get_total_turns() > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="stat-box"><h1>{tracker.get_total_turns()}</h1><p>Total Turns</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-box"><h1>{tracker.get_total_words_spoken()}</h1><p>Words Spoken</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="stat-box"><h1>{tracker.get_average_words_per_turn()}</h1><p>Avg/Turn</p></div>', unsafe_allow_html=True)
        with col4:
            perfect = tracker.get_correction_free_turns()
            total = tracker.get_total_turns()
            pct = round(perfect/total*100, 1) if total > 0 else 0
            st.markdown(f'<div class="stat-box"><h1>{pct}%</h1><p>Accuracy</p></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🔴 Top Recurring Errors")
        recurring = tracker.get_recurring_errors(top_n=5)
        if recurring:
            for i, (error, count) in enumerate(recurring, 1):
                st.write(f"**{i}.** [{count}x] {error}")
        else:
            st.success("✅ No recurring errors!")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📝 Start practicing to see your progress!")

# ==================== PAGE 3: VOCABULARY ====================
elif page == "📚 Vocab":
    st.markdown('<div class="glow-title">📚 Vocabulary Learned</div>', unsafe_allow_html=True)
    
    tracker = ProgressTracker()
    vocab = tracker.get_vocabulary_learned()
    
    if vocab:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write(f"### 🎯 **{len(vocab)} terms learned**")
        cols = st.columns(3)
        for i, word in enumerate(sorted(vocab)):
            with cols[i % 3]:
                st.write(f"✨ {word}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📝 No vocabulary yet!")

# ==================== PAGE 4: SETTINGS ====================
elif page == "⚙️ Settings":
    st.markdown('<div class="glow-title">⚙️ Settings & About</div>', unsafe_allow_html=True)
    st.markdown('<div class="credit-box">🌟 Created by KINDO Nathan 🌟</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("""
    ### About English AI Tutor
    Your personal AI-powered English learning companion!
    
    **Features:**
    - 🎤 Voice input (Whisper STT)
    - 🔊 Voice output (pyttsx3 TTS)
    - 🤖 AI responses (Groq LLM)
    - ✏️ Grammar corrections
    - 📚 Vocabulary tracking
    - 📊 Progress analytics
    """)
    st.markdown('</div>', unsafe_allow_html=True)
