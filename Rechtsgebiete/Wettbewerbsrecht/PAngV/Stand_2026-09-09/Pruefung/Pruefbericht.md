# Prüfbericht: PAngV

**Ergebnis:** Alle 28 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/pangv_2022/BJNR492110021.html). Die bereitgestellte PDF (`PAngV.pdf`, 13 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Preisangabenverordnung vom 12. November 2021 (BGBl. I S. 4921), die zuletzt durch Artikel 8 des Gesetzes vom 12. Mai 2026 (BGBl. 2026 I Nr. 139) geändert worden ist"

- Zuletzt geändert durch Art. 8 G v. 12.5.2026 I Nr. 139
- Ersetzt V 720-17-1 v. 14.3.1985 I 580 (PAngV)

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 28 vollständig |
| PDF/XML | 28 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 54 zeichengenau identisch |
| Tabellen | 8 |
| Tabellenzeilen und -zellen | 27 Zeilen; 48 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 2 vollständig eingebettet |
| Interne Links | 43 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Alle 2 aus XML referenzierten Formelbilder wurden unverändert archiviert und lokal eingebettet; die Originalabbildungen wurden visuell geprüft.

## Reproduzierbarkeit

Konvertierung aus dem Hauptverzeichnis:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Wettbewerbsrecht/PAngV/Stand_2026-09-09/Pruefung/konfiguration.json
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
| Markdown | `f644c263af7883198b167dfdbf8582d1d6cf598cb431bed71f53ac777cfdca4c` |
| Original-PDF | `fc8d84968214be8c50bf637e6ddf528b6bc09c48f9d599e8df0910287c9f7142` |
| XML | `cdb0bf043b6faa14745c9aa868758b91ee3fc9da2186fe5973436cb80cb42679` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).

[Visuelle Quellenkontrolle](Visuelle_Pruefung/Sichtpruefung.md).

[Bildvergleich zur Original-PDF](Bildpruefung.json).
