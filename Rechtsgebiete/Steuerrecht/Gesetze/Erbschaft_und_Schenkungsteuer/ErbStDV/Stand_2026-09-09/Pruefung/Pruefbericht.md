# Prüfbericht: ErbStDV-Webkopie nach Markdown

Quelle: vom Nutzer bereitgestellte Datei `ErbStDV.txt`, UTF-8 ohne BOM mit CRLF-Zeilenenden, 1.113 Zeilen (die letzte Zeile ohne Zeilenende), 37.516 Bytes, SHA-256 `dbb708bb0865ed7a3edd3de4a141eb4d6af7cef9f2cd14a7f22fc493de3c7c08`. Zeile 1 ist die Tab-Metazeile der Kopie („Text gilt vom 30.12.2025 bis unbestimmt“); weitere Website-Navigation, Suchmaske, Fassungsliste oder Fußzeile enthält die Kopie nicht. Die unveränderte Quelle liegt unter [Quellen/ErbStDV_Webkopie.txt](../Quellen/ErbStDV_Webkopie.txt); zusätzlich wird sie bytegleich im versionierten Web-Archiv geführt.

## Umfang und Übernahme

Alle 576 nichtleeren Sachtextzeilen von Zeile 2 (Titel) bis Zeile 1.113 (Fußnotentext zu Muster 6) werden genau einmal übernommen; 14 Zeilen, die nur ein Leerzeichen enthalten (Formularabstände in den Mustern), zählen als Leerzeilen. 161 Quellblöcke ordnen die Originalzeilen der Markdown-Datei zu. Jeder Block wird mit `markdown-it-py` gerendert; der sichtbare Text muss nach Entfernung ausschließlich von Leerraum zeichengenau mit den Quellzeilen übereinstimmen. Buchstaben, Ziffern, Satzzeichen, Sonderleerzeichen (U+2004 in Normverweisen, U+2009 als Tausendertrenner), weiche Trennzeichen (U+00AD in den Mustern), Ankreuzkästchen und Punktlinien der Kopie bleiben unverändert. Die Tab-Metazeile (Zeile 1) wird nicht als Text übernommen; sie bleibt in der Originalkopie erhalten.

Die strukturierte Datei enthält den Dokumentkopf (Titel, Kurztitel mit Kopffußnote, Datum, Fundstelle, FNA, Änderungsvermerk), ein redaktionell erzeugtes Inhaltsverzeichnis, den Verordnungstext und die sechs Muster. Erkannt wurden:

| Element | Anzahl | Umsetzung |
| --- | ---: | --- |
| Gliederungsgruppen („Zu § 33 ErbStG“, „Zu § 34 ErbStG“, „Schlußvorschriften“) | 3 | Überschrift Ebene 3 mit Sprungmarke |
| Paragraphen („§ 1 …“ bis „§ 13 …“) | 13 | Überschrift Ebene 4 mit Sprungmarke `par-n`; erkannt nur, wenn die Vorzeile keine Fußnotendefinition ist (33 Fußnotentexte beginnen ebenfalls mit „§ n“) |
| Nummerierte Absätze „(n)“ | 28 | Absatz mit Sprungmarke `par-n-abs-m` |
| Absatztexte ohne Absatznummer (Paragraphen ohne Absätze, Fortsetzungen nach Aufzählungen) | 11 | Absatz |
| Aufzählungen mit angeklebten Nummern („1.wenn …“, „2.[2]wenn …“, „2a.[2]Europäische …“) | 11 (40 Punkte) | Liste ohne Listenzeichen; Nummer, Marker und Text bleiben erhalten, nur ein Leerzeichen wird eingefügt; Sprungmarke `…-nr-k` je Punkt |
| Hochgestellte Satznummern | 48 auf 21 Zeilen | `<sup>`; Regel: ein- bis zweistellige Zahl unmittelbar vor Großbuchstabe, „§“ oder „„“ |
| Muster („Muster 1[1]“ bis „Muster 6[1]“) | 6 | Überschrift Ebene 3 mit Sprungmarke `muster-n`; Bezugszeile „(zu § n ErbStDV)“ als Absatz |
| Binnentitel der Vordrucke („Anzeige“, „Totenliste“, „Anleitung für …“, „Fehlanzeige“) | 5 | Überschrift Ebene 4 |
| Seitenmarker „(Seite 2)“, „(Seite 3)“ in Muster 3 | 2 | eigener Absatz |
| Formularblöcke (Zellen der abgeflachten Vordrucke) | 34 | Absatz mit Zeilenumbrüchen; Blockgrenzen an Positionsnummern („1.“ bis „7.“), Binnentiteln, Seitenmarkern und Fußnoten; Positionsnummern hervorgehoben |
| Sprungmarken insgesamt | 133 | Fußnoten, Gruppen, Paragraphen, Absätze, Aufzählungspunkte, Muster, Navigation |

