using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;
using System.Text.Json;
using System.Text;
using System.Diagnostics; // Pour Process
using System.Runtime.InteropServices; // Pour les API Windows
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public abstract class AIActionBase : PluginDynamicCommand
    {
        // --- IMPORT API WINDOWS POUR LE FOCUS ---
        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        private static readonly object _lock = new object();
        
        // On change la structure stockée pour inclure le nom du process
        protected static AIActionRoot SharedData = new AIActionRoot();
        
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
                    
                    // On désérialise maintenant l'objet racine
                    var root = JsonSerializer.Deserialize<AIActionRoot>(jsonContent, options);
                    
                    if (root != null && root.Items != null) {
                        lock (_lock) SharedData = root;
                        OnListUpdated?.Invoke(null, EventArgs.Empty);
                    }
                }
            } catch { }
        }

        protected override BitmapImage GetCommandImage(string actionParameter, PluginImageSize imageSize)
        {
            AIActionItem action = null;
            lock (_lock) {
                if (SharedData.Items != null && MyIndex < SharedData.Items.Count) 
                    action = SharedData.Items[MyIndex];
            }

            using (var bitmap = new BitmapBuilder(imageSize))
            {
                bitmap.Clear(BitmapColor.Black);

                if (action != null)
                {
                    if (!string.IsNullOrEmpty(action.ImageData))
                    {
                        try {
                            var base64Data = action.ImageData.Replace("data:image/jpeg;base64,", "");
                            byte[] bytes = Convert.FromBase64String(base64Data);
                            var img = BitmapImage.FromArray(bytes);
                            bitmap.DrawImage(img, 0, -12); 
                        } catch { }
                    }

                    int fontSize = 15;
                    int textHeight = 30;
                    int yPos = bitmap.Height - textHeight; 
                    int width = bitmap.Width;

                    bitmap.DrawText(action.Label, 0, yPos, width, textHeight, new BitmapColor(255, 255, 255), fontSize);
                }
                else
                {
                    bitmap.DrawText(".", new BitmapColor(50, 50, 50), 20);
                }

                return bitmap.ToImage();
            }
        }

        protected override string GetCommandDisplayName(string actionParameter, PluginImageSize imageSize)
        {
            return " "; 
        }

        protected override void RunCommand(string actionParameter)
        {
            string keys = null;
            string targetProcess = "";

            lock (_lock) { 
                if (SharedData.Items != null && MyIndex < SharedData.Items.Count) {
                    keys = SharedData.Items[MyIndex].Keys;
                    targetProcess = SharedData.TargetProcess;
                }
            }

            if (!string.IsNullOrEmpty(keys))
            {
                // 1. On essaie de remettre le focus sur l'application cible
                if (!string.IsNullOrEmpty(targetProcess))
                {
                    FocusApplication(targetProcess);
                }

                // 2. On envoie les touches
                try { SendKeys.SendWait(keys); } catch { }
            }
        }

        // --- NOUVELLE FONCTION : FOCUS FENETRE ---
        private void FocusApplication(string processName)
        {
            try
            {
                // On enlève le .exe si présent
                processName = processName.Replace(".exe", "");
                
                Process[] processes = Process.GetProcessesByName(processName);
                if (processes.Length > 0)
                {
                    // On prend le premier processus trouvé qui a une fenêtre
                    foreach (var p in processes)
                    {
                        if (p.MainWindowHandle != IntPtr.Zero)
                        {
                            SetForegroundWindow(p.MainWindowHandle);
                            
                            // Petite pause pour laisser le temps à Windows de changer le focus
                            System.Threading.Thread.Sleep(100); 
                            return;
                        }
                    }
                }
            }
            catch { }
        }
    }

    // --- CLASSES SUPPORT ---

    public class AIAction1 : AIActionBase { public AIAction1() : base("AI_BTN_01", "1. Action IA", 0) { } }
    public class AIAction2 : AIActionBase { public AIAction2() : base("AI_BTN_02", "2. Action IA", 1) { } }
    public class AIAction3 : AIActionBase { public AIAction3() : base("AI_BTN_03", "3. Action IA", 2) { } }
    public class AIAction4 : AIActionBase { public AIAction4() : base("AI_BTN_04", "4. Action IA", 3) { } }

    // Nouvelle structure JSON
    public class AIActionRoot
    {
        public string TargetProcess { get; set; } = "";
        public List<AIActionItem> Items { get; set; } = new List<AIActionItem>();
    }

    public class AIActionItem
    {
        public string Label { get; set; } = "";
        public string Keys { get; set; } = "";
        public string ImageData { get; set; } = "";
    }
}