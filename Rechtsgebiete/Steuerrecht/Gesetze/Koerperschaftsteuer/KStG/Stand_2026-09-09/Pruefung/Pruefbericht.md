# Prüfbericht – Körperschaftsteuergesetz (KStG)

**Ergebnis: vollständig übernommen und geprüft.** Quellenabgleich: **09.09.2026**.

Die bereitgestellte Datei `KStG.pdf` ist bytegleich mit der am Prüftag von [Gesetze im Internet](https://www.gesetze-im-internet.de/kstg_1977/) abgerufenen PDF-Gesamtausgabe. Alle 48 PDF-Seiten und sämtliche 60 XML-Normdatensätze wurden im Textvergleich berücksichtigt. Die strukturierte Wiedergabe beruht auf der zugehörigen, unverändert archivierten XML-Gesamtausgabe.

## Stand und Quellen

"Körperschaftsteuergesetz in der Fassung der Bekanntmachung vom 15. Oktober 2002 (BGBl. I S. 4144), das zuletzt durch Artikel 30 des Gesetzes vom 4. Februar 2026 (BGBl. 2026 I Nr. 33) geändert worden ist"

- Neugefasst durch Bek. v. 15.10.2002 I 4144;
- zuletzt geändert durch Art. 30 G v. 4.2.2026 I Nr. 33

Das Ordnerdatum bezeichnet den Quellenabgleich. Es ist kein einheitliches Inkrafttretensdatum der einzelnen Vorschriften. Anwendungsvorschriften und dokumentarische Hinweise bleiben im Gesetzestext erhalten.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 60 vollständig |
| Gliederungsteile | 10 |
| Vorschriftendatensätze | 48 einschließlich weggefallener Vorschriften und zusammengefasster Bereiche |
| Anlagendatensätze | 0 einschließlich ggf. zusammengefasster weggefallener Anlagen |
| Tabellen | 2 mit 87 Originalzeilen und 210 Originalzellen |
| Aufzählungskennzeichen | 216 |
| XML gegen gerendertes Markdown | 162 Inhalts-, Fußnoten- und Überschriftenblöcke ohne Textverlust |
| Unabhängige Kontrolle des zusammengesetzten Markdown | Alle 59 Normabschnitte nach dem Dokumentkopf vollständig und in Originalreihenfolge; jede Tabellenzelle einzeln identisch |
| Interne Sprungziele | Alle 51 Verweise gültig, keine doppelten Anker |

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
| Bereitgestellte und aktuell abgerufene PDF | `84799bc3d379dd311ae2d1878f7a4b21b6f7c0793d9c1ecf15d0b1badb57aef4` |
| XML | `26b626af4cdda0710b99b18cca7ea8e7be8e326117d424be18e93dd37c75f36e` |
| Markdown | `292e208dc2dd04610f8a02331a9a93d7232cdf9b5effbd94ab4f650b43ffa364` |
