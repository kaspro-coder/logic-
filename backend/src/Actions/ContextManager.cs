using System;
using System.Drawing; // Pour Bitmap et Graphics
using System.Drawing.Imaging; // Pour sauvegarder en JPEG/PNG
using System.IO;
using System.Runtime.InteropServices; // Pour User32.dll
using System.Text;
using System.Windows.Automation; // Pour lire l'URL de Chrome (Nécessite la réf UIAutomationClient)

namespace Loupedeck.TutorialPlugin
{
    public class ContextManager
    {
        // --- IMPORTATIONS WINDOWS (User32) ---
        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        [StructLayout(LayoutKind.Sequential)]
        public struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }

        // --- FONCTION PRINCIPALE ---
        public string GetContextJson(string processName, string windowTitle)
        {
            IntPtr handle = GetForegroundWindow();
            
            // 1. Récupérer l'URL (si c'est un navigateur)
            string url = "N/A";
            if (processName.ToLower().Contains("chrome") || processName.ToLower().Contains("edge"))
            {
                url = GetBrowserUrl(handle);
            }

            // 2. Prendre le screenshot en Base64
            string base64Image = CaptureWindowToBase64(handle);

            // 3. Construire le JSON manuellement (pour éviter les dépendances externes comme Newtonsoft)
            // Attention : On échappe les guillemets avec \
            string json = $@"
            {{
                ""timestamp"": ""{DateTime.Now:yyyy-MM-ddTHH:mm:ss}"",
                ""process"": ""{EscapeJson(processName)}"",
                ""title"": ""{EscapeJson(windowTitle)}"",
                ""url"": ""{EscapeJson(url)}"",
                ""screenshot_base64"": ""{base64Image}""
            }}";

            return json;
        }

        // --- LOGIQUE SCREENSHOT ---
        private string CaptureWindowToBase64(IntPtr handle)
        {
            try
            {
                if (GetWindowRect(handle, out RECT rect))
                {
                    int width = rect.Right - rect.Left;
                    int height = rect.Bottom - rect.Top;

                    if (width <= 0 || height <= 0) return null;

                    using (Bitmap bmp = new Bitmap(width, height, PixelFormat.Format32bppArgb))
                    {
                        using (Graphics g = Graphics.FromImage(bmp))
                        {
                            // Copie ce qu'il y a à l'écran à l'endroit de la fenêtre
                            g.CopyFromScreen(rect.Left, rect.Top, 0, 0, bmp.Size, CopyPixelOperation.SourceCopy);
                        }

                        // Conversion en Base64 (Format léger JPEG pour pas faire exploser le JSON)
                        using (MemoryStream ms = new MemoryStream())
                        {
                            bmp.Save(ms, ImageFormat.Jpeg); // JPEG est plus léger que PNG pour le JSON
                            byte[] imageBytes = ms.ToArray();
                            return Convert.ToBase64String(imageBytes);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                return "Erreur Capture: " + ex.Message;
            }
            return null;
        }

        // --- LOGIQUE URL (UI AUTOMATION) ---
        // C'est une méthode un peu "hacky" car les navigateurs cachent bien leur URL
        private string GetBrowserUrl(IntPtr handle)
        {
            try
            {
                if (handle == IntPtr.Zero) return null;

                AutomationElement element = AutomationElement.FromHandle(handle);
                if (element == null) return null;

                // On cherche la barre d'édition (l'URL bar)
                // Note: C'est gourmand en ressources, à utiliser avec parcimonie
                Condition condition = new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Edit);
                AutomationElement editBox = element.FindFirst(TreeScope.Descendants, condition);

                if (editBox != null)
                {
                    // On essaie de récupérer la valeur (l'URL)
                    object valuePatternObj;
                    if (editBox.TryGetCurrentPattern(ValuePattern.Pattern, out valuePatternObj))
                    {
                        return ((ValuePattern)valuePatternObj).Current.Value;
                    }
                }
            }
            catch
            {
                // L'accès à l'UI Automation peut échouer pour plein de raisons (droits, etc.)
                return "Erreur lecture URL";
            }
            return "URL non trouvée";
        }

        // Petit utilitaire pour éviter de casser le JSON si le titre contient des guillemets
        private string EscapeJson(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"");
        }
    }
}
