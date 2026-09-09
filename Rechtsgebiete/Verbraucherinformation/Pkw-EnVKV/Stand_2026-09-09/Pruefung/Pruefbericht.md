# Prüfbericht: Pkw-EnVKV

**Prüfdatum: 09.09.2026.** Die vollständige [Markdown-Fassung](../Pkw-EnVKV.md) wurde gegen archivierte Quellen geprüft. Die bereitgestellte PDF ist bytegleich mit der am Prüftag von [Gesetze im Internet](https://www.gesetze-im-internet.de/pkw-envkv/) abgerufenen PDF.

## Quellenstand

- Zuletzt geändert durch Art. 1 V v. 2.3.2026 I Nr. 55

Ausfertigungsdatum: 2004-05-28. Original-PDF: 23 Seiten. Alle Stand- und Bearbeitungshinweise sowie das Vollzitat sind im Markdown-Dokument enthalten.

## Vollständigkeit

Der vollständige PDF/XML-Vergleich erfasst 19 Normdatensätze einschließlich Gliederungen, Überschriften, Texten und Fußnoten. Sämtliche Datensätze stimmen nach Vereinheitlichung von Unicode und Leerraum sowie Entfernung wiederkehrender PDF-Servicezeilen und Seitennummern vollständig überein. Fußnotenmarker werden aus den XML-Attributen rekonstruiert.

Der Konverter hat 37 Text-, Überschriften- und Fußnotenblöcke aus dem gerenderten Markdown zurückgelesen und vollständig mit XML verglichen. Eine unabhängige Prüfung der gespeicherten Gesamtdatei bestätigt zusätzlich jeden vollständigen Normabschnitt, jede Tabellenzelle, die Zeilenzahl und alle Navigationsziele.

| Prüfgegenstand | Umfang |
| --- | --- |
| XML-Normdatensätze | 19 |
| Vorschriftendatensätze | 12 |
| Gliederungsteile | 0 |
| Anlagen/Anhänge | 4 |
| Tabellen | 10 |
| Tabellenzeilen | 25 |
| Tabellenzellen | 37 |
| Originalabbildungen | 5 |

Maschinenlesbare Nachweise: [PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Markdown-Prüfung](Markdown_Strukturpruefung.json).

## Musterabbildungen

Alle fünf in der XML-Quelle referenzierten Musterabbildungen sind in der Markdown-Datei an den ursprünglichen Positionen eingebunden. Die JPEG-Dateien wurden unverändert aus dem amtlichen XML-Paket übernommen; Dateipfade und SHA-256-Prüfsummen stehen im Konvertierungsbericht. Alle fünf Abbildungen wurden visuell kontrolliert. Ihr grafischer und eingebetteter textlicher Inhalt bleibt als Originalabbildung erhalten.

## Darstellung

Navigation und generische Spaltenüberschriften sind redaktionelle Ergänzungen. Die Originalnummerierung, weggefallene Vorschriften, Fundstellen und Anwendungshinweise bleiben enthalten. Fußnotenmarker aus den Quellattributen sind verlinkt. Komplexe Tabellen bleiben als HTML-Tabellen innerhalb der Markdown-Datei mit verbundenen Zellen und relevanten Trennlinien erhalten. Lediglich seitenbedingte Wiederholungen entfallen.

## Reproduzierbarkeit

Vom Ordner `Pruefung` aus:

```powershell
py konvertieren.py
py pdf_xml_abgleichen.py
py markdown_struktur_pruefen.py
```

Benötigt werden Python, `markdown-it-py` und Poppler `pdftotext`. Der Konverter liegt gemeinsam unter `Werkzeuge/gesetz_konvertieren.py`; die gesetzesspezifische Konfiguration steht in [konfiguration.json](konfiguration.json). Alle Aufrufe lesen ausschließlich archivierte Quellen; sie laden keine neue Gesetzesfassung.
