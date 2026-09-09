# Prüfbericht – Umsatzsteuer-Durchführungsverordnung (UStDV)

**Ergebnis: vollständig übernommen und geprüft.** Quellenabgleich: **09.09.2026**.

Die bereitgestellte Datei `UStDV.pdf` ist bytegleich mit der am Prüftag von [Gesetze im Internet](https://www.gesetze-im-internet.de/ustdv_1980/) abgerufenen PDF-Gesamtausgabe. Alle 27 PDF-Seiten und sämtliche 108 XML-Normdatensätze wurden im Textvergleich berücksichtigt. Die strukturierte Wiedergabe beruht auf der zugehörigen, unverändert archivierten XML-Gesamtausgabe.

## Stand und Quellen

"Umsatzsteuer-Durchführungsverordnung in der Fassung der Bekanntmachung vom 21. Februar 2005 (BGBl. I S. 434), die zuletzt durch Artikel 7 der Verordnung vom 19. Dezember 2025 (BGBl. 2025 I Nr. 372) geändert worden ist"

- Neugefasst durch Bek. v. 21.2.2005 I 434;
- zuletzt geändert durch Art. 7 V v. 19.12.2025 I Nr. 372

Das Ordnerdatum bezeichnet den Quellenabgleich. Es ist kein einheitliches Inkrafttretensdatum der einzelnen Vorschriften. Anwendungsvorschriften und dokumentarische Hinweise bleiben im Gesetzestext erhalten.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 108 vollständig |
| Gliederungsteile | 29 |
| Vorschriftendatensätze | 76 einschließlich weggefallener Vorschriften und zusammengefasster Bereiche |
| Anlagendatensätze | 1 einschließlich ggf. zusammengefasster weggefallener Anlagen |
| Tabellen | 1 mit 171 Originalzeilen und 298 Originalzellen |
| Aufzählungskennzeichen | 181 |
| XML gegen gerendertes Markdown | 234 Inhalts-, Fußnoten- und Überschriftenblöcke ohne Textverlust |
| Unabhängige Kontrolle des zusammengesetzten Markdown | Alle 107 Normabschnitte nach dem Dokumentkopf vollständig und in Originalreihenfolge; jede Tabellenzelle einzeln identisch |
| Interne Sprungziele | Alle 79 Verweise gültig, keine doppelten Anker |

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
| Bereitgestellte und aktuell abgerufene PDF | `741ee8b7d88bbfece5344c55b32bd26703caf6d2eb302f5e4f0dc753a06a252b` |
| XML | `612198591bd683762cfc2a4998a96978282a2ed8de294fd491c767bb77b5108b` |
| Markdown | `269fb0e5d7eddb2b986c25c8c12f35773d6b69e369729ef84c85a60dea643608` |
