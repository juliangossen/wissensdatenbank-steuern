# Prüfbericht: StBVV

**Ergebnis:** Alle 58 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/stbgebv/BJNR014420981.html). Die bereitgestellte PDF (`StBVV.pdf`, 25 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Steuerberatervergütungsverordnung vom 17. Dezember 1981 (BGBl. I S. 1442), die zuletzt durch Artikel 5 der Verordnung vom 19. Dezember 2025 (BGBl. 2025 I Nr. 372) geändert worden ist"

- Zuletzt geändert durch Art. 5 V v. 19.12.2025 I Nr. 372

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 58 vollständig |
| PDF/XML | 53 unmittelbar identisch; 5 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 120 zeichengenau identisch |
| Tabellen | 31 |
| Tabellenzeilen und -zellen | 448 Zeilen; 975 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 94 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

**§ 24:** 22 linke Tabellenkennzeichnungen werden von pdftotext nach statt vor dem ersten Textblock der jeweiligen Zeile ausgegeben. Jede Kennzeichnung in XML einmal, im PDF einmal und durch genau ein Verschiebungspaar nachgewiesen. Alle übrigen Textzeichen und Zahlen stimmen in gleicher Reihenfolge überein.

**Anlage 1:** Nur wiederholte Original-Tabellenköpfe nach Seiten- oder Spaltenumbrüchen. Sämtliche Zahlen und übrigen Zeichen in gleicher Reihenfolge identisch. Die zusätzlichen Köpfe sind wortgleich mit den im XML enthaltenen Tabellenköpfen.

**Anlage 2:** Nur wiederholte Original-Tabellenköpfe nach Seiten- oder Spaltenumbrüchen. Sämtliche Zahlen und übrigen Zeichen in gleicher Reihenfolge identisch. Die zusätzlichen Köpfe sind wortgleich mit den im XML enthaltenen Tabellenköpfen.

**Anlage 3:** Nur wiederholte Original-Tabellenköpfe nach Seiten- oder Spaltenumbrüchen. Sämtliche Zahlen und übrigen Zeichen in gleicher Reihenfolge identisch. Die zusätzlichen Köpfe sind wortgleich mit den im XML enthaltenen Tabellenköpfen.

**Anlage 4:** Nur wiederholte Original-Tabellenköpfe nach Seiten- oder Spaltenumbrüchen. Sämtliche Zahlen und übrigen Zeichen in gleicher Reihenfolge identisch. Die zusätzlichen Köpfe sind wortgleich mit den im XML enthaltenen Tabellenköpfen.

## Reproduzierbarkeit

Konvertierung aus dem Hauptverzeichnis:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Steuerrecht/Berufsrecht/StBVV/Stand_2026-09-09/Pruefung/konfiguration.json
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
| Markdown | `6512e74b49dfe8c940b1133527481535fd69bf4eb3e2697ce16045fe2f824aea` |
| Original-PDF | `a19bb551e4ba0d59c9b9de68855ace5af19a62bb3299f0eefcb02bddad1969c1` |
| XML | `4f5f7fd53313217733c7785516a272b25384306f86b1f1f7ab574e13f8151608` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).

[Visuelle Quellenkontrolle](Sichtpruefung/Sichtpruefung.md).
