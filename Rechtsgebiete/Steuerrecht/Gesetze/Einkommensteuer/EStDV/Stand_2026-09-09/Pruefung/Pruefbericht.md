# Prüfbericht – Einkommensteuer-Durchführungsverordnung (EStDV)

**Ergebnis: vollständig übernommen und geprüft.** Quellenabgleich: **09.09.2026**.

Die bereitgestellte Datei `EStDV_1955.pdf` ist bytegleich mit der am Prüftag von [Gesetze im Internet](https://www.gesetze-im-internet.de/estdv_1955/) abgerufenen PDF-Gesamtausgabe. Alle 28 PDF-Seiten und sämtliche 99 XML-Normdatensätze wurden im Textvergleich berücksichtigt. Die strukturierte Wiedergabe beruht auf der zugehörigen, unverändert archivierten XML-Gesamtausgabe.

## Stand und Quellen

"Einkommensteuer-Durchführungsverordnung in der Fassung der Bekanntmachung vom 10. Mai 2000 (BGBl. I S. 717), die zuletzt durch Artikel 2 der Verordnung vom 19. Dezember 2025 (BGBl. 2025 I Nr. 372) geändert worden ist"

- Neugefasst durch Bek. v. 10.5.2000 I 717;
- zuletzt geändert durch Art. 2 V v. 19.12.2025 I Nr. 372

Das Ordnerdatum bezeichnet den Quellenabgleich. Es ist kein einheitliches Inkrafttretensdatum der einzelnen Vorschriften. Anwendungsvorschriften und dokumentarische Hinweise bleiben im Gesetzestext erhalten.

Die Anlagegruppen werden originalgetreu geführt: Anlage 1, zusammengefasste weggefallene Anlagen 2 bis 4, Anlage 5 und Anlage 6. Das ergibt vier Anlagendatensätze. Der mehrseitige Tabellenkopf des § 55 wurde zusätzlich anhand von PDF-Seite 12 visuell geprüft.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 99 vollständig |
| Gliederungsteile | 22 |
| Vorschriftendatensätze | 71 einschließlich weggefallener Vorschriften und zusammengefasster Bereiche |
| Anlagendatensätze | 4 einschließlich ggf. zusammengefasster weggefallener Anlagen |
| Tabellen | 2 mit 159 Originalzeilen und 442 Originalzellen |
| Aufzählungskennzeichen | 108 |
| XML gegen gerendertes Markdown | 233 Inhalts-, Fußnoten- und Überschriftenblöcke ohne Textverlust |
| Unabhängige Kontrolle des zusammengesetzten Markdown | Alle 98 Normabschnitte nach dem Dokumentkopf vollständig und in Originalreihenfolge; jede Tabellenzelle einzeln identisch |
| Interne Sprungziele | Alle 77 Verweise gültig, keine doppelten Anker |

Der PDF/XML-Abgleich normalisiert ausschließlich Leerraum, Unicode-NFC und unsichtbare weiche Trennzeichen. Fußnotenkennzeichen werden aus den XML-Attributen für den PDF-Vergleich ergänzt. Die technische XML-Kennung `(XXXX)` wird entsprechend der sichtbaren PDF nicht ausgegeben. Alle Wörter, Zahlen, Satzzeichen, Absätze, Fußnotentexte, Anlagen und Tabelleninhalte bleiben erhalten.

Der XML/Markdown-Abgleich normalisiert Leerraum und Unicode-NFC. Redaktionelle Navigationslinks, Fußnotenverknüpfungen und generische Tabellenspaltenköpfe werden gesondert behandelt. Inhaltliche Tabellenüberschriften und sämtliche Originalzellen werden vollständig verglichen. Komplexe Tabellen bleiben als HTML mit verbundenen Zellen im Markdown; die Quelldateien sind unverändert.

## Nachgewiesene PDF-Layoutunterschiede

- **§ 55**: Tabellenkopf-Lesereihenfolge und/oder Wiederholung am Seitenumbruch. Anschließend ist der gesamte restliche Normtext zeichenidentisch.

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
| Bereitgestellte und aktuell abgerufene PDF | `66cdeb9a11787c752b11eae99bb99a6e0784109f7b83b820b512a6a8e0700c9f` |
| XML | `917f896d8d11e0e1be257e284495ccb789e95497e238a4d9604ea62d81e764a9` |
| Markdown | `f88fd1a916e9f3ce936a0e1267502a186afc1752818941327109605b1e7ab616` |
