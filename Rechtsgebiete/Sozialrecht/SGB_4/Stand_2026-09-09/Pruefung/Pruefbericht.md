# Prüfbericht: SGB_4

**Ergebnis:** Alle 244 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/sgb_4/BJNR138450976.html). Die bereitgestellte PDF (`SGB_4.pdf`, 105 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Das Vierte Buch Sozialgesetzbuch – Gemeinsame Vorschriften für die Sozialversicherung – in der Fassung der Bekanntmachung vom 12. November 2009 (BGBl. I S. 3710, 3973; 2011 I S. 363), das zuletzt durch Artikel 2 des Gesetzes vom 24. Juli 2026 (BGBl. 2026 I Nr. 228) geändert worden ist"

- Neugefasst durch Bek. v. 12.11.2009 I 3710, 3973; 2011 I 363;
- zuletzt geändert durch Art. 2 G v. 24.7.2026 I Nr. 228

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 244 vollständig |
| PDF/XML | 243 unmittelbar identisch; 1 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 525 zeichengenau identisch |
| Tabellen | 31 |
| Tabellenzeilen und -zellen | 226 Zeilen; 453 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 2 vollständig eingebettet |
| Interne Links | 424 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

**Anhang EV:** Ein Auslassungszeichen: XML enthält drei Punkte, PDF das einzelne typografische Zeichen U+2026. Originalseite 105 visuell geprüft. Keine Textauslassung.

Alle 2 aus XML referenzierten Formelbilder wurden unverändert archiviert und lokal eingebettet; die Originalabbildungen wurden visuell geprüft.

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
| Markdown | `e875d25135309eba67cc634af8700d91e748e976ee8720a5d52e502d739efff9` |
| Original-PDF | `eb2891e82029f31a8332f6f6f13a1e47027f62672e8a008fd8d6dbaa605ca2b4` |
| XML | `ec8703c7a8601dc8a2597ee35d7d024b4466848cb83d43ac1f8a137c21b13793` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).

[Visuelle Quellenkontrolle](Visuelle_Pruefung/Sichtpruefung.md).

[Bildvergleich zur Original-PDF](Bildpruefung.json).
