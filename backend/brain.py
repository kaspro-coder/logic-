import time
import json
import os
import base64
import io
import threading
import tkinter as tk
from tkinter import scrolledtext
import tkinter.ttk as ttk
import google.generativeai as genai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyBcTnPtenab0Fd6m3dnaaYtJFaQsh2keIk" # Votre clé API

genai.configure(api_key=GEMINI_API_KEY)

# --- SÉLECTION INTELLIGENTE DU MODÈLE ---
def get_working_model():
    print("\n🔍 Recherche du modèle compatible...")
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        preferences = [
            "models/gemini-2.5-flash",
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]

        selected_model_name = None
        for pref in preferences:
            if pref in all_models:
                selected_model_name = pref
                break
        
        if not selected_model_name and all_models:
            selected_model_name = all_models[0]

        if selected_model_name:
            print(f"✅ Modèle activé : {selected_model_name}")
            return genai.GenerativeModel(selected_model_name)
        return None

    except Exception as e:
        print(f"❌ Erreur modèle : {e}")
        return None

model = get_working_model()

# --- OUTILS IMAGE ---
def emoji_to_base64(emoji, size=80):
    try:
        img = Image.new('RGB', (size, size), color='black')
        d = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("seguiemj.ttf", size=int(size*0.6))
        except: font = ImageFont.load_default()
        d.text((size/2, size/2), emoji, font=font, anchor="mm", fill="white")
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except: return ""

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

# --- GUI : LOADING SCREEN ---
def show_loading_screen(app_name, mode="Analyse"):
    state = {"running": True}

    def run():
        root = tk.Tk()
        root.overrideredirect(True) # Pas de bordure
        
        # Centrage
        w, h = 350, 120
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        root.geometry(f"{w}x{h}+{x}+{y}")
        
        root.configure(bg="#1e1e1e")
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.90)
        
        # Design
        frame = tk.Frame(root, bg="#1e1e1e", highlightbackground="#00ff9d", highlightthickness=2)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_text = f"IA : {mode} de {app_name}..."
        lbl = tk.Label(frame, text=title_text, fg="white", bg="#1e1e1e", font=("Segoe UI", 12, "bold"))
        lbl.pack(pady=(30, 15))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Cyan.Horizontal.TProgressbar", troughcolor='#333', background='#00ff9d', bordercolor="#1e1e1e", lightcolor="#00ff9d", darkcolor="#00ff9d")
        
        pb = ttk.Progressbar(frame, style="Cyan.Horizontal.TProgressbar", orient="horizontal", length=280, mode="indeterminate")
        pb.pack()
        pb.start(15)
        
        def check_stop():
            if not state["running"]:
                root.quit()
                root.destroy()
            else:
                root.after(100, check_stop)
        
        root.after(100, check_stop)
        root.mainloop()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    
    def stop_loading():
        state["running"] = False
        t.join()
    
    return stop_loading

# --- GUI : RESULTAT ---
def show_summary_popup(text, source_app):
    def run_gui():
        root = tk.Tk()
        root.title(f"Résumé IA - {source_app}")
        root.geometry("600x500")
        root.configure(bg="#1e1e1e")
        root.attributes("-topmost", True)
        
        lbl = tk.Label(root, text=f"Analyse : {source_app}", bg="#1e1e1e", fg="#00ff9d", font=("Arial", 14, "bold"))
        lbl.pack(pady=15)
        
        text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, bg="#252526", fg="#e0e0e0", bd=0, padx=15, pady=15, font=("Consolas", 11))
        text_area.pack(padx=20, pady=5, expand=True, fill='both')
        text_area.insert(tk.INSERT, text)
        text_area.configure(state='disabled')
        
        tk.Button(root, text="Fermer", command=root.destroy, bg="#007acc", fg="white", relief="flat", padx=20, pady=5).pack(pady=15)
        root.mainloop()
    threading.Thread(target=run_gui, daemon=True).start()

# --- ANALYSE ---
def analyze_for_buttons(process_name, image_part):
    if not model: return
    
    # 1. Démarrage du Loading Screen pour les BOUTONS
    stop_loading = show_loading_screen(process_name, mode="Configuration")
    print(f"[Boutons] Analyse de {process_name}...")
    
    prompt = f"""
    Contexte : App "{process_name}".
    Donne 4 actions rapides.
    IMPORTANT : Pour chaque action, choisis un EMOJI unique qui servira d'icône.
    JSON: [ {{"label": "Titre", "keys": "Raccourci", "icon": "Emoji"}} ]
    """
    
    try:
        for attempt in range(3):
            try:
                response = model.generate_content([prompt, image_part])
                text = response.text
                start, end = text.find('['), text.rfind(']') + 1
                if start != -1 and end != -1:
                    actions = json.loads(text[start:end])
                    for action in actions:
                        action['imageData'] = emoji_to_base64(action.get('icon', '🔹'))
                    
                    with open(ACTIONS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(actions, f, ensure_ascii=False, indent=2)
                    print("-> Boutons mis à jour.")
                    
                    # Succès : on arrête le loading et on sort de la boucle
                    stop_loading()
                    return
            except Exception as e:
                if "429" in str(e): time.sleep(5)
                else: print(f"Erreur: {e}"); break
                
    except Exception as e:
        print(f"Erreur Générale Boutons: {e}")
    finally:
        # Sécurité : on s'assure que le loading s'arrête quoi qu'il arrive
        stop_loading()

def analyze_for_summary(process_name, image_part):
    if not model: return
    
    # 1. Démarrage du Loading Screen pour le RÉSUMÉ
    stop_loading = show_loading_screen(process_name, mode="Lecture")
    print(f"[Résumé] Lecture de {process_name}...")
    
    try:
        # 2. Appel IA (Bloquant)
        response = model.generate_content(["Fais un résumé structuré et clair.", image_part])
        
        # 3. Arrêt du Loading Screen
        stop_loading()
        
        # 4. Affichage du résultat
        show_summary_popup(response.text, process_name)
        
    except Exception as e: 
        stop_loading() # Toujours arrêter le loading même en cas d'erreur
        print(f"Erreur Résumé: {e}")

# --- SURVEILLANCE ---
class ContextHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_trigger_time = 0
        self.cooldown = 2.0 

    def on_modified(self, event):
        is_context = os.path.normpath(event.src_path) == os.path.normpath(CONTEXT_FILE)
        is_summary = os.path.normpath(event.src_path) == os.path.normpath(SUMMARY_FILE)

        if is_context or is_summary:
            current_time = time.time()
            if current_time - self.last_trigger_time < self.cooldown:
                return
            self.last_trigger_time = current_time
            time.sleep(0.2) 
            
            if is_context: process_file(CONTEXT_FILE, "buttons")
            elif is_summary: process_file(SUMMARY_FILE, "summary")

def process_file(filepath, mode):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        proc = data.get('process', 'Unknown')
        img_b64 = data.get('screenshot_base64', '')
        if not img_b64: return

        img_bytes = base64.b64decode(img_b64)
        img_part = {"mime_type": "image/jpeg", "data": img_bytes}
        
        if mode == "buttons": analyze_for_buttons(proc, img_part)
        elif mode == "summary": analyze_for_summary(proc, img_part)
    except: pass

if __name__ == "__main__":
    if not model: exit()
    print(f"--- Cerveau IA v7 (Full Loading UI) ---")
    observer = Observer()
    observer.schedule(ContextHandler(), path=DESKTOP_DIR, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: observer.stop()
    observer.join()