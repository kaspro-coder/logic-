using System;
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public class CaptureCommand : PluginDynamicCommand
    {
        // Constructeur : Définit le nom et la catégorie du bouton dans l'interface Loupedeck
        public CaptureCommand() 
            : base("Forcer Analyse IA", "Prend un screenshot et analyse le contexte immédiatement", "IA Tools")
        {
        }

        // Cette méthode se lance quand tu appuies sur le bouton
        protected override void RunCommand(string actionParameter)
        {
            // On récupère l'instance principale de ton plugin
            var plugin = (TutorialPlugin)this.Plugin;

            if (plugin != null)
            {
                // On appelle la méthode qu'on vient de créer
                plugin.ForceCapture();
            }
        }

        // (Optionnel) Permet d'afficher un texte dynamique sur le bouton si besoin
        protected override string GetCommandDisplayName(string actionParameter, PluginImageSize imageSize)
        {
            return "Scan Context";
        }
    }
}