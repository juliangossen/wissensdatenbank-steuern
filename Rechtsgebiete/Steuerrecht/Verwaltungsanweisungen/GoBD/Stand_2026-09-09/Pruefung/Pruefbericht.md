# Prüfbericht: GoBD

Prüf- und Quellenabgleichdatum: **09.09.2026**.

## Ergebnis

Alle **57 PDF-Seiten** der drei bereitgestellten Dokumente sind übernommen. Die 184 Randnummern des Grundschreibens sind lückenlos vorhanden. Die 47 Gliederungspunkte des Grundschreibens sowie alle 19 tatsächlich vorhandenen Änderungsziffern von 2024 und alle 11 Änderungsziffern von 2025 sind navigierbar. Die Anlage des Änderungsschreibens 2024 ist vollständig enthalten.

| Dokument | Seiten | Geprüfte Quellblöcke | PDF-Text vollständig erfasst | Markdown-Rückvergleich | Gerendertes HTML zurück zum Text | Unabhängige Textextraktion |
| --- | ---: | ---: | --- | --- | --- | --- |
| 2019-11-28-GoBD | 44 | 388 | Bestanden | Bestanden | Bestanden | Bestanden |
| 2024-03-11-aenderung-gobd | 9 | 95 | Bestanden | Bestanden | Bestanden | Bestanden |
| 2025-07-14-GoBD-2-aenderung | 4 | 41 | Bestanden | Bestanden | Bestanden | Bestanden |

## Verfahren und Aussagekraft

1. **Unveränderte Originale:** Die bereitgestellten PDF-Dateien wurden bytegleich nach `Quellen/` kopiert. SHA-256-Werte stehen im [Quellenmanifest](../Quellen/Quellenmanifest.json) und in den dokumentbezogenen Prüfdateien.
2. **Vollständige Extraktion:** Poppler `pdftotext -layout -enc UTF-8` extrahierte jede Seite, einschließlich Briefköpfen, Seitenkennzeichnungen, Fußzeilen, Inhaltsübersicht, Zitat- und Verweistext. Die unveränderten Extraktionstexte sind hier archiviert. Es wurde kein erfasster Quelltext wegen vermeintlicher Unwichtigkeit ausgelassen.
3. **Quellblöcke und Rückvergleich:** Jeder Quellblock ist in `*-Quellbloecke.json` dokumentiert und durch unsichtbare Kommentare im Markdown eindeutig adressiert. Der gespeicherte Markdown-Text wird zurückgelesen, ausschließlich die hinzugefügte Formatierung entfernt und mit dem zugehörigen PDF-Text verglichen. Nach Normalisierung von Unicode, Leerraum und Bindestrichen stimmen sämtliche Quellblöcke überein. Bei den beiden mehrspaltigen Tabellenteilen wird wegen geänderter Lesereihenfolge das vollständige Zeichenmultiset verglichen. Ein zusätzlicher Gesamtvergleich bestätigt, dass alle Zeichen der PDF-Extraktion in den Quellblöcken erfasst sind. Diese Normalisierung prüft Vollständigkeit; sie ist keine eigenständige sprachliche oder rechtliche Berichtigung.
4. **Renderingprüfung:** Alle Quellblöcke wurden mit `markdown-it-py` nach CommonMark mit Tabellenunterstützung in HTML gerendert. Der daraus zurückgewonnene sichtbare Text stimmt unter derselben Normalisierung mit der Quelle überein. Damit wurde zusätzlich geprüft, dass die Markdown-Syntax keine Inhalte verschluckt oder eine Quellnummerierung verändert.
5. **Unabhängige Extraktion:** PyMuPDF extrahierte dieselben PDF-Dateien unabhängig von Poppler. Die Multisets sämtlicher Buchstaben und Ziffern stimmen für jedes der drei Dokumente exakt überein. Diese Gegenprobe ergänzt den geordneten Quellblockvergleich; sie ersetzt ihn nicht.
6. **Struktur:** Die Randnummernfolge des Grundschreibens ist exakt `1, 2, …, 184`. Die Änderungsziffern sind 2024 exakt `1–18, 22` und 2025 exakt `1–11`. Die 47 Überschriften des Grundschreibens wurden anhand der Fettschrift im PDF erkannt und auf Gliederungsebene geprüft. Briefköpfe und amtliche Inhaltsübersicht bleiben als Textblöcke in ihrer ursprünglichen Spaltenanordnung erhalten.
7. **Tabellen und Bilder:** Die Tabelle zu Rz. 77 wurde auf PDF-Seiten 19 und 20 aus den tatsächlichen Zellenkoordinaten extrahiert und als Markdown-Tabelle wiedergegeben. Die am Seitenumbruch geteilte Zeile wird entsprechend dem Original auf Seite 20 fortgesetzt; beide Tabellenköpfe bleiben erhalten. Die [Abbildung von Seite 19](../Quellen/Abbildungen/2019-11-28-GoBD-seite-19.png) und [Abbildung von Seite 20](../Quellen/Abbildungen/2019-11-28-GoBD-seite-20.png) sind zusätzlich archiviert. Die Behördenlogos wurden aus den PDFs extrahiert und an den entsprechenden Seiten wieder eingebunden; die vier 2025-Seiten enthalten dasselbe Logo. Weitere inhaltliche Rasterbilder oder getrennte Fußnotenapparate wurden in diesen drei PDFs nicht festgestellt; sämtliche inline enthaltenen Fundstellen und Hinweise sind übernommen.
8. **Visuelle Sichtprüfung:** Die Original-Briefköpfe aller drei Schreiben, beide Tabellenseiten 2019 sowie die 2024-Seiten 4 (Nummerierungssprung und Beginn der Anlage) und 8 (Schluss der Anlage mit Übergangsregeln) wurden gerendert und visuell kontrolliert. Die Sichtprüfung war gezielt auf die layoutkritischen Stellen beschränkt; sie wird nicht als manuelles Lesen aller 57 Seiten ausgegeben.

