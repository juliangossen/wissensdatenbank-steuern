# Prüfbericht: EGBGB

**Ergebnis:** Alle 519 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/bgbeg/BJNR006049896.html). Die bereitgestellte PDF (`EGBGB.pdf`, 154 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Einführungsgesetz zum Bürgerlichen Gesetzbuche in der Fassung der Bekanntmachung vom 21. September 1994 (BGBl. I S. 2494; 1997 I S. 1061), das zuletzt durch Artikel 2 des Gesetzes vom 16. Juli 2026 (BGBl. 2026 I Nr. 212) geändert worden ist"

- Neugefasst durch Bek. v. 21.9.1994 I 2494; 1997, 1061;
- zuletzt geändert durch Art. 1 G v. 2.7.2026 I Nr. 198
- Änderung durch Art. 2 G v. 16.7.2026 I Nr. 212 textlich nachgewiesen, dokumentarisch noch nicht abschließend bearbeitet

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 519 vollständig |
| PDF/XML | 517 unmittelbar identisch; 2 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 1811 zeichengenau identisch |
| Tabellen | 39 |
| Tabellenzeilen und -zellen | 444 Zeilen; 846 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 529 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Die XML wiederholt Gliederungsmetadaten bei untergeordneten Paragraphen. 518 Metadatenvorkommen ergeben 289 verschiedene Gliederungsschlüssel. Artikel, darin enthaltene Paragraphen und Anlagen besitzen eindeutige, vollständige Überschriften und eine gemeinsame Navigation. 21 reine technische Minus-Platzhalter vor Anlagen werden ausgeblendet; die Anlagen bleiben vollständig erhalten.

**Anlage 4:** Ein zusammenhängender Teil der linken Formularzelle wird beim PDF-Textabruf nach der rechten Zelle ausgegeben. Genau derselbe Textblock einmal gelöscht/einmal eingefügt; alle übrigen Zeichen in gleicher Reihenfolge. Zellzuordnung anhand Originalseiten vor und nach dem Seitenumbruch geprüft. Markdown bewahrt XML-Zellen.

**Anlage 5:** Ein zusammenhängender Teil der linken Formularzelle wird beim PDF-Textabruf nach der rechten Zelle ausgegeben. Genau derselbe Textblock einmal gelöscht/einmal eingefügt; alle übrigen Zeichen in gleicher Reihenfolge. Zellzuordnung anhand Originalseiten vor und nach dem Seitenumbruch geprüft. Markdown bewahrt XML-Zellen.

## Reproduzierbarkeit

Konvertierung aus diesem Stand-Ordner:

```powershell
py Pruefung/konvertieren.py --config Pruefung/konfiguration.json
```

Unabhängige Prüfprogramme aus diesem Stand-Ordner:

```powershell
py Pruefung/pdf_xml_abgleichen.py
py Pruefung/markdown_gesamtpruefen.py
py Pruefung/markdown_struktur_pruefen.py
```

Python 3, `markdown-it-py` und Poppler werden benötigt. Die archivierten Quellen genügen; kein neuer Abruf erfolgt.

## Dateifingerabdrücke

| Datei | SHA-256 |
| --- | --- |
| Markdown | `78a18f7715f2f0ecf177f21280676a256bc946d1d887bc90c0a6fbc8be446eb3` |
| Original-PDF | `9a4a0234d93fa68326f8f837af600e010c6f56e59582803d19f3eb028c820f6f` |
| XML | `c57de5f1ae86a97cb57b15e78d7d33dc16c82203bbcf16453385256ff8438a33` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).

[Visuelle Quellenkontrolle](Visuelle_Pruefung/Sichtpruefung.md).
