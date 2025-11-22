@echo off
setlocal

:: ==========================================
:: CONFIGURATION DES CHEMINS
:: ==========================================

:: 1. Dossier racine (Là où est ce fichier .bat, normalement dans 'backend')
set "ROOT_DIR=%~dp0"

:: 2. Dossier Source CORRIGÉ
:: Le .csproj Loupedeck ne crée pas de dossier "net8.0-windows", mais un dossier "bin"
set "SOURCE=%ROOT_DIR%bin\Debug\bin"

:: 3. Dossier d'installation Loupedeck
set "DEST=%LocalAppData%\Loupedeck\Plugins\TutorialPlugin"

:: ==========================================
:: EXECUTION
:: ==========================================

echo.
echo [1/3] ARRET DE LOUPEDECK...
taskkill /F /IM Loupedeck.exe >nul 2>&1

echo.
echo [2/3] COPIE DES FICHIERS...
echo Source : %SOURCE%
echo Dest   : %DEST%

:: Vérification de sécurité
if not exist "%SOURCE%" (
    echo.
    echo [ERREUR] Le dossier source est introuvable !
    echo -------------------------------------------------------
    echo Chemin cherche : %SOURCE%
    echo -------------------------------------------------------
    echo CAUSE PROBABLE :
    echo 1. Tu n'as pas lance "dotnet build".
    echo 2. Ton fichier .bat n'est pas dans le dossier "backend".
    echo.
    echo Essaie de lancer "dotnet build" dans le terminal avant de reessayer.
    pause
    exit /b
)

:: Création du dossier de destination
if not exist "%DEST%" mkdir "%DEST%"

:: Copie des fichiers
xcopy "%SOURCE%\*" "%DEST%\" /E /Y /Q

echo.
echo [3/3] REDEMARRAGE DE LOUPEDECK...
if exist "C:\Program Files\Loupedeck\Loupedeck.exe" (
    start "" "C:\Program Files\Loupedeck\Loupedeck.exe"
) else if exist "C:\Program Files (x86)\Loupedeck\Loupedeck.exe" (
    start "" "C:\Program Files (x86)\Loupedeck\Loupedeck.exe"
) else (
    echo [AVIS] Loupedeck introuvable dans les chemins standards. Lance-le manuellement.
)

echo.
echo --- TERMINE ! ---
timeout /t 5