# Prüfbericht: StGB

**Ergebnis:** Der Gesetzesvolltext wurde vollständig aus der archivierten GII-XML übernommen. Alle 630 Normdatensätze einschließlich Dokumentkopf, Gliederungen, Vorschriften und Anlagen sind nachgewiesen. Sämtliche fertigen Markdown-Normtexte, Tabellenzellen und internen Verweise haben die unabhängigen Prüfungen bestanden.

## Quellen und Fassungsstand

Quellenabgleich am **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/stgb/). Die bereitgestellte PDF und die am Prüftag abgerufene PDF sind bytegleich (SHA-256) und enthalten denselben extrahierten Text. Die Gesamtausgabe umfasst **173 Seiten**. PDF, XML-Quellenpaket, entpackte XML und HTML wurden unverändert unter [Quellen](../Quellen/README.md) archiviert.

**Vollzitat der Quelle:**

"Strafgesetzbuch in der Fassung der Bekanntmachung vom 13. November 1998 (BGBl. I S. 3322), das zuletzt durch Artikel 1 des Gesetzes vom 20. März 2026 (BGBl. 2026 I Nr. 95) geändert worden ist"

**Vollständige Stand- und Bearbeitungshinweise der Quelle:**

- Neugefasst durch Bek. v. 13.11.1998 I 3322;
- zuletzt geändert durch Art. 1 G v. 20.3.2026 I Nr. 95

Das Datum des Stand-Ordners ist das Datum des Quellenabgleichs. Es ersetzt nicht die im Gesetz genannten Anwendungs-, Übergangs- oder Inkrafttretensregelungen.

## Vollständigkeitsnachweis

| Prüfgegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 630 vollständig und in Originalreihenfolge |
| Vorschriften-Datensätze | 562 einschließlich weggefallener Vorschriften und Sammelüberschriften |
| Gliederungsteile | 66 |
| Anlagen und Anhänge | 0 |
| Tabellen | 2 mit 806 Originalzeilen und 2126 Originalzellen |
| Aufzählungskennzeichnungen | 1169 |
| Eingebettete Fußnotenverweise | 1, Kennzeichnung und Zuordnung vollständig erhalten |
| Konvertierungsprüfung | 1347 Inhalts-, Fußnoten- und Überschriftsblöcke zeichengenau rückverglichen |
| Unabhängiger Gesamtdateivergleich | Alle 630 vollständigen Normtexte identisch |
| Interne Links | 565; sämtliche Ziele vorhanden, keine doppelten Anker |

„Vorschriften-Datensatz“ bezeichnet eine Einzel- oder Sammelüberschrift der Quelle. Eine Sammelüberschrift wie „§§ 3 bis 6“ zählt einmal; auch aufgehobene Vorschriften und ihre Hinweise sind enthalten. Der [Normbestand](Normbestand.json) weist jeden Datensatz mit Quell-ID, Bezeichnung und Textfingerabdruck nach.

Der unabhängige PDF/XML-Vergleich prüft jede vollständige Überschrift, jeden vollständigen Normtext und sämtliche Fußnoten. 629 von 630 Normdatensätzen stimmen nach Entfernung von Whitespace, PDF-Servicezeilen und Seitenzählern vollständig überein. Die Quellmarker aus Fußnotenattributen werden dabei rekonstruiert. Die maschinenlesbaren Ergebnisse stehen in [PDF_XML_Abgleich.json](PDF_XML_Abgleich.json).

Zusätzlich wurden die **fertige Gesamtdatei** erneut gerendert und alle Normabschnitte gegen XML verglichen, einschließlich Gliederungsüberschriften und Dokumentkopf. Die [Gesamtprüfung](Markdown_Gesamtpruefung.json) bestätigt sämtliche Normtexte und Fußnotenmarker; die [Strukturprüfung](Markdown_Strukturpruefung.json) prüft zusätzlich jede Tabellenzelle in Reihenfolge, alle Tabellen- und Zeilenzahlen sowie alle Sprungmarken. Das sind Vollprüfungen, keine Stichproben.

