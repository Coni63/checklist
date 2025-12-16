@echo off

setlocal

echo.
echo Running ruff
echo.

uv run ruff format .
uv run ruff check --fix .

echo.
echo Ruff run
echo.

echo.
echo Building requirements.txt
echo.

uv export --no-hashes --no-header --no-annotate --no-dev --format requirements.txt > requirements.txt

echo.
echo requirements.txt created
echo.

:: --- Copy file but currently django tailwind does it ---
exit 0

:: --- Configuration des chemins ---
set "SOURCE_DIR=checklistapp\theme\static\css"
set "DEST_DIR=checklistapp\static\css"

:: --- Vérification de l'existence du dossier source ---
if not exist "%SOURCE_DIR%" (
    echo Erreur : Le dossier source n'existe pas.
    echo Chemin attendu : "%SOURCE_DIR%"
    goto :eof
)

:: --- Création du dossier de destination si nécessaire ---
if not exist "%DEST_DIR%" (
    echo Le dossier de destination n'existe pas, creation...
    mkdir "%DEST_DIR%"
)

echo.
echo Tentative de fusion des fichiers de :
echo Source : "%SOURCE_DIR%"
echo Destination : "%DEST_DIR%"
echo.

:: --- La commande XCOPY ---
:: /E : Copie les répertoires et les sous-répertoires, y compris les répertoires vides.
:: /H : Copie également les fichiers cachés et les fichiers système.
:: /K : Conserve les attributs. Xcopy réinitialise habituellement les attributs en lecture seule.
:: /Y : Supprime l'invite pour confirmer l'écrasement d'un fichier de destination existant.
xcopy "%SOURCE_DIR%" "%DEST_DIR%" /E /H /K /Y

if %ERRORLEVEL% equ 0 (
    echo.
    echo --- Fusion terminee avec succes ---
) else (
    echo.
    echo --- Une erreur s'est produite lors de la copie (Code d'erreur : %ERRORLEVEL%) ---
)

endlocal
pause