@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist "Werkzeuge\Recherche\.venv\Scripts\python.exe" (
  echo Bitte zuerst die Einrichtung in Werkzeuge\Recherche\README.md ausfuehren.
  pause
  exit /b 1
)
"Werkzeuge\Recherche\.venv\Scripts\python.exe" -B "Werkzeuge\Recherche\cloud\connect_project.py"
pause
