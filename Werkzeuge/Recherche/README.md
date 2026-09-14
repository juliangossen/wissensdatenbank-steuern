# Wissensdatenbank für Claude und ChatGPT

Stand: 14.09.2026. Die Fragen werden direkt in Claude oder ChatGPT gestellt. Die persönliche Verbindung verwendet den offiziellen Supabase-MCP und die gemeinsame Datenbank `steuerrecht-wissensdatenbank`. Dafür sind kein eigener MCP-Server und kein laufendes Recherchefenster auf diesem PC erforderlich. Einrichtung und Projektanweisung: **[Chat_KI_starten.md](../../Chat_KI_starten.md)**.

## Aktueller Stand

**Alle 60 registrierten Dokumente sind vollständig in Supabase gespeichert und aktiviert.** Die Cloudfassung `r-d3c4b6a7e0e2bb66a0693478` enthält **14.195 Fundstellen und Dokumentteile**, **23.358 Suchvektoren** sowie **1.187 Dateieinträge mit insgesamt 280.955.832 Bytes**. Der Import wurde am **14.09.2026 um 21:24 Uhr (UTC)** erfolgreich abgeschlossen. Alle gespeicherten Texte, Metadaten, Vektoren und Dateiinhalte wurden zurückgelesen und verglichen; sämtliche Fundstellen wurden zusätzlich über **14.485 Textfenster** der Lese-API geprüft.

Die persönliche Supabase-Anmeldung und der Abruf der früheren Pilotfassung aus Claude wurden vom Nutzer bestätigt. Die aktuelle Fassung ist im Importlauf über die Datenbank-Lese-API geprüft; ein neuer Test mit separater Leseranmeldung oder innerhalb der Claude- beziehungsweise ChatGPT-Oberfläche ist damit nicht dokumentiert. Eine bestehende Verbindung muss wegen des neuen Datenstands nicht erneut eingerichtet werden. Den freigegebenen Bestand zeigt `SELECT kb.release_info();`.

## Was zum vollständigen Bestand gehört

Das Register [Bestand.json](../../Bestand.json) enthält **60 Hauptdokumente mit 52 PDF- und 8 TXT-Ursprungsdateien**. Durchsucht werden die zugehörigen aufbereiteten Markdown-Texte: Paragraphen, Artikel, Richtlinienabschnitte, Randnummern und bislang nicht zugeordnete Textteile. Ergänzungen bleiben als eigene Quellen gekennzeichnet und behalten ihren eigenen Quellpfad und ihre Prüfsumme.

Alle Dateien der zugehörigen Standordner werden zusätzlich unverändert archiviert, einschließlich Originalen, Quellenabbildungen, Ergänzungen und Prüfbelegen. Die Dateieinträge sind deshalb zahlreicher als die 60 Hauptdokumente. Prüfunterlagen bleiben von Rechtsnormen unterscheidbar. Programmcode, virtuelle Umgebung, Modelle und Cache gehören nicht zu diesem Quellenarchiv.

Texte, Metadaten, Fußnoten, HTML-Tabellen und Verweise bleiben erhalten. Lange Texte werden in aufeinanderfolgenden Textfenstern gelesen. Importdatum, dokumentierter Quellenstand und fachlich belegte Geltungszeiträume bleiben getrennt; ein aktiver Sammlungsstand beweist keine rechtliche Geltung an einem bestimmten Tag.

## Benutzung und Aktualisierung

| Datei im Hauptordner | Aufgabe |
| --- | --- |
| [Chat_KI_starten.md](../../Chat_KI_starten.md) | Verbindung in Claude oder ChatGPT einrichten, Projektanweisung speichern und Fragen stellen |
| [Cloud_Aktualisieren.cmd](../../Cloud_Aktualisieren.cmd) | Alle registrierten Dokumente und zugehörigen Dateien prüfen, lokal indexieren und als geprüfte neue Supabase-Fassung veröffentlichen |
| [Cloud_Recherche_starten.cmd](../../Cloud_Recherche_starten.cmd) | Optionale Konsolenrecherche mit Texten aus Supabase und lokal berechnetem Suchvektor |
| [Recherche_starten.cmd](../../Recherche_starten.cmd) | Optionale Recherche im lokalen SQLite-Bestand |
| [Recherche_aktualisieren.cmd](../../Recherche_aktualisieren.cmd) | Gesamten registrierten Bestand lokal indexieren; ohne Cloudübertragung |

Geänderte Quellen müssen vor der Aktualisierung vollständig aufbereitet, geprüft und in `Bestand.json` registriert sein. Unveränderte Embeddings werden wiederverwendet. Die bisherige Cloudfassung bleibt verfügbar, während die nächste importiert wird. Erst nach dem vollständigen Rücklesen und Vergleichen der Texte, Vektoren und Dateien wird die neue Fassung aktiviert; frühere Fassungen bleiben abrufbar.

Nach erfolgreicher Cloudübertragung sind Fragen aus den verbundenen Chatkonten auch bei ausgeschaltetem PC möglich. Für neue lokale Änderungen muss der Aktualisierungslauf auf diesem Rechner ausgeführt werden.

