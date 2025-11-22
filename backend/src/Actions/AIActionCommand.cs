using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;
using System.Text.Json;
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public class AIActionCommand : PluginDynamicCommand
    {
        // CHANGEMENT D'ID : "AI_Magic_V1" pour forcer l'apparition du dossier
        public AIActionCommand() 
            : base("AI_Magic_V1", "Commandes IA", "IA Tools")
        {
            // On définit les 4 boutons ici. C'est la méthode compatible SDK 5.x
            // Le 3ème argument "Groupe" crée le dossier dans l'interface
            this.AddParameter("0", "1. Haut Gauche", "Choisir Position");
            this.AddParameter("1", "2. Haut Droite", "Choisir Position");
            this.AddParameter("2", "3. Bas Gauche", "Choisir Position");
            this.AddParameter("3", "4. Bas Droite", "Choisir Position");
        }

        private string _actionsFilePath;
        private List<AIActionItem> _currentActions = new List<AIActionItem>();
        private FileSystemWatcher _watcher;
        private System.Timers.Timer _safetyTimer;
        private DateTime _lastReadTime = DateTime.MinValue;

        protected override bool OnLoad()
        {
            string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
            string oneDrivePath = Path.Combine(Environment.GetEnvironmentVariable("USERPROFILE"), "OneDrive", "Desktop");
            string targetDir = Directory.Exists(oneDrivePath) ? oneDrivePath : desktopPath;

            _actionsFilePath = Path.Combine(targetDir, "loupedeck_actions.json");

            CheckFileUpdate(true);
            
            try {
                if (Directory.Exists(targetDir)) {
                    _watcher = new FileSystemWatcher(targetDir, "loupedeck_actions.json");
                    _watcher.NotifyFilter = NotifyFilters.LastWrite;
                    _watcher.Changed += (s, e) => CheckFileUpdate();
                    _watcher.EnableRaisingEvents = true;
                }
                _safetyTimer = new System.Timers.Timer(1000);
                _safetyTimer.Elapsed += (s, e) => CheckFileUpdate();
                _safetyTimer.Start();
            } catch {}
            
            return base.OnLoad();
        }

        protected override bool OnUnload()
        {
            _watcher?.Dispose();
            _safetyTimer?.Stop();
            return base.OnUnload();
        }

        private void CheckFileUpdate(bool force = false)
        {
            if (!File.Exists(_actionsFilePath)) return;
            try {
                DateTime lastWrite = File.GetLastWriteTimeUtc(_actionsFilePath);
                if (force || lastWrite > _lastReadTime) {
                    _lastReadTime = lastWrite;
                    ReadActions();
                }
            } catch { }
        }

        private void ReadActions()
        {
            for (int i = 0; i < 3; i++) {
                try {
                    string jsonContent = File.ReadAllText(_actionsFilePath);
                    if (!string.IsNullOrWhiteSpace(jsonContent)) {
                        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                        var newActions = JsonSerializer.Deserialize<List<AIActionItem>>(jsonContent, options);
                        if (newActions != null) {
                            _currentActions = newActions;
                            this.ActionImageChanged();
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
            if (int.TryParse(actionParameter, out int index))
            {
                if (index >= 0 && index < _currentActions.Count)
                {
                    return _currentActions[index].Label;
                }
            }
            // Si l'action n'est pas chargée, on affiche son numéro pour aider
            return $"IA #{int.Parse(actionParameter) + 1}"; 
        }

        protected override void RunCommand(string actionParameter)
        {
            if (int.TryParse(actionParameter, out int index))
            {
                if (index >= 0 && index < _currentActions.Count)
                {
                    string keys = _currentActions[index].Keys;
                    if (!string.IsNullOrEmpty(keys))
                    {
                        try { SendKeys.SendWait(keys); } catch {}
                    }
                }
            }
        }

        public class AIActionItem 
        { 
            public string Label { get; set; } = ""; 
            public string Keys { get; set; } = ""; 
        }
    }
}