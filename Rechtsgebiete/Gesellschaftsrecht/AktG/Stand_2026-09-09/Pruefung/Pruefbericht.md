# Prüfbericht: AktG

**Ergebnis:** Alle 463 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/aktg/BJNR010890965.html). Die bereitgestellte PDF (`AktG.pdf`, 131 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Aktiengesetz vom 6. September 1965 (BGBl. I S. 1089), das zuletzt durch Artikel 23 des Gesetzes vom 4. Februar 2026 (BGBl. 2026 I Nr. 33) geändert worden ist"

- Zuletzt geändert durch Art. 23 G v. 4.2.2026 I Nr. 33

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 463 vollständig |
| PDF/XML | 463 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 1009 zeichengenau identisch |
| Tabellen | 3 |
| Tabellenzeilen und -zellen | 80 Zeilen; 366 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 395 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Keine weiteren Ausnahmen vom vollständigen Zeichenvergleich.

## Reproduzierbarkeit

Konvertierung aus dem Hauptverzeichnis:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Gesellschaftsrecht/AktG/Stand_2026-09-09/Pruefung/konfiguration.json
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
| Markdown | `6142b561f746eaad9bd230899e453bfd39d8860bf100d0d3c08697f98c242e89` |
| Original-PDF | `791f5e6e371a0e2eeb8eb92c281065147fba54e4329444728427f58c27a01bd0` |
| XML | `8225725c9f6eaf61f4426b2a4fead02eb35c1e94794f4c02b1ea2af9277921ea` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).
