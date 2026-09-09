"""Archivierten Volltext reproduzieren: py Pruefung/konvertieren.py"""
from pathlib import Path
import sys
from konverter_snapshot import Converter
sys.stdout.reconfigure(encoding="utf-8")
Converter(Path(__file__).resolve().parent/"konfiguration.json").run()
