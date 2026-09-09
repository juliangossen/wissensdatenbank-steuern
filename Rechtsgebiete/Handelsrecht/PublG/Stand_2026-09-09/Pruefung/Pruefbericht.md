# Prüfbericht: PublG

**Ergebnis:** Alle 29 XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.

## Quellen und Fassungsstand

Quellenabgleich **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/publg/BJNR011890969.html). Die bereitgestellte PDF (`PublG.pdf`, 13 Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.

"Publizitätsgesetz vom 15. August 1969 (BGBl. I S. 1189), das zuletzt durch Artikel 59 des Gesetzes vom 10. August 2021 (BGBl. I S. 3436) geändert worden ist"

- Zuletzt geändert durch Art. 59 G v. 10.8.2021 I 3436

## Vollständigkeitsnachweis

| Gegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 29 vollständig |
| PDF/XML | 29 unmittelbar identisch; 0 gezielt bestätigte Druck-/Layoutfälle |
| Konvertierte Textblöcke | 66 zeichengenau identisch |
| Tabellen | 0 |
| Tabellenzeilen und -zellen | 0 Zeilen; 0 Zellen vollständig und in Reihenfolge |
| XML-Formelbilder | 0 vollständig eingebettet |
| Interne Links | 26 mit vorhandenen eindeutigen Zielen |

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).

Verglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.

## Besonderheiten

Keine weiteren Ausnahmen vom vollständigen Zeichenvergleich.

## Reproduzierbarkeit

Konvertierung aus dem Hauptverzeichnis:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Handelsrecht/PublG/Stand_2026-09-09/Pruefung/konfiguration.json
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
| Markdown | `a220b405638704cfd353c5e98dc2fe5289653200bc212fa7d1d554793a91a0ee` |
| Original-PDF | `edd500689b70acc24120f81b1965c24c38a6a9779f1ea819a341b2acd84c6876` |
| XML | `fe2485fe7430aa9c33eef976d9f277231e819de054976dbe0eda9dd0e5ceca4a` |

[Alle Quellfingerabdrücke](Quellenabgleich.json).
