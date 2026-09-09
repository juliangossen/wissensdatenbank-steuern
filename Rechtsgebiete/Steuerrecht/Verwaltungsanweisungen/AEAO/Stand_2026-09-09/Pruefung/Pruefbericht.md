# Prüfbericht: AEAO-Webkopie nach Markdown

Quelle: vom Nutzer bereitgestellte Datei `AEAO.txt`, UTF-8 mit CRLF-Zeilenenden, 18.428 Zeilen. Die Kopfzeilen nennen beck-online, die Fassungsangabe „Text gilt seit 02.07.2026“ und in den Zeilen 31 bis 84 die Liste der historischen Geltungszeiträume. Die unveränderte Quelle liegt unter [Quellen/AEAO_Webkopie.txt](../Quellen/AEAO_Webkopie.txt); zusätzlich wird sie bytegleich im versionierten Web-Archiv geführt.

## Umfang und Übernahme

Alle 10.073 nichtleeren Sachtextzeilen von Zeile 87 (Titel) bis Zeile 18.404 (Schlusszeile der Anlage 3) werden genau einmal übernommen. 6.063 Quellblöcke ordnen die Originalzeilen der Markdown-Datei zu. Jeder Block wird mit `markdown-it-py` gerendert; der sichtbare Text muss nach Entfernung ausschließlich von Leerraum zeichengenau mit den Quellzeilen übereinstimmen. Buchstaben, Ziffern, Satzzeichen, Auslassungspunkte und Sonderzeichen der Kopie bleiben unverändert. Website-Navigation, Suchmaske, Fassungsliste und Fußzeile der Kopie (Zeilen 1 bis 86 und ab 18.405) werden nicht als Erlasstext übernommen; sie bleiben in der Originalkopie erhalten.

Die strukturierte Datei enthält den Dokumentkopf mit Fundstelle und drei Kopffußnoten, den Einleitungssatz, ein redaktionell erzeugtes Gesamtinhaltsverzeichnis, die 224 Gliederungspositionen („AEAO zu § …“, „AEAO zu §§ …“, „AEAO vor § …“, „AEAO vor §§ …“) und die drei Anlagen. Innerhalb der Positionen wurden erkannt:

| Element | Anzahl | Umsetzung |
| --- | ---: | --- |
| Nummerierte Überschriften (z. B. „6.1. Auslandsaufenthalt eines Arbeitnehmers“) | 498 | Überschriften der Ebenen 4 bis 6 nach Gliederungstiefe; 249 auf Ebene 1, 166 auf Ebene 2, 83 tiefer |
| Nummerierte Absätze (z. B. „1.1. ¹Nach § 8 AO …“) | 1.672 | Absatz mit hervorgehobener Nummer |
| Sprungmarken nummerierter Gliederungspunkte | 2.152 | Anker `…-nr-6-1` für die erste Nennung jeder Nummer innerhalb einer Position |
| Inhaltsübersichten einzelner Positionen | 20 | Tabelle mit Links auf die vorhandenen Sprungmarken; Gruppenzeilen ohne Nummer bleiben erhalten |
| Zwischenüberschriften nach Form („Zu § 55 Abs. 1 Nr. 1 AO:“, „Beispiel …:“, „§ 1“ der Mustersatzung) | 158 | Überschrift Ebene 4 |
| Zwischenüberschriften nach Kontext (z. B. „Zinslauf“, „Argentinien“) | 49 | Überschrift Ebene 4; erkannt an Form, Folgezeile und Vorzeile |
| Aufzählungen mit den Zeichen „–“, „•“, „1.“ oder „a)“ | 279 | Liste; das Originalzeichen bleibt Teil des Texts |
| Blöcke kurzer Quellzeilen (abgeflachte Tabellen) | 160 | Zusammengefasster Absatz mit Zeilenumbrüchen |
| Hochgestellte Satznummern | 5.822 | `<sup>`; Regel: ein- bis zweistellige Zahl unmittelbar vor Großbuchstabe, „§“ oder „„“ |

Alle Gliederungsentscheidungen stehen mit Quellzeile, Art und Ebene in [Gliederungsentscheidungen.json](Gliederungsentscheidungen.json). Die 49 kontextbasierten Zwischenüberschriften wurden einzeln gesichtet.

