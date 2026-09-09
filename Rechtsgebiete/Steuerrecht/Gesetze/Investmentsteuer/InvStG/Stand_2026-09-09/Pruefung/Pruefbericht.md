# Prüfbericht – Investmentsteuergesetz (InvStG)

**Ergebnis: vollständig in Markdown übernommen und geprüft; mit dokumentierter Ergänzung aus der amtlichen XML.** Quellenabgleich: 09.09.2026.

Die bereitgestellte Datei `InvStG.pdf` ist bytegleich mit der am Prüftag abgerufenen [PDF-Gesamtausgabe](https://www.gesetze-im-internet.de/invstg_2018/InvStG.pdf). Alle 42 Seiten und 73 XML-Normdatensätze sind berücksichtigt. Die unveränderte XML-Gesamtausgabe stammt von derselben offiziellen Gesetzesseite.

**Dokumentierte Ergänzung:** Auf PDF-Seite 1 ist die lange Anwendungshinweis-Zeile am rechten Seitenrand abgeschnitten. Das Markdown enthält die vollständige Zeile aus der zugehörigen amtlichen XML-Datei. Die 119 im PDF fehlenden Zeichen sind im Prüfbericht einzeln dokumentiert; der übrige Text ist identisch.

## Stand und Quellen

"Investmentsteuergesetz vom 19. Juli 2016 (BGBl. I S. 1730), das zuletzt durch Artikel 28 des Gesetzes vom 4. Februar 2026 (BGBl. 2026 I Nr. 33) geändert worden ist"

- Zuletzt geändert durch Art. 28 G v. 4.2.2026 I Nr. 33 Ersetzt G 610-6-15 v. 15.12.2003 I 2676, 2724 (InvStG)

Das Ordnerdatum bezeichnet die Erfassung und Quellenprüfung. Es bestätigt kein einheitliches Inkrafttretensdatum. Sämtliche dokumentarischen Hinweise und Anwendungsvorschriften stehen im Volltext.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | 73 |
| Gliederungsteile | 13 |
| Vorschriftendatensätze | 58 einschließlich weggefallener Normen und ggf. zusammengefasster Bereiche |
| Anlagen/Anhänge | 0 |
| Tabellen | 11 mit 58 Zeilen und 116 Zellen |
| Aufzählungskennzeichen | 259 |
| Originalabbildungen | 0 |
| XML gegen gerendertes Markdown | 188 Text-, Fußnoten-, Gliederungs- und Überschriftenblöcke identisch |
| Unabhängige Markdown-Strukturprüfung | 72 vollständige Normabschnitte nach dem Dokumentkopf sowie jede Tabellenzelle in Originalreihenfolge identisch |
| Interne Links | Alle 118 Ziele vorhanden; keine doppelten Anker |

## PDF-Layout und Quellenbesonderheiten

Alle Vorschriften und Gliederungen sind unmittelbar identisch. Im Dokumentkopf fehlen im PDF die folgenden **119 Zeichen ohne Leerraum** am rechten Seitenrand:

```text
s.7,41Abs.2,42Abs.1bis3,43Abs.2,43Abs.3,44,45Abs.1,47Abs.4,48Abs.2,48Abs.5,49,50Abs.2,50Abs.3,53Abs.3,53Abs.4,56,57+++)
```

Diese Zeichen werden aus der bytearchivierten amtlichen XML-Gesamtausgabe übernommen. Der [Screenshot von Seite 1](PDF_Seite_001.png) zeigt den abgeschnittenen Anwendungshinweis. Der übrige Text des Dokumentkopfs ist identisch. Das Prüffeld `alle_normen_vollstaendig_gleich` bleibt deshalb ausdrücklich `false`; `abgleich_erfolgreich_mit_dokumentierter_ergaenzung` bezeichnet den erfolgreich abgegrenzten Sonderfall.

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

## SHA-256-Prüfsummen

| Datei | SHA-256 |
| --- | --- |
| Original-PDF und am Prüftag abgerufene PDF | `7571848ce2718b71de2b35ad7f580d0312cbeaa94306ce7324ed336c9b9af54e` |
| XML | `26e468a75bf1be3ddd072f409ffc05a7b51828b0e55e270e1a199dca6d033900` |
| Markdown | `b3a170787e3548396bfc77f74508348957ec30e748c7114c63625f434937a301` |
