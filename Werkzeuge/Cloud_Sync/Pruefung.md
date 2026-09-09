# Prüfung der Cloud-Übergabe

Geprüft am 09.09.2026 unter Windows mit Python 3.14.3 und Tkinter 8.6.

- **Erweiterter Bestand mit UStAE:** 22 Dokumente (21 PDF-Dokumente mit 2.031 Seiten und 1 Webkopie), 455 Exportdateien, 146.292.771 Bytes erfolgreich mit der Kommandozeilenprüfung geprüft. Quellenstand und Einschränkungen der Webkopie bleiben im Bestand und Export erhalten.
- **Vollständiger lokaler Testexport mit UStAE:** alle 455 Dateien erfolgreich in einem kontrollierten temporären Ordner bereitgestellt. UStAE-Originaltext und Markdown stimmen bytegenau mit den lokalen Quellen überein; der Prüfnachweis ist enthalten. Die neu im Hauptordner abgelegte, noch unbearbeitete `AEAO.txt` wurde korrekt ausgeschlossen. Erneute Bereitstellung verwendete dieselbe Fassung und kopierte 0 Dateien. Der Quellbestand blieb unverändert; der nach Lage und Namenspräfix geprüfte temporäre Zielordner wurde anschließend entfernt. Inhaltskennung: `341394e4094f0b27c93f8e7c58053fa07a2a61c98a2479628b389dd05b821b50`.
- **Ursprünglicher PDF-Bestand:** Vor der UStAE-Erweiterung wurden 21 Dokumente, 392 Exportdateien, 107.172.444 Bytes erfolgreich gegen Bestand, Archivregister und vorhandene Prüfnachweise geprüft.
- **Vollständiger lokaler Testexport des ursprünglichen PDF-Bestands:** in einem separaten temporären Ordner erstellt; anschließend wieder entfernt. 323 lokale Verknüpfungen aus gerendertem Markdown einschließlich HTML-Verweisen zeigen auf vorhandene Ziele.
- **Wiederholung:** derselbe Fassungspfad, 0 erneut kopierte Dateien, korrekte Referenz in `AKTUELL.json`.
- **Integrität nach Erweiterung um Webkopien:** 14 automatisierte Tests bestanden. Erfasst sind unter anderem widersprüchliche Register und Prüfsummen, fehlende Prüfbelege, abgebrochene Übertragungen, Wiederaufnahme, Erhalt früherer Fassungen, veränderte Zieldateien, unzulässige Zielpfade und Ausschluss unbearbeiteter Eingänge. Der gemischte PDF/TXT-Testbestand wird vollständig exportiert, ohne eine PDF für den Webtext zu erfinden. Fehlendes Webregister, widersprüchliche Zuordnungen, fehlender Prüfbericht, fehlende oder erfolglose Prüfung, veralteter Quellhash und veränderte Textquelle führen vor dem ersten Zielschreibzugriff zum Abbruch.
- **Oberfläche:** Start und Aufbau aller Tkinter-Elemente im ausgeblendeten Testfenster erfolgreich; Kommandozeilenprüfung mit dem echten Bestand erfolgreich.

Wiederholen aus der Projektwurzel:

```powershell
py Werkzeuge/Cloud_Sync/gui.py --check
py Werkzeuge/Cloud_Sync/gui.py --smoke-test
py -m unittest discover -s Werkzeuge/Cloud_Sync -p "test_*.py" -v
```

Es wurde kein Upload durchgeführt und kein Google- oder Claude-Konto verbunden. Der tatsächliche Drive-Upload und der Zugriff durch Claude müssen nach der persönlichen Kontoeinrichtung geprüft werden. Die lokale Bereitstellung führt keinen neuen amtlichen Quellenabgleich durch.
