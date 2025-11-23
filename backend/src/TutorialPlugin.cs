using System;
using System.IO;
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public class TutorialPlugin : Plugin
    {
        public override bool HasNoApplication => true;
        public override bool UsesApplicationApiOnly => true;

        private WindowWatcher _watcher;
        private ContextManager _contextManager;
        
        // Deux fichiers de sortie différents
        private string _contextFilePath; // Pour les boutons
        private string _summaryFilePath; // Pour le résumé

        public override void Load()
        {
            base.Load();
            string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
            
            // Essai OneDrive
            string oneDrive = Path.Combine(Environment.GetEnvironmentVariable("USERPROFILE"), "OneDrive", "Desktop");
            if (Directory.Exists(oneDrive)) desktopPath = oneDrive;

            this._contextFilePath = Path.Combine(desktopPath, "loupedeck_context.json");
            this._summaryFilePath = Path.Combine(desktopPath, "loupedeck_summary.json");

            this._watcher = new WindowWatcher();
            this._contextManager = new ContextManager();
        }

        public override void Unload()
        {
            base.Unload();
        }

        // Méthode pour les boutons (Mise à jour des actions)
        public void ForceCapture()
        {
            CaptureAndSave(this._contextFilePath);
        }

        // Méthode pour le résumé (Nouveau)
        public void ForceSummary()
        {
            CaptureAndSave(this._summaryFilePath);
        }

        private void CaptureAndSave(string filePath)
        {
            try
            {
                var currentProcess = this._watcher.GetActiveProcessName();
                var currentTitle = this._watcher.GetActiveWindowTitle();
                string jsonContent = this._contextManager.GetContextJson(currentProcess, currentTitle);
                
                File.WriteAllText(filePath, jsonContent);
            }
            catch (Exception ex)
            {
                PluginLog.Error($"Erreur Capture: {ex.Message}");
            }
        }
    }
}