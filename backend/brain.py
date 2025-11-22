import time
import json
import os
import base64
import google.generativeai as genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION API ---
# Remplacez ceci par votre vraie clé API Google
GEMINI_API_KEY = "AIzaSyD0EZxDuLrdutjY2fypk7qJ_R-G7XTcFKM" 

# Configuration globale
genai.configure(api_key=GEMINI_API_KEY)

# --- SÉLECTION INTELLIGENTE ET ROBUSTE ---
def get_working_model():
    print("\n🔍 DIAGNOSTIC DES MODÈLES DISPONIBLES...")
    try:
        # On récupère tout ce qui peut générer du contenu
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not all_models:
            print("❌ AUCUN modèle trouvé. Votre clé API est peut-être invalide ou n'a accès à rien.")
            return None

        # Ordre de préférence mis à jour avec vos logs (2.5 Flash en priorité !)
        preferences = [
            "models/gemini-2.5-flash",          # LE MEILLEUR POUR VOUS (Rapide & Dispo)
            "models/gemini-2.5-flash-lite",     # Alternative légère
            "models/gemini-2.0-flash",          # Version précédente très stable
            "models/gemini-2.0-flash-exp",      # Expérimental rapide
            "models/gemini-1.5-flash",          # Ancien standard
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]

        selected_model = None
        
        # 1. On cherche dans nos préférences
        for pref in preferences:
            if pref in all_models:
                selected_model = pref
                print(f"\n✅ VICTOIRE : On utilise '{selected_model}'")
                break
        
        # 2. Si rien trouvé dans nos favoris, on prend le premier qui contient "flash"
        if not selected_model:
            for m in all_models:
                if "flash" in m:
                    selected_model = m
                    print(f"\n⚠️ FALLBACK INTELLIGENT : On utilise '{selected_model}' (contient 'flash')")
                    break

        # 3. Si vraiment rien, le premier de la liste
        if not selected_model:
            selected_model = all_models[0]
            print(f"\n⚠️ FALLBACK ULTIME : On utilise '{selected_model}'")

        return genai.GenerativeModel(selected_model)

    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE lors du listing : {e}")
        return None

# Initialisation globale
model = None

# --- UTILITAIRES FICHIERS ---
def find_desktop_file():
    filename = "loupedeck_context.json"
    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    possible_paths = [
        os.path.join(user_profile, "Desktop"),
        os.path.join(user_profile, "OneDrive", "Desktop"),
        os.path.join(user_profile, "OneDrive", "Bureau"),
        os.path.join(user_profile, "Bureau")
    ]
    for path in possible_paths:
        full_path = os.path.join(path, filename)
        if os.path.exists(path): return full_path
    return os.path.join(user_profile, "Desktop", filename)

WATCH_FILE = find_desktop_file()

class ContextHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if os.path.normpath(event.src_path) == os.path.normpath(WATCH_FILE):
            time.sleep(0.2)
            process_with_gemini()

def process_with_gemini():
    if not model:
        print("❌ Pas de modèle configuré. Abandon.")
        return

    print(f"\n[Oeil] Détection de changement...")
    if not os.path.exists(WATCH_FILE): return

    try:
        with open(WATCH_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content: return
            data = json.loads(content)
    except Exception: return

    process_name = data.get('process', 'Inconnu')
    window_title = data.get('title', '')
    image_b64 = data.get('screenshot_base64', '')

    if not image_b64: return

    print(f"[Cerveau] Analyse de : {process_name}")

    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception: return

    image_part = {"mime_type": "image/jpeg", "data": image_bytes}

    prompt = f"""
    Contexte : L'utilisateur est sur "{process_name}" (Titre: "{window_title}").
    Analyse l'écran. Donne-moi 4 raccourcis ou actions ULTRA pertinents.
    Réponds UNIQUEMENT en JSON brut :
    [ {{"label": "Action", "shortcut": "Key", "description": "Why"}} ]
    """

    print("[Gemini] Réflexion en cours...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt, image_part])
            
            print("\n" + "="*40)
            print(f"SUGGESTIONS ({process_name.upper()}) :")
            print("="*40)
            
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            try:
                actions = json.loads(clean_text)
                for i, action in enumerate(actions):
                    print(f"{i+1}. {action['label']} ({action.get('shortcut', '')})")
                    print(f"   > {action['description']}")
            except:
                print(clean_text)
            print("="*40 + "\n")
            break 

        except Exception as e:
            if "429" in str(e):
                print(f"⏳ Quota atteint, attente 5s... ({attempt+1}/{max_retries})")
                time.sleep(5)
            else:
                print(f"❌ Erreur Gemini : {e}")
                break

if __name__ == "__main__":
    watch_dir = os.path.dirname(WATCH_FILE)
    
    # Lancement du diagnostic
    model = get_working_model()
    
    if not model:
        print("Impossible de démarrer sans modèle.")
        exit(1)

    if not os.path.exists(watch_dir):
        print(f"[ERREUR] Dossier introuvable : {watch_dir}")
        exit(1)

    print(f"--- Cerveau IA Démarré ---")
    print(f"Surveillance : {WATCH_FILE}")
    
    observer = Observer()
    observer.schedule(ContextHandler(), path=watch_dir, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: observer.stop()
    observer.join()