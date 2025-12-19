import json
import os
from collections import Counter
from datetime import datetime


class ProgressTracker:
    """
    Analyse les progrès de l'utilisateur à partir des conversations sauvegardées.
    """
    
    def __init__(self, conversations_file="data/conversations.json"):
        """
        Initialise le tracker avec le fichier de conversations.
        """
        self.conversations_file = conversations_file
        self.conversations = []
        self.load_conversations()
    
    def load_conversations(self):
        """
        Charge les conversations depuis le fichier JSON.
        """
        if os.path.exists(self.conversations_file):
            try:
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)
            except Exception as e:
                print(f"❌ Error loading conversations: {e}")
                self.conversations = []
    
    def get_total_turns(self):
        """
        Retourne le nombre total de tours de conversation.
        """
        return len(self.conversations)
    
    def get_total_words_spoken(self):
        """
        Retourne le nombre total de mots parlés par l'utilisateur.
        """
        total = 0
        for turn in self.conversations:
            words = turn.get("user", "").split()
            total += len(words)
        return total
    
    def get_total_words_heard(self):
        """
        Retourne le nombre total de mots entendus de l'IA.
        """
        total = 0
        for turn in self.conversations:
            words = turn.get("ai_response", "").split()
            total += len(words)
        return total
    
    def get_recurring_errors(self, top_n=5):
        """
        Retourne les erreurs les plus récurrentes.
        
        Returns:
            list: Liste des (erreur, count) triée par fréquence
        """
        error_counter = Counter()
        
        for turn in self.conversations:
            corrections = turn.get("corrections", [])
            for correction in corrections:
                if correction.strip() and correction != "None - well done!":
                    error_counter[correction] += 1
        
        return error_counter.most_common(top_n)
    
    def get_vocabulary_learned(self):
        """
        Retourne tout le vocabulaire appris.
        
        Returns:
            set: Ensemble des mots/expressions de vocabulaire
        """
        vocab_set = set()
        
        for turn in self.conversations:
            vocabulary = turn.get("vocabulary", [])
            for vocab in vocabulary:
                if vocab.strip():
                    vocab_set.add(vocab)
        
        return vocab_set
    
    def get_grammar_tips(self):
        """
        Retourne tous les tips grammaticaux.
        
        Returns:
            set: Ensemble des tips grammaticaux
        """
        tips_set = set()
        
        for turn in self.conversations:
            tips = turn.get("grammar_tips", [])
            for tip in tips:
                if tip.strip():
                    tips_set.add(tip)
        
        return tips_set
    
    def get_average_words_per_turn(self):
        """
        Retourne la moyenne de mots par turn de l'utilisateur.
        """
        if not self.conversations:
            return 0
        
        total_words = self.get_total_words_spoken()
        turns = self.get_total_turns()
        
        return round(total_words / turns, 1) if turns > 0 else 0
    
    def get_correction_free_turns(self):
        """
        Retourne le nombre de turns sans correction (excellents tours).
        """
        count = 0
        for turn in self.conversations:
            corrections = turn.get("corrections", [])
            if not corrections or corrections == ["None - well done!"]:
                count += 1
        
        return count
    
    def get_report(self):
        """
        Génère un rapport texte complet des progrès.
        
        Returns:
            str: Rapport formaté
        """
        total_turns = self.get_total_turns()
        total_words = self.get_total_words_spoken()
        avg_words = self.get_average_words_per_turn()
        perfect_turns = self.get_correction_free_turns()
        vocab = self.get_vocabulary_learned()
        
        report = f"""
📊 PROGRESS REPORT
{'='*60}

📈 Statistics
─────────────────────────────────
• Total conversations: {total_turns} turns
• Total words spoken: {total_words} words
• Average words per turn: {avg_words}
• Perfect turns (no corrections): {perfect_turns}/{total_turns} ({round(perfect_turns/total_turns*100, 1)}%)

📚 Learning Progress
─────────────────────────────────
• Vocabulary learned: {len(vocab)} terms
• Grammar tips discovered: {len(self.get_grammar_tips())} tips

🔴 Top Recurring Errors
─────────────────────────────────
"""
        
        recurring = self.get_recurring_errors(top_n=5)
        if recurring:
            for i, (error, count) in enumerate(recurring, 1):
                report += f"\n{i}. [{count}x] {error}"
        else:
            report += "\n✅ No recurring errors - great job!"
        
        report += f"\n\n{'='*60}\n"
        
        return report
    
    def get_daily_progress(self):
        """
        Retourne les statistiques groupées par jour.
        
        Returns:
            dict: {date: {turns, words}}
        """
        daily_stats = {}
        
        for turn in self.conversations:
            timestamp = turn.get("timestamp", "")
            if not timestamp:
                continue
            
            # Extraire la date (format: 2025-12-18T...)
            date = timestamp.split("T")[0]
            
            if date not in daily_stats:
                daily_stats[date] = {"turns": 0, "words": 0}
            
            daily_stats[date]["turns"] += 1
            words = len(turn.get("user", "").split())
            daily_stats[date]["words"] += words
        
        return daily_stats
