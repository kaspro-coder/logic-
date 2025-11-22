using System;
using System.IO;
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public class TutorialPlugin : Plugin
    {
        private WindowWatcher _watcher;
        private string _lastDetectedApp = "";
        private string _logFilePath;

        public override void Load()
        {
            base.Load();

            // Path to the log file on desktop
            string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
            _logFilePath = Path.Combine(desktopPath, "log_loupedeck.txt");

            try
            {
                File.AppendAllText(_logFilePath, $"--- Plugin started: {DateTime.Now} ---\n");
            }
            catch (Exception ex)
            {
                PluginLog.Error($"File write error: {ex.Message}");
            }

            // Initialize the event-based watcher
            _watcher = new WindowWatcher();

            // Subscribe to instant window change notifications
            _watcher.OnActiveApplicationChanged += this.OnAppChanged;
        }

        public override void Unload()
        {
            // No timer to dispose — WindowWatcher hook is released automatically
            base.Unload();
        }

        private void OnAppChanged(string currentApp)
        {
            // Avoid duplicates
            if (string.IsNullOrEmpty(currentApp) || currentApp == _lastDetectedApp)
                return;

            _lastDetectedApp = currentApp;

            try
            {
                string logMessage = $"{DateTime.Now:HH:mm:ss} -> {currentApp}\n";
                File.AppendAllText(_logFilePath, logMessage);
            }
            catch 
            {
                // swallow write errors if log is locked
            }
        }
    }
}
