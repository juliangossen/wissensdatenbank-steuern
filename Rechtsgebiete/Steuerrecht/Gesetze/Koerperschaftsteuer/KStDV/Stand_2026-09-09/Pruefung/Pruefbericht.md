# Prüfbericht – Körperschaftsteuer-Durchführungsverordnung 1994 (KStDV 1994)

**Ergebnis: vollständig in Markdown übernommen und geprüft.** Quellenabgleich: 09.09.2026.

Die bereitgestellte Datei `KStDV_1994.pdf` ist bytegleich mit der am Prüftag abgerufenen [PDF-Gesamtausgabe](https://www.gesetze-im-internet.de/kstdv_1977/KStDV_1994.pdf). Alle 2 Seiten und 13 XML-Normdatensätze sind berücksichtigt. Die unveränderte XML-Gesamtausgabe stammt von derselben offiziellen Gesetzesseite.



## Stand und Quellen

"Körperschaftsteuer-Durchführungsverordnung 1994 in der Fassung der Bekanntmachung vom 22. Februar 1996 (BGBl. I S. 365), die zuletzt durch Artikel 2 Absatz 11 des Gesetzes vom 1. April 2015 (BGBl. I S. 434) geändert worden ist"

- Neugefasst durch Bek. v. 22.2.1996 I 365; zuletzt geändert durch Art. 2 Abs. 11 G v. 1.4.2015 I 434

Das Ordnerdatum bezeichnet die Erfassung und Quellenprüfung. Es bestätigt kein einheitliches Inkrafttretensdatum. Sämtliche dokumentarischen Hinweise und Anwendungsvorschriften stehen im Volltext.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 13 |
| Gliederungsteile | 4 |
| Vorschriftendatensätze | 7 einschließlich weggefallener Normen und ggf. zusammengefasster Bereiche |
| Anlagen/Anhänge | 1 |
| Tabellen | 2 mit 9 Zeilen und 27 Zellen |
| Aufzählungskennzeichen | 10 |
| Originalabbildungen | 0 |
| XML gegen gerendertes Markdown | 28 Text-, Fußnoten-, Gliederungs- und Überschriftenblöcke identisch |
| Unabhängige Markdown-Strukturprüfung | 12 vollständige Normabschnitte nach dem Dokumentkopf sowie jede Tabellenzelle in Originalreihenfolge identisch |
| Interne Links | Alle 9 Ziele vorhanden; keine doppelten Anker |

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
| Original-PDF und am Prüftag abgerufene PDF | `dcb08e4c18e3430953f6b2b3fce5119428f9212db5aeb0ae8c272c4f5587a812` |
| XML | `3f7a5df179222fbd146bd048d9ae348aa4893f5846539b70cddeea1bb1e23b21` |
| Markdown | `d6b7d668f9c78aef6ad0673823a149836e72620c85d77126ee282d40308d9968` |
