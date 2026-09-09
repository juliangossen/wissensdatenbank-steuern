# Prüfbericht: GewO

**Ergebnis:** Der Gesetzesvolltext wurde vollständig aus der archivierten GII-XML übernommen. Alle 194 Normdatensätze einschließlich Dokumentkopf, Gliederungen, Vorschriften und Anlagen sind nachgewiesen. Sämtliche fertigen Markdown-Normtexte, Tabellenzellen und internen Verweise haben die unabhängigen Prüfungen bestanden.

## Quellen und Fassungsstand

Quellenabgleich am **09.09.2026** mit [Gesetze im Internet](https://www.gesetze-im-internet.de/gewo/). Die bereitgestellte PDF und die am Prüftag abgerufene PDF sind bytegleich (SHA-256) und enthalten denselben extrahierten Text. Die Gesamtausgabe umfasst **86 Seiten**. PDF, XML-Quellenpaket, entpackte XML und HTML wurden unverändert unter [Quellen](../Quellen/README.md) archiviert.

**Vollzitat der Quelle:**

"Gewerbeordnung in der Fassung der Bekanntmachung vom 22. Februar 1999 (BGBl. I S. 202), die zuletzt durch Artikel 1 des Gesetzes vom 20. Juli 2026 (BGBl. 2026 I Nr. 215) geändert worden ist"

**Vollständige Stand- und Bearbeitungshinweise der Quelle:**

- Neugefasst durch Bek. v. 22.2.1999 I 202
- Zuletzt geändert durch Art. 1 G v. 20.7.2026 I Nr. 215

Das Datum des Stand-Ordners ist das Datum des Quellenabgleichs. Es ersetzt nicht die im Gesetz genannten Anwendungs-, Übergangs- oder Inkrafttretensregelungen.

## Vollständigkeitsnachweis

| Prüfgegenstand | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 194 vollständig und in Originalreihenfolge |
| Vorschriften-Datensätze | 170 einschließlich weggefallener Vorschriften und Sammelüberschriften |
| Gliederungsteile | 21 |
| Anlagen und Anhänge | 1 |
| Tabellen | 2 mit 209 Originalzeilen und 370 Originalzellen |
| Aufzählungskennzeichnungen | 742 |
| Eingebettete Fußnotenverweise | 0, Kennzeichnung und Zuordnung vollständig erhalten |
| Konvertierungsprüfung | 400 Inhalts-, Fußnoten- und Überschriftsblöcke zeichengenau rückverglichen |
| Unabhängiger Gesamtdateivergleich | Alle 194 vollständigen Normtexte identisch |
| Interne Links | 173; sämtliche Ziele vorhanden, keine doppelten Anker |

„Vorschriften-Datensatz“ bezeichnet eine Einzel- oder Sammelüberschrift der Quelle. Eine Sammelüberschrift wie „§§ 3 bis 6“ zählt einmal; auch aufgehobene Vorschriften und ihre Hinweise sind enthalten. Der [Normbestand](Normbestand.json) weist jeden Datensatz mit Quell-ID, Bezeichnung und Textfingerabdruck nach.

Der unabhängige PDF/XML-Vergleich prüft jede vollständige Überschrift, jeden vollständigen Normtext und sämtliche Fußnoten. 194 von 194 Normdatensätzen stimmen nach Entfernung von Whitespace, PDF-Servicezeilen und Seitenzählern vollständig überein. Die Quellmarker aus Fußnotenattributen werden dabei rekonstruiert. Die maschinenlesbaren Ergebnisse stehen in [PDF_XML_Abgleich.json](PDF_XML_Abgleich.json).

Zusätzlich wurden die **fertige Gesamtdatei** erneut gerendert und alle Normabschnitte gegen XML verglichen, einschließlich Gliederungsüberschriften und Dokumentkopf. Die [Gesamtprüfung](Markdown_Gesamtpruefung.json) bestätigt sämtliche Normtexte und Fußnotenmarker; die [Strukturprüfung](Markdown_Strukturpruefung.json) prüft zusätzlich jede Tabellenzelle in Reihenfolge, alle Tabellen- und Zeilenzahlen sowie alle Sprungmarken. Das sind Vollprüfungen, keine Stichproben.

## Darstellungsregeln

- Whitespace und Unicode-NFC werden nur für den Vergleich vereinheitlicht. Inhaltliche Zeichen und Zahlen bleiben erhalten.
- PDF-Servicezeilen, Seitenzähler und reine wiederholte Tabellenköpfe gehören zur Seitendarstellung und werden im Markdown nicht wiederholt.
- 17 technische XML-Präfixe `(XXXX)` werden vor Normüberschriften ausgeblendet; die zugehörigen Vorschriften und Wegfallhinweise bleiben vollständig erhalten.
- Komplexe Tabellen werden als eingebettete HTML-Tabellen dargestellt, einschließlich verbundener Zellen. Einfache Tabellen erhalten bei Bedarf ausdrücklich generische Spaltenüberschriften.
- Navigation und Prüfmetadaten sind redaktionelle Ergänzungen. Fußnotenmarker werden aus den XML-Attributen übernommen und bleiben mit dem zugehörigen Fußnotentext verbunden.
- In dieser XML-Gesamtausgabe sind keine externen Bilddateien referenziert.

## Reproduzierbarkeit

Konvertierung vom Hauptverzeichnis der Wissensdatenbank aus:

```powershell
py Werkzeuge/gesetz_konvertieren.py --config Rechtsgebiete/Gewerberecht/GewO/Stand_2026-09-09/Pruefung/konfiguration.json
```

Die nachfolgenden Prüfprogramme können aus jedem Arbeitsverzeichnis über ihren Pfad gestartet werden. Ohne Parameter lesen sie die benachbarte `konfiguration.json`:

```powershell
py "Rechtsgebiete/Gewerberecht/GewO/Stand_2026-09-09/Pruefung/pdf_xml_abgleichen.py"
py "Rechtsgebiete/Gewerberecht/GewO/Stand_2026-09-09/Pruefung/markdown_gesamtpruefen.py"
py "Rechtsgebiete/Gewerberecht/GewO/Stand_2026-09-09/Pruefung/markdown_struktur_pruefen.py"
```

Voraussetzungen: Python 3; `markdown-it-py` für die Markdown-Prüfung; Poppler `pdftotext` für die PDF-Prüfung. Die Prüfungen arbeiten mit den archivierten Quellen und benötigen keinen Netzwerkzugriff. Die Ergebnisse werden als JSON im Prüfungsordner gespeichert.

## Dateifingerabdrücke

| Datei | SHA-256 |
| --- | --- |
| Markdown | `10fe79f0ad2d92718f5d9db421cdff62d70482774cdf9c80ee51c391c853e117` |
| XML | `9d72811ec7c3d4fb0f030a7696b3ea936a352e1aeee58fc63d83cf7fac4ac561` |
| Bereitgestellte und aktuelle PDF | `d34caed37d1a8af1dffd1032cd911f02358ef438414a5947d68c55986a893845` |

Weitere Quellfingerabdrücke: [Quellenabgleich.json](Quellenabgleich.json). Der detaillierte blockweise Rückvergleich steht in [Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json).
