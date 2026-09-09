# Prüfbericht – Erbschaftsteuer- und Schenkungsteuergesetz (ErbStG)

**Ergebnis: vollständig in Markdown übernommen und geprüft.** Quellenabgleich: 09.09.2026.

Die bereitgestellte Datei `ErbStG.pdf` ist bytegleich mit der am Prüftag abgerufenen [PDF-Gesamtausgabe](https://www.gesetze-im-internet.de/erbstg_1974/ErbStG.pdf). Alle 36 Seiten und 54 XML-Normdatensätze sind berücksichtigt. Die unveränderte XML-Gesamtausgabe stammt von derselben offiziellen Gesetzesseite.



## Stand und Quellen

"Erbschaftsteuer- und Schenkungsteuergesetz in der Fassung der Bekanntmachung vom 27. Februar 1997 (BGBl. I S. 378), das zuletzt durch Artikel 10 des Gesetzes vom 22. Juni 2026 (BGBl. 2026 I Nr. 192) geändert worden ist"

- Neugefasst durch Bek. v. 27.2.1997 I 378; zuletzt geändert durch Art. 10 G v. 22.6.2026 I Nr. 192

Das Ordnerdatum bezeichnet die Erfassung und Quellenprüfung. Es bestätigt kein einheitliches Inkrafttretensdatum. Sämtliche dokumentarischen Hinweise und Anwendungsvorschriften stehen im Volltext.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 54 |
| Gliederungsteile | 5 |
| Vorschriftendatensätze | 47 einschließlich weggefallener Normen und ggf. zusammengefasster Bereiche |
| Anlagen/Anhänge | 0 |
| Tabellen | 7 mit 65 Zeilen und 145 Zellen |
| Aufzählungskennzeichen | 217 |
| Originalabbildungen | 0 |
| XML gegen gerendertes Markdown | 139 Text-, Fußnoten-, Gliederungs- und Überschriftenblöcke identisch |
| Unabhängige Markdown-Strukturprüfung | 53 vollständige Normabschnitte nach dem Dokumentkopf sowie jede Tabellenzelle in Originalreihenfolge identisch |
| Interne Links | Alle 98 Ziele vorhanden; keine doppelten Anker |

## PDF-Layout und Quellenbesonderheiten

In § 19 wird im PDF der verbundene Gruppenkopf „Prozentsatz in der Steuerklasse“ vor dem mehrzeiligen linken Kopf gelesen. Die genau protokollierte Kopfumsortierung erhält sämtliche Zeichen; der übrige Text einschließlich aller Tabellenwerte ist unverändert.

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
| Original-PDF und am Prüftag abgerufene PDF | `a99eb7335fac93a98590d2a2f0a46c4926077a193769bbddf96dedf3b63b6015` |
| XML | `0be82e8e1b128bfb91f002b18612b7e7d1fd7eddf96908b6afb0cc0d1a7f1794` |
| Markdown | `f17a54454c1ae6c1a8720612e0c346ac3ff87e0cb98841cd2d74dbe5ec1834a9` |
