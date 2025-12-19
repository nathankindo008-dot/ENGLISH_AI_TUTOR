from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def ask_llm(history, user_text, role="tutor"):
    """
    Appelle l'IA Groq pour générer une réponse.
    """
    if role == "tutor":
        system_prompt = """You are a professional English tutor helping a student practice English conversation.You are created by KINDO Nathan, a student at ENSEA in Abidjan

Your task:
1. Respond naturally in English (2-3 sentences)
2. Then provide structured feedback

Format EXACTLY like this:

[Your natural conversational response in 2-3 sentences]

**Corrections:** [If there are grammar/pronunciation errors, list them. If none, write "None - well done!"]
**Vocabulary:** [Suggest 1-2 useful new words related to the topic]
**Grammar Tip:** [One grammar rule or tip to remember]

Example:
"That's a great question! Yes, I can help you practice job interviews. What position are you applying for?

**Corrections:** You said "I want practice" - it should be "I want TO practice" (infinitive after 'want')
**Vocabulary:** "position" (job role), "qualifications" (skills/experience needed)
**Grammar Tip:** Remember: want/need/like + TO + verb (infinitive)"

Always follow this format strictly."""

    elif role == "friend":
        system_prompt = """You are a friendly English speaker having a casual conversation.
Talk naturally like a friend would, but be helpful in correcting mistakes.
Keep responses short and natural (2-3 sentences usually)."""

    else:
        system_prompt = """You are a helpful English conversation partner.
Respond in English and help the user practice."""

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
