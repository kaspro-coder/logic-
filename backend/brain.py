import time
import json
import os
import base64
import google.generativeai as genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyD0EZxDuLrdutjY2fypk7qJ_R-G7XTcFKM" # Remets ta clé ici !

genai.configure(api_key=GEMINI_API_KEY)

def find_desktop_file(filename):
    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    possible_paths = [
        os.path.join(user_profile, "Desktop"),
        os.path.join(user_profile, "OneDrive", "Desktop"),
        os.path.join(user_profile, "OneDrive", "Bureau"),
        os.path.join(user_profile, "Bureau")
    ]
    for path in possible_paths:
        full_path = os.path.join(path, filename)
        # On vérifie juste le dossier parent
        if os.path.exists(path): return full_path
    return os.path.join(user_profile, "Desktop", filename)

WATCH_FILE = find_desktop_file("loupedeck_context.json")
ACTIONS_FILE = find_desktop_file("loupedeck_actions.json") # Nouveau fichier de sortie

def get_working_model():
    # (Version simplifiée qui prend le Flash directement, comme validé avant)
    return genai.GenerativeModel('models/gemini-2.5-flash')

model = get_working_model()

class ContextHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if os.path.normpath(event.src_path) == os.path.normpath(WATCH_FILE):
            time.sleep(0.2)
            process_with_gemini()

def process_with_gemini():
    print(f"\n[Oeil] Détection...")
    if not os.path.exists(WATCH_FILE): return

    try:
        with open(WATCH_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content: return
            data = json.loads(content)
    except: return

    process_name = data.get('process', 'Inconnu')
    image_b64 = data.get('screenshot_base64', '')

    if not image_b64: return

    print(f"[Cerveau] Analyse de : {process_name}")

    try:
        image_bytes = base64.b64decode(image_b64)
    except: return

    image_part = {"mime_type": "image/jpeg", "data": image_bytes}

    # PROMPT MIS À JOUR POUR LE MAPPING
    prompt = f"""
    Contexte : L'utilisateur utilise "{process_name}".
    Analyse l'écran. Donne-moi 4 raccourcis clavier utiles.
    
    IMPORTANT : Ajoute un champ 'keys' compatible avec C# SendKeys :
    - Ctrl = ^, Alt = %, Shift = +
    - Ctrl+C -> ^c
    - Entrée -> {{ENTER}}
    - Espace ->  (espace)
    - Page Down -> {{PGDN}}
    
    Réponds UNIQUEMENT en JSON brut :
    [ 
      {{"label": "Titre Court", "keys": "^c", "description": "Copier"}} 
    ]
    """

    try:
        response = model.generate_content([prompt, image_part])
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        
        # 1. Affichage Console
        print("\n" + "="*40)
        actions = json.loads(clean_text)
        for i, action in enumerate(actions):
            print(f"{i+1}. {action['label']} ({action.get('keys', '')})")
        print("="*40 + "\n")

        # 2. Sauvegarde pour le Plugin C#
        with open(ACTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(actions, f, indent=2)
        print(f"[Cerveau] Actions sauvegardées dans {ACTIONS_FILE}")

    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    watch_dir = os.path.dirname(WATCH_FILE)
    print(f"--- Cerveau Connecté ---")
    print(f"Entrée : {WATCH_FILE}")
    print(f"Sortie : {ACTIONS_FILE}")
    
    observer = Observer()
    observer.schedule(ContextHandler(), path=watch_dir, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: observer.stop()
    observer.join()