## Darstellungsregeln

- Whitespace und Unicode-NFC werden nur für den Vergleich vereinheitlicht. Inhaltliche Zeichen und Zahlen bleiben erhalten.
- PDF-Servicezeilen, Seitenzähler und reine wiederholte Tabellenköpfe gehören zur Seitendarstellung und werden im Markdown nicht wiederholt.
- 9 technische XML-Präfixe `(XXXX)` werden vor Normüberschriften ausgeblendet; die zugehörigen Vorschriften und Wegfallhinweise bleiben vollständig erhalten.
- Komplexe Tabellen werden als eingebettete HTML-Tabellen dargestellt, einschließlich verbundener Zellen. Einfache Tabellen erhalten bei Bedarf ausdrücklich generische Spaltenüberschriften.
- Navigation und Prüfmetadaten sind redaktionelle Ergänzungen. Fußnotenmarker werden aus den XML-Attributen übernommen und bleiben mit dem zugehörigen Fußnotentext verbunden.
- In dieser XML-Gesamtausgabe sind keine externen Bilddateien referenziert.

### Dokumentierte PDF-Extraktionsabweichung in § 127

Im Rohtext der PDF werden vier kombinierende Umlautzeichen vor dem betroffenen Vokal ausgegeben. Betroffen sind „ermöglichen“, „fördern“, „Betäubungsmittelgesetzes“ und „Grundstoffüberwachungsgesetzes“. Die [Originalseite 84 als Prüfbild](StGB_Seite_84.png) wurde visuell kontrolliert. Die XML-Datei enthält die korrekt zugeordneten Zeichen. Nach ausschließlich diesen vier, jeweils einmal vorkommenden Korrekturen stimmt auch dieser Normdatensatz vollständig überein; die exakten Zeichenfolgen, Häufigkeiten und das Ergebnis sind in `PDF_XML_Abgleich.json` gespeichert. Das Markdown übernimmt die XML-Zeichen und sämtliche übrigen Zeichen unverändert.

## Reproduzierbarkeit

Konvertierung vom Hauptverzeichnis der Wissensdatenbank aus:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Strafrecht/StGB/Stand_2026-09-09/Pruefung/konfiguration.json
```

Die nachfolgenden Prüfprogramme können aus jedem Arbeitsverzeichnis über ihren Pfad gestartet werden. Ohne Parameter lesen sie die benachbarte `konfiguration.json`:

```powershell
py "Rechtsgebiete/Strafrecht/StGB/Stand_2026-09-09/Pruefung/pdf_xml_abgleichen.py"
py "Rechtsgebiete/Strafrecht/StGB/Stand_2026-09-09/Pruefung/markdown_gesamtpruefen.py"
py "Rechtsgebiete/Strafrecht/StGB/Stand_2026-09-09/Pruefung/markdown_struktur_pruefen.py"
```

Voraussetzungen: Python 3; `markdown-it-py` für die Markdown-Prüfung; Poppler `pdftotext` für die PDF-Prüfung. Die Prüfungen arbeiten mit den archivierten Quellen und benötigen keinen Netzwerkzugriff. Die Ergebnisse werden als JSON im Prüfungsordner gespeichert.

## Dateifingerabdrücke

| Datei | SHA-256 |
| --- | --- |
| Markdown | `fac86b85519a83e0bcfa5c413301a8373fdc29f21bd456a64c5627ae6ca61b12` |
| XML | `1f2528c072b16ab170fe1baa63100900494f06731ef096f67cb8895894a4fad0` |
| Bereitgestellte und aktuelle PDF | `77b3fdc0b1926f6bbdf50d7b35d00a2f8a4c6ffdb623eca786cd99f08e17e6cc` |

Weitere Quellfingerabdrücke: [Quellenabgleich.json](Quellenabgleich.json). Der detaillierte blockweise Rückvergleich steht in [Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json).
