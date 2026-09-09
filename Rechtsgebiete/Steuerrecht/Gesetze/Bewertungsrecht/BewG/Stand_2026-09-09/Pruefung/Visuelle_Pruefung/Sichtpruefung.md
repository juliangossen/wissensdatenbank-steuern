# BewG: ergänzende Sichtprüfung komplexer Anlagen

Geprüft am 09.09.2026 durch separate Sichtung der mit Poppler gerenderten Original-PDF-Seiten 73, 74, 120, 121, 159 und 160. Die daneben geprüften XML-Zellen stammen aus der archivierten amtlichen Gesamtausgabe. Diese gezielte Sichtprüfung ergänzt den vollständigen maschinellen Text- und Tabellenabgleich.

## Anlage 14 – PDF-Seiten 73–74

Der Tabellenkopf mit den sechs Spaltennummern und den Beschriftungen Region, Nutzungsart/Betriebsform, Betriebsgröße, Reingewinn, Pachtpreis und Besatzkapital wiederholt sich am Seitenwechsel. Die ersten Beschriftungen Schleswig-Holstein und Ackerbau beginnen auf Seite 73; die zugehörigen folgenden Betriebsgrößen stehen auf Seite 74. Diese Zellen sind hier oben ausgerichtet, während verbundene Zellen an anderen Stellen auch mittig ausgerichtet sein können. Leere Fortsetzungszellen dürfen nicht als fehlende Regionen oder Betriebsformen interpretiert werden.

Stichproben der drei Werte je Zeile stimmen mit XML überein:

- Schleswig-Holstein/Ackerbau/Kleinbetriebe: −428; 240; 129.
- Fortsetzung Mittelbetriebe: −19; 286; 90.
- Fortsetzung Großbetriebe: 124; 338; 78.
- Milchvieh/Kleinbetriebe: −572; 161; 241.

Der Wechsel zu Braunschweig am unteren Rand von Seite 74 ist sichtbar. PDF-Zeilenauslesung über den Seitenwechsel muss den wiederholten Tabellenkopf entfernen, ohne die weitergeführten Zahlenzeilen zu verändern.

## Anlage 24 – PDF-Seiten 120–121

Die Anlage beginnt auf Seite 120 mit dem Begriff der Brutto-Grundfläche und der Überschrift der Regelherstellungskosten. Der Tabelleninhalt setzt sich auf Seite 121 fort. Das hochgestellte Quadratzeichen gehört zur Einheit Euro/m² BGF.

Die Hausquerschnitte links sind eigenständiger Sachinhalt. Sie veranschaulichen Dachausbau, Flachdach und Geschosse und müssen in den entsprechenden verbundenen Tabellenzellen erhalten bleiben. Die XML-Dateien `bgbl1_2015_j1834-1_0010.jpg` bis `..._0050.jpg` sind den ersten fünf sichtbaren Bauformen zugeordnet; die spätere sechste Bauform beginnt außerhalb dieser Stichprobe.

Die Standardstufen 1 bis 5 sind im PDF eindeutig als Spalten gekennzeichnet. Beispiel 1.01/freistehende Einfamilienhäuser: 655; 725; 835; 1005; 1260. Beispiel 1.011/freistehende Zweifamilienhäuser: 688; 761; 877; 1055; 1323. Beide Zahlenfolgen stimmen mit den XML-Zellen überein. Die hochgestellte Fußnote 1 bei Zweifamilienhäusern ist ein eigener Verweis und darf nicht mit der Gebäudekennziffer verschmelzen. Wiederholungen von „Standardstufe“ innerhalb verschiedener Geschossgruppen sind Bestandteil der Tabelle, keine pauschal zu löschenden Servicezeilen.

## Anlage 39 – PDF-Seiten 159–160

Die Länder- und Gebäudeartbeschriftungen stehen vertikal mittig in über mehrere Zeilen verbundenen Zellen. Deshalb erscheinen sie bei zeilenweiser PDF-Textextraktion später als in der XML-Zellreihenfolge. XML kennzeichnet dies ausdrücklich durch `morerows` und `valign="middle"`. Die Spalten für fünf Baujahrsgruppen bleiben in derselben Reihenfolge.

Stichproben Baden-Württemberg/Einfamilienhaus stimmen mit XML überein:

- Unter 60 m²: 7,13; 6,88; 7,01; 8,73; 9,40.
- Von 60 bis unter 100 m²: 6,24; 6,41; 6,62; 7,58; 7,51.
- 100 m² und mehr: 5,53; 6,10; 6,37; 6,61; 7,78.

Seite 160 beginnt nach wiederholtem Tabellenkopf mit der letzten Bayern-Zeile aus der vorherigen Seite, anschließend folgen Berlin, Brandenburg und Bremen. Leere Länder-/Gebäudeartzellen dieser ersten Fortsetzungszeile bedeuten keine fehlende Klassifikation. Bei jeder maschinellen Korrektur der Lesereihenfolge müssen die Zahlenwerte und ihre Zuordnung zu Wohnflächen- und Baujahrsgruppen unverändert bleiben.

## Nachweise

- [Seite 73](BewG-073.png) und [Seite 74](BewG-074.png).
- [Seite 120](BewG-120.png) und [Seite 121](BewG-121.png).
- [Seite 159](BewG-159.png) und [Seite 160](BewG-160.png).

Ergebnis: Die untersuchten Lesereihenfolgeabweichungen sind durch sichtbare Seitenumbrüche, wiederholte Tabellenköpfe und verbundene Zellen erklärbar. Die genannten Stichproben zeigen keine inhaltliche Abweichung zwischen sichtbarer PDF und XML. Der vollständige Zahlen- und Zellvergleich bleibt Gegenstand der separaten maschinellen Prüfung.
