# Prüfbericht – Finanzgerichtsordnung (FGO)

**Ergebnis: vollständig übernommen und geprüft.** Quellenabgleich: **09.09.2026**.

Die bereitgestellte Datei `FGO.pdf` ist bytegleich mit der am Prüftag von [Gesetze im Internet](https://www.gesetze-im-internet.de/fgo/) abgerufenen PDF-Gesamtausgabe. Alle 36 PDF-Seiten und sämtliche 196 XML-Normdatensätze wurden im Textvergleich berücksichtigt. Die strukturierte Wiedergabe beruht auf der zugehörigen, unverändert archivierten XML-Gesamtausgabe.

## Stand und Quellen

"Finanzgerichtsordnung in der Fassung der Bekanntmachung vom 28. März 2001 (BGBl. I S. 442, 2262; 2002 I S. 679), die zuletzt durch Artikel 12 Absatz 2 des Gesetzes vom 29. Juni 2026 (BGBl. 2026 I Nr. 197) geändert worden ist"

- Neugefasst durch Bek. v. 28.3.2001 I 442, 2262; 2002 I 679;
- zuletzt geändert durch Art. 18 G v. 22.12.2025 I Nr. 349
- Änderung durch Art. 10 G v. 20.5.2026 I Nr. 152 textlich nachgewiesen, dokumentarisch noch nicht abschließend bearbeitet
- Änderung durch Art. 12 Abs. 2 G v. 29.6.2026 I Nr. 197 ist berücksichtigt
- Mittelbare Änderung durch Art. 154a Nr. 3 Buchst. a G v. 20.11.2019 I 1626 ist nicht ausführbar, da das geänderte G v. 21.6.2019 I 846 zum Zeitpunkt des Inkrafttretens des mittelbaren Änderungsgesetzes bereits zum 1.11.2019 in Kraft getreten war

Das Ordnerdatum bezeichnet den Quellenabgleich. Es ist kein einheitliches Inkrafttretensdatum der einzelnen Vorschriften. Anwendungsvorschriften und dokumentarische Hinweise bleiben im Gesetzestext erhalten.

Die Quelle weist die Änderung vom 20. Mai 2026 als textlich nachgewiesen, dokumentarisch noch nicht abschließend bearbeitet aus. Die Änderung vom 29. Juni 2026 ist berücksichtigt. Sämtliche fünf Stand-/Bearbeitungshinweise sind unverändert in der Markdown-Datei enthalten.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 196 vollständig |
| Gliederungsteile | 22 |
| Vorschriftendatensätze | 173 einschließlich weggefallener Vorschriften und zusammengefasster Bereiche |
| Anlagendatensätze | 0 einschließlich ggf. zusammengefasster weggefallener Anlagen |
| Tabellen | 0 mit 0 Originalzeilen und 0 Originalzellen |
| Aufzählungskennzeichen | 124 |
| XML gegen gerendertes Markdown | 251 Inhalts-, Fußnoten- und Überschriftenblöcke ohne Textverlust |
| Unabhängige Kontrolle des zusammengesetzten Markdown | Alle 195 Normabschnitte nach dem Dokumentkopf vollständig und in Originalreihenfolge; jede Tabellenzelle einzeln identisch |
| Interne Sprungziele | Alle 174 Verweise gültig, keine doppelten Anker |

Der PDF/XML-Abgleich normalisiert ausschließlich Leerraum, Unicode-NFC und unsichtbare weiche Trennzeichen. Fußnotenkennzeichen werden aus den XML-Attributen für den PDF-Vergleich ergänzt. Die technische XML-Kennung `(XXXX)` wird entsprechend der sichtbaren PDF nicht ausgegeben. Alle Wörter, Zahlen, Satzzeichen, Absätze, Fußnotentexte, Anlagen und Tabelleninhalte bleiben erhalten.

Der XML/Markdown-Abgleich normalisiert Leerraum und Unicode-NFC. Redaktionelle Navigationslinks, Fußnotenverknüpfungen und generische Tabellenspaltenköpfe werden gesondert behandelt. Inhaltliche Tabellenüberschriften und sämtliche Originalzellen werden vollständig verglichen. Komplexe Tabellen bleiben als HTML mit verbundenen Zellen im Markdown; die Quelldateien sind unverändert.

## Nachgewiesene PDF-Layoutunterschiede

Alle Normdatensätze stimmen nach der beschriebenen Grundnormalisierung unmittelbar und vollständig überein.

Die exakten Transformationen, Zeichenvergleiche und Einzelresultate stehen im [PDF/XML-Abgleich](PDF_XML_Abgleich.json). Keine verbleibende Textabweichung wurde pauschal oder ohne Prüfung ausgenommen.

## Reproduzierbarkeit

Erforderlich: Python 3, `markdown-it-py`, für den PDF-Vergleich zusätzlich Poppler `pdftotext` im PATH. Die archivierten Scripte arbeiten ohne Netzwerkzugriff.

```powershell
py Pruefung/konvertieren.py
py Pruefung/pdf_xml_pruefen.py
py Pruefung/markdown_struktur_pruefen.py
```

Die Aufrufe sind aus dem Standordner möglich. Alle Quelldateien und ihre Pfade sind in [konfiguration.json](konfiguration.json) dokumentiert. Der Konvertersnapshot liegt bei und macht diesen Stand unabhängig von späteren Änderungen des gemeinsamen Werkzeugs.

- [Vollständigkeitsprüfung](Vollstaendigkeitspruefung.json): Zeichenvergleich jedes übernommenen Textblocks.
- [Markdown-Strukturprüfung](Markdown_Strukturpruefung.json): unabhängiger Vergleich vollständiger Normabschnitte, jeder Tabellenzelle und sämtlicher Links.
- [Normenbestand](Normenbestand.json): vollständiges Normverzeichnis mit Original-Datensatzkennungen.
- [PDF/XML-Abgleich](PDF_XML_Abgleich.json): Volltextvergleich über alle PDF-Seiten und Normdatensätze.

## Prüfsummen (SHA-256)

| Datei | SHA-256 |
| --- | --- |
| Bereitgestellte und aktuell abgerufene PDF | `704954a4478aff08c5adaf41cd36d17d267cb1401f8e205741238b7526bec3a3` |
| XML | `1f6af7b3b82581e5c91095aac06a354608962cde476fd81ade6363f9a0f00f1b` |
| Markdown | `8e5a84b5db68058e393e628a659052062095d9a4dffd9e43c638c2d17da992a3` |
