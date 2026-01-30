import tkinter as tk
from tkinter import ttk
import threading
from config import TTS_RATE_MIN, TTS_RATE_MAX, TTS_RATE_STEP, tts_settings


class SpeedControlWindow:
    """
    Fenêtre flottante avec boutons pour contrôler la vitesse de parole.
    """
    
    def __init__(self):
        self.root = None
        self.speed_label = None
        self.thread = None
        self.running = False
    
    def _create_window(self):
        """Crée la fenêtre tkinter."""
        self.root = tk.Tk()
        self.root.title("Speech Speed")
        self.root.geometry("200x120")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)  # Toujours au premier plan
        
        # Style
        self.root.configure(bg="#2b2b2b")
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg="#2b2b2b", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # Label titre
        title_label = tk.Label(
            main_frame, 
            text="🔊 Speech Speed", 
            font=("Segoe UI", 11, "bold"),
            bg="#2b2b2b", 
            fg="white"
        )
        title_label.pack(pady=(0, 10))
        
        # Frame pour les boutons et la valeur
        control_frame = tk.Frame(main_frame, bg="#2b2b2b")
        control_frame.pack()
        
        # Bouton diminuer
        btn_slower = tk.Button(
            control_frame,
            text="➖",
            font=("Segoe UI", 14),
            width=3,
            command=self._decrease_speed,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            relief="flat",
            cursor="hand2"
        )
        btn_slower.pack(side="left", padx=5)
        
        # Label vitesse actuelle
        self.speed_label = tk.Label(
            control_frame,
            text=str(tts_settings["rate"]),
            font=("Segoe UI", 16, "bold"),
            width=5,
            bg="#3498db",
            fg="white"
        )
        self.speed_label.pack(side="left", padx=5)
        
        # Bouton augmenter
        btn_faster = tk.Button(
            control_frame,
            text="➕",
            font=("Segoe UI", 14),
            width=3,
            command=self._increase_speed,
            bg="#27ae60",
            fg="white",
            activebackground="#1e8449",
            relief="flat",
            cursor="hand2"
        )
        btn_faster.pack(side="left", padx=5)
        
        # Empêcher la fermeture de la fenêtre principale
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _update_label(self):
        """Met à jour l'affichage de la vitesse."""
        if self.speed_label:
            self.speed_label.config(text=str(tts_settings["rate"]))
    
    def _increase_speed(self):
        """Augmente la vitesse."""
        new_rate = tts_settings["rate"] + TTS_RATE_STEP
        tts_settings["rate"] = min(TTS_RATE_MAX, new_rate)
        self._update_label()
        print(f"⚡ Speed: {tts_settings['rate']}")
    
    def _decrease_speed(self):
        """Diminue la vitesse."""
        new_rate = tts_settings["rate"] - TTS_RATE_STEP
        tts_settings["rate"] = max(TTS_RATE_MIN, new_rate)
        self._update_label()
        print(f"🐢 Speed: {tts_settings['rate']}")
    
    def _on_close(self):
        """Gère la fermeture de la fenêtre."""
        self.running = False
        if self.root:
            self.root.destroy()
            self.root = None
    
    def _run(self):
        """Lance la boucle principale tkinter."""
        self._create_window()
        self.running = True
        self.root.mainloop()
    
    def start(self):
        """Démarre la fenêtre dans un thread séparé."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Arrête la fenêtre."""
        if self.root and self.running:
            self.root.after(0, self._on_close)


# Instance globale
_speed_control = None


def start_speed_control():
    """Démarre la fenêtre de contrôle de vitesse."""
    global _speed_control
    _speed_control = SpeedControlWindow()
    _speed_control.start()


def stop_speed_control():
    """Arrête la fenêtre de contrôle de vitesse."""
    global _speed_control
    if _speed_control:
        _speed_control.stop()
        _speed_control = None
