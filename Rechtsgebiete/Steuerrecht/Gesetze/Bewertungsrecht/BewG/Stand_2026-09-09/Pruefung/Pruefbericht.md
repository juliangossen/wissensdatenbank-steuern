# Prüfbericht – Bewertungsgesetz (BewG)

**Ergebnis: vollständig in Markdown übernommen und geprüft.** Quellenabgleich: 09.09.2026.

Die bereitgestellte Datei `BewG.pdf` ist bytegleich mit der am Prüftag abgerufenen [PDF-Gesamtausgabe](https://www.gesetze-im-internet.de/bewg/BewG.pdf). Alle 174 Seiten und 272 XML-Normdatensätze sind berücksichtigt. Die unveränderte XML-Gesamtausgabe stammt von derselben offiziellen Gesetzesseite.



## Stand und Quellen

"Bewertungsgesetz in der Fassung der Bekanntmachung vom 1. Februar 1991 (BGBl. I S. 230), das zuletzt durch Artikel 19 des Gesetzes vom 22. Juni 2026 (BGBl. 2026 I Nr. 192) geändert worden ist"

- Neugefasst durch Bek. v. 1.2.1991 I 230; zuletzt geändert durch Art. 19 G v. 22.6.2026 I Nr. 192

Das Ordnerdatum bezeichnet die Erfassung und Quellenprüfung. Es bestätigt kein einheitliches Inkrafttretensdatum. Sämtliche dokumentarischen Hinweise und Anwendungsvorschriften stehen im Volltext.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 272 |
| Gliederungsteile | 66 |
| Vorschriftendatensätze | 169 einschließlich weggefallener Normen und ggf. zusammengefasster Bereiche |
| Anlagen/Anhänge | 35 |
| Tabellen | 121 mit 2768 Zeilen und 17209 Zellen |
| Aufzählungskennzeichen | 281 |
| Originalabbildungen | 20 |
| XML gegen gerendertes Markdown | 689 Text-, Fußnoten-, Gliederungs- und Überschriftenblöcke identisch |
| Unabhängige Markdown-Strukturprüfung | 271 vollständige Normabschnitte nach dem Dokumentkopf sowie jede Tabellenzelle in Originalreihenfolge identisch |
| Interne Links | Alle 377 Ziele vorhanden; keine doppelten Anker |

## PDF-Layout und Quellenbesonderheiten

250 von 272 Normdatensätzen stimmen unmittelbar überein. In der Inhaltsübersicht und 21 Anlagen bestehen ausschließlich nachgewiesene Layoutunterschiede. Der spezielle Tabellenprüfer konsumiert jede nichtleere XML-Zelle genau einmal mit identischem Text. Reine Zahlen, Prozentwerte und Wertebereiche ohne Zeilenverbund behalten in jeder Datenzeile ihre Spaltenfolge. Andere Zellen dürfen nur innerhalb der durch ihre XML-Zeilenspanne belegten Zeilen in abweichender Druckreihenfolge auftreten.

Wiederholte Tabellenköpfe werden nur als exakte Wiederholung des vollständig geprüften Originalkopfs entfernt. Geteilte Zellen werden nur an XML-Zeilenumbrüchen oder unabhängig extrahierten physischen PDF-Zeilenenden zusammengesetzt. Der Umbruch „Gäste-WC“ auf Seiten 127/128 ist gesondert belegt. Manuelle Fußnoten werden für den PDF-Vergleich an ihrer XML-FnArea-Druckposition berücksichtigt. Jede Umordnung, Kopf-Wiederholung und Zellteilung steht in `PDF_XML_Abgleich.json`; keine inhaltliche Abweichung wird pauschal ausgenommen.

## Prüfmethoden und Reproduzierbarkeit

Der PDF/XML-Abgleich normalisiert Unicode-NFC, Leerraum und unsichtbare weiche Trennzeichen. Wiederkehrende PDF-Servicezeilen und Seitennummern werden entfernt. Fußnotenmarker stammen aus den XML-Attributen; der technische Marker `(XXXX)` wird wie im PDF nicht als Normbezeichnung ausgegeben. Alle übrigen Abweichungen sind einzeln nachgewiesen.

Der XML/Markdown-Abgleich vergleicht jedes gerenderte Inhaltssegment zeichengetreu nach NFC- und Leerraumnormalisierung. Nur ausdrücklich redaktionelle Fußnotenverknüpfungen und generische Spaltenüberschriften werden vom Vergleich ausgenommen. Ein zweiter Prüfer untersucht unabhängig davon jeden vollständigen Normabschnitt, die Normreihenfolge und jede einzelne Tabellenzelle. Komplexe Tabellen behalten verbundene Zellen als HTML im Markdown.

Erforderlich: Python 3, `markdown-it-py`, Poppler `pdftotext` im PATH; für die zusätzliche BewG-Bildprüfung `PyMuPDF`. Die archivierten Prüfer arbeiten ohne Netzwerkzugriff. Aufruf aus dem Standordner:

```powershell
py Pruefung/konvertieren.py
py Pruefung/markdown_struktur_pruefen.py
py Pruefung/pdf_xml_pruefen.py
```

- [Konfiguration](konfiguration.json): Quellenpfade, Fassungsangaben und Hashes.
- [Vollständigkeitsprüfung](Vollstaendigkeitspruefung.json): jeder XML/Markdown-Inhaltsblock.
- [Markdown-Strukturprüfung](Markdown_Strukturpruefung.json): vollständige Normabschnitte und Tabellen.
- [Normenbestand](Normenbestand.json): vollständiges Normverzeichnis und Originalkennungen.
- [PDF/XML-Abgleich](PDF_XML_Abgleich.json): alle PDF-Seiten und XML-Normdatensätze.

- [Bildprüfung](Bildpruefung.json): alle 20 JPEG-Bildvorkommen in PDF und XML-Paket in Originalreihenfolge bytegleich.
- [Visuelle Prüfung](Visuelle_Pruefung/Sichtpruefung.md): Tabellen, verbundene Zellen und Hausquerschnitte auf PDF-Seiten 73, 74, 120, 121, 159 und 160.

## SHA-256-Prüfsummen

| Datei | SHA-256 |
| --- | --- |
| Original-PDF und am Prüftag abgerufene PDF | `554fcacb1c36a889d78d4888ba1ef4fe7d0508c81c7d8b24b8f65d4f6ababb82` |
| XML | `579c8ebeb7f1daec155d201715a7e4fa26d7a9833c21915489887bf70b4ecdc9` |
| Markdown | `4cebe531b049939d67fe010e9d31e0cf5b0833605ba5af58e967dda6225154ee` |
