using System;
using System.IO; // Nécessaire pour écrire dans le fichier
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public class TutorialPlugin : Plugin
    {
        // On suppose que la classe WindowWatcher est définie dans un autre fichier de ton projet
        private WindowWatcher _watcher;
        private System.Timers.Timer _appTimer;
        private string _lastDetectedApp = "";
        private string _logFilePath;

        public override void Load()
        {
            base.Load();

            // 1. On définit le chemin du fichier sur le Bureau
            string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
            this._logFilePath = Path.Combine(desktopPath, "log_loupedeck.txt");

            // Petit message pour dire qu'on commence
            try 
            {
                File.AppendAllText(this._logFilePath, $"--- Démarrage du Plugin : {DateTime.Now} ---\n");
            }
            catch (Exception ex)
            {
                PluginLog.Error($"Erreur d'écriture fichier: {ex.Message}");
            }

            // 2. On initialise le détecteur (qui existe déjà ailleurs)
            this._watcher = new WindowWatcher();

            // 3. On lance le timer (chaque seconde)
            this._appTimer = new System.Timers.Timer(1000);
            this._appTimer.Elapsed += this.OnAppCheck;
            this._appTimer.AutoReset = true;
            this._appTimer.Enabled = true;
        }

        public override void Unload()
        {
            if (this._appTimer != null)
            {
                this._appTimer.Stop();
                this._appTimer.Dispose();
            }
            base.Unload();
        }

        private void OnAppCheck(Object source, System.Timers.ElapsedEventArgs e)
        {
            // CORRECTION : On utilise le nom exact de la méthode définie dans ton WindowWatcher
            var currentApp = this._watcher.GetActiveProcessName(); 

            // Si le titre a changé, on l'écrit dans le fichier
            if (!string.IsNullOrEmpty(currentApp) && currentApp != this._lastDetectedApp)
            {
                this._lastDetectedApp = currentApp;
                
                try
                {
                    string logMessage = $"{DateTime.Now:HH:mm:ss} -> {currentApp}\n";
                    File.AppendAllText(this._logFilePath, logMessage);
                }
                catch
                {
                    // Ignorer les erreurs d'écriture si le fichier est verrouillé
                }
            }
        }
    }
}