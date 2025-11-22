using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

namespace Loupedeck.TutorialPlugin
{
    public class WindowWatcher
    {
        // --- IMPORTATIONS WINDOWS (User32) ---
        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        // AJOUT : Pour lire le titre de la fenêtre
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        // --- MÉTHODES ---

        // Méthode 1 : Récupère le nom du processus (ex: "chrome")
        public string GetActiveProcessName()
        {
            _procDelegate = new WinEventDelegate(WinEventCallback);

            _hook = SetWinEventHook(
                EVENT_SYSTEM_FOREGROUND,
                EVENT_SYSTEM_FOREGROUND,
                IntPtr.Zero,
                _procDelegate,
                0,
                0,
                WINEVENT_OUTOFCONTEXT
            );
        }

        private void WinEventCallback(
            IntPtr hWinEventHook, uint eventType, IntPtr hwnd,
            int idObject, int idChild, uint dwEventThread, uint dwmsEventTime)
        {
            if (hwnd == IntPtr.Zero) return;

            // Retrieve process name
            uint pid;
            GetWindowThreadProcessId(hwnd, out pid);

            try
            {
                IntPtr hWnd = GetForegroundWindow();
                if (hWnd == IntPtr.Zero) return null;

                GetWindowThreadProcessId(hWnd, out uint processId);
                Process proc = Process.GetProcessById((int)processId);
                return proc.ProcessName;
            }
            catch
            {
                return null;
            }
            catch { }
        }

        // Méthode 2 : Récupère le titre de la fenêtre (ex: "Boîte de réception - Gmail")
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
