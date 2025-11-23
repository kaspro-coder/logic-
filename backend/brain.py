import time
import json
import os
import base64
import threading
import tkinter as tk
from tkinter import scrolledtext
import google.generativeai as genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyCl_TpHFZ9amKxUQ5qCXKHiMWySXgkp66E" # Remets ta clé ici !

genai.configure(api_key=GEMINI_API_KEY)

# --- SÉLECTION INTELLIGENTE DU MODÈLE (Le retour du fix !) ---
def get_working_model():
    print("\n🔍 Recherche du modèle compatible...")
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ordre de préférence (du plus rapide au plus puissant)
        preferences = [
            "models/gemini-2.5-flash",          # Celui qui marchait pour vous
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]

        selected_model_name = None
        
        # 1. On cherche dans nos préférences
        for pref in preferences:
            if pref in all_models:
                selected_model_name = pref
                break
        
        # 2. Fallback
        if not selected_model_name and all_models:
            selected_model_name = all_models[0]

        if selected_model_name:
            print(f"✅ Modèle activé : {selected_model_name}")
            return genai.GenerativeModel(selected_model_name)
        else:
            print("❌ Aucun modèle trouvé.")
            return None

    except Exception as e:
        print(f"❌ Erreur lors du choix du modèle : {e}")
        return None

# Initialisation du modèle
model = get_working_model()

# --- GESTION DES CHEMINS ---
def find_desktop_path():
    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    possible_paths = [
        os.path.join(user_profile, "Desktop"),
        os.path.join(user_profile, "OneDrive", "Desktop"),
        os.path.join(user_profile, "OneDrive", "Bureau"),
        os.path.join(user_profile, "Bureau")
    ]
    for path in possible_paths:
        if os.path.exists(path): return path
    return os.path.join(user_profile, "Desktop")

DESKTOP_DIR = find_desktop_path()
CONTEXT_FILE = os.path.join(DESKTOP_DIR, "loupedeck_context.json")
SUMMARY_FILE = os.path.join(DESKTOP_DIR, "loupedeck_summary.json")
ACTIONS_FILE = os.path.join(DESKTOP_DIR, "loupedeck_actions.json")

# --- INTERFACE GRAPHIQUE (POP-UP) ---
def show_summary_popup(text, source_app):
    def run_gui():
        root = tk.Tk()
        root.title(f"Résumé IA - {source_app}")
        root.geometry("600x500")
        root.configure(bg="#1e1e1e")
        root.attributes("-topmost", True)

        # Header
        header_frame = tk.Frame(root, bg="#1e1e1e")
        header_frame.pack(pady=10, fill=tk.X)
        
        lbl = tk.Label(header_frame, text=f"Analyse : {source_app}", font=("Segoe UI", 14, "bold"), bg="#1e1e1e", fg="#00ff9d")
        lbl.pack()

        # Zone de texte
        text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, font=("Consolas", 11), bg="#252526", fg="#d4d4d4", bd=0, padx=10, pady=10)
        text_area.pack(padx=15, pady=5, fill=tk.BOTH, expand=True)
        
        text_area.insert(tk.INSERT, text)
        text_area.configure(state='disabled')

        # Bouton Fermer
        btn = tk.Button(root, text="Fermer", command=root.destroy, bg="#007acc", fg="white", font=("Segoe UI", 10), relief="flat", padx=20, pady=5)
        btn.pack(pady=15)

        root.mainloop()

    gui_thread = threading.Thread(target=run_gui)
    gui_thread.daemon = True
    gui_thread.start()

# --- INTELLIGENCE GEMINI ---
def analyze_for_buttons(process_name, image_part):
    if not model: return
    print(f"[Boutons] Analyse de {process_name}...")
    
    prompt = f"""Contexte: App "{process_name}". Donne 4 raccourcis utiles.
    JSON uniquement: [ {{"label": "Titre", "keys": "Raccourci"}} ]"""
    
    try:
        response = model.generate_content([prompt, image_part])
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        
        with open(ACTIONS_FILE, 'w', encoding='utf-8') as f:
            f.write(clean_text)
        print("-> Boutons mis à jour.")
    except Exception as e: print(f"Erreur Boutons: {e}")

def analyze_for_summary(process_name, image_part):
    if not model: return
    print(f"[Résumé] Lecture de {process_name}...")
    
    prompt = f"""
    Tu es un assistant de productivité expert.
    L'utilisateur regarde l'application "{process_name}".
    
    Analyse l'image fournie (texte, code, email, article).
    Génère un résumé structuré en Français (Markdown) :
    
    ## 📌 Sujet Principal
    [Une phrase courte]
    
    ## 🔑 Points Clés
    - Point 1
    - Point 2
    - Point 3
    
    ## 💡 Action Suggérée
    [Ce que l'utilisateur devrait faire ensuite]
    """
    
    try:
        response = model.generate_content([prompt, image_part])
        print("-> Résumé généré !")
        show_summary_popup(response.text, process_name)
    except Exception as e: print(f"Erreur Résumé: {e}")

# --- SURVEILLANCE ---
class ContextHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if os.path.normpath(event.src_path) == os.path.normpath(CONTEXT_FILE):
            time.sleep(0.2)
            process_file(CONTEXT_FILE, "buttons")
            
        elif os.path.normpath(event.src_path) == os.path.normpath(SUMMARY_FILE):
            time.sleep(0.2)
            process_file(SUMMARY_FILE, "summary")

def process_file(filepath, mode):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        proc = data.get('process', 'Unknown')
        img_b64 = data.get('screenshot_base64', '')
        if not img_b64: return

        img_bytes = base64.b64decode(img_b64)
        img_part = {"mime_type": "image/jpeg", "data": img_bytes}

        if mode == "buttons":
            analyze_for_buttons(proc, img_part)
        elif mode == "summary":
            analyze_for_summary(proc, img_part)

    except Exception as e: print(f"Erreur processing: {e}")

if __name__ == "__main__":
    if not model:
        print("ERREUR: Impossible d'initialiser le modèle Gemini.")
        exit()

    print(f"--- Cerveau IA Actif ---")
    print(f"Dossier : {DESKTOP_DIR}")
    
    observer = Observer()
    observer.schedule(ContextHandler(), path=DESKTOP_DIR, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: observer.stop()
    observer.join()