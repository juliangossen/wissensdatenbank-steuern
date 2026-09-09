@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
"Werkzeuge\Recherche\.venv\Scripts\python.exe" -B "Werkzeuge\Recherche\cloud\client.py" interactive
pause
