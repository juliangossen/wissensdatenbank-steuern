# Prüfbericht – Einkommensteuergesetz (EStG)

**Ergebnis: vollständig übernommen und geprüft.** Quellenabgleich: **09.09.2026**.

Die bereitgestellte Datei `EStG.pdf` ist bytegleich mit der am Prüftag von [Gesetze im Internet](https://www.gesetze-im-internet.de/estg/) abgerufenen PDF-Gesamtausgabe. Alle 284 PDF-Seiten und sämtliche 293 XML-Normdatensätze wurden im Textvergleich berücksichtigt. Die strukturierte Wiedergabe beruht auf der zugehörigen, unverändert archivierten XML-Gesamtausgabe.

## Stand und Quellen

"Einkommensteuergesetz in der Fassung der Bekanntmachung vom 8. Oktober 2009 (BGBl. I S. 3366, 3862), das zuletzt durch Artikel 7 des Gesetzes vom 29. Juni 2026 (BGBl. 2026 I Nr. 197) geändert worden ist"

- Neugefasst durch Bek. v. 8.10.2009 I 3366, 3862;
- zuletzt geändert durch Art. 7 G v. 29.6.2026 I Nr. 197

Das Ordnerdatum bezeichnet den Quellenabgleich. Es ist kein einheitliches Inkrafttretensdatum der einzelnen Vorschriften. Anwendungsvorschriften und dokumentarische Hinweise bleiben im Gesetzestext erhalten.

Die Bruchformel in § 35 wurde zusätzlich anhand von PDF-Seite 145 visuell kontrolliert. Der Bruchstrich bleibt in der HTML-Tabelle als untere Zelllinie erhalten; Zähler, Nenner und rechter Multiplikationsfaktor behalten ihre Zuordnung. Die mehrzeiligen Tabellenköpfe des § 19 wurden zusätzlich auf PDF-Seite 102 visuell geprüft.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 293 vollständig |
| Gliederungsteile | 44 |
| Vorschriftendatensätze | 243 einschließlich weggefallener Vorschriften und zusammengefasster Bereiche |
| Anlagendatensätze | 4 einschließlich ggf. zusammengefasster weggefallener Anlagen |
| Tabellen | 65 mit 565 Originalzeilen und 1463 Originalzellen |
| Aufzählungskennzeichen | 1651 |
| XML gegen gerendertes Markdown | 757 Inhalts-, Fußnoten- und Überschriftenblöcke ohne Textverlust |
| Unabhängige Kontrolle des zusammengesetzten Markdown | Alle 292 Normabschnitte nach dem Dokumentkopf vollständig und in Originalreihenfolge; jede Tabellenzelle einzeln identisch |
| Interne Sprungziele | Alle 492 Verweise gültig, keine doppelten Anker |

Der PDF/XML-Abgleich normalisiert ausschließlich Leerraum, Unicode-NFC und unsichtbare weiche Trennzeichen. Fußnotenkennzeichen werden aus den XML-Attributen für den PDF-Vergleich ergänzt. Die technische XML-Kennung `(XXXX)` wird entsprechend der sichtbaren PDF nicht ausgegeben. Alle Wörter, Zahlen, Satzzeichen, Absätze, Fußnotentexte, Anlagen und Tabelleninhalte bleiben erhalten.

Der XML/Markdown-Abgleich normalisiert Leerraum und Unicode-NFC. Redaktionelle Navigationslinks, Fußnotenverknüpfungen und generische Tabellenspaltenköpfe werden gesondert behandelt. Inhaltliche Tabellenüberschriften und sämtliche Originalzellen werden vollständig verglichen. Komplexe Tabellen bleiben als HTML mit verbundenen Zellen im Markdown; die Quelldateien sind unverändert.

## Nachgewiesene PDF-Layoutunterschiede

- **§ 19**: Tabellenkopf-Lesereihenfolge und/oder Wiederholung am Seitenumbruch. Anschließend ist der gesamte restliche Normtext zeichenidentisch.
- **§ 22**: Tabellenkopf-Lesereihenfolge und/oder Wiederholung am Seitenumbruch. Anschließend ist der gesamte restliche Normtext zeichenidentisch.
- **§ 24a**: Tabellenkopf-Lesereihenfolge und/oder Wiederholung am Seitenumbruch. Anschließend ist der gesamte restliche Normtext zeichenidentisch.
- **§ 35**: Bruchformel: PDF liest Zähler/Nenner vor rechtem Faktor; XML zeilenweise. Anschließend ist der gesamte restliche Normtext zeichenidentisch.
- **Anlage 1**: Tabellenkopf-Lesereihenfolge und/oder Wiederholung am Seitenumbruch. Anschließend ist der gesamte restliche Normtext zeichenidentisch.
- **Anlage 1a**: Tabellenkopf-Lesereihenfolge und/oder Wiederholung am Seitenumbruch. Anschließend ist der gesamte restliche Normtext zeichenidentisch.

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
| Bereitgestellte und aktuell abgerufene PDF | `e9480c773127a89216c2439b02534d56321c9174f28f1f4d591afa8b754a5445` |
| XML | `13ff1917a1080a63f1dddb8900a14ba1624f516fa7eb7a547e8bb0f910e2fd5c` |
| Markdown | `5921b1434a854663b898ef0cd762706991404c48e875ee0bf75974b9e54f92a6` |
