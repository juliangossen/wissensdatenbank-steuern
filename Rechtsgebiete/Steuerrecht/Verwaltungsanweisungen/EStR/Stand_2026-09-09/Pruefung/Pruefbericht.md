# Prüfbericht: EStR 2012 mit EStH 2025

Grundlage ist die vom Nutzer bereitgestellte beck-online-Webkopie `EStR 2012.txt`. Sie enthält 20.085 Zeilen und ist unverändert als [Textquelle](../Quellen/EStR_2012_Webkopie.txt) erhalten. Der SHA-256-Wert lautet `08d3c8ad5bf40cb5b2b1bbbb32979e458b1c42eebf7eb3ce36d4105ee8173ef3`.

## Vollständigkeit gegenüber der gelieferten Kopie

Alle **10.924 nichtleeren Sachtextzeilen von Zeile 33 bis 20.085** werden in 10.081 Quellblöcken genau einmal übernommen. Die vorgeschalteten Navigations- und doppelten Titelzeilen verbleiben in der unveränderten Originaldatei. Jeder Quellblock wird gerendert und sein sichtbarer Text nach Entfernung ausschließlich von Leerraum vollständig mit dem Ausgangstext verglichen. Buchstaben, Zahlen, Satzzeichen und vorhandene Trennzeichen bleiben erhalten.

Die Gliederung umfasst 118 Paragraphengruppen, 302 R-Blöcke, 344 H-Blöcke und sechs Anlagenpositionen. Neun historische R-Überschriften und zwei historische H-Überschriften werden gesondert gekennzeichnet. Acht weitere mit „R“ beginnende Verweis- oder Fließtextzeilen werden nicht fälschlich als aktuelle Richtlinienüberschriften geführt. Elf historische Überschriften und acht ausgeschlossene Verweiszeilen sind mit ihren Quellzeilen im Konverter festgehalten.

Alle **507 Fußnotenverweise** werden der jeweils nächsten folgenden isolierten Definition derselben Nummer zugeordnet. Die Zuordnung ist bijektiv: Jeder Verweis trifft genau eine Definition, jede Definition gehört zu genau einem Verweis. Die Anker benutzen Quellzeilen statt wiederkehrender Fußnotennummern.

Die Tabellenaufbereitung der Anlagen 1 und 6 bewahrt die ursprüngliche Reihenfolge sämtlicher Texte. Die Tabelle in Anlage 1 verwendet die amtlich belegte Spaltenstruktur. Anlage 6 enthält 77 Länder/Gebiete der kopierten Fassung. `tabellen.py` prüft zusätzlich die lückenlose Reihenfolge aller verwendeten Quellzeilen. Anlage 2 wird wegen unklarer Zellverbindungen und abweichender amtlicher Vergleichsfassung nicht anhand vermuteter Spalten nachgebaut.

## Stände und amtliche Quellen

Die Kopie kombiniert die EStR 2012 in der Fassung der EStÄR vom 25.03.2013 mit den Einkommensteuer-Hinweisen 2025. Der Redaktionsschluss 20.01.2026 ist eine Angabe des kopierten Vorworts. Der Standordner 09.09.2026 bezeichnet die Erfassung und Quellenprüfung, keine neu verkündete Richtlinienfassung.

Der [amtliche Abgleich](../Quellen/Onlineabgleich/Abgleich.json) dokumentiert genaue Quellenadressen, archivierte Dateien und Prüfsummen. Die amtliche Gliederung bestätigt, dass § 1 nur R 1 enthält und H 1a mit „Allgemeines“ beginnt; das Fehlen einer gesonderten Überschrift H 1 in der Kopie ist daher keine nachgewiesene Lücke. Auch das Ende der Staatenliste bei Uganda ist amtlich belegt und allein kein Hinweis auf einen abgeschnittenen Text.

## Quelllücken und gekennzeichnete Ergänzungen

- **Anlage 4:** Die Webkopie enthält 18 Musterbeschriftungen sowie Beschriftungen für fünf Anlagen zu Sammelbestätigungen, aber keine eigentlichen Formularabbildungen. Passende amtliche Muster des in der Kopie bezeichneten historischen Stands 2013/2014 sind mit Quellenhinweis ergänzt: 24 Abbildungsseiten, einschließlich einer zweiten Seite von Muster 15 trotz nur einer zugehörigen Beschriftung in der Kopie. Der Verweis im amtlichen EStH 2025 führt hierfür zur früheren Ausgabe EStH 2019.
- **Anlagen 3 und 5:** ausdrücklich „nicht belegt“; keine Ergänzung erfunden.
- **Anlage 2:** Die historische Übersicht in der Kopie weicht von der amtlichen Übersicht im EStH 2025 ab, unter anderem bei der ältesten Zeitstufe und § 7 Abs. 5a EStG. Die amtliche Vergleichsfassung liegt [separat](../Ergaenzungen/Anlage_2_BMF_2025.md).
- **Anlage 6:** Die kopierte Staatenliste stimmt nicht vollständig mit der amtlichen Liste im EStH 2025 überein; beispielsweise fehlt Andorra. Die amtliche Übersicht liegt [separat](../Ergaenzungen/Anlage_6_BMF_2025.md). Die Originalkopie wird nicht stillschweigend mit dieser Fassung verschmolzen.
- **Unveränderte Auffälligkeiten:** Zeile 83 nennt BStBl. I 2026 S. 291, die zugehörige Fußnote in Zeile 143 dagegen BStBl. I 2025 S. 291. Zeile 19516 enthält die auffällige Formulierung „ist das verfahren keine zwingende Voraussetzung“. Solche Angaben werden nicht ohne Kennzeichnung redaktionell korrigiert.

## Wiederholung

Aus der Projektwurzel:

```powershell
py -B Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/EStR/Stand_2026-09-09/Pruefung/konvertieren.py
py -B Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/EStR/Stand_2026-09-09/Pruefung/pruefen.py
```

[Quellbloecke.json](Quellbloecke.json) enthält die genaue Zuordnung sämtlicher Sachtextzeilen. [Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json) enthält aktuelle Quell- und Zielprüfsummen und Zählwerte. Die lesende Prüfung vergleicht die gespeicherte Markdown-Datei erneut mit den Originalzeilen und kontrolliert Anker, Links und ergänzte Abbildungen.

Nachgewiesen sind die vollständige Übernahme der bereitgestellten Sachtexte und der dokumentierte amtliche Stand-/Strukturabgleich mit ausdrücklich gekennzeichneten Ergänzungen. Ein vollständiger Wortlautvergleich der gesamten redaktionell angereicherten Kopie mit sämtlichen amtlichen BMF-Inhalten wird nicht behauptet.
