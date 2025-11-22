using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

namespace Loupedeck.TutorialPlugin
{
    public class WindowWatcher
    {
        private const uint EVENT_SYSTEM_FOREGROUND = 0x0003;
        private const uint WINEVENT_OUTOFCONTEXT = 0;

        private delegate void WinEventDelegate(
            IntPtr hWinEventHook, uint eventType, IntPtr hwnd,
            int idObject, int idChild, uint dwEventThread, uint dwmsEventTime);

        private WinEventDelegate _procDelegate;
        private IntPtr _hook;

        public event Action<string> OnActiveApplicationChanged;

        public WindowWatcher()
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
                var process = Process.GetProcessById((int)pid);
                OnActiveApplicationChanged?.Invoke(process.ProcessName);
            }
            catch { }
        }

        #region WinAPI

        [DllImport("user32.dll")]
        private static extern IntPtr SetWinEventHook(
            uint eventMin, uint eventMax, IntPtr hmodWinEventProc,
            WinEventDelegate lpfnWinEventProc, uint idProcess,
            uint idThread, uint dwFlags);

        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(
            IntPtr hWnd, out uint processId);

        #endregion
    }
}
