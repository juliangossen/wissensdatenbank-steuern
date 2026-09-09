# Vollständigkeitsprüfung: MwStSystRL

Geprüft am 2026-09-09.

**Bestanden:** Die lokale PDF stimmt bytegenau mit der amtlichen EUR-Lex-PDF der ursprünglichen Amtsblattfassung überein.

- 118 PDF-Seiten; alle extrahierten nichtleeren Textzeilen einzeln nachgewiesen.
- 414 Artikel, 67 Erwägungsgründe, 12 Anhänge.
- 16 Fußnotenblöcke, 156 Datentabellen einschließlich Amtsblattkopf, 0 Abbildungen.
- 2723 Inhaltskomponenten und der gesamte HTML-Körper nach Markdown-Rendering textidentisch (nur Whitespace normalisiert).
- Sämtliche 32 internen Querverweise haben ein vorhandenes Ziel.

Bei PDF → HTML sind ausschließlich Layoutzeichen, Trennstriche, Groß-/Kleinschreibung und die abweichende Fußnotenzählung für die Suchprüfung normalisiert. Die PDF-Einzelzeilen bleiben im [Prüfprotokoll](PDF_Textabgleich.json) vollständig lesbar. Der zusätzliche strenge HTML → Markdown-Abgleich bewahrt sämtliche Buchstaben, Ziffern, Satzzeichen und Tabellenzellen. Fußnoten und Anhänge sind nicht ausgelassen. Nur wiederkehrende Seitenköpfe und Seitenzahlen werden im strukturierten Lesetext nicht auf jeder Seite wiederholt. Sie stehen im [PDF-Seitentext](../Quellen/PDF_Seitentext.txt) und im Original.

Die HTML-Oberfläche (Skripte und zwei Schaltflächen „Text von Bild“) ist kein Normtext; bei vorhandenen Bildtexten wird deren voller Inhalt übernommen. Verschmolzene Tabellenzellen bleiben als HTML-Tabellen innerhalb der Markdown-Datei erhalten.

**Fassungsgrenze:** Ursprüngliche Amtsblattfassung vom 11.12.2006, ABl. L 347, S. 1–118; Rechtsakt vom 2006-11-28. Keine konsolidierte Fassung: spätere Änderungen und Berichtigungen sind nicht in diese Originalfassung eingearbeitet. Import und Abgleich am 2026-09-09; das Ordnerdatum bezeichnet den Importstand, nicht einen aktuellen Rechtsstand.

[Maschinenlesbarer Nachweis](Vollstaendigkeitspruefung.json) · [Quellenmetadaten](../Quellen/Quellenabgleich.json)