## Welche Suche verwendet wird

| Zugang | Suchverfahren |
| --- | --- |
| Offizieller Supabase-MCP in Claude oder ChatGPT | Lesende SQL-Abfragen, deutsche Volltextsuche und exakter Fundstellenabruf |
| Lokale Python-Recherche und eigener Python-MCP | Volltextsuche, semantische Suche mit lokalem `multilingual-e5-small` oder deren Kombination |

Die Cloud speichert die vorhandenen 384-dimensionalen Vektoren. Der offizielle Supabase-MCP führt das lokale Embedding-Modell jedoch nicht automatisch aus. Ein Aufruf von `kb.hybrid_search` ohne Suchvektor ist daher eine Volltextsuche. Die Projektanweisung nutzt mehrere kurze Suchanfragen, Synonyme und vollständige Folgeabrufe. Details zum lokalen Modell und seiner festen Revision stehen in [EMBEDDINGS.md](EMBEDDINGS.md).

Der eigene Python-MCP mit `search`, `fetch`, `get_provision`, `list_versions` und `fetch_asset` bleibt für lokale Nutzung verfügbar. Sein zusätzliches Hosting und eine eigene OAuth-Integration sind für die gewählte direkte Verbindung nicht erforderlich. Die direkte SQL-Verbindung zeigt gespeicherte Bilddateien nicht automatisch als betrachtete Bilder an.

## Technische Ablage und Nachweise

Die lokale Datenbank verwendet SQLite/FTS5 und NumPy; Supabase verwendet PostgreSQL mit deutscher Volltextsuche und pgvector. Originaldateien liegen privat als unveränderte Bytes in `kb.asset_contents`. Ein Supabase-Storagebucket ist nicht Teil dieser Ablage. Der lokale Export unter `.daten/Cloud_Pakete/` enthält JSONL-Dateien, Originaldateien und ein Prüfsummenmanifest. Der aktuelle Paketpfad steht in `.daten/Cloud_Paketpfad.json`; ein zweites normalisiertes Dateipaket ist beim neuen Aktualisierungslauf nicht erforderlich.

- [Cloud-Einrichtung und Leserechte](cloud/READMECloudSetup.md)
- [BFH-Ergänzung und aktueller Cloudabschluss](../BFH_Import_2026-09-14/Abschluss.md), [fester Importnachweis](../BFH_Import_2026-09-14/Cloud_Importpruefung.json) und [aktueller Projektstatus](cloud/projekt.json)
- Historische Fassung mit 58 Dokumenten: [Vollimport und Abnahme](cloud/Vollimport_Pruefung.md) und [damalige separate Leserprüfung](cloud/Vollimport_Lesepruefung.json)
- [Historischer lokaler Exportvertrag für 58 Dokumente](cloud/Vollimport_Exportvertrag.json): ausdrücklich ein Test ohne Cloudübertragung
- [Supabase-MCP-Freigabe und vom Nutzer bestätigte Anmeldung](cloud/Supabase_MCP_Berechtigungen.json)
- Historische Pilotnachweise: [Cloudimport vom 09.09.2026](cloud/Importpruefung_Pilot_2026-09-09.json), [Pruefung.md](Pruefung.md), [Python-MCP mit Cloudreader](cloud/MCP_Cloudpruefung.json), [lokaler HTTP-Transport mit Cloudreader](cloud/HTTP_Cloudpruefung.json)

## Technische Befehle

PowerShell im Hauptordner der Wissensdatenbank:

```powershell
# Vollständiger lokaler Import; die Umgebung ist auf diesem PC eingerichtet
& 'Werkzeuge/Recherche/.venv/Scripts/python.exe' -B Werkzeuge/Recherche/cli.py import

# Sachverhaltssuche im lokalen Index
& 'Werkzeuge/Recherche/.venv/Scripts/python.exe' -B Werkzeuge/Recherche/cli.py search 'Vorsteuer bei privater Nutzung eines Firmenwagens'

# Exakte Fundstelle; längere Texte anschließend mit --offset weiter lesen
& 'Werkzeuge/Recherche/.venv/Scripts/python.exe' -B Werkzeuge/Recherche/cli.py get UStG '§ 15'

# Gesamten Bestand prüfen und in Supabase veröffentlichen
& 'Werkzeuge/Recherche/.venv/Scripts/python.exe' -B Werkzeuge/Recherche/cloud/sync.py
```

Für einen neuen Rechner werden die virtuelle Umgebung und Abhängigkeiten aus `requirements.txt` eingerichtet; das Modell wird beim ersten Start geladen. Zugangsdaten für lokale Cloudprogramme liegen in der Windows-Anmeldeinformationsverwaltung. Die persönliche Verbindung in Claude und ChatGPT verwendet stattdessen die Supabase-Anmeldung.

Querverweise müssen gezielt nachgeladen werden. Eine fehlende historische Quelle oder ein unbelegter Geltungszeitraum wird durch den Suchindex nicht ergänzt. Antworten sollen konkrete Fundstellen nennen und den Sachverhaltszeitraum sowie die dokumentierten Quellenstände berücksichtigen.
