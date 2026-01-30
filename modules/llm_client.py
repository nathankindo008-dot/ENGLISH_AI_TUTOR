from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

# Modes d'apprentissage disponibles
LEARNING_MODES = {
    "general": {
        "name": "General English",
        "description": "Practice everyday English conversation",
        "icon": "🗣️"
    },
    "toeic": {
        "name": "TOEIC Preparation",
        "description": "Business English for TOEIC exam",
        "icon": "💼"
    },
    "toefl": {
        "name": "TOEFL Preparation", 
        "description": "Academic English for TOEFL exam",
        "icon": "🎓"
    },
    "ielts": {
        "name": "IELTS Preparation",
        "description": "Academic & General English for IELTS",
        "icon": "📝"
    },
    "business": {
        "name": "Business English",
        "description": "Professional workplace English",
        "icon": "👔"
    },
    "travel": {
        "name": "Travel English",
        "description": "English for traveling abroad",
        "icon": "✈️"
    }
}


def get_system_prompt(role="tutor", learning_mode="general"):
    """
    Génère le prompt système en fonction du rôle et du mode d'apprentissage.
    """
    base_intro = "You are created by KINDO Nathan, a student at ENSEA in Abidjan."
    
    # Prompts spécifiques par mode d'apprentissage
    mode_contexts = {
        "general": "Focus on everyday conversation topics like hobbies, daily life, opinions, and general knowledge.",
        
        "toeic": """Focus on TOEIC exam preparation:
- Business vocabulary (meetings, emails, negotiations, reports)
- Workplace scenarios (office, travel, customer service)
- Formal expressions and professional communication
- Reading comprehension strategies for business documents
- Listening skills for announcements and conversations
Include TOEIC-style vocabulary and expressions in your responses.""",
        
        "toefl": """Focus on TOEFL exam preparation:
- Academic vocabulary and formal language
- University and campus life scenarios
- Lecture comprehension and note-taking
- Opinion essays and integrated writing topics
- Speaking tasks (independent and integrated)
Include academic vocabulary and complex sentence structures.""",
        
        "ielts": """Focus on IELTS exam preparation:
- Both academic and general training topics
- Part 1, 2, and 3 speaking test formats
- Paraphrasing and vocabulary range
- Coherence and fluency practice
- Task response and lexical resource
Include band-score improving vocabulary and expressions.""",
        
        "business": """Focus on professional Business English:
- Meeting vocabulary and expressions
- Email and report writing language
- Presentation skills and phrases
- Negotiation and persuasion techniques
- Corporate culture and etiquette
Include professional idioms and business jargon.""",
        
        "travel": """Focus on Travel English:
- Airport and transportation vocabulary
- Hotel and accommodation phrases
- Restaurant and food ordering
- Asking for directions and help
- Emergency situations
Include practical travel phrases and cultural tips."""
    }
    
    mode_context = mode_contexts.get(learning_mode, mode_contexts["general"])
    
    if role == "tutor":
        system_prompt = f"""You are a professional English tutor helping a student practice English conversation. {base_intro}

LEARNING MODE: {LEARNING_MODES.get(learning_mode, LEARNING_MODES['general'])['name']}
{mode_context}

Your task:
1. Respond naturally in English (2-3 sentences) related to the learning mode
2. Then provide structured feedback

Format EXACTLY like this:

[Your natural conversational response in 2-3 sentences]

**Corrections:** [If there are grammar/pronunciation errors, list them. If none, write "None - well done!"]
**Vocabulary:** [Suggest 1-2 useful new words related to the topic and learning mode]
**Grammar Tip:** [One grammar rule or tip to remember]

Example:
"That's a great question! Yes, I can help you practice job interviews. What position are you applying for?

**Corrections:** You said "I want practice" - it should be "I want TO practice" (infinitive after 'want')
**Vocabulary:** "position" (job role), "qualifications" (skills/experience needed)
**Grammar Tip:** Remember: want/need/like + TO + verb (infinitive)"

Always follow this format strictly."""

    elif role == "friend":
        system_prompt = f"""You are a friendly English speaker having a casual conversation. {base_intro}

LEARNING MODE: {LEARNING_MODES.get(learning_mode, LEARNING_MODES['general'])['name']}
{mode_context}

Talk naturally like a friend would, but subtly incorporate vocabulary and topics from the learning mode.
Keep responses short and natural (2-3 sentences usually).
If you notice mistakes, mention them casually like a friend would."""

    else:
        system_prompt = f"""You are a helpful English conversation partner. {base_intro}
Respond in English and help the user practice.
{mode_context}"""
    
    return system_prompt


def ask_llm(history, user_text, role="tutor", learning_mode="general"):
    """
    Appelle l'IA Groq pour générer une réponse.
    """
    system_prompt = get_system_prompt(role, learning_mode)

    if not history or history[0].get("role") != "system":
        history = [{"role": "system", "content": system_prompt}] + history
    else:
        history[0]["content"] = system_prompt

    history.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=history,
            max_tokens=500,
            temperature=0.7,
        )

        assistant_message = response.choices[0].message.content

        history.append({"role": "assistant", "content": assistant_message})

        return assistant_message, history

    except Exception as e:
        error_message = f"Error calling Groq API: {e}"
        print(f"❌ {error_message}")
        return error_message, history
