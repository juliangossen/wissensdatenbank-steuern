# Prüfbericht: Insolvenzordnung

Die vom Nutzer bereitgestellte `InsO.pdf` mit 90 Seiten wurde unverändert als [Quellenkopie](../Quellen/InsO.pdf) erhalten. Ihr SHA-256-Wert lautet `4ed5d81dafd60986a38ff26587bd632954eae2163f1d783acd481f4d44c404f2`.

Am 09.09.2026 wurden die [amtliche PDF](https://www.gesetze-im-internet.de/inso/InsO.pdf) und die zugehörige XML-Gesamtausgabe abgerufen. Die lokale und die abgerufene PDF sind bytegleich. Rechtsstand und Vollzitat wurden aus dem PDF-Dokumentkopf sowie den XML-Metadaten übernommen. Der Ordner bezeichnet den Quellenabgleich, keine neue Gesetzesfassung.

## Vollständigkeit

- Sämtliche 448 XML-Normdatensätze sind in der PDF in derselben Reihenfolge vollständig textgleich nachgewiesen, einschließlich Fußnoten und Gliederungsteilen. Normalisiert werden ausschließlich NFC, Leerraum und unsichtbare weiche Trennzeichen. Wiederkehrende Servicezeilen und Seitenzahlen werden entfernt. Es waren keine besonderen Korrekturen von Lesereihenfolgen erforderlich.
- Der Konverter prüft 937 Inhalts-, Überschriften- und Fußnotenblöcke durch Rücklesen des gerenderten Markdown auf vollständige Zeichengleichheit mit XML; ausgenommen sind Leerraum, NFC und ausdrücklich redaktionelle Markierungen.
- Die unabhängige Strukturprüfung bestätigt zusätzlich sämtliche 447 Abschnitte nach dem Dokumentkopf, deren Reihenfolge und interne Verweise. 411 Vorschriften und 36 Gliederungsteile bleiben erhalten. Das Dokument enthält keine Tabellen oder Abbildungen.
- Der XML-Tag `small` in § 9 wird als HTML-Kleinschrift innerhalb des Markdown bewahrt. Die technische XML-Kennung `(XXXX)` bei weggefallenen Vorschriften entfällt entsprechend der PDF-Darstellung.

Die Übersicht und Sprungmarken sind redaktionelle Navigation. Der Gesetzestext wird nicht zusammengefasst oder redaktionell berichtigt.

## Nachweise und Wiederholung

[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Markdown-Vollständigkeitsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Strukturprüfung](Markdown_Strukturpruefung.json) und [Quellenkonfiguration mit Prüfsummen](konfiguration.json).

Aus der Projektwurzel:

```powershell
py -B Rechtsgebiete/Insolvenzrecht/InsO/Stand_2026-09-09/Pruefung/konvertieren.py
py -B Rechtsgebiete/Insolvenzrecht/InsO/Stand_2026-09-09/Pruefung/pdf_xml_pruefen.py
py -B Rechtsgebiete/Insolvenzrecht/InsO/Stand_2026-09-09/Pruefung/markdown_struktur_pruefen.py
```

Der Konverter-Snapshot arbeitet ausschließlich mit archivierten Quellen. Spätere Fassungen benötigen einen neuen Quellenabgleich und einen eigenen Standordner.
