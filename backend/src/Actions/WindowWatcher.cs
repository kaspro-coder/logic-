using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

namespace Loupedeck.TutorialPlugin
{
    public class WindowWatcher
    {
        // --- 1. IMPORTATION DES OUTILS WINDOWS (Win32 API) ---
        
        // Récupère l'identifiant unique (Handle) de la fenêtre active
        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        // Récupère l'ID du processus qui possède cette fenêtre
        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        // --- 2. LOGIQUE DE DÉTECTION ---

        public string GetActiveProcessName()
        {
            try
            {
                // A. On demande à Windows quelle fenêtre est au premier plan
                IntPtr hWnd = GetForegroundWindow();
                
                // Si aucune fenêtre n'est active (cas rare mais possible), on renvoie null
                if (hWnd == IntPtr.Zero) return null;

                // B. On récupère l'ID du processus (PID) lié à cette fenêtre
                GetWindowThreadProcessId(hWnd, out uint processId);

                // C. On récupère l'objet Processus C# grâce à l'ID
                Process proc = Process.GetProcessById((int)processId);

                // D. On retourne le nom (ex: "devenv" pour Visual Studio, "photoshop" pour Adobe)
                return proc.ProcessName;
            }
            catch (Exception)
            {
                // En cas d'erreur (ex: fenêtre système protégée), on ignore
                return null;
            }
        }
    }
}