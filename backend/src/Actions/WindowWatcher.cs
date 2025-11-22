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

        // MANQUANT : Permet de lire le titre de la fenêtre (Ex: "Google - Chrome")
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        // --- 2. LOGIQUE DE DÉTECTION ---

        // Méthode A : Récupère le nom du processus (Ex: "chrome")
        public string GetActiveProcessName()
        {
            try
            {
                IntPtr hWnd = GetForegroundWindow();
                
                if (hWnd == IntPtr.Zero) return null;

                GetWindowThreadProcessId(hWnd, out uint processId);

                Process proc = Process.GetProcessById((int)processId);

                return proc.ProcessName;
            }
            catch (Exception)
            {
                return null;
            }
        }

        // Méthode B : Récupère le titre complet (Ex: "Mon Document - Word")
        // C'est celle-ci qui manquait et causait l'erreur CS1061
        public string GetActiveWindowTitle()
        {
            const int nChars = 256;
            StringBuilder Buff = new StringBuilder(nChars);
            IntPtr handle = GetForegroundWindow();

            if (GetWindowText(handle, Buff, nChars) > 0)
            {
                return Buff.ToString();
            }
            return null;
        }
    }
}