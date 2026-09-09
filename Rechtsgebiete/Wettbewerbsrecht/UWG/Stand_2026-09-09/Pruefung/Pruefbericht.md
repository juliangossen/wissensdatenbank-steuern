# Prüfbericht: UWG

**Ergebnis:** Der Gesetzesvolltext wurde vollständig aus der archivierten GII-XML übernommen. Alle 36 Normdatensätze einschließlich Dokumentkopf, Gliederungen, Vorschriften und Anlagen sind nachgewiesen. Sämtliche fertigen Markdown-Normtexte, Tabellenzellen und internen Verweise haben die unabhängigen Prüfungen bestanden.

## Quellen und Fassungsstand

Quellenabgleich am **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/uwg_2004/). Die bereitgestellte PDF und die am Prüftag abgerufene PDF sind bytegleich (SHA-256) und enthalten denselben extrahierten Text. Die Gesamtausgabe umfasst **18 Seiten**. PDF, XML-Quellenpaket, entpackte XML und HTML wurden unverändert unter [Quellen](../Quellen/README.md) archiviert.

**Vollzitat der Quelle:**

"Gesetz gegen den unlauteren Wettbewerb in der Fassung der Bekanntmachung vom 3. März 2010 (BGBl. I S. 254), das zuletzt durch Artikel 6 des Gesetzes vom 12. Mai 2026 (BGBl. 2026 I Nr. 139) geändert worden ist"

**Vollständige Stand- und Bearbeitungshinweise der Quelle:**

- Neugefasst durch Bek. v. 3.3.2010 I 254;
- Zuletzt geändert durch Art. 6 G v. 12.5.2026 I Nr. 139

Das Datum des Stand-Ordners ist das Datum des Quellenabgleichs. Es ersetzt nicht die im Gesetz genannten Anwendungs-, Übergangs- oder Inkrafttretensregelungen.

## Vollständigkeitsnachweis

| Prüfgegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 36 vollständig und in Originalreihenfolge |
| Vorschriften-Datensätze | 30 einschließlich weggefallener Vorschriften und Sammelüberschriften |
| Gliederungsteile | 4 |
| Anlagen und Anhänge | 1 |
| Tabellen | 0 mit 0 Originalzeilen und 0 Originalzellen |
| Aufzählungskennzeichnungen | 160 |
| Eingebettete Fußnotenverweise | 0, Kennzeichnung und Zuordnung vollständig erhalten |
| Konvertierungsprüfung | 76 Inhalts-, Fußnoten- und Überschriftsblöcke zeichengenau rückverglichen |
| Unabhängiger Gesamtdateivergleich | Alle 36 vollständigen Normtexte identisch |
| Interne Links | 32; sämtliche Ziele vorhanden, keine doppelten Anker |

„Vorschriften-Datensatz“ bezeichnet eine Einzel- oder Sammelüberschrift der Quelle. Eine Sammelüberschrift wie „§§ 3 bis 6“ zählt einmal; auch aufgehobene Vorschriften und ihre Hinweise sind enthalten. Der [Normbestand](Normbestand.json) weist jeden Datensatz mit Quell-ID, Bezeichnung und Textfingerabdruck nach.

Der unabhängige PDF/XML-Vergleich prüft jede vollständige Überschrift, jeden vollständigen Normtext und sämtliche Fußnoten. 36 von 36 Normdatensätzen stimmen nach Entfernung von Whitespace, PDF-Servicezeilen und Seitenzählern vollständig überein. Die Quellmarker aus Fußnotenattributen werden dabei rekonstruiert. Die maschinenlesbaren Ergebnisse stehen in [PDF_XML_Abgleich.json](PDF_XML_Abgleich.json).

Zusätzlich wurden die **fertige Gesamtdatei** erneut gerendert und alle Normabschnitte gegen XML verglichen, einschließlich Gliederungsüberschriften und Dokumentkopf. Die [Gesamtprüfung](Markdown_Gesamtpruefung.json) bestätigt sämtliche Normtexte und Fußnotenmarker; die [Strukturprüfung](Markdown_Strukturpruefung.json) prüft zusätzlich jede Tabellenzelle in Reihenfolge, alle Tabellen- und Zeilenzahlen sowie alle Sprungmarken. Das sind Vollprüfungen, keine Stichproben.

## Darstellungsregeln

- Whitespace und Unicode-NFC werden nur für den Vergleich vereinheitlicht. Inhaltliche Zeichen und Zahlen bleiben erhalten.
- PDF-Servicezeilen, Seitenzähler und reine wiederholte Tabellenköpfe gehören zur Seitendarstellung und werden im Markdown nicht wiederholt.
- 1 technische XML-Präfixe `(XXXX)` werden vor Normüberschriften ausgeblendet; die zugehörigen Vorschriften und Wegfallhinweise bleiben vollständig erhalten.
- Komplexe Tabellen werden als eingebettete HTML-Tabellen dargestellt, einschließlich verbundener Zellen. Einfache Tabellen erhalten bei Bedarf ausdrücklich generische Spaltenüberschriften.
- Navigation und Prüfmetadaten sind redaktionelle Ergänzungen. Fußnotenmarker werden aus den XML-Attributen übernommen und bleiben mit dem zugehörigen Fußnotentext verbunden.
- In dieser XML-Gesamtausgabe sind keine externen Bilddateien referenziert.

## Reproduzierbarkeit

Konvertierung vom Hauptverzeichnis der Wissensdatenbank aus:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Wettbewerbsrecht/UWG/Stand_2026-09-09/Pruefung/konfiguration.json
```

Die nachfolgenden Prüfprogramme können aus jedem Arbeitsverzeichnis über ihren Pfad gestartet werden. Ohne Parameter lesen sie die benachbarte `konfiguration.json`:

```powershell
py "Rechtsgebiete/Wettbewerbsrecht/UWG/Stand_2026-09-09/Pruefung/pdf_xml_abgleichen.py"
py "Rechtsgebiete/Wettbewerbsrecht/UWG/Stand_2026-09-09/Pruefung/markdown_gesamtpruefen.py"
py "Rechtsgebiete/Wettbewerbsrecht/UWG/Stand_2026-09-09/Pruefung/markdown_struktur_pruefen.py"
```

Voraussetzungen: Python 3; `markdown-it-py` für die Markdown-Prüfung; Poppler `pdftotext` für die PDF-Prüfung. Die Prüfungen arbeiten mit den archivierten Quellen und benötigen keinen Netzwerkzugriff. Die Ergebnisse werden als JSON im Prüfungsordner gespeichert.

## Dateifingerabdrücke

| Datei | SHA-256 |
| --- | --- |
| Markdown | `d8b055bfbf399b91091ffa6baa94dcf1fbb3aba107204cda18143af6735a6703` |
| XML | `9adf4b9c3ada6937f3b590e6d2d6916a527e10266e3eb31c8dcdf96b8b7e641a` |
| Bereitgestellte und aktuelle PDF | `9d885ce60a336f85d94b40c8e637ed551ce034792d32e5c04b3175234a085858` |

Weitere Quellfingerabdrücke: [Quellenabgleich.json](Quellenabgleich.json). Der detaillierte blockweise Rückvergleich steht in [Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json).