Alle Strukturentscheidungen stehen mit Quellzeile, Art und Ebene in [Gliederungsentscheidungen.json](Gliederungsentscheidungen.json). Die Fallstricke der Kopie wurden berücksichtigt: Fußnotentexte, die mit „§ n Abs./Satz“ oder „Muster n geänd.“ beginnen, werden nicht als Überschriften erkannt; „2a.“ ist eine Nummer, kein Satz; die Zahl „2“ in „vergangen sind. 2Das gilt nicht …“ (§ 7 Abs. 4 Nr. 4) ist eine Satznummer innerhalb des Aufzählungspunkts; Zeile 202 („zu befragen …“) ist der Rest von § 8 Abs. 1 Satz 3 nach der Aufzählung.

## Fußnoten

Alle 40 Fußnotenverweise haben genau eine zugehörige Definition. Die Definition wird jeweils anhand der nächsten folgenden Definition derselben Nummer bestimmt (die Nummerierung beginnt je Paragraph und je Muster neu bei [1]); die Zuordnung ist bijektiv, und die Anker verwenden die ursprüngliche Zeilennummer (`fn-z<Zeile>`). Die Marker stehen am Kurztitel (1), in Paragraphenüberschriften (5), nach Absatznummern (14), zwischen Aufzählungsnummer und Text (14) und an Musterüberschriften (6). Die Fußnoten stammen vom Anbieter der Webkopie: eine Kopffußnote („Zur Anwendung siehe § 12.“) und 39 Änderungsnachweise („… geänd. durch VO v. … ; zur Anwendung siehe § 12 Abs. …“). Sie sind kein amtlicher Verordnungstext; eine mit „[Amtl. Anm.:]“ gekennzeichnete Anmerkung enthält die Kopie nicht. Die Satzzählung der Kopie ist nicht amtlich; die amtliche Fassung enthält keine Satznummern.

## Amtlicher Abgleich

Am 09.09.2026 wurden von Gesetze im Internet die Übersichtsseite, die HTML-Gesamtausgabe, das XML-Paket (`xml.zip`, Last-Modified 30.06.2026, enthält `BJNR265800998.xml` mit builddate 20260630215606 und den BGBl-Auszug `bgbl1_2025_j0372_0010.pdf` zu Muster 5) und die PDF-Gesamtausgabe geladen und unter [Quellen/Onlineabgleich](../Quellen/Onlineabgleich/) gesichert. Adressen, HTTP-Antwortköpfe, Bytes und Prüfsummen stehen in [Abgleich.json](../Quellen/Onlineabgleich/Abgleich.json).

Stand: Die XML nennt „Zuletzt geändert durch Art. 11 G v. 22.6.2026 I Nr. 192“; die Kopie nennt in Zeile 7 dasselbe Änderungsgesetz. Titel, Datum, Fundstelle, die drei Gliederungsbezeichnungen und alle 13 Paragraphenüberschriften stimmen überein. Die Kopie weist „Text gilt vom 30.12.2025“ aus; eine textliche Wirkung des Gesetzes vom 22.6.2026 auf die ErbStDV ist weder aus der Kopie noch aus der amtlichen Fassung ersichtlich, und die amtlichen Seiten enthalten keinen Hinweis auf eine künftige Fassung.

Wortlaut: [wortlautabgleich.py](wortlautabgleich.py) vergleicht die §§ 1 bis 13 der Kopie (ohne Anbieterfußnoten, Marker und Satznummern; Sonderleerzeichen normalisiert, weiche Trennzeichen entfernt, Leerraum zusammengezogen) mit dem Text der XML-Gesamtausgabe und schreibt [Wortlautabgleich.json](../Quellen/Onlineabgleich/Wortlautabgleich.json). Ergebnis:

| Paragraph | Ergebnis |
| --- | --- |
| §§ 1, 4, 5, 6, 7, 8, 9, 12 | zeichenidentisch (1.439 / 2.446 / 408 / 650 / 3.339 / 1.713 / 409 / 896 Zeichen) |
| § 2 | nur Typografie: Kopie „–“, XML „-“ (zweimal in Nr. 3) |
| § 3 | nur Leerzeichen: Kopie „Lebens-(Sterbegeld-)“, XML „Lebens- (Sterbegeld-)“ |
| § 10 | Kopie „Anerkennungen“ / XML „Anerkennung“; Kopie „Rechtsgeschäfte“ / XML „Rechtsgeschäfts“; Kopie „Erwerben“ / XML „Erwerbern“ |
| § 11 | Kopie „ihres Zuständigkeitsbereichs“ / XML „ihre Zuständigkeitsbereichs“ |
| § 13 | Kopie enthält zusätzlich Satz 2 (Außerkrafttreten der ErbStDV BGBl. III 611-8-1); XML und PDF nur Satz 1 |

