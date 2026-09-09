# Prüfbericht zur UStG-Markdown-Fassung

Prüfdatum: **09.09.2026**. Ergebnis: Der Inhalt der bereitgestellten PDF wurde vollständig in die [Markdown-Fassung](../UStG.md) übernommen. Die Prüfungen ergaben keine inhaltlichen Auslassungen oder Änderungen.

## Quellen und dokumentierter Änderungsstand

Die ursprünglich bereitgestellte Datei `UStG.pdf` umfasst 98 Seiten. Die archivierte [Quellenkopie](../Quellen/UStG.pdf) und die am Prüftag abgerufene [PDF-Gesamtausgabe bei Gesetze im Internet](https://www.gesetze-im-internet.de/ustg_1980/UStG.pdf) sind bytegleich.

Das Vollzitat und die Standangabe stimmen mit der [HTML-Gesamtausgabe](https://www.gesetze-im-internet.de/ustg_1980/BJNR119530979.html) überein: zuletzt geändert durch Artikel 5 des Gesetzes vom 29. Juni 2026 (BGBl. 2026 I Nr. 197). Im Kopf der Quelle wird keine noch ausstehende Einarbeitung weiterer Änderungen ausgewiesen. Das Datum des Quellenabgleichs wird getrennt vom Änderungsdatum dokumentiert; zur Bedeutung der Standangabe siehe die [Hinweise von Gesetze im Internet](https://www.gesetze-im-internet.de/hinweise.html).

Das [XML-Paket](../Quellen/UStG.xml.zip) wurde von `https://www.gesetze-im-internet.de/ustg_1980/xml.zip` abgerufen. Die enthaltene [XML-Datei](../Quellen/XML/BJNR119530979.xml) trägt die Erstellungskennung `20260831215512` und dient als strukturierte Grundlage der Markdown-Konvertierung.

| Quelle | SHA-256 |
| --- | --- |
| PDF, lokal und online identisch | `33f6390556be7dcbfd52c2a3fc68ea95e877276b73d69a7c8ced6e59e3f0aac6` |
| XML | `d25fccc9b7c1a7bec9fcfce55b5400ea521f818adfdbe9452ab9fcfd8d98f777` |

Die Prüfsumme der erzeugten Markdown-Datei steht im [maschinenlesbaren Konvertierungsbericht](Vollstaendigkeitspruefung.json).

## Vollständigkeit PDF gegen XML

Alle 102 XML-Normdatensätze wurden gegen den vollständigen PDF-Text verglichen. Erfasst wurden Gesetzeskopf-Fußnoten, Inhaltsübersicht, Abschnittstitel, Paragraphen mit Überschriften, Fußnoten und sämtliche Anlagen. Vollzitat, Ausfertigungsdatum und Standangaben wurden zusätzlich separat abgeglichen.

99 Datensätze stimmen nach Vereinheitlichung von Unicode und Leerraum sowie Entfernung wiederkehrender PDF-Servicezeilen und Seitennummern vollständig überein. Die drei übrigen Datensätze wurden gesondert geprüft:

- **Anlage 2:** Die PDF-Textextraktion gibt elf vertikal angeordnete laufende Nummern an versetzter Position aus. Die Nummern `1, 5, 10, 14, 26, 40, 48, 49, 52, 54, 55` wurden in beiden Quellen jeweils einmal nachgewiesen. Nach isolierter Herausnahme dieser Nummern ist der gesamte übrige Text zeichen- und reihenfolgegleich.
- **Anlage 3:** Nach Entfernung genau eines am Seitenumbruch wiederholten Tabellenkopfs vollständige Übereinstimmung.
- **Anlage 4:** Nach Entfernung genau eines am Seitenumbruch wiederholten Tabellenkopfs vollständige Übereinstimmung.

Alle vier Fundstellenhinweise in den XML-Elementen `noindex/kommentar` zu Anlagen 2–5 wurden mitverglichen und übernommen. Anlage 5 einschließlich sämtlicher Berechnungsschemata stimmt vollständig überein.

Prüfprogramm: [pdf_xml_pruefen.py](pdf_xml_pruefen.py). Detailliertes Ergebnis: [PDF_XML_Abgleich.json](PDF_XML_Abgleich.json).

## Vollständigkeit XML gegen Markdown

Das Konvertierungsprogramm verarbeitet sämtliche Textknoten einschließlich verschachtelter Aufzählungen, Absatzkennzeichnungen, Fundstellen, Fußnoten und Tabellen. Unbekannte Inhaltselemente führen zum Abbruch. Jede Überschrift und jeder Inhalts- bzw. Fußnotenblock wird aus dem erzeugten Markdown zurück in sichtbaren Text überführt und mit dem XML-Text verglichen. Dabei werden nur Leerraum und ausdrücklich ergänzte Tabellenüberschriften ausgenommen; alle sonstigen Zeichen einschließlich Satzzeichen und Zahlen müssen übereinstimmen.

| Geprüfter Umfang | Ergebnis |
| --- | --- |
| XML-Normdatensätze | 102 |
| Abschnitte | 7 |
| Paragraphen einschließlich weggefallener Vorschriften | 88 |
| Anlagen einschließlich weggefallener Anlage 1 | 5 |
| Tabellen einschließlich Inhaltsübersicht und Berechnungsschemata | 7 |
| Original-Tabellenzeilen einschließlich Originalkopfzeilen | 255 |
| Original-Tabellenzellen | 680 |
| Nummern-/Buchstabenkennzeichnungen in XML-Aufzählungen | 831 |
| Rückverglichene Text-, Fußnoten- und Überschriftenblöcke | 225, ohne Textabweichung |
| Interne Navigationslinks | 103, alle Ziele vorhanden |

Die Ergebnisse mit Prüfsummen je Textblock stehen in [Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json).

Eine unabhängige Prüfung der gespeicherten Markdown-Datei bestätigt außerdem die korrekte Listenebene sämtlicher Textzeichen und die unveränderten Wortgrenzen in allen 88 Paragraphen. Sämtliche Zellen der sechs Anlagentabellen stimmen nach Auflösung verbundener Zellen mit der XML-Vorlage überein. Es gibt keine unbeabsichtigten Codeblöcke oder sichtbaren Markdown-Syntaxreste. Der einzige ausdrücklich formatierte Textblock enthält die allgemeine Gesetzesfußnote. Details: [Markdown_Strukturpruefung.json](Markdown_Strukturpruefung.json).

## Darstellung und redaktionelle Ergänzungen

Die Markdown-Datei enthält ein verlinktes Inhaltsverzeichnis, Abschnitts- und Paragraphenüberschriften sowie stabile Sprungmarken. Gesetzliche Kennzeichnungen werden wörtlich beibehalten; für Aufzählungen werden feste Nummern und Buchstaben verwendet, damit Markdown-Programme sie nicht automatisch umnummerieren.

Anlagentabellen behalten ihre Warenbezeichnungen und Zolltarifzuordnungen. Leere Fortsetzungszellen ersetzen verbundene Zellen. In der Inhaltsübersicht stehen Beschreibungen einheitlich in der Spalte „Inhalt“. Die drei Berechnungstabellen aus Anlage 5 erhalten die zusätzlichen Spaltenüberschriften „Rechenzeichen“ und „Rechengröße“.

Entfernt wurden ausschließlich wiederkehrende PDF-Servicezeilen, Seitennummern und wiederholte Tabellenköpfe an Seitenumbrüchen. Harte Zeilen- und Seitenumbrüche werden durch absatzgerechte Markdown-Struktur ersetzt. Die bereitgestellte Ausgangsdatei wurde nicht verändert.

## Reproduzierbarkeit

Die Scripte verwenden ausschließlich die archivierten Quellen. Sie aktualisieren das Gesetz nicht über das Netzwerk.

Vom Ordner `Pruefung` aus:

```powershell
py konvertieren.py
py pdf_xml_pruefen.py
py markdown_struktur_pruefen.py
```

Voraussetzungen: Python 3, `markdown-it-py` für die Konvertierung und den Markdown-Rückvergleich sowie Poppler `pdftotext` für den PDF/XML-Abgleich.
