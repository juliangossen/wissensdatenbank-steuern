# Prüfbericht: StBerG

**Ergebnis:** Alle 270 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/stberg/BJNR013010961.html). Die bereitgestellte PDF (`StBerG.pdf`, 89 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Steuerberatungsgesetz in der Fassung der Bekanntmachung vom 4. November 1975 (BGBl. I S. 2735), das zuletzt durch Artikel 1 des Gesetzes vom 29. Juni 2026 (BGBl. 2026 I Nr. 197) geändert worden ist"

- Neugefasst durch Bek. v. 4.11.1975 I 2735;
- zuletzt geändert durch Art. 1 G v. 29.6.2026 I Nr. 197

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 270 vollständig |
| PDF/XML | 270 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 573 zeichengenau identisch |
| Tabellen | 29 |
| Tabellenzeilen und -zellen | 306 Zeilen; 600 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 466 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Keine weiteren Ausnahmen vom vollständigen Zeichenvergleich.

## Reproduzierbarkeit

Konvertierung aus dem Hauptverzeichnis:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Steuerrecht/Berufsrecht/StBerG/Stand_2026-09-09/Pruefung/konfiguration.json
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
| Markdown | `ae04fbe1c7cb38a2f5d9b92518e3741d99176992486dd300c4f8bcf138190e73` |
| Original-PDF | `3a1c32085f44a6f4732586160269b4ee042ef9c926e96f6627ec354fc5861c29` |
| XML | `90fca87d08696e54c5b5b39f6dc961b890220f051ace6f66d314d3c91e266d37` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).
