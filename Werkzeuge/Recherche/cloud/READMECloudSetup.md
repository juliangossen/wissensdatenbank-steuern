# Supabase mit Claude und ChatGPT verwenden

Stand: 14.09.2026. Die gewählte persönliche Verbindung nutzt den **offiziellen Supabase-MCP**. Supabase stellt den Remote-Endpunkt und die Anmeldung bereit. Ein eigener Python-Server oder ein selbst eingerichteter OAuth-Dienst ist für diesen Zugang nicht erforderlich. Die Schrittfolge und kopierbare Projektanweisung stehen in **[Chat_KI_starten.md](../../../Chat_KI_starten.md)**.

## Verbindungs- und Importstand

Die Lesefunktionen im privaten Schema `kb` sind für den Supabase-MCP freigegeben. Der Nutzer hat die Anmeldung und den Abruf der früheren Pilotfassung aus Claude bestätigt. Ein Abruf der neuen Vollfassung innerhalb der Claude-Oberfläche ist noch nicht dokumentiert. ChatGPT erhält eine eigene Verbindung mit derselben Projektadresse.

**Der vollständige Bestand ist in Supabase gespeichert und aktiviert.** Die aktive Fassung `r-d3c4b6a7e0e2bb66a0693478` umfasst **60 Dokumente, 14.195 Fundstellen und Dokumentteile, 23.358 Suchvektoren sowie 1.187 Dateieinträge**. Die Dateiinhalte umfassen zusammen **280.955.832 Bytes**. Der Import wurde am **14.09.2026 um 21:24 Uhr (UTC)** erfolgreich festgeschrieben; der Importlauf fragte die aktive Fassung nach dem COMMIT erneut ab.

Alle Datenzeilen einschließlich Texte, Metadaten und Vektoren sowie alle Dateibytes wurden verglichen. Die Lese-API lieferte sämtliche Fundstellen vollständig über **14.485 Textfenster**; Volltextsuche und **1.095 exakte Referenz- und Aliasprüfungen** deckten alle 60 Dokumente ab. Nachweise: [BFH-Importabschluss](../../BFH_Import_2026-09-14/Abschluss.md) und [fester Importbericht mit `committed=true`](../../BFH_Import_2026-09-14/Cloud_Importpruefung.json). Die frühere Pilotfassung `r-ad68e666980668e7ca4e6b81` bleibt als historische Fassung erhalten; ihr [Importbericht ist separat archiviert](Importpruefung_Pilot_2026-09-09.json).

Die [gesonderte Leserprüfung nach COMMIT](Vollimport_Lesepruefung.json) gehört zur historischen Fassung `r-2ba1572b7978ca909270331f` mit 58 Dokumenten. Sie bestätigte damals den Umfang über die eigene Leseranmeldung, vollständige Abrufe von EStG § 7 und AO § 146 einschließlich SHA-256 sowie einen passenden Volltextsuchtreffer. Für die aktuelle Fassung wurde kein zusätzlicher Test mit separater Leseranmeldung und kein erneuter Abruf aus einer Claude- oder ChatGPT-Oberfläche durchgeführt; die aktuellen Leseprüfungen gehören zum Importlauf.

## Persönliche MCP-Verbindung

Projekt: `steuerrecht-wissensdatenbank` (`vtriyndfmuwzqwrkpkde`). Diese vollständige Adresse verwenden:

```text
https://mcp.supabase.com/mcp?project_ref=vtriyndfmuwzqwrkpkde&read_only=true&features=database
```

