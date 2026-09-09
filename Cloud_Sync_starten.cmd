@echo off
py "%~dp0Werkzeuge\Cloud_Sync\gui.py"
if errorlevel 1 (
  echo Das Tool konnte nicht gestartet werden. Python 3 mit Tkinter muss installiert sein.
  pause
)
