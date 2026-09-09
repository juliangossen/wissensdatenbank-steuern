# Prüfbericht: SvEV

**Ergebnis:** Alle 5 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/svev/BJNR338510006.html). Die bereitgestellte PDF (`SvEV.pdf`, 4 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Sozialversicherungsentgeltverordnung vom 21. Dezember 2006 (BGBl. I S. 3385), die zuletzt durch Artikel 11 des Gesetzes vom 16. Januar 2026 (BGBl. 2026 I Nr. 14) geändert worden ist"

- Zuletzt geändert durch Art. 11 G v. 16.1.2026 I Nr. 14

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 5 vollständig |
| PDF/XML | 5 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 9 zeichengenau identisch |
| Tabellen | 0 |
| Tabellenzeilen und -zellen | 0 Zeilen; 0 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 5 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Keine weiteren Ausnahmen vom vollständigen Zeichenvergleich.

## Reproduzierbarkeit

Konvertierung aus dem Hauptverzeichnis:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Sozialrecht/SvEV/Stand_2026-09-09/Pruefung/konfiguration.json
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
| Markdown | `e0944fff35c89e7f871f0fae57a509461c2c87f61bec2fc1a61b35a4c200ef60` |
| Original-PDF | `86636fe5ec430899b8599c8f0acdfb2b248c0f9e0470405aa545eccdb1629fd6` |
| XML | `b91f7481b6632df8ed4fd12fc86da35697d8a27d57ccc46305228f300b39052c` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).
