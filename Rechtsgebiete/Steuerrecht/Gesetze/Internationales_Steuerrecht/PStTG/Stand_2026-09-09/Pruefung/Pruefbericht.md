# Prüfbericht – Gesetz über die Meldepflicht und den automatischen Austausch von Informationen meldender Plattformbetreiber in Steuersachen (PStTG)

**Ergebnis: vollständig in Markdown übernommen und geprüft.** Quellenabgleich: 09.09.2026.

Die bereitgestellte Datei `PStTG.pdf` ist bytegleich mit der am Prüftag abgerufenen [PDF-Gesamtausgabe](https://www.gesetze-im-internet.de/psttg/PStTG.pdf). Alle 18 Seiten und 40 XML-Normdatensätze sind berücksichtigt. Die unveränderte XML-Gesamtausgabe stammt von derselben offiziellen Gesetzesseite.



## Stand und Quellen

"Plattformen-Steuertransparenzgesetz vom 20. Dezember 2022 (BGBl. I S. 2730), das zuletzt durch Artikel 5 des Gesetzes vom 22. Dezember 2025 (BGBl. 2025 I Nr. 352) geändert worden ist"

- Zuletzt geändert durch Art. 5 G v. 22.12.2025 I Nr. 352

Das Ordnerdatum bezeichnet die Erfassung und Quellenprüfung. Es bestätigt kein einheitliches Inkrafttretensdatum. Sämtliche dokumentarischen Hinweise und Anwendungsvorschriften stehen im Volltext.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 40 |
| Gliederungsteile | 9 |
| Vorschriftendatensätze | 29 einschließlich weggefallener Normen und ggf. zusammengefasster Bereiche |
| Anlagen/Anhänge | 0 |
| Tabellen | 8 mit 29 Zeilen und 58 Zellen |
| Aufzählungskennzeichen | 150 |
| Originalabbildungen | 0 |
| XML gegen gerendertes Markdown | 80 Text-, Fußnoten-, Gliederungs- und Überschriftenblöcke identisch |
| Unabhängige Markdown-Strukturprüfung | 39 vollständige Normabschnitte nach dem Dokumentkopf sowie jede Tabellenzelle in Originalreihenfolge identisch |
| Interne Links | Alle 60 Ziele vorhanden; keine doppelten Anker |

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
| Original-PDF und am Prüftag abgerufene PDF | `68faf85905d8db3bb1ae7f2c0ff140b2c397324e38e9315521db3773af5c2d71` |
| XML | `303609e5ba009c30453c614083f00c51cdcabdc6e03e1865a572fbe16f411ee6` |
| Markdown | `acae16b8c677347f55f004e584293018d03c908ffe1d0f39e7ffe4e3f19ac91b` |
