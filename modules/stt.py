import whisper
import sounddevice as sd
import soundfile as sf
from config import STT_LANGUAGE, STT_TIMEOUT

# Charger le modèle une seule fois
_model = None


def _get_model():
    global _model
    if _model is None:
        print("📥 Loading Whisper model (first time only)...")
        _model = whisper.load_model("base")
    return _model


def listen_once(timeout=STT_TIMEOUT):
    """
    Écoute au micro avec détection de fin de parole.
    """
    print("🎤 Listening... Speak now!")
    print("   (Parle assez fort, en anglais)")
    print("   (Je vais arrêter automatiquement quand tu finiras de parler)")
    
    try:
        samplerate = 16000
        duration = 10  # Enregistre max 15 secondes
        
        print(f"   (Recording for up to {duration} seconds...)")
        recording = sd.rec(
            int(samplerate * duration),
            samplerate=samplerate,
            channels=1,
            dtype='float32',
            device=None
        )
        sd.wait()
        
        temp_file = "temp_audio.wav"
        sf.write(temp_file, recording, samplerate)
        
        model = _get_model()
        
        print("🔄 Recognizing...")
        result = model.transcribe(temp_file, language=STT_LANGUAGE)
        
        text = result["text"].strip()
        
        # Filtrer les silences
        if not text or len(text) < 2:
            print("❌ No speech detected (silence). Try again.")
            return None
        
        print(f"✅ You said: {text}")
        return text
    
    except Exception as e:
        print(f"❌ Error in listen_once: {e}")
        return None

def transcribe_audio_file(file_path):
    """
    Transcribe an audio file using Whisper.
    """
    try:
        model = _get_model()
        result = model.transcribe(file_path, language=STT_LANGUAGE)
        text = result["text"].strip()
        
        if not text or len(text) < 2:
            print("❌ No speech detected")
            return None
        
        print(f"✅ Transcribed: {text}")
        return text
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
