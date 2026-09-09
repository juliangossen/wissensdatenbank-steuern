# Zusätzlicher PDF-Import vom 09.09.2026

Dieser Import umfasst 31 bereitgestellte PDFs mit zusammen 1.370 Seiten. Die [Eingangsliste](Eingang.json) hält die ursprünglichen Dateinamen, Seitenzahlen und SHA-256-Prüfsummen fest.

**Abgeschlossen:** Alle 31 Original-PDFs sind unverändert archiviert und im Gesamtbestand registriert. Die [Abschlussprüfung](Abschlusspruefung.json) bestätigt die Zuordnung, Prüfsummen und 5.402 lokale Verweise. Der [Importabschluss](Importabschluss.json) enthält die vollständigen Einträge; der [Ablageplan](Ablageplan.json) dokumentiert die ursprünglichen und endgültigen Pfade.

Die Dokumente werden in die passenden Rechtsgebiete eingeordnet. Der Standordner bezeichnet den Quellenabgleich. Die ursprünglichen EU-Amtsblattfassungen und das historische Solidaritätszuschlaggesetz von 1991 behalten ihre eigene zeitliche Einordnung. Eine in der InvStG-PDF abgeschnittene Fußnotenzeile wird ausdrücklich dokumentiert aus der passenden amtlichen XML-Ausgabe ergänzt.

## Konvertierung und Nachweise

Die einzelnen Standordner enthalten Markdown-Volltexte, archivierte Quellen, Konverter und Prüfberichte. Gesetze-im-Internet-Dokumente werden anhand der zugehörigen XML-Ausgabe strukturiert. EU-Dokumente verwenden die zum gelieferten Amtsblatt-PDF gehörende amtliche HTML-Fassung. Tabellen, verbundene Zellen, Fußnoten, Anlagen und Originalabbildungen werden einbezogen. Quellenbesonderheiten sind einzeln dokumentiert.

## Archivablauf

1. `py -B Werkzeuge/PDF_Import_2026-09-09/archivieren.py vorbereiten` vergleicht alle Eingangsdateien, Konfigurationen, Prüfergebnisse und Markdown-Prüfsummen. Daraus entsteht der Ablageplan; noch keine Originaldatei wird verschoben.
2. `Werkzeuge/PDF_Import_2026-09-09/archivieren.ps1` prüft absolute Quell- und Zielpfade sowie Prüfsummen erneut und verschiebt ausschließlich diese geprüften Originale in das versionierte PDF-Archiv.
3. `py -B Werkzeuge/PDF_Import_2026-09-09/archivieren.py registrieren` prüft die archivierten Dateien und ergänzt das Register. Die vorherige Registerfassung bleibt im Importjournal erhalten.
4. Die zentralen Indexwerkzeuge erstellen die PDF-Archivübersicht, die Web-Archivübersicht und den Gesamtbestand neu.
5. `py -B Werkzeuge/PDF_Import_2026-09-09/abschluss_pruefen.py` prüft die neuen Einträge gegen den Gesamtbestand und kontrolliert die lokalen Verweise in Volltexten, Readmes und Prüfberichten. Anschließend erfolgt die lesende Cloud-Sync-Prüfung mit `py -B Werkzeuge/Cloud_Sync/gui.py --check`.

Die Schritte 1–3 beschreiben diesen einmaligen Import. Spätere Quellenfassungen erhalten einen eigenen Import mit eigenem Eingangs- und Quellenabgleich; abgeschlossene Fassungen werden dabei nicht überschrieben.

[Zur Werkzeugübersicht](../README.md) · [Zum Gesamtbestand](../../README.md).
