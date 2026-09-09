# Prüfung des Recherche-Piloten und der Cloudübernahme

**Historischer Pilotbericht:** Seit 10.09.2026 ist die vollständige Sammlung mit 58 Dokumenten aktiv. Der aktuelle [Vollimport-Prüfnachweis](cloud/Vollimport_Pruefung.md) und der [archivierte Pilot-Importbericht](cloud/Importpruefung_Pilot_2026-09-09.json) trennen die beiden Prüfstände.

Geprüft am 09.09.2026 mit Python 3.14 unter Windows. Aktiver Pilotstand:
`r-ad68e666980668e7ca4e6b81`, Parser `registered-provisions-v3`.

## Lokaler Pilotlauf

| Prüfung | Ergebnis |
| --- | --- |
| Registrierte Quellen | UStG, UStAE und BewG |
| Vollständig abrufbare Fundstellen | 733 |
| Semantische Suchabschnitte | 3.226, jeweils 384 Dimensionen |
| Vollständige Textrekonstruktion | Alle 733 Fundstellen über 964 Textseiten zeichengetreu mit dem Parsergebnis verglichen |
| Originalabschnitte | Alle Normabschnitte stimmen mit den unveränderten Slices der registrierten Markdown-Dateien überein; zugehörige Fußnoten werden zusätzlich erhalten |
| Dateien | 61 registrierte Assets einschließlich der drei primären Originalquellen; sämtliche Bytes anhand SHA-256 geprüft |
| Exakte Referenzen | Mehrteilige UStAE-Nummern, Buchstabenzusätze und die zusammengefassten aufgehobenen Abschnitte 23.1–23.4 geprüft |
| Aktualisierung | Fehler während Import oder Embedding aktivieren keinen neuen Stand; vollständige frühere Fassungen bleiben über ihre IDs unverändert abrufbar |
| Cache | Geprüfte Vektoren beim erneuten Import wiederverwendet; Modell und Revision werden mitgeführt |
| MCP | Fünf lesende Werkzeuge; vollständiger Normtext und echtes Quellenbild erfolgreich über den SDK-Client abgerufen |
| HTTP | Eigenen temporären Server auf Loopback gestartet; SDK-Handshake, Werkzeugsuche und search/fetch über Streamable HTTP erfolgreich; Testserver danach beendet |
| Lokaler Cloud-Export | Manifest, JSONL, Originaltexte, Vektoren und Dateien erfolgreich in das PostgreSQL-Importformat übernommen; 3 Dokumente, 733 Fundstellen, 3.226 Suchabschnitte, 61 Assets |

Der erste Entwicklungsindex mit Parser v1 ist separat unter
`.daten/Entwicklung/` archiviert. Er ist nicht der aktive Recherchebestand.
Weitere vollständig importierte Sammlungsstände bleiben in der lokalen
Datenbank erhalten. Keiner dieser technischen Importstände wird als
automatisch gültige Gesetzesfassung ausgewiesen.

## Suchprobelauf

Sechs vorab gewählte technische Suchaufgaben: exakte Vorschrift, gemischt
genutzter Pkw, kleine Umsätze, Grundstücksbewertung, Betriebsvorrichtungen
und Rechnungsvoraussetzung. Bei jeder Aufgabe lag mindestens ein erwarteter
Ankertreffer unter den ersten acht Ergebnissen – sowohl bei der hybriden Suche
als auch in den beiden Einzelverfahren.

Die hybride Suche benötigte nach dem Laden des Modells rund **76–141 ms** pro
Frage; die erste Abfrage einschließlich Modellstart rund **4,1 Sekunden**.
Das sind Messwerte dieses Rechners und dieses kleinen Bestands, keine
Cloud-Latenzzusage. Aus diesem kleinen Probelauf lässt sich noch keine
Überlegenheit gegenüber reiner Begriffssuche ableiten. Die erwarteten
Ankerstellen sind keine fachlich geprüfte vollständige Vorschriftenliste.

