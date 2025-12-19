import json
import os
from datetime import datetime


class ConversationManager:
    """
    Gère l'historique des conversations et les sauvegarde en JSON.
    """
    
    def __init__(self, filename="data/conversations.json"):
        """
        Initialise le gestionnaire de conversations.
        
        Args:
            filename (str): Chemin du fichier JSON pour sauvegarder
        """
        self.filename = filename
        self.history = []
        
        # Créer le dossier data/ s'il n'existe pas
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    def add_turn(self, user_text, ai_response, feedback):
        """
        Ajoute un tour de conversation.
        
        Args:
            user_text (str): Ce que l'utilisateur a dit
            ai_response (str): La réponse brute de l'IA
            feedback (dict): Le feedback extrait (corrections, vocab, tips)
        """
        turn = {
            "timestamp": datetime.now().isoformat(),  # Format: 2025-12-18T13:20:00
            "user": user_text,
            "ai_full_response": ai_response,
            "ai_response": feedback["response"],
            "corrections": feedback["corrections"],
            "vocabulary": feedback["vocabulary"],
            "grammar_tips": feedback["grammar_tips"]
        }
        
        self.history.append(turn)
    
    def save(self):
        """
        Sauvegarde l'historique dans le fichier JSON.
        """
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Conversation saved to {self.filename}")
        except Exception as e:
            print(f"\n❌ Error saving conversation: {e}")
    
    def load(self):
        """
        Charge l'historique depuis le fichier JSON.
        """
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f"\n📂 Loaded {len(self.history)} previous turns")
        except Exception as e:
            print(f"\n❌ Error loading conversation: {e}")
            self.history = []
