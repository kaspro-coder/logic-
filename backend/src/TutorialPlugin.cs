using System;
using System.IO;
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public class TutorialPlugin : Plugin
    {
        // Configuration pour plugin universel
        public override bool HasNoApplication => true;
        public override bool UsesApplicationApiOnly => true;

        private WindowWatcher _watcher;
        private ContextManager _contextManager;
        private System.Timers.Timer _appTimer;
        
        private string _lastDetectedTitle = "";
        private string _jsonFilePath;

        public override void Load()
        {
            base.Load();

            string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
            this._jsonFilePath = Path.Combine(desktopPath, "loupedeck_context.json");

            this._watcher = new WindowWatcher();
            this._contextManager = new ContextManager();

            // Le timer continue de tourner pour garder le plugin "vivant", 
            // mais il ne fera plus d'actions lourdes (comme le screenshot)
            this._appTimer = new System.Timers.Timer(1000);
            this._appTimer.Elapsed += this.OnAppCheck;
            this._appTimer.AutoReset = true;
            this._appTimer.Enabled = true;

            PluginLog.Info("TutorialPlugin : Prêt (Mode Manuel uniquement).");
        }

        public override void Unload()
        {
            // No timer to dispose — WindowWatcher hook is released automatically
            base.Unload();
        }

        // Cette boucle tourne toutes les secondes mais ne fait plus rien de visible
        private void OnAppCheck(Object source, System.Timers.ElapsedEventArgs e)
        {
            var currentTitle = this._watcher.GetActiveWindowTitle();
            
            if (!string.IsNullOrEmpty(currentTitle) && currentTitle != this._lastDetectedTitle)
            {
                this._lastDetectedTitle = currentTitle;
                
                // --- MODIFICATION ICI ---
                // J'ai commenté la ligne ci-dessous. 
                // Le plugin ne prendra PLUS de screenshot automatiquement en changeant de fenêtre.
                
                // this.ForceCapture(); 
            }
        }

        // Cette fonction est maintenant appelée UNIQUEMENT quand tu appuies sur ton bouton "Scan Context"
        public void ForceCapture()
        {
            try
            {
                var currentProcess = this._watcher.GetActiveProcessName();
                var currentTitle = this._watcher.GetActiveWindowTitle();

                // On génère le JSON
                string jsonContent = this._contextManager.GetContextJson(currentProcess, currentTitle);
                
                // On écrit le fichier
                File.WriteAllText(this._jsonFilePath, jsonContent);
                
                // Petit log pour confirmer
                PluginLog.Info($"Scan manuel effectué : {currentTitle}");
            }
            catch (Exception ex)
            {
                PluginLog.Error($"Erreur Capture: {ex.Message}");
            }
        }
    }
}
