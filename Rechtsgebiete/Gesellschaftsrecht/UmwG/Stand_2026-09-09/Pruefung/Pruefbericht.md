# Prüfbericht: UmwG

**Ergebnis:** Alle 465 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/umwg_1995/BJNR321010994.html). Die bereitgestellte PDF (`UmwG.pdf`, 86 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Umwandlungsgesetz vom 28. Oktober 1994 (BGBl. I S. 3210; 1995 I S. 428), das zuletzt durch Artikel 17 des Gesetzes vom 23. Oktober 2024 (BGBl. 2024 I Nr. 323) geändert worden ist"

- Zuletzt geändert durch Art. 17 G v. 23.10.2024 I Nr. 323

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 465 vollständig |
| PDF/XML | 465 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 1021 zeichengenau identisch |
| Tabellen | 1 |
| Tabellenzeilen und -zellen | 127 Zeilen; 433 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 378 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Keine weiteren Ausnahmen vom vollständigen Zeichenvergleich.

## Reproduzierbarkeit

Konvertierung aus dem Hauptverzeichnis:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Gesellschaftsrecht/UmwG/Stand_2026-09-09/Pruefung/konfiguration.json
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
| Markdown | `add76756f3e623f922da50622ef52a0f87bed5958fd92b325fa25ed3143635f5` |
| Original-PDF | `18daee2bd1423c97bb8c36295b8d53060433cf0fbf9600e96b382f06ac4c8f9e` |
| XML | `211ff91490d17f3570cd749c5eebf2cc7fc8a29c31c061cff6abadb0f2fba03f` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).
