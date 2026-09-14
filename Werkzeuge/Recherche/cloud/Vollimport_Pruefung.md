# Vollständiger Import nach Supabase

**Historischer Nachweis:** Dieser Bericht beschreibt die Fassung mit 58 Dokumenten vom 10.09.2026. Den aktuellen Bestand mit der BFH-Ergänzung dokumentiert der [Importabschluss vom 14.09.2026](../../BFH_Import_2026-09-14/Abschluss.md).

Abgeschlossen am **10.09.2026 um 00:11 Uhr (Europe/Berlin)**. Alle 58 in `Bestand.json` registrierten Dokumente sind in Supabase veröffentlicht; der Quellenimport bleibt auf den **09.09.2026** datiert.

Aktive Fassung: `r-2ba1572b7978ca909270331f` im Projekt `vtriyndfmuwzqwrkpkde`.

| Bestand | Anzahl |
| --- | ---: |
| Registrierte Dokumente | 58 |
| Vollständig abrufbare Fundstellen | 14.099 |
| Suchabschnitte mit je einem 384-dimensionalen Vektor | 23.261 |
| Dateieinträge einschließlich Originalquellen und Belegen | 1.173 |
| Dateibytes | 280.675.147 |

Die Fundstellen umfassen 11.705 Vorschriften bzw. nummerierte Abschnitte, 2.391 zusätzliche Quelltextteile und drei gesondert gekennzeichnete Ergänzungen. Die registrierten Originalquellen bestehen aus 52 PDF- und sechs TXT-Dateien. Gemeinsam verwendete Dateien können mehreren Dokumenten zugeordnet sein; die Zahl der Dateieinträge ist daher keine Zahl unterschiedlicher Dateien.

## Durchgeführte Prüfungen

- Alle Dokumente, Fundstellen, Metadaten, Suchabschnitte und Vektoren nach der Übertragung mit dem geprüften Export verglichen.
- Alle 1.173 Dateieinträge übertragen und vollständig zurückgelesen; Dateigröße und SHA-256 stimmen überein.
- Alle 14.099 Fundstellen über den Lesezugang vollständig rekonstruiert und auf 14.389 Textseiten mit dem Export verglichen.
- Volltextsuche für jedes der 58 Dokumente erfolgreich ausgeführt; 1.089 exakte Referenzen und Aliase dokumentübergreifend geprüft.
- Leserechte, gesperrte Schreibzugriffe und Unveränderlichkeit abgeschlossener Fassungen geprüft.
- Neue Fassung erst nach erfolgreichen Prüfungen innerhalb der Importtransaktion veröffentlicht; aktive Fassung nach dem Commit erneut abgefragt.
- Mit einem separaten Leserlogin anschließend EStG § 7 (12.522 Zeichen) und AO § 146 (5.583 Zeichen) vollständig abgerufen und per SHA-256 geprüft. Die Volltextsuche „Absetzungen Abnutzung“ im EStG liefert § 7 an erster Stelle.

Die technischen Vergleiche belegen die vollständige Übernahme der registrierten Sammlung. Sie sind kein neuer Wortlautvergleich sämtlicher Quellen mit amtlichen Veröffentlichungen. Dokumentierte Quellenstände und bestehende Hinweise zur Quellengüte bleiben erhalten.

## Nutzung aus Claude oder ChatGPT

Die vorhandenen Lesefunktionen sind für den offiziellen Supabase-MCP freigegeben. Der Nutzer hat den Chat-Zugriff auf die frühere Drei-Dokumente-Fassung bestätigt. Die vollständige neue Fassung ist über die Datenbank-Lesezugänge geprüft; ein neuer Aufruf in der Chatoberfläche ist nicht Teil dieses Nachweises.

Die bestehende Verbindung verwendet dieselbe Adresse. Ein laufender Chat muss den aktiven Bestand erneut mit `SELECT kb.release_info();` abfragen, wenn er noch die alte Kennung festhält. [Anleitung und Projektanweisung](../../../Chat_KI_starten.md)

Über den offiziellen Supabase-MCP funktionieren Volltextsuche und gezieltes Nachschlagen. Die gespeicherten Vektoren allein berechnen keinen Vektor für eine neue Frage: Dafür wird weiterhin das passende e5-Modell benötigt. Die lokale Recherche bietet diese hybride Suche bereits; in der direkten Chat-Anbindung ist sie nicht automatisch enthalten. Gespeicherte Bildbytes bedeuten außerdem nicht, dass ein Chatmodell die Bilder gesehen hat.

## Nachweise

- [Vollständiger Importbericht mit erfolgreichem Commit](../../BFH_Import_2026-09-14/Cloud_Vorbestand.json)
- [Unabhängige Prüfung über den separaten Leserlogin nach dem Commit](Vollimport_Lesepruefung.json)
- [Historischer Bericht zum Drei-Dokumente-Piloten](Importpruefung_Pilot_2026-09-09.json)
- [Freigabe für den offiziellen Supabase-MCP](Supabase_MCP_Berechtigungen.json)
