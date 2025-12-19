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
TTS_RATE = 150
TTS_VOLUME = 0.9

# Voix activée ou pas
USE_VOICE_OUTPUT = True
