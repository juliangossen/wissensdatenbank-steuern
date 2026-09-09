# Prüfbericht: DVStB

**Ergebnis:** Alle 61 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/stbdv/BJNR019220979.html). Die bereitgestellte PDF (`DVStB.pdf`, 16 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Verordnung zur Durchführung der Vorschriften über Steuerberater, Steuerbevollmächtigte und Berufsausübungsgesellschaften vom 12. November 1979 (BGBl. I S. 1922), die zuletzt durch Artikel 4 der Verordnung vom 19. Dezember 2025 (BGBl. 2025 I Nr. 372) geändert worden ist"

- Zuletzt geändert durch Art. 4 V v. 19.12.2025 I Nr. 372

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 61 vollständig |
| PDF/XML | 61 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 118 zeichengenau identisch |
| Tabellen | 7 |
| Tabellenzeilen und -zellen | 56 Zeilen; 112 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 102 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Keine weiteren Ausnahmen vom vollständigen Zeichenvergleich.

## Reproduzierbarkeit

Konvertierung aus dem Hauptverzeichnis:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Steuerrecht/Berufsrecht/DVStB/Stand_2026-09-09/Pruefung/konfiguration.json
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
| Markdown | `ab16e0f397df5bdb5602c3e76cf725aae6a1c97c1f617446f740497a4c60f20e` |
| Original-PDF | `ca5e29edaa78e107e69280dd1c5fb635a9bd2e685c5a20b259bd949fe10dcc26` |
| XML | `60be3d993c0c2bb649659db5ab99396acc8ba0efdacd324a299efed4260e76af` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).
