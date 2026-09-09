# Prüfbericht: GmbHG

**Ergebnis:** Alle 135 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/gmbhg/BJNR004770892.html). Die bereitgestellte PDF (`GmbHG.pdf`, 36 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Gesetz betreffend die Gesellschaften mit beschränkter Haftung in der im Bundesgesetzblatt Teil III, Gliederungsnummer 4123-1, veröffentlichten bereinigten Fassung, das zuletzt durch Artikel 21 des Gesetzes vom 23. Oktober 2024 (BGBl. 2024 I Nr. 323) geändert worden ist"

- Zuletzt geändert durch Art. 21 G v. 23.10.2024 I Nr. 323

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 135 vollständig |
| PDF/XML | 135 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 279 zeichengenau identisch |
| Tabellen | 8 |
| Tabellenzeilen und -zellen | 194 Zeilen; 343 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 165 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Anlage 1 enthält im GII-Gesamtdokument einen Dateiverweis. Die mitgelieferte amtliche PDF-Dateianlage wurde zusätzlich vollständig als durchsuchbarer Text und mit beiden Originalformularseiten eingebettet. [Separater Nachweis](Datei_Anlagenpruefung.json). Die HTML-Markierung `data-redaktionell="volltext-aus-xml-dateianhang"` trennt nur den separaten Dateiinhalt vom XML-Textvergleich; der Inhalt wird nicht ausgeblendet.

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
| Markdown | `59ee7970ef3f311408f1d662eaffd30429011dbd3aa7d83822b0471743aa9832` |
| Original-PDF | `81fba1a18a253e6da28f99cfde7d311511a162576082d7ee4e59683c40f127f8` |
| XML | `7edd80dab48bb8e08c548b856d04e9225d7e75af36b986994898857be853681f` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).

[Visuelle Quellenkontrolle](Sichtpruefung.md).