Die Parameter begrenzen die Verbindung auf dieses Projekt, Lesezugriff und Datenbankwerkzeuge. Anmeldung und Organisationsauswahl erfolgen bei Supabase. Claude und ChatGPT werden jeweils separat verbunden; der Datenbankzugang aus der Windows-Anmeldeinformationsverwaltung wird dabei nicht in den Chat kopiert. [Offizielle Supabase-MCP-Anleitung](https://supabase.com/docs/guides/ai-tools/mcp).

Der Connector verwendet `execute_sql`. Die Projektanweisung in [Chat_KI_starten.md](../../../Chat_KI_starten.md) beginnt mit `kb.release_info()`, ermittelt Dokumentkennungen, sucht mit `kb.hybrid_search` und liest Treffer über `kb.read_item` vollständig nach. Exakte Vorschriften werden mit `kb.lookup_provision` aufgelöst. Folgeabrufe verwenden dieselbe `release_id`, damit eine laufende Recherche bei einer Aktualisierung nicht unbemerkt zwischen Fassungen wechselt.

Ohne übergebenen Suchvektor arbeitet `kb.hybrid_search` als deutsche Volltextsuche. Das lokal ausgeführte E5-Modell wird vom offiziellen MCP nicht automatisch gestartet. Mehrere kurze Fachbegriffe und Synonyme sind deshalb Teil der Rechercheanweisung. Quellenbilder liegen in der Datenbank; ihre Existenz bedeutet nicht, dass der SQL-Connector sie visuell gelesen hat.

## Umfang und Ablage

Die **60 registrierten Hauptdokumente stammen aus 52 PDF- und 8 TXT-Originalen**. Die zugehörigen Markdown-Haupttexte werden vollständig erschlossen. Alle Dateien der registrierten Standordner werden zusätzlich archiviert: Originale, Quellenabbildungen, Ergänzungen und Prüfbelege. Programmcode, Modelle und Cache sind nicht Bestandteil dieses Quellenarchivs.

| Inhalt | Private Datenbankablage |
| --- | --- |
| Unveränderliche Fassungen und aktive Fassung | `kb.releases`, `kb.active_release` |
| Vollständige Markdown-Texte, Fundstellen und Quellenangaben | `kb.documents`, `kb.provisions` |
| Deutsche Volltextsuche und vorhandene 384-dimensionale Vektoren | `kb.search_chunks` |
| Dateimetadaten und unveränderte Datei-Bytes | `kb.assets`, `kb.asset_contents` |

Ein Supabase-Storagebucket wurde hierfür nicht erstellt. `storage_bucket` und `object_key` in den Exportmetadaten stammen aus dem portierbaren Exportformat; der tatsächliche Speicher ist PostgreSQL. Die Lese-API meldet `storage_backend='postgres'`.

Ergänzungen behalten ihren eigenen Quellpfad und ihre eigene Prüfsumme. Metadaten unterscheiden Vorschriften, ergänzende Quellen und sonstige Dokumentteile. Generierte Fundstellenkennungen werden nicht als angeblich vorhandene Anker in der Originaldatei ausgegeben. Quellenstand, Importdatum und belegte Geltungszeiträume bleiben getrennt; ohne Beleg bleiben Geltungsdaten unbekannt.

## Aktualisieren

**[Cloud_Aktualisieren.cmd](../../../Cloud_Aktualisieren.cmd)** prüft und veröffentlicht jetzt den gesamten registrierten Bestand. Neue oder geänderte Quellen werden zuerst lokal aufbereitet, geprüft und in `Bestand.json` registriert. Danach erstellt der Lauf den lokalen Index und das Exportpaket; unveränderte Embeddings werden wiederverwendet.

Der Import vergleicht alle Datenzeilen einschließlich vollständiger Texte, Metadaten und Vektoren. Originaldateien werden nach dem Upload zurückgelesen und anhand von Größe und SHA-256 geprüft. Zusätzlich werden alle Fundstellen über die Lese-API vollständig gelesen, für jedes Dokument Such- und Referenzprüfungen durchgeführt und die Zugriffsgrenzen getestet. Erst wenn diese Prüfungen erfolgreich sind, werden Versiegelung und Wechsel der aktiven Fassung gemeinsam festgeschrieben. Eine unvollständige Übertragung ersetzt die bisherige Cloudfassung nicht.

Der maßgebliche lokale Export liegt unter `../.daten/Cloud_Pakete/`; der konkrete Pfad steht in `../.daten/Cloud_Paketpfad.json`. `publish.py` validiert dieses Paket direkt. Historische Pilotordner können zusätzlich ein normalisiertes Unterverzeichnis `Supabase` enthalten; neue Aktualisierungen benötigen diese zweite Dateikopie nicht. Frühere Cloudfassungen bleiben gezielt abrufbar.

## Leserechte und optionaler Python-Zugang

| Rolle oder Zugang | Aufgabe |
| --- | --- |
| Einrichtungszugang | Schema und Migrationen einrichten; lokal in der Windows-Anmeldeinformationsverwaltung gespeichert |
| `kb_importer` | Neue Fassungen importieren und nach Prüfung aktivieren |
| `kb_mcp` / `kb_reader_login` | Feste Lese-API für den Python-Adapter |
| `supabase_read_only_user` | Leseabfragen des offiziellen Supabase-MCP einschließlich der freigegebenen festen `kb`-Lesefunktionen |
| `anon` / `authenticated` | Kein Zugriff auf das private Schema und dessen Lesefunktionen |

Die [Migration 004](004_supabase_mcp_reader.sql) ergänzt die Leserechte für den offiziellen MCP. Der [Berechtigungsnachweis](Supabase_MCP_Berechtigungen.json) dokumentiert erfolgreiche Leseprüfungen und abgewiesene Aktivierungs-, Schreib- und anonyme Leseversuche; außerdem die vom Nutzer bestätigte Claude-Anmeldung. Das private Schema `kb` ist nicht über die Data API exponiert. Bereits angewandte Migrationen bleiben unverändert.

Der vorhandene [Python-Adapter](postgres_store.py) unterstützt weiterhin `search`, `fetch`, `get_provision`, `list_versions` und `fetch_asset`. Er berechnet Suchvektoren lokal und verbindet sich als eigener Leser mit verifiziertem TLS. [Cloud_Recherche_starten.cmd](../../../Cloud_Recherche_starten.cmd) nutzt diesen Zugang. Er ist eine zusätzliche Möglichkeit für hybride Suche und Dateiabrufe auf diesem PC; die direkte Chatverbindung benötigt sein Hosting nicht.

## Nachweise

- [Aktueller BFH-Importabschluss](../../BFH_Import_2026-09-14/Abschluss.md), [fester Cloud-Importnachweis](../../BFH_Import_2026-09-14/Cloud_Importpruefung.json) und [Projektstatus](projekt.json)
- Historische Fassung mit 58 Dokumenten: [Vollimport und Abnahme](Vollimport_Pruefung.md), [damaliger Importbericht](../../BFH_Import_2026-09-14/Cloud_Vorbestand.json) und [separate Leserprüfung](Vollimport_Lesepruefung.json)
- [Historischer Vollimport-Exportvertrag für 58 Dokumente](Vollimport_Exportvertrag.json): lokaler Vertragstest, keine Cloudübertragung
- [Supabase-MCP-Berechtigungen und Benutzerbestätigung](Supabase_MCP_Berechtigungen.json)
- Historische Pilotprüfungen: [Cloudimport vom 09.09.2026](Importpruefung_Pilot_2026-09-09.json), [Rechercheprüfung](../Pruefung.md), [Python-MCP mit Cloudreader](MCP_Cloudpruefung.json), [lokaler HTTP-Transport](HTTP_Cloudpruefung.json)

Die historischen Pilotmessungen beziehen sich auf drei Dokumente; die Vollimport- und Leserprüfung vom 10.09.2026 betrifft 58 Dokumente. Der aktuelle Cloudimport mit 60 Dokumenten ist im BFH-Importbericht separat nachgewiesen. Die bisherigen Quellen behalten ihre Erfassung vom 09.09.2026; die beiden BFH-Webkopien wurden am 14.09.2026 ergänzt. Weder Erfassung noch Cloudabschluss sind neue rechtliche Geltungsdaten.