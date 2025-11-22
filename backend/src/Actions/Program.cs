using System;
using System.Timers; // Attention d'utiliser System.Timers
using Loupedeck.TutorialPlugin;

class Program
{
    // Variable pour se souvenir de la dernière app (pour ne pas spammer l'IA)
    private static string _lastDetectedApp = "";
    private static WindowWatcher _watcher = new WindowWatcher();

    static void Main(string[] args)
    {
        Console.WriteLine("--- Démarrage du détecteur d'App ---");

        // 1. Créer un Timer qui tourne toutes les 1 seconde (1000ms)
        Timer timer = new Timer(1000);
        
        // 2. Ce qui se passe à chaque "Tick" du timer
        timer.Elapsed += OnTimedEvent;
        
        // 3. Lancer le timer
        timer.AutoReset = true;
        timer.Enabled = true;

        // Empêcher la console de se fermer
        Console.ReadLine(); 
    }

    private static void OnTimedEvent(Object source, ElapsedEventArgs e)
    {
        // 1. Quel est le processus actuel ?
        string currentApp = _watcher.GetActiveProcessName();

        // 2. Est-ce qu'il est valide et est-ce qu'il a changé ?
        if (!string.IsNullOrEmpty(currentApp) && currentApp != _lastDetectedApp)
        {
            // C'est ici que la magie opère !
            _lastDetectedApp = currentApp;
            
            Console.WriteLine($"CHANGEMENT DÉTECTÉ : Vous êtes maintenant sur [{currentApp}]");

            // TODO : C'est ICI que tu appelles ta fonction qui contacte l'IA ou charge le profil
            // Exemple : UpdateLogitechProfile(currentApp);
        }
    }
}