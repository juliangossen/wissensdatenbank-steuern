# Vollständigkeitsprüfung: DSGVO

Geprüft am 2026-09-09.

**Bestanden:** Die lokale PDF stimmt bytegenau mit der amtlichen EUR-Lex-PDF der ursprünglichen Amtsblattfassung überein.

- 88 PDF-Seiten; alle extrahierten nichtleeren Textzeilen einzeln nachgewiesen.
- 99 Artikel, 173 Erwägungsgründe, 0 Anhänge.
- 21 Fußnotenblöcke, 1 Datentabellen einschließlich Amtsblattkopf, 0 Abbildungen.
- 1693 Inhaltskomponenten und der gesamte HTML-Körper nach Markdown-Rendering textidentisch (nur Whitespace normalisiert).
- Sämtliche 42 internen Querverweise haben ein vorhandenes Ziel.

Bei PDF → HTML sind ausschließlich Layoutzeichen, Trennstriche, Groß-/Kleinschreibung und die abweichende Fußnotenzählung für die Suchprüfung normalisiert. Die PDF-Einzelzeilen bleiben im [Prüfprotokoll](PDF_Textabgleich.json) vollständig lesbar. Der zusätzliche strenge HTML → Markdown-Abgleich bewahrt sämtliche Buchstaben, Ziffern, Satzzeichen und Tabellenzellen. Fußnoten und Anhänge sind nicht ausgelassen. Nur wiederkehrende Seitenköpfe und Seitenzahlen werden im strukturierten Lesetext nicht auf jeder Seite wiederholt. Sie stehen im [PDF-Seitentext](../Quellen/PDF_Seitentext.txt) und im Original.

Die HTML-Oberfläche (Skripte und zwei Schaltflächen „Text von Bild“) ist kein Normtext; bei vorhandenen Bildtexten wird deren voller Inhalt übernommen. Verschmolzene Tabellenzellen bleiben als HTML-Tabellen innerhalb der Markdown-Datei erhalten.

**Fassungsgrenze:** Ursprüngliche Amtsblattfassung vom 04.05.2016, ABl. L 119, S. 1–88; Rechtsakt vom 2016-04-27. Keine konsolidierte Fassung: spätere Änderungen und Berichtigungen sind nicht in diese Originalfassung eingearbeitet. Import und Abgleich am 2026-09-09; das Ordnerdatum bezeichnet den Importstand, nicht einen aktuellen Rechtsstand.

[Maschinenlesbarer Nachweis](Vollstaendigkeitspruefung.json) · [Quellenmetadaten](../Quellen/Quellenabgleich.json)
