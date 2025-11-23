using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;
using System.Text.Json;
using System.Text;
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public abstract class AIActionBase : PluginDynamicCommand
    {
        private static readonly object _lock = new object();
        protected static List<AIActionItem> SharedActions = new List<AIActionItem>();
        private static FileSystemWatcher _sharedWatcher;
        private static string _actionsFilePath;

        public static event EventHandler OnListUpdated;
        protected int MyIndex;

        public AIActionBase(string id, string name, int index) : base(id, name, "IA Tools")
        {
            this.MyIndex = index;
            OnListUpdated += (sender, e) => this.ActionImageChanged();
        }

        protected override bool OnLoad()
        {
            if (_sharedWatcher == null) SetupSharedWatcher();
            return base.OnLoad();
        }

        private void SetupSharedWatcher()
        {
            string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
            string oneDrivePath = Path.Combine(Environment.GetEnvironmentVariable("USERPROFILE"), "OneDrive", "Desktop");
            string targetDir = Directory.Exists(oneDrivePath) ? oneDrivePath : desktopPath;
            _actionsFilePath = Path.Combine(targetDir, "loupedeck_actions.json");
            
            try {
                if (Directory.Exists(targetDir)) {
                    _sharedWatcher = new FileSystemWatcher(targetDir, "loupedeck_actions.json");
                    _sharedWatcher.NotifyFilter = NotifyFilters.LastWrite;
                    _sharedWatcher.Changed += (s, e) => ReadActions();
                    _sharedWatcher.EnableRaisingEvents = true;
                }
                ReadActions(); 
            } catch { }
        }

        private void ReadActions()
        {
            System.Threading.Thread.Sleep(100);
            try {
                if (File.Exists(_actionsFilePath)) {
                    string jsonContent = File.ReadAllText(_actionsFilePath, Encoding.UTF8);
                    var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                    var newActions = JsonSerializer.Deserialize<List<AIActionItem>>(jsonContent, options);
                    if (newActions != null) {
                        lock (_lock) SharedActions = newActions;
                        OnListUpdated?.Invoke(null, EventArgs.Empty);
                    }
                }
            } catch { }
        }

        protected override BitmapImage GetCommandImage(string actionParameter, PluginImageSize imageSize)
        {
            AIActionItem action = null;
            lock (_lock) {
                if (MyIndex < SharedActions.Count) action = SharedActions[MyIndex];
            }

            // On utilise un seul bloc 'using' pour garantir qu'on retourne toujours une image
            using (var bitmap = new BitmapBuilder(imageSize))
            {
                bitmap.Clear(BitmapColor.Black);

                if (action != null)
                {
                    // 1. L'IMAGE (Emoji)
                    if (!string.IsNullOrEmpty(action.ImageData))
                    {
                        try {
                            var base64Data = action.ImageData.Replace("data:image/jpeg;base64,", "");
                            byte[] bytes = Convert.FromBase64String(base64Data);
                            var img = BitmapImage.FromArray(bytes);
                            // Image remontée (-12) pour laisser de la place au texte
                            bitmap.DrawImage(img, 20, -5); 
                        } catch { }
                    }

                    // 2. LE TEXTE (Label)
                    int fontSize = 15;
                    int textHeight = 35;
                    
                    // Position en bas
                    int yPos = bitmap.Height - textHeight; 
                    int width = bitmap.Width;

                    bitmap.DrawText(action.Label, 0, yPos, width, textHeight, new BitmapColor(255, 255, 255), fontSize);
                }
                else
                {
                    // Cas bouton vide : un simple point gris
                    bitmap.DrawText(".", new BitmapColor(50, 50, 50), 20);
                }

                return bitmap.ToImage();
            }
        }

        // --- CORRECTION ICI : On renvoie un ESPACE pour écraser le texte par défaut ---
        protected override string GetCommandDisplayName(string actionParameter, PluginImageSize imageSize)
        {
            return " "; 
        }

        protected override void RunCommand(string actionParameter)
        {
            string keys = null;
            lock (_lock) { if (MyIndex < SharedActions.Count) keys = SharedActions[MyIndex].Keys; }
            if (!string.IsNullOrEmpty(keys)) { try { SendKeys.SendWait(keys); } catch { } }
        }
    }

    // --- LES 4 BOUTONS ---
    public class AIAction1 : AIActionBase { public AIAction1() : base("AI_BTN_01", "1. Action IA", 0) { } }
    public class AIAction2 : AIActionBase { public AIAction2() : base("AI_BTN_02", "2. Action IA", 1) { } }
    public class AIAction3 : AIActionBase { public AIAction3() : base("AI_BTN_03", "3. Action IA", 2) { } }
    public class AIAction4 : AIActionBase { public AIAction4() : base("AI_BTN_04", "4. Action IA", 3) { } }

    public class AIActionItem
    {
        public string Label { get; set; } = "";
        public string Keys { get; set; } = "";
        public string ImageData { get; set; } = "";
    }
}