import os
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# Récupérer la clé API Groq depuis .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Paramètres de la reconnaissance vocale
STT_LANGUAGE = "en"  # Whisper utilise "en" pas "en-US"
STT_TIMEOUT = 10

# Paramètres de synthèse vocale
TTS_RATE_DEFAULT = 150
TTS_RATE_MIN = 80
TTS_RATE_MAX = 250
TTS_RATE_STEP = 20
TTS_VOLUME = 0.9

# Variable mutable pour la vitesse actuelle (peut être modifiée pendant l'exécution)
tts_settings = {
    "rate": TTS_RATE_DEFAULT
}

# Voix activée ou pas
USE_VOICE_OUTPUT = True