Die PDF-Gesamtausgabe von Gesetze im Internet lautet an allen abweichenden Stellen wie die XML (Gegenprobe in Abgleich.json). Eingangsformel und Schlußformel der amtlichen Fassung fehlen in der Kopie. Die Muster 1 bis 4 und 6 wurden als Wortmengen gegen die ASCII-Tabellen (pre-Blöcke) der XML verglichen, Muster 5 gegen die pdftotext-Extraktion des BGBl-Auszugs: Die Differenzen sind Spaltentrenner und Silbentrennungen der amtlichen Vorlage, die Bezugszeile („(zu § n ErbStDV)“ gegenüber XML-Titel „(§ n ErbStDV)“), zwei Groß-/Kleinschreibungen (Muster 3 „bei/Bei minderjährigen“, Muster 4 „Im/im Standesamtsbezirk“) sowie folgende Abweichungen der Kopie: Muster 2 „als Begünstiger*“ (amtlich „Begünstigter“), Muster 3 „einenWohnsitz“, „welchenWert“, „angeben angeben“ und „land-“ (amtlich „Land-“), Muster 5 „Testament­vollstrecker­zeugnisses“ (amtlich „Testamentsvollstreckerzeugnisses“). Keine dieser Stellen wurde geändert.

## Grenzen der Ausgangskopie

- Die Muster 1 bis 6 sind in der Kopie zellenweise abgeflacht: Positionsnummern, Buchstaben, Spaltenköpfe, Spaltennummern (1 bis 8), 74 Punktlinien, 19 Ankreuzkästchen und mehrzeilig zerrissene Zellen (z. B. Zeilen 578 bis 582) stehen jeweils auf eigenen Zeilen. Sie bleiben als Formularblöcke in Originalreihenfolge erhalten; das Tabellenlayout wird nicht rekonstruiert. Die amtliche Anordnung ist in der XML (ASCII-Tabellen) und in der PDF-Gesamtausgabe einsehbar; Muster 5 liegt amtlich nur als PDF vor.
- Die Kopie enthält weder Eingangsformel noch Schlußformel; beide werden nicht aus der amtlichen Fassung ergänzt.
- Die Wortabweichungen gegenüber Gesetze im Internet (§ 10, § 11, § 13 Satz 2, Muster 2, 3 und 5) bleiben unverändert; welche Fassung dem Bundesgesetzblatt entspricht, wurde nicht gegen das Bundesgesetzblatt geprüft.
- Die Blockbildung der Muster, die Überschriftenebenen der Binnentitel und die Behandlung der Seitenmarker sind redaktionelle Entscheidungen und dokumentiert.
- Schreibweisen der Kopie, etwa „Lebens-(Sterbegeld-)“, die Fußnote zu § 3 Abs. 3 („§ 3 Satz 2 geänd. …“ ohne Absatzangabe), Unicode-Sonderleerzeichen und weiche Trennzeichen, werden nicht berichtigt.

## Wiederholbare Prüfung

Aus der Projektwurzel (Windows: `py -B` mit `PYTHONUTF8=1`):

```powershell
py -B Rechtsgebiete/Steuerrecht/Gesetze/Erbschaft_und_Schenkungsteuer/ErbStDV/Stand_2026-09-09/Pruefung/konvertieren.py
py -B Rechtsgebiete/Steuerrecht/Gesetze/Erbschaft_und_Schenkungsteuer/ErbStDV/Stand_2026-09-09/Pruefung/wortlautabgleich.py
py -B Rechtsgebiete/Steuerrecht/Gesetze/Erbschaft_und_Schenkungsteuer/ErbStDV/Stand_2026-09-09/Pruefung/pruefen.py
```

Der Konverter liest nur die archivierte Textkopie und schreibt `ErbStDV.md`, [Quellbloecke.json](Quellbloecke.json), [Gliederungsentscheidungen.json](Gliederungsentscheidungen.json) und [Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json) mit Quell- und Zielprüfsummen. Der Wortlautabgleich liest die Textkopie und die gesicherten amtlichen Dateien und schreibt `Wortlautabgleich.json`; die bewerteten Abweichungen sind im Skript hinterlegt und werden per Assertion gegen das Vergleichsergebnis geprüft. Die unabhängige Leseprüfung vergleicht die gespeicherten Dateien erneut, einschließlich Prüfsummen von Quell- und Archivkopie, Zeilenabdeckung, Fußnotenanker, lokaler Links, Sprungmarken, der Prüfsummen der archivierten Abgleichdateien und der Kennzahlen des Wortlautabgleichs. Voraussetzungen: Python 3 und `markdown-it-py`; Poppler `pdftotext` nur zur Erzeugung der Textextraktionen.

## Grenze des Nachweises

Nachgewiesen sind die vollständige, zeichengetreue Übernahme der bereitgestellten Sachtexte, die Übereinstimmung des Stands mit der amtlichen Gesamtausgabe von Gesetze im Internet und der Wortlautvergleich der §§ 1 bis 13 mit dieser Gesamtausgabe einschließlich der einzeln aufgeführten Abweichungen. Nicht nachgewiesen sind die Richtigkeit der abweichenden Stellen gegenüber dem Bundesgesetzblatt, die Wiedergabe des Tabellenlayouts der Muster sowie die Vollständigkeit der Muster gegenüber der amtlichen Vorlage über den Wortmengenvergleich hinaus.
