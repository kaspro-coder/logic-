using System;
using Loupedeck;

namespace Loupedeck.TutorialPlugin
{
    public class SummarizeCommand : PluginDynamicCommand
    {
        public SummarizeCommand() 
            : base("Résumé IA", "Résume le texte à l'écran (Mail, Slack, etc.)", "IA Tools")
        {
        }

        protected override void RunCommand(string actionParameter)
        {
            var plugin = (TutorialPlugin)this.Plugin;
            if (plugin != null)
            {
                // Appelle la nouvelle méthode dédiée au résumé
                plugin.ForceSummary(); 
            }
        }
    }
}