## Quellenabgleich und Fassung

Die amtlich heruntergeladenen 2024- und 2025-PDFs sind jeweils bytegleich mit den bereitgestellten PDFs. Es gibt deshalb keine getrennte inhaltlich abweichende „aktuelle Abruffassung“ dieser Schreiben. Die in Web-Suchergebnissen teilweise abweichende Darstellung einzelner Wörter wurde nicht als Änderung der amtlichen PDF übernommen. Insbesondere steht auf Seite 3 der direkt abgerufenen Juli-2025-PDF weiterhin „strukturieren Datenteils“; die Wiedergabe erhält den Originalwortlaut.

Für 2019 wurde eine amtliche HTML-Wiedergabe im AO-Handbuch 2023 gefunden und unverändert archiviert. Die getesteten alten BMF-PDF-URLs lieferten HTTP 404. Daher wird **kein bytegleicher Online-PDF-Abgleich für 2019 behauptet**. Für seine vollständige Konvertierung ist die bereitgestellte 44-seitige PDF maßgeblich.

Die BMF-Publikationsseite zur zweiten Änderung und die BMF-Übersicht zur Abgabenordnung führen die GoBD-Änderung vom 14.07.2025. Die ergänzende Suche nach späteren GoBD-Änderungen bis zum Quellenabgleich ergab keinen späteren Treffer. Das ist ein dokumentierter Recherchebefund, keine Garantie für eine erschöpfende Negativsuche. URLs, Abrufstatus, erfolgreiche Originalabrufe und Suchbegriffe stehen im [Quellenmanifest](../Quellen/Quellenmanifest.json).

Es wurde kein konsolidierter Normtext erzeugt. Die drei Originalschreiben bleiben getrennt. Aus den angegebenen Anwendungsdaten wurde kein einheitliches, möglicherweise unzutreffendes Inkrafttretensdatum konstruiert; Besonderheiten sind in der [Fassungsübersicht](../README.md) erläutert.

## Reproduzieren

Voraussetzungen: Python 3, PyMuPDF, markdown-it-py und Poppler (`pdftotext` im PATH). Aus dem Projektverzeichnis:

Bestehende Dateien ohne Änderung prüfen:

```powershell
py Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/GoBD/Stand_2026-09-09/Pruefung/verify_gobd.py
```

Markdown und Konvertierungsprüfungen neu erzeugen:

```powershell
py Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/GoBD/Stand_2026-09-09/Pruefung/convert_gobd.py
```

Das Skript nutzt die archivierten lokalen PDF-Dateien, erzeugt die drei Markdown-Dateien reproduzierbar neu und schreibt die Prüfdateien erneut. Die Quellen-PDFs werden nicht verändert. Für einen späteren neuen Rechtsstand ist ein eigener Stand-Ordner anzulegen und der Quellenabgleich erneut durchzuführen.