Die einzelnen Fragen, Treffer und Messwerte stehen unter
`.daten/Pilotpruefung.json`; `evaluate.py` reproduziert die Prüfung. Ein
unabhängig fachlich geprüfter Fragenkatalog mit komplexen Sachverhalten,
historischen Zeiträumen und Quellenlücken steht noch aus.

## Automatisierte Prüfungen

40 Tests für Parser, Embeddings und lokalen Store sowie inzwischen 24 Cloudtests
(je acht für Normalisierung, Verbindungsprüfung und PostgreSQL-Leseadapter) bestanden. Die echten Modelltests
liefen mit `HF_HUB_OFFLINE=1`. Fehlerfälle verwenden ausschließlich temporäre
Testquellen. Die Verbindungsprüfung wurde ohne echte Zugangsdaten mit einem
Testadapter auf zulässiges Projekt, sichere Fehlerausgabe und ausschließlich
lesenden Datenbankzugriff geprüft.

Nach dem gemeldeten Verbindungsfehler wurde am 09.09.2026 die fehlende
Supabase-Root-CA ergänzt. Der vorherige TLS-Fehler war ohne Passwort
reproduzierbar. Mit der offiziellen CA wurden Zertifikatskette und Hostname
erfolgreich geprüft, sowohl über einen TLS-Protokolltest als auch mit dem
tatsächlich verwendeten psycopg/libpq-Treiber (`verify-full`). Der Treibertest
verweigerte mit `require_auth=none` absichtlich den anschließenden SASL-Austausch,
bevor ein Passwort gesendet wurde. Dieser Diagnosetest prüft TLS und Erreichbarkeit,
aber keine Anmeldung. Acht Verbindungstests prüfen unter anderem
CA-Manipulation, Migration des alten certifi-Pfads und Fehlerausgaben ohne
Geheimnisse. Details zur CA stehen in [cloud/zertifikate/README.md](cloud/zertifikate/README.md).

