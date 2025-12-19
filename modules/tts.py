import pyttsx3
from config import TTS_RATE, TTS_VOLUME


def speak(text):
    """
    Convertit du texte en voix en anglais.
    """
    engine = pyttsx3.init()
    
    # Forcer une voix anglaise
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'english' in voice.name.lower() or 'en' in voice.languages[0].lower() if voice.languages else False:
            engine.setProperty('voice', voice.id)
            break
    
    engine.setProperty('rate', TTS_RATE)
    engine.setProperty('volume', TTS_VOLUME)

    print(f"🔊 AI: {text[:100]}...")

    engine.say(text)
    engine.runAndWait()
