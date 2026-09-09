# Prüfbericht: HGB

**Ergebnis:** Der Gesetzesvolltext wurde vollständig aus der archivierten GII-XML übernommen. Alle 814 Normdatensätze einschließlich Dokumentkopf, Gliederungen, Vorschriften und Anlagen sind nachgewiesen. Sämtliche fertigen Markdown-Normtexte, Tabellenzellen und internen Verweise haben die unabhängigen Prüfungen bestanden.

## Quellen und Fassungsstand

Quellenabgleich am **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/hgb/). Die bereitgestellte PDF und die am Prüftag abgerufene PDF sind bytegleich (SHA-256) und enthalten denselben extrahierten Text. Die Gesamtausgabe umfasst **218 Seiten**. PDF, XML-Quellenpaket, entpackte XML und HTML wurden unverändert unter [Quellen](../Quellen/README.md) archiviert.

**Vollzitat der Quelle:**

"Handelsgesetzbuch in der im Bundesgesetzblatt Teil III, Gliederungsnummer 4100-1, veröffentlichten bereinigten Fassung, das zuletzt durch Artikel 4 des Gesetzes vom 4. Februar 2026 (BGBl. 2026 I Nr. 33) geändert worden ist"

**Vollständige Stand- und Bearbeitungshinweise der Quelle:**

- Zuletzt geändert durch Art. 4 G v. 4.2.2026 I Nr. 33
- Mittelbare Änderung durch Art. 59 Nr. 1 G v. 4.2.2026 I Nr. 33 ist berücksichtigt

Das Datum des Stand-Ordners ist das Datum des Quellenabgleichs. Es ersetzt nicht die im Gesetz genannten Anwendungs-, Übergangs- oder Inkrafttretensregelungen.

## Vollständigkeitsnachweis

| Prüfgegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 814 vollständig und in Originalreihenfolge |
| Vorschriften-Datensätze | 696 einschließlich weggefallener Vorschriften und Sammelüberschriften |
| Gliederungsteile | 117 |
| Anlagen und Anhänge | 0 |
| Tabellen | 0 mit 0 Originalzeilen und 0 Originalzellen |
| Aufzählungskennzeichnungen | 1121 |
| Eingebettete Fußnotenverweise | 0, Kennzeichnung und Zuordnung vollständig erhalten |
| Konvertierungsprüfung | 1666 Inhalts-, Fußnoten- und Überschriftsblöcke zeichengenau rückverglichen |
| Unabhängiger Gesamtdateivergleich | Alle 814 vollständigen Normtexte identisch |
| Interne Links | 697; sämtliche Ziele vorhanden, keine doppelten Anker |

„Vorschriften-Datensatz“ bezeichnet eine Einzel- oder Sammelüberschrift der Quelle. Eine Sammelüberschrift wie „§§ 3 bis 6“ zählt einmal; auch aufgehobene Vorschriften und ihre Hinweise sind enthalten. Der [Normbestand](Normbestand.json) weist jeden Datensatz mit Quell-ID, Bezeichnung und Textfingerabdruck nach.

Der unabhängige PDF/XML-Vergleich prüft jede vollständige Überschrift, jeden vollständigen Normtext und sämtliche Fußnoten. 814 von 814 Normdatensätzen stimmen nach Entfernung von Whitespace, PDF-Servicezeilen und Seitenzählern vollständig überein. Die Quellmarker aus Fußnotenattributen werden dabei rekonstruiert. Die maschinenlesbaren Ergebnisse stehen in [PDF_XML_Abgleich.json](PDF_XML_Abgleich.json).

Zusätzlich wurden die **fertige Gesamtdatei** erneut gerendert und alle Normabschnitte gegen XML verglichen, einschließlich Gliederungsüberschriften und Dokumentkopf. Die [Gesamtprüfung](Markdown_Gesamtpruefung.json) bestätigt sämtliche Normtexte und Fußnotenmarker; die [Strukturprüfung](Markdown_Strukturpruefung.json) prüft zusätzlich jede Tabellenzelle in Reihenfolge, alle Tabellen- und Zeilenzahlen sowie alle Sprungmarken. Das sind Vollprüfungen, keine Stichproben.

