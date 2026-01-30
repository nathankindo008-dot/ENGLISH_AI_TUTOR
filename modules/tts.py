import tempfile
import os
import re
import asyncio
import hashlib
import edge_tts
from config import TTS_RATE_MIN, TTS_RATE_MAX, TTS_RATE_STEP, tts_settings


# Cache pour éviter de régénérer les mêmes audios
_audio_cache = {}
MAX_CACHE_SIZE = 50

# Voix disponibles (edge-tts - Microsoft)
VOICES = {
    "male_us": {
        "id": "en-US-GuyNeural",
        "name": "🇺🇸 Guy (Male US)",
        "flag": "🇺🇸",
        "gender": "male"
    },
    "female_us": {
        "id": "en-US-JennyNeural",
        "name": "🇺🇸 Jenny (Female US)",
        "flag": "🇺🇸",
        "gender": "female"
    },
    "male_uk": {
        "id": "en-GB-RyanNeural",
        "name": "🇬🇧 Ryan (Male UK)",
        "flag": "🇬🇧",
        "gender": "male"
    },
    "female_uk": {
        "id": "en-GB-SoniaNeural",
        "name": "🇬🇧 Sonia (Female UK)",
        "flag": "🇬🇧",
        "gender": "female"
    },
}

# Voix par défaut
DEFAULT_VOICE_KEY = "male_us"

# Configuration globale de la voix
voice_settings = {
    "current_voice": DEFAULT_VOICE_KEY
}


def get_current_voice_id():
    """Retourne l'ID de la voix actuellement sélectionnée."""
    key = voice_settings["current_voice"]
    return VOICES.get(key, VOICES[DEFAULT_VOICE_KEY])["id"]


def set_voice(voice_key):
    """Change la voix sélectionnée."""
    if voice_key in VOICES:
        voice_settings["current_voice"] = voice_key
    return voice_settings["current_voice"]


def get_voice():
    """Retourne la clé de la voix actuelle."""
    return voice_settings["current_voice"]

# Dictionnaire de corrections de prononciation (français -> phonétique anglaise)
PRONUNCIATION_FIXES = {
    # Nom du créateur - prononciation française
    r'\bKINDO\b': 'Keen-doh',
    r'\bKindo\b': 'Keen-doh',
    r'\bNathan\b': 'Nah-tahn',
    r'\bENSEA\b': 'En-say-ah',
    r'\bAbidjan\b': 'Ah-bid-jahn',
    # Ajoute d'autres mots si nécessaire
}


def fix_pronunciation(text):
    """
    Corrige la prononciation de certains mots (noms français, etc.)
    pour qu'ils soient prononcés correctement par le TTS en anglais.
    """
    for pattern, replacement in PRONUNCIATION_FIXES.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _get_cache_key(text, rate, voice):
    """Génère une clé de cache unique pour le texte et les paramètres."""
    key_str = f"{text}_{rate}_{voice}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _get_rate_string(rate):
    """
    Convertit le taux de vitesse (80-250) en format edge-tts.
    edge-tts utilise des pourcentages: -50% à +100%
    """
    # Normaliser: 80 -> -50%, 150 -> 0%, 250 -> +66%
    if rate <= 80:
        return "-50%"
    elif rate >= 250:
        return "+66%"
    else:
        # Interpolation linéaire
        # 80 -> -50, 150 -> 0, 250 -> +66
        if rate < 150:
            percent = int(-50 + (rate - 80) * (50 / 70))
        else:
            percent = int((rate - 150) * (66 / 100))
        
        if percent >= 0:
            return f"+{percent}%"
        return f"{percent}%"


async def _speak_async(text, voice, rate_str, output_path):
    """Génère l'audio de manière asynchrone avec edge-tts."""
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    await communicate.save(output_path)


def speak(text, save_to_file=True, voice=None):
    """
    Convertit du texte en voix en anglais avec edge-tts (Microsoft Edge TTS).
    Plus rapide que gTTS avec meilleure qualité.
    Retourne le chemin du fichier audio MP3.
    """
    if not text or not text.strip():
        return None
    
    # Corriger la prononciation des mots français
    text = fix_pronunciation(text)
    
    # Utiliser la voix sélectionnée si non spécifiée
    if voice is None:
        voice = get_current_voice_id()
    
    # Obtenir le taux de vitesse au format edge-tts
    rate = tts_settings["rate"]
    rate_str = _get_rate_string(rate)
    
    # Vérifier le cache
    cache_key = _get_cache_key(text, rate, voice)
    if cache_key in _audio_cache:
        cached_path = _audio_cache[cache_key]
        if os.path.exists(cached_path):
            print(f"🔊 AI (cached, rate={rate_str}): {text[:60]}...")
            return cached_path
    
    print(f"🔊 AI (rate={rate_str}): {text[:60]}...")

    try:
        # Créer fichier temporaire
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        temp_file.close()
        
        # Exécuter la génération asynchrone
        asyncio.run(_speak_async(text, voice, rate_str, temp_path))
        
        # Vérifier que le fichier existe et a du contenu
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            # Gérer le cache (limiter la taille)
            if len(_audio_cache) >= MAX_CACHE_SIZE:
                # Supprimer le plus ancien
                oldest_key = next(iter(_audio_cache))
                oldest_path = _audio_cache.pop(oldest_key)
                if os.path.exists(oldest_path):
                    try:
                        os.remove(oldest_path)
                    except:
                        pass
            
            _audio_cache[cache_key] = temp_path
            return temp_path
        return None
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return None


def set_speech_rate(rate):
    """
    Définit la vitesse de parole.
    """
    tts_settings["rate"] = max(TTS_RATE_MIN, min(TTS_RATE_MAX, rate))
    return tts_settings["rate"]


def increase_speech_rate():
    """
    Augmente la vitesse de parole.
    """
    new_rate = tts_settings["rate"] + TTS_RATE_STEP
    return set_speech_rate(new_rate)


def decrease_speech_rate():
    """
    Diminue la vitesse de parole.
    """
    new_rate = tts_settings["rate"] - TTS_RATE_STEP
    return set_speech_rate(new_rate)


def get_speech_rate():
    """
    Retourne la vitesse de parole actuelle.
    """
    return tts_settings["rate"]
