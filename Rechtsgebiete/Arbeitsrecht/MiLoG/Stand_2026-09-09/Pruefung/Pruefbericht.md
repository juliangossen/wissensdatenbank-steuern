# Prüfbericht: MiLoG

**Ergebnis:** Alle 32 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/milog/BJNR134810014.html). Die bereitgestellte PDF (`MiLoG.pdf`, 11 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Mindestlohngesetz vom 11. August 2014 (BGBl. I S. 1348), das zuletzt durch Artikel 8 Absatz 3 des Gesetzes vom 12. Mai 2026 (BGBl. 2026 I Nr. 137) geändert worden ist"

- Zuletzt geändert durch Art. 8 Abs. 3 G v. 12.5.2026 I Nr. 137

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 32 vollständig |
| PDF/XML | 32 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 65 zeichengenau identisch |
| Tabellen | 5 |
| Tabellenzeilen und -zellen | 24 Zeilen; 48 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 50 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Keine weiteren Ausnahmen vom vollständigen Zeichenvergleich.

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
| Markdown | `cfea35f837dc58d9c0ee7e1f6064c897406eb4489b7a7c2ffe9ba922593b0a14` |
| Original-PDF | `738f2e35b2c7c3a47b2f8dc31407420b8671ca0d0fdf04a24bdb833adf31949e` |
| XML | `f9133387b010444d85b54e6473e3f5d57aab3553cc2125422aa2da49cbde51f3` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).