Alle 983 Fußnotenverweise haben genau eine zugehörige Definition. Die Definition wird jeweils anhand der nächsten folgenden Definition derselben Nummer bestimmt; die Zuordnung ist bijektiv, und die Anker verwenden die ursprüngliche Zeilennummer. Die Fußnoten stammen vom Anbieter der Webkopie: Sie enthalten Änderungsnachweise („neu gef. mWv … durch BMF v. …“) und Hinweise auf Rechtsprechung und Literatur; sie sind kein amtlicher Erlasstext. Nach Kopffußnote 2 der Kopie ist die Satzzählung nicht amtlich.

## Amtlicher Standabgleich

Die BMF-Übersichtsseite zum AEAO wurde am 09.09.2026 abgerufen und archiviert. Sie listet Änderungsschreiben bis zum 2. Juli 2026; ein späteres Änderungsschreiben ist dort nicht veröffentlicht. Das [Änderungsschreiben vom 2.7.2026](../Quellen/Onlineabgleich/2026-07-02-aenderung-aeao-51-52-usw.pdf) (9 Seiten) wurde geladen und mit `pdftotext` ausgewertet. Es ändert den AEAO zu §§ 51, 52, 53, 55, 56, 57, 64, 65, 66 und 67a und nennt als Vorgänger das Schreiben vom 17. März 2026.

Die Webkopie gibt als letzte Änderung „BMF vom 2.7.2026 (BStBl. I, 950)“ an. Genau die zehn im Schreiben geänderten Positionen tragen in der Kopie Fußnoten mit dem Änderungsnachweis „BMF v. 2.7.2026“; die Änderung vom 17.3.2026 ist ebenfalls nachgewiesen. Adressen, Prüfsummen und das Ergebnis stehen in [Abgleich.json](../Quellen/Onlineabgleich/Abgleich.json).

Eine amtliche konsolidierte Gesamtfassung des AEAO mit dem Stand 2.7.2026 liegt als PDF nicht vor; das BMF veröffentlicht auf der Übersichtsseite nur die Änderungsschreiben. Ein Wortlautvergleich der Webkopie mit einer amtlichen Gesamtfassung wurde deshalb nicht durchgeführt.

## Grenzen der Ausgangskopie

- Die zwei Formularseiten der Anlage 1 (Abtretungs-/Verpfändungsanzeige) sind in der Kopie nur als Platzhalterzeilen „Seite 1/2 des Formulars …“ enthalten. Sie werden nicht aus anderen Quellen ergänzt.
- Tabellen der Kopie sind in Einzelzeilen abgeflacht (Berechnungsbeispiele zu §§ 55, 58, 62, 64, 233a und 238, Anschriften- und Bescheidkopfbeispiele zu § 122, Kürzelübersicht zu § 122, Zahlungsbeispiele zu § 238). Sie bleiben als Textzeilen in Originalreihenfolge erhalten; verlorene Spaltenzuordnungen werden nicht geraten.
- Zwischenüberschriften ohne Nummer sind in der Kopie nicht ausgezeichnet. Ihre Erkennung und die Gliederungsebenen sind redaktionelle Entscheidungen und dokumentiert.
- Schreibweisen der Kopie, etwa „Nr. 9eingef.“ in einer Fußnote oder Unicode-Sonderleerzeichen, werden nicht berichtigt.

## Wiederholbare Prüfung

Aus der Projektwurzel:

```powershell
py -B Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/AEAO/Stand_2026-09-09/Pruefung/konvertieren.py
py -B Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/AEAO/Stand_2026-09-09/Pruefung/pruefen.py
```

Der Konverter liest nur die archivierte Textkopie und schreibt `AEAO.md`, [Quellbloecke.json](Quellbloecke.json), [Gliederungsentscheidungen.json](Gliederungsentscheidungen.json) und [Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json) mit Quell- und Zielprüfsummen. Die unabhängige Leseprüfung vergleicht die gespeicherten Dateien erneut, einschließlich Zeilenabdeckung, Fußnotenanker, lokaler Links, Sprungmarken und der Prüfsummen der archivierten Abgleichdateien. Voraussetzungen: Python 3 und `markdown-it-py`; Poppler `pdftotext` nur für die Auswertung des Änderungsschreibens.

## Grenze des Nachweises

Nachgewiesen ist die vollständige, zeichengetreue Übernahme der bereitgestellten Sachtexte sowie der Standabgleich mit den auf der BMF-Übersichtsseite veröffentlichten Änderungsschreiben. Nicht nachgewiesen sind die Vollständigkeit und Richtigkeit der Webkopie gegenüber einer amtlichen Gesamtfassung sowie die Wiedergabe von Formularen und Tabellenlayouts.
