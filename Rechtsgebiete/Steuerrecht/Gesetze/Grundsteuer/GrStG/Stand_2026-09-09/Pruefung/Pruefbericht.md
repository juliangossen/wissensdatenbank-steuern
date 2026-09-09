# Prüfbericht – Grundsteuergesetz (GrStG)

**Ergebnis: vollständig in Markdown übernommen und geprüft.** Quellenabgleich: 09.09.2026.

Die bereitgestellte Datei `GrStG.pdf` ist bytegleich mit der am Prüftag abgerufenen [PDF-Gesamtausgabe](https://www.gesetze-im-internet.de/grstg_1973/GrStG.pdf). Alle 15 Seiten und 45 XML-Normdatensätze sind berücksichtigt. Die unveränderte XML-Gesamtausgabe stammt von derselben offiziellen Gesetzesseite.



## Stand und Quellen

"Grundsteuergesetz vom 7. August 1973 (BGBl. I S. 965), das zuletzt durch Artikel 32 des Gesetzes vom 2. Dezember 2024 (BGBl. 2024 I Nr. 387) geändert worden ist"

- Zuletzt geändert durch Art. 32 G v. 2.12.2024 I Nr. 387

Das Ordnerdatum bezeichnet die Erfassung und Quellenprüfung. Es bestätigt kein einheitliches Inkrafttretensdatum. Sämtliche dokumentarischen Hinweise und Anwendungsvorschriften stehen im Volltext.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 45 |
| Gliederungsteile | 5 |
| Vorschriftendatensätze | 38 einschließlich weggefallener Normen und ggf. zusammengefasster Bereiche |
| Anlagen/Anhänge | 0 |
| Tabellen | 5 mit 38 Zeilen und 76 Zellen |
| Aufzählungskennzeichen | 56 |
| Originalabbildungen | 0 |
| XML gegen gerendertes Markdown | 106 Text-, Fußnoten-, Gliederungs- und Überschriftenblöcke identisch |
| Unabhängige Markdown-Strukturprüfung | 44 vollständige Normabschnitte nach dem Dokumentkopf sowie jede Tabellenzelle in Originalreihenfolge identisch |
| Interne Links | Alle 78 Ziele vorhanden; keine doppelten Anker |

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
| Original-PDF und am Prüftag abgerufene PDF | `d1501382c2269e1c723296204e20f434767ab0e3e86b06e304205510b3861c66` |
| XML | `9e3c182c877c0b6db6b5f5d04f3801a8577ee9ad395c87e924baed18cf99ece4` |
| Markdown | `712c511078d09cf24777657015f9ca841cf38d045cfbb90a2ca3654e80210f6b` |
