using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;
using System.Text.Json;
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    // --- CLASSE DE BASE (CERVEAU COMMUN) ---
    public abstract class AIActionBase : PluginDynamicCommand
    {
        // Données partagées entre les 4 boutons (Static = Unique pour tous)
        protected static List<AIActionItem> SharedActions = new List<AIActionItem>();
        
        // Le surveillant de fichier (Static pour qu'il n'y en ait qu'un seul)
        private static FileSystemWatcher _sharedWatcher;
        private static System.Timers.Timer _sharedTimer;
        private static DateTime _lastReadTime = DateTime.MinValue;
        private static string _actionsFilePath;

        // Événement "Radio" pour prévenir tous les boutons qu'il faut changer l'image
        public static event EventHandler OnListUpdated;

        protected int TargetIndex; // L'index spécifique de ce bouton (0, 1, 2 ou 3)

        public AIActionBase(string id, string name, int index) : base(id, name, "IA Tools")
        {
            TargetIndex = index;
            // On s'abonne au signal : quand la liste change, on met à jour ce bouton
            OnListUpdated += (sender, e) => this.ActionImageChanged();
        }

        protected override bool OnLoad()
        {
            // Le premier bouton qui se charge initialise la surveillance pour tout le monde
            if (_sharedWatcher == null)
            {
                SetupSharedWatcher();
            }
            return base.OnLoad();
        }

        private void SetupSharedWatcher()
        {
            string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
            string oneDrivePath = Path.Combine(Environment.GetEnvironmentVariable("USERPROFILE"), "OneDrive", "Desktop");
            // On privilégie OneDrive s'il existe
            string targetDir = Directory.Exists(oneDrivePath) ? oneDrivePath : desktopPath;

            _actionsFilePath = Path.Combine(targetDir, "loupedeck_actions.json");

            // Lecture immédiate au démarrage
            CheckFileUpdate(true);

            try
            {
                if (Directory.Exists(targetDir))
                {
                    _sharedWatcher = new FileSystemWatcher(targetDir, "loupedeck_actions.json");
                    _sharedWatcher.NotifyFilter = NotifyFilters.LastWrite;
                    _sharedWatcher.Changed += (s, e) => CheckFileUpdate();
                    _sharedWatcher.EnableRaisingEvents = true;
                }
                
                // Timer de sécurité (vérifie toutes les 1s au cas où le Watcher rate un truc)
                _sharedTimer = new System.Timers.Timer(1000);
                _sharedTimer.Elapsed += (s, e) => CheckFileUpdate();
                _sharedTimer.Start();
            }
            catch { }
        }

        private void CheckFileUpdate(bool force = false)
        {
            if (!File.Exists(_actionsFilePath)) return;
            try
            {
                DateTime lastWrite = File.GetLastWriteTimeUtc(_actionsFilePath);
                // On ne relit que si le fichier est plus récent
                if (force || lastWrite > _lastReadTime)
                {
                    _lastReadTime = lastWrite;
                    ReadActions();
                }
            }
            catch { }
        }

        private void ReadActions()
        {
            // On essaie 3 fois au cas où le fichier est verrouillé par Python
            for (int i = 0; i < 3; i++)
            {
                try
                {
                    string jsonContent = File.ReadAllText(_actionsFilePath);
                    if (!string.IsNullOrWhiteSpace(jsonContent))
                    {
                        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                        var newActions = JsonSerializer.Deserialize<List<AIActionItem>>(jsonContent, options);

                        if (newActions != null)
                        {
                            SharedActions = newActions;
                            
                            // CORRECTION : On déclenche l'événement statique "Radio"
                            // Tous les boutons (AIAction1, 2, 3, 4) vont recevoir ce signal
                            OnListUpdated?.Invoke(null, EventArgs.Empty);
                        }
                        return;
                    }
                }
                catch (IOException) { System.Threading.Thread.Sleep(50); }
                catch { break; }
            }
        }

        protected override string GetCommandDisplayName(string actionParameter, PluginImageSize imageSize)
        {
            // Si on a une action pour cet index précis dans la liste partagée
            if (TargetIndex < SharedActions.Count)
            {
                return SharedActions[TargetIndex].Label;
            }
            return ""; // Sinon on affiche rien (plus propre)
        }

        protected override void RunCommand(string actionParameter)
        {
            if (TargetIndex < SharedActions.Count)
            {
                string keys = SharedActions[TargetIndex].Keys;
                if (!string.IsNullOrEmpty(keys))
                {
                    try { SendKeys.SendWait(keys); } catch { }
                }
            }
        }
    }

    // --- LES 4 BOUTONS DISTINCTS (Ceux que vous verrez dans la liste Loupedeck) ---
    
    public class AIAction1 : AIActionBase
    {
        public AIAction1() : base("AI_BTN_1", "1. Action IA (Haut G)", 0) { }
    }

    public class AIAction2 : AIActionBase
    {
        public AIAction2() : base("AI_BTN_2", "2. Action IA (Haut D)", 1) { }
    }

    public class AIAction3 : AIActionBase
    {
        public AIAction3() : base("AI_BTN_3", "3. Action IA (Bas G)", 2) { }
    }

    public class AIAction4 : AIActionBase
    {
        public AIAction4() : base("AI_BTN_4", "4. Action IA (Bas D)", 3) { }
    }

    // Classe de données pour le JSON
    public class AIActionItem
    {
        public string Label { get; set; } = "";
        public string Keys { get; set; } = "";
    }
}