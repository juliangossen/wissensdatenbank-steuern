# Offline reproduzieren und prüfen

Dieser Standordner enthält sämtliche benötigten Quellen und Programme. Es sind keine Onlineabrufe und keine Dateien außerhalb dieses Standordners erforderlich. Der Konverter bearbeitet ausschließlich dieses Dokument; der Importstand bleibt 2026-09-09.

Voraussetzungen: Python mit `pymupdf`, `beautifulsoup4`, `lxml` und `markdown-it-py`.

Im Standordner ausführen:

```powershell
py -B Pruefung/konvertieren.py
py -B Pruefung/pruefen.py
```

Der erste Aufruf erstellt Markdown und Nachweise aus der archivierten amtlichen HTML-Fassung und der Original-PDF erneut. Der zweite prüft die vorhandenen Artefakte schreibgeschützt: vollständiger HTML-Text, Prüfsummen, Links, Bilder, verbundene Tabellenzellen und PDF-Zeilenprotokoll. Für eine reine Kontrolle genügt der zweite Aufruf.

Die ursprüngliche Byteidentität mit der am 2026-09-09 abgerufenen amtlichen PDF ist in `../Quellen/Quellenabgleich.json` festgehalten. Offline wird die lokale PDF gegen diese gespeicherte Prüfsumme geprüft. Das ist kein erneuter Nachweis eines späteren Rechtsstands.
