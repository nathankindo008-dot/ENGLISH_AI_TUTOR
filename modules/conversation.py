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
        """
        self.filename = filename
        self.session_history = []  # Historique de la session actuelle
        self.all_history = []      # Toutes les conversations (anciennes + nouvelles)
        
        # Créer le dossier data/ s'il n'existe pas
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Charger les conversations existantes
        self._load_existing()
    
    def _load_existing(self):
        """
        Charge les conversations existantes depuis le fichier.
        """
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.all_history = json.load(f)
                print(f"📂 Loaded {len(self.all_history)} previous conversations")
        except Exception as e:
            print(f"❌ Error loading conversations: {e}")
            self.all_history = []
    
    def add_turn(self, user_text, ai_response, feedback):
        """
        Ajoute un tour de conversation.
        """
        turn = {
            "timestamp": datetime.now().isoformat(),
            "user": user_text,
            "ai_full_response": ai_response,
            "ai_response": feedback["response"],
            "corrections": feedback["corrections"],
            "vocabulary": feedback["vocabulary"],
            "grammar_tips": feedback["grammar_tips"]
        }
        
        self.session_history.append(turn)
        self.all_history.append(turn)
        
        # Auto-save après chaque tour
        self._auto_save()
    
    def _auto_save(self):
        """
        Sauvegarde automatique après chaque tour.
        """
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Auto-save error: {e}")
    
    def save(self):
        """
        Sauvegarde manuelle l'historique dans le fichier JSON.
        """
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_history, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Conversation saved to {self.filename}")
        except Exception as e:
            print(f"\n❌ Error saving conversation: {e}")
    
    def load(self):
        """
        Charge l'historique depuis le fichier JSON.
        """
        self._load_existing()
    
    def get_session_count(self):
        """
        Retourne le nombre de tours de la session actuelle.
        """
        return len(self.session_history)
    
    def get_total_count(self):
        """
        Retourne le nombre total de tous les tours.
        """
        return len(self.all_history)