## Darstellungsregeln

- Whitespace und Unicode-NFC werden nur für den Vergleich vereinheitlicht. Inhaltliche Zeichen und Zahlen bleiben erhalten.
- PDF-Servicezeilen, Seitenzähler und reine wiederholte Tabellenköpfe gehören zur Seitendarstellung und werden im Markdown nicht wiederholt.
- 7 technische XML-Präfixe `(XXXX)` werden vor Normüberschriften ausgeblendet; die zugehörigen Vorschriften und Wegfallhinweise bleiben vollständig erhalten.
- Komplexe Tabellen werden als eingebettete HTML-Tabellen dargestellt, einschließlich verbundener Zellen. Einfache Tabellen erhalten bei Bedarf ausdrücklich generische Spaltenüberschriften.
- Navigation und Prüfmetadaten sind redaktionelle Ergänzungen. Fußnotenmarker werden aus den XML-Attributen übernommen und bleiben mit dem zugehörigen Fußnotentext verbunden.
- In dieser XML-Gesamtausgabe sind keine externen Bilddateien referenziert.

### Leerer Darstellungsplatzhalter bei §§ 153 bis 160

Die PDF zeigt hinter „§§ 153 bis 160“ vier Bindestriche (`----`). Die XML-Quelle enthält an dieser Stelle eine leere Textzelle und keine entsprechende Zeichenfolge. Das ist ein von der PDF-Ausgabe ergänzter Darstellungsplatzhalter. Im Markdown sind die Sammelüberschrift sowie die vollständige Fußnote „Weggefallen aufgrund Neuregelung … mWv 1.1.2024“ erhalten. Der inhaltsleere PDF-Platzhalter wurde nicht als zusätzlicher Gesetzestext eingefügt. Beim PDF/XML-Vergleich wird genau dieser Platzhalter berücksichtigt.

## Reproduzierbarkeit

Konvertierung vom Hauptverzeichnis der Wissensdatenbank aus:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Handelsrecht/HGB/Stand_2026-09-09/Pruefung/konfiguration.json
```

Die nachfolgenden Prüfprogramme können aus jedem Arbeitsverzeichnis über ihren Pfad gestartet werden. Ohne Parameter lesen sie die benachbarte `konfiguration.json`:

```powershell
py "Rechtsgebiete/Handelsrecht/HGB/Stand_2026-09-09/Pruefung/pdf_xml_abgleichen.py"
py "Rechtsgebiete/Handelsrecht/HGB/Stand_2026-09-09/Pruefung/markdown_gesamtpruefen.py"
py "Rechtsgebiete/Handelsrecht/HGB/Stand_2026-09-09/Pruefung/markdown_struktur_pruefen.py"
```

Voraussetzungen: Python 3; `markdown-it-py` für die Markdown-Prüfung; Poppler `pdftotext` für die PDF-Prüfung. Die Prüfungen arbeiten mit den archivierten Quellen und benötigen keinen Netzwerkzugriff. Die Ergebnisse werden als JSON im Prüfungsordner gespeichert.

## Dateifingerabdrücke

| Datei | SHA-256 |
| --- | --- |
| Markdown | `cbc92edd45443d33c48653a49237d9381dd356e613b8ff381eb5bcd21547f1e3` |
| XML | `0ab160e58571476215e0a8e5f658569a2383f3fbbaffd01de4e54913abf36361` |
| Bereitgestellte und aktuelle PDF | `30dd1fc834d186097de827e80c3ebda61a63967996066525701658c3871acc09` |

Weitere Quellfingerabdrücke: [Quellenabgleich.json](Quellenabgleich.json). Der detaillierte blockweise Rückvergleich steht in [Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json).
