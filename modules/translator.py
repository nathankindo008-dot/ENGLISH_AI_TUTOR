from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def translate_word(word, from_lang="French", to_lang="English"):
    """
    Traduit un mot ou une expression d'une langue à une autre.
    Retourne la traduction avec une courte explication.
    """
    if not word or not word.strip():
        return None
    
    prompt = f"""Translate the following {from_lang} word/phrase to {to_lang}.
Give a concise response with:
1. The translation
2. A brief example sentence in {to_lang}

Word to translate: "{word}"

Format your response EXACTLY like this:
**Translation:** [the translation]
**Example:** [a short example sentence using the word]"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"You are a helpful translator from {from_lang} to {to_lang}. Be concise and accurate."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error: {e}"


def translate_to_english(french_word):
    """
    Traduit un mot français en anglais.
    """
    return translate_word(french_word, "French", "English")


def translate_to_french(english_word):
    """
    Traduit un mot anglais en français.
    """
    return translate_word(english_word, "English", "French")
