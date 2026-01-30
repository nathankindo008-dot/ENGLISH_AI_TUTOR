from modules.stt import listen_once
from modules.tts import speak
from modules.llm_client import ask_llm
from modules.feedback import extract_feedback
from modules.conversation import ConversationManager
from modules.speed_control import start_speed_control, stop_speed_control
from config import USE_VOICE_OUTPUT
import time


def main():
    """
    Boucle principale avec système de feedback et auto-save.
    """
    print("\n" + "="*60)
    print("🎓 English AI Tutor - Day 2: Feedback System")
    print("="*60)
    print("Commands: Say 'stop', 'exit', 'quit' or 'goodbye'")
    print("Or: Press Ctrl+C to exit and save\n")
    
    # Lancer la fenêtre de contrôle de vitesse
    start_speed_control()
    print("📊 Speed control window opened (use +/- buttons)\n")
    
    # Initialiser l'historique LLM
    history = []
    
    # Initialiser le gestionnaire de conversations
    conv_manager = ConversationManager()
    
    # Choisir un rôle
    print("Choose your tutor role:")
    print("1. Tutor (corrections + feedback)")
    print("2. Friend (casual conversation)")
    
    role_choice = input("Enter choice (1-2, default 1): ").strip() or "1"
    role_map = {"1": "tutor", "2": "friend"}
    role = role_map.get(role_choice, "tutor")
    
    print(f"\n✨ Role selected: {role.upper()}")
    print("Starting conversation...\n")
    
    # Saluer l'utilisateur
    initial_message = "Let's practice English together! Feel free to talk about anything."
    print(f"🔊 AI: {initial_message}\n")
    if USE_VOICE_OUTPUT:
        speak(initial_message)
    
    # Boucle principale
    turn = 0
    last_activity = time.time()
    
    while True:
        turn += 1
        print(f"\n{'='*60}")
        print(f"--- Turn {turn} ---")
        print(f"{'='*60}\n")
        
        # ÉTAPE 1 : Écouter l'utilisateur
        user_text = listen_once()
        
        # Si rien n'a été dit
        if user_text is None:
            continue
        
        last_activity = time.time()
        
        # Si l'utilisateur demande à arrêter
        stop_words = ["stop", "exit", "quit", "bye", "goodbye"]
        if any(word in user_text.lower() for word in stop_words):
            farewell = "Great practice! Keep it up. Goodbye!"
            print(f"\n🔊 AI: {farewell}\n")
            if USE_VOICE_OUTPUT:
                speak(farewell)
            
            # Sauvegarder avant de quitter
            print("\n💾 Saving conversation...")
            conv_manager.save()
            
            # Fermer la fenêtre de contrôle
            stop_speed_control()
            
            print("\n" + "="*60)
            print("Thanks for practicing! See you next time! 👋")
            print("="*60 + "\n")
            break
        
        # ÉTAPE 2 : Appeler l'IA Groq
        print(f"\n💭 Thinking...")
        response, history = ask_llm(history, user_text, role=role)
        
        # ÉTAPE 3 : Extraire le feedback
        feedback = extract_feedback(response)
        
        # ÉTAPE 4 : Afficher la réponse avec feedback structuré
        print(f"\n{'─'*60}")
        print(f"🎤 You: {user_text}")
        print(f"{'─'*60}")
        print(f"🤖 Tutor: {feedback['response']}")
        
        # Afficher les corrections
        if feedback['corrections'] and feedback['corrections'] != ["None - well done!"]:
            print(f"\n❌ Corrections:")
            for correction in feedback['corrections']:
                if correction.strip():
                    print(f"   • {correction}")
        else:
            print(f"\n✅ No corrections - excellent!")
        
        # Afficher le vocabulaire
        if feedback['vocabulary']:
            print(f"\n📚 Vocabulary:")
            for vocab in feedback['vocabulary']:
                if vocab.strip():
                    print(f"   • {vocab}")
        
        # Afficher les tips grammaticaux
        if feedback['grammar_tips']:
            print(f"\n📖 Grammar Tips:")
            for tip in feedback['grammar_tips']:
                if tip.strip():
                    print(f"   • {tip}")
        
        print(f"{'─'*60}\n")
        
        # ÉTAPE 5 : Parler la réponse
        if USE_VOICE_OUTPUT:
            speak(feedback['response'])
        
        # ÉTAPE 6 : Sauvegarder le tour
        conv_manager.add_turn(user_text, response, feedback)


# Point d'entrée du script
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stop_speed_control()
        print("\n\n⏹️ Interrupted by user.")
        print("Goodbye!")
    except Exception as e:
        stop_speed_control()
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
