# Prüfbericht – Gesetz über die Besteuerung bei Auslandsbeziehungen (AStG)

**Ergebnis: vollständig in Markdown übernommen und geprüft.** Quellenabgleich: 09.09.2026.

Die bereitgestellte Datei `AStG.pdf` ist bytegleich mit der am Prüftag abgerufenen [PDF-Gesamtausgabe](https://www.gesetze-im-internet.de/astg/AStG.pdf). Alle 20 Seiten und 32 XML-Normdatensätze sind berücksichtigt. Die unveränderte XML-Gesamtausgabe stammt von derselben offiziellen Gesetzesseite.



## Stand und Quellen

"Außensteuergesetz vom 8. September 1972 (BGBl. I S. 1713), das zuletzt durch Artikel 6 des Gesetzes vom 22. Dezember 2025 (BGBl. 2025 I Nr. 353) geändert worden ist"

- Zuletzt geändert durch Art. 6 G v. 22.12.2025 I Nr. 353

Das Ordnerdatum bezeichnet die Erfassung und Quellenprüfung. Es bestätigt kein einheitliches Inkrafttretensdatum. Sämtliche dokumentarischen Hinweise und Anwendungsvorschriften stehen im Volltext.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 32 |
| Gliederungsteile | 7 |
| Vorschriftendatensätze | 23 einschließlich weggefallener Normen und ggf. zusammengefasster Bereiche |
| Anlagen/Anhänge | 0 |
| Tabellen | 7 mit 23 Zeilen und 46 Zellen |
| Aufzählungskennzeichen | 89 |
| Originalabbildungen | 0 |
| XML gegen gerendertes Markdown | 84 Text-, Fußnoten-, Gliederungs- und Überschriftenblöcke identisch |
| Unabhängige Markdown-Strukturprüfung | 31 vollständige Normabschnitte nach dem Dokumentkopf sowie jede Tabellenzelle in Originalreihenfolge identisch |
| Interne Links | Alle 48 Ziele vorhanden; keine doppelten Anker |

## PDF-Layout und Quellenbesonderheiten

Alle Normdatensätze stimmen nach der Grundnormalisierung unmittelbar überein.

## Prüfmethoden und Reproduzierbarkeit

Der PDF/XML-Abgleich normalisiert Unicode-NFC, Leerraum und unsichtbare weiche Trennzeichen. Wiederkehrende PDF-Servicezeilen und Seitennummern werden entfernt. Fußnotenmarker stammen aus den XML-Attributen; der technische Marker `(XXXX)` wird wie im PDF nicht als Normbezeichnung ausgegeben. Alle übrigen Abweichungen sind einzeln nachgewiesen.

Der XML/Markdown-Abgleich vergleicht jedes gerenderte Inhaltssegment zeichengetreu nach NFC- und Leerraumnormalisierung. Nur ausdrücklich redaktionelle Fußnotenverknüpfungen und generische Spaltenüberschriften werden vom Vergleich ausgenommen. Ein zweiter Prüfer untersucht unabhängig davon jeden vollständigen Normabschnitt, die Normreihenfolge und jede einzelne Tabellenzelle. Komplexe Tabellen behalten verbundene Zellen als HTML im Markdown.

Erforderlich: Python 3, `markdown-it-py`, Poppler `pdftotext` im PATH; für die zusätzliche BewG-Bildprüfung `PyMuPDF`. Die archivierten Prüfer arbeiten ohne Netzwerkzugriff. Aufruf aus dem Standordner:

```powershell
py Pruefung/konvertieren.py
py Pruefung/markdown_struktur_pruefen.py
py Pruefung/pdf_xml_pruefen.py
```

- [Konfiguration](konfiguration.json): Quellenpfade, Fassungsangaben und Hashes.
- [Vollständigkeitsprüfung](Vollstaendigkeitspruefung.json): jeder XML/Markdown-Inhaltsblock.
- [Markdown-Strukturprüfung](Markdown_Strukturpruefung.json): vollständige Normabschnitte und Tabellen.
- [Normenbestand](Normenbestand.json): vollständiges Normverzeichnis und Originalkennungen.
- [PDF/XML-Abgleich](PDF_XML_Abgleich.json): alle PDF-Seiten und XML-Normdatensätze.

## SHA-256-Prüfsummen

| Datei | SHA-256 |
| --- | --- |
| Original-PDF und am Prüftag abgerufene PDF | `d92333fdb6c421d3f444b97c9f714b88e3c08ad201000ac01ff5dbc86869392f` |
| XML | `f9ad61bde5ca690fd1784130363b84ccc33329c22c49d6b5f4b5586ed9d251fd` |
| Markdown | `4700416f76575b4ebc5639b592b243f980c94e9f1c3926b87a76b237231222dd` |
