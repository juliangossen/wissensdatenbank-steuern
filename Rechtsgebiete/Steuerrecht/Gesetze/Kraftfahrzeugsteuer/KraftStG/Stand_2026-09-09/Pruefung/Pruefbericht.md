# Prüfbericht – Kraftfahrzeugsteuergesetz 2002 (KraftStG)

**Ergebnis: vollständig übernommen und geprüft.** Quellenabgleich: **09.09.2026**.

Die bereitgestellte Datei `KraftStG_2002.pdf` ist bytegleich mit der am Prüftag von [Gesetze im Internet](https://www.gesetze-im-internet.de/kraftstg/) abgerufenen PDF-Gesamtausgabe. Alle 19 PDF-Seiten und sämtliche 30 XML-Normdatensätze wurden im Textvergleich berücksichtigt. Die strukturierte Wiedergabe beruht auf der zugehörigen, unverändert archivierten XML-Gesamtausgabe.

## Stand und Quellen

"Kraftfahrzeugsteuergesetz 2002 in der Fassung der Bekanntmachung vom 26. September 2002 (BGBl. I S. 3818), das zuletzt durch Artikel 1 des Gesetzes vom 22. Dezember 2025 (BGBl. 2025 I Nr. 342) geändert worden ist"

- Neugefasst durch Bek. v. 26.9.2002 I 3818;
- zuletzt geändert durch Art. 1 G v. 22.12.2025 I Nr. 342

Das Ordnerdatum bezeichnet den Quellenabgleich. Es ist kein einheitliches Inkrafttretensdatum der einzelnen Vorschriften. Anwendungsvorschriften und dokumentarische Hinweise bleiben im Gesetzestext erhalten.

Die Umsetzungshinweise im Gesetzeskopf vor der ersten Fußnote sind vollständig enthalten. § 9 wurde zusätzlich anhand von PDF-Seite 8 visuell geprüft; Tabellenzellen behalten ihre Zuordnung zu Fremd- und Selbstzündungsmotoren.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 30 vollständig |
| Gliederungsteile | 0 |
| Vorschriftendatensätze | 28 einschließlich weggefallener Vorschriften und zusammengefasster Bereiche |
| Anlagendatensätze | 0 einschließlich ggf. zusammengefasster weggefallener Anlagen |
| Tabellen | 27 mit 137 Originalzeilen und 315 Originalzellen |
| Aufzählungskennzeichen | 123 |
| XML gegen gerendertes Markdown | 61 Inhalts-, Fußnoten- und Überschriftenblöcke ohne Textverlust |
| Unabhängige Kontrolle des zusammengesetzten Markdown | Alle 29 Normabschnitte nach dem Dokumentkopf vollständig und in Originalreihenfolge; jede Tabellenzelle einzeln identisch |
| Interne Sprungziele | Alle 57 Verweise gültig, keine doppelten Anker |

Der PDF/XML-Abgleich normalisiert ausschließlich Leerraum, Unicode-NFC und unsichtbare weiche Trennzeichen. Fußnotenkennzeichen werden aus den XML-Attributen für den PDF-Vergleich ergänzt. Die technische XML-Kennung `(XXXX)` wird entsprechend der sichtbaren PDF nicht ausgegeben. Alle Wörter, Zahlen, Satzzeichen, Absätze, Fußnotentexte, Anlagen und Tabelleninhalte bleiben erhalten.

Der XML/Markdown-Abgleich normalisiert Leerraum und Unicode-NFC. Redaktionelle Navigationslinks, Fußnotenverknüpfungen und generische Tabellenspaltenköpfe werden gesondert behandelt. Inhaltliche Tabellenüberschriften und sämtliche Originalzellen werden vollständig verglichen. Komplexe Tabellen bleiben als HTML mit verbundenen Zellen im Markdown; die Quelldateien sind unverändert.

## Nachgewiesene PDF-Layoutunterschiede

- **§ 9**: Tabellenkopf-Lesereihenfolge und/oder Wiederholung am Seitenumbruch. Anschließend ist der gesamte restliche Normtext zeichenidentisch.

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
| Bereitgestellte und aktuell abgerufene PDF | `3a3b08fc24a98b74cc351a1b0d9a17c360c4f72471e2c6b02e63c39e81851540` |
| XML | `296752748f0e36b6d7fd6eee1f3a0d910ceda97813cfe0a32820678724fab48e` |
| Markdown | `cb807c6e02782bb5e7f264bd449349b7237abbea3d2c76c017be3793f9a2a23a` |