Der anschließende Nutzerlauf erreichte erfolgreich die Datenbankabfrage und
scheiterte erst mit `WINDOWS_SPEICHER (TypeError)` an `CredWrite`. Ursache war
die Übergabe vorab codierter Bytes: pywin32 erwartet beim Schreiben einen
Unicode-String und liefert beim Lesen UTF-16-LE-Bytes zurück
([offizielle Typdokumentation](https://mhammond.github.io/pywin32/PyCREDENTIAL.html)).
Die Schreibfunktion wurde korrigiert und liest den Zugang zur Kontrolle direkt
zurück. Ein echter Windows-Speichertest mit ausschließlich synthetischen Daten
bestätigte Schreiben, Lesen und Aktualisieren einschließlich Unicode und
Sonderzeichen. Er verwendet einen zufälligen eigenen Testeintrag und entfernt
diesen anschließend; echte Projektzugänge werden dabei nicht gelesen.

Der ursprüngliche Vorbereitungsstand wurde mit pglast v8.4 strukturell geparst
(61 Statements); dieser historische Stand ist in [cloud/Pruefung.json](cloud/Pruefung.json)
festgehalten. Inzwischen wurden die Migrationen und Funktionen zusätzlich auf
PostgreSQL 17.6 ausgeführt und die unten aufgeführten Laufzeitprüfungen abgeschlossen.

## Tatsächlicher Cloud-Stand

Im Supabase-Projekt `vtriyndfmuwzqwrkpkde` wurde die Pilotfassung
`r-ad68e666980668e7ca4e6b81` vollständig importiert, geprüft und aktiviert.
Der erste vollständige Lauf wurde mit ROLLBACK abgeschlossen; der folgende
Import wurde erfolgreich COMMITtet. Nachweise:
[Projektstatus](cloud/projekt.json), [Rollback-Probe](cloud/Importpruefung_rollback_rehearsal.json)
und [archivierter Pilot-Importbericht](cloud/Importpruefung_Pilot_2026-09-09.json).

| Cloudprüfung | Ergebnis |
| --- | --- |
| Zeilenvergleich mit Export | 3 Dokumente, 733 Fundstellen, 3.226 Suchvektoren und 61 Assets vollständig verglichen |
| Reader-SQL-Textabruf | Alle 733 Fundstellen über 832 Textfenster vollständig geprüft; Metadaten und Hashes erhalten |
| Originaldateien | Alle 61 Dateien zurückgelesen und geprüft; zusammen 25.216.644 Bytes |
| Exakte Referenzen | Hauptreferenzen und Metadaten-Aliase geprüft |
| Begriffssuche | Für alle drei Pilotdokumente ausgeführt |
| Rechte | Direkter Tabellenzugriff für `anon`, `authenticated` und `kb_mcp` verweigert; öffentliche Funktionsaufrufe verweigert |
| Unveränderlichkeit | Aktivierung durch Leser, Änderung durch Importer und Änderung versiegelter Inhalte verweigert |
| Leseranmeldung | Eigener `kb_reader_login`: tatsächliche Session-Pooler-Anmeldung und ausschließlich lesender Zugriff ohne direkte Tabellenrechte geprüft |

Die 832 Cloud-Textfenster verwenden andere Fenstergrößen als die 964 Seiten des
oben dokumentierten lokalen Probelaufs; beide Prüfungen betreffen sämtliche
733 Fundstellen. Diese Zahlen sind keine PDF-Seitenzahlen.

Die Quelldateien liegen privat als Bytes in `kb.asset_contents`. **Es wurde kein
Supabase-Storagebucket erstellt.** `storage_bucket` und `object_key` in älteren,
unveränderten Exportmetadaten bleiben lediglich ein späteres Portierungsziel.
Der tatsächliche Speicher ist `private_postgres_bytea`. Die Data API bleibt
auf Nutzerwunsch eingeschaltet; das private Schema `kb` wird nicht exponiert.

Einrichtungs- und Leserzugang liegen getrennt in der Windows-Anmeldeinformationsverwaltung.
Der Leser verwendet das Ziel `Wissensdatenbank/Supabase/vtriyndfmuwzqwrkpkde/Lesen`.
Zugangsdaten werden nicht in diesen Berichten gespeichert.

Auch der vollständige MCP-Lauf mit dem Cloudadapter ist inzwischen geprüft:
alle fünf Werkzeuge, Volltext mit SHA-256, BewG-Quellenbild, Referenzalias und
korrekte Ablehnung einer fehlenden Referenz. Bei sechs bekannten Suchaufgaben
erreichte die hybride Suche alle sechs erwarteten Anker. Warm lagen die
Antwortzeiten bei 183–208 ms, mit Modellstart bei rund 4,6 Sekunden. Das ist
ein technischer Probelauf dieses Pilotbestands, keine fachliche Vollständigkeitsprüfung.
Nachweis: [MCP-Cloudprüfung](cloud/MCP_Cloudpruefung.json).

Ein tatsächlich gestarteter lokaler HTTP-Server mit Cloudreader bestand
SDK-Verbindung, Auflistung aller fünf Werkzeuge sowie Suche und Textabruf:
[HTTP-Cloudprüfung](cloud/HTTP_Cloudpruefung.json). Der Aktualisierungslauf über
`Cloud_Aktualisieren.cmd`/`sync.py` wurde gegen die echte Cloud erfolgreich für
die unveränderte Fassung durchlaufen. Beide CMD-Startdateien stehen bereit.

**Noch offen:** dauerhaftes Hosting, OAuth und Remote-Verbindung zu ChatGPT/Claude.
Die Hostingwahl steht noch aus. Die geprüften lokalen MCP-Transporte stellen
noch keinen dauerhaft erreichbaren Remote-Connector bereit.

Das vollständige Übertragungspaket bleibt lokal erhalten:

```text
.daten/Cloud_Pakete/Stand_2026-09-09/r-ad68e666980668e7ca4e6b81/
├── Export/      # geprüfte lokale Recherchefassung mit Originaldateien
└── Supabase/    # geprüftes und inzwischen importiertes PostgreSQL-Format
```

Die nebenläufige TXT-Aufbereitung und die registrierten Markdown-Quelldateien
wurden nicht verändert. Registrierte archivierte Originale wurden nur gelesen.
