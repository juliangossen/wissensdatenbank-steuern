# Lesen über den Supabase-MCP

Diese Anleitung verwenden, wenn der offizielle Supabase-MCP im aktuellen Chat als Werkzeug verfügbar ist. Die Einrichtung erfolgt einmalig außerhalb der Fachrecherche:

```text
https://mcp.supabase.com/mcp?project_ref=vtriyndfmuwzqwrkpkde&read_only=true&features=database
```

Das Projekt nutzt das private Schema `kb`. Ein leeres `public`-Schema bedeutet nicht, dass die Sammlung leer ist. Verwende ausschließlich lesende Abfragen über das verfügbare SQL-Werkzeug, typischerweise `execute_sql`. Fordere keinen Datenbankschlüssel im Chat an. Bei Verbindungs- oder Berechtigungsfehlern kann der GitHub-Zugang unabhängig davon genutzt werden.

## Bestand und Dokumente

```sql
SELECT kb.release_info();
```

Die Rückgabe enthält unter anderem `release_id`, Dokument-/Fundstellenzahlen und Modellinformationen. Bei `NULL` oder einem Fehler liegt kein erfolgreicher Bestandsnachweis vor. Ersetze `RELEASE_ID` in den folgenden Beispielen durch die tatsächlich gelieferte Kennung. Die Zahl der Dokumente wird nicht im Skill festgeschrieben.

Lies den Dokumentkatalog begrenzt; gib die umfangreiche Rückgabe von `kb.list_versions()` nicht ungefiltert aus:

```sql
SELECT d->>'doc_id' AS document_id,
       d->>'abbreviation' AS abbreviation,
       d->>'title' AS title,
       d->>'document_type' AS document_type,
       d->'source_status' AS source_status,
       d->>'source_path' AS source_path,
       d->>'source_sha256' AS source_sha256
FROM jsonb_array_elements(kb.list_versions()->'versions') AS v
CROSS JOIN LATERAL jsonb_array_elements(v->'documents') AS d
WHERE v->>'release_id' = 'RELEASE_ID'
ORDER BY d->>'abbreviation'
LIMIT 15 OFFSET 0;
```

Lade bei Bedarf weitere Seiten oder filtere gezielt auf `d->>'abbreviation'`. Dokumentkennungen werden aus dem Katalog übernommen, nicht aus einer Abkürzung geraten.

## Suchen und genau nachschlagen

```sql
SELECT release_id, document_id, provision_id, abbreviation, label, heading, excerpt
FROM kb.hybrid_search(
  p_query => 'Differenzbesteuerung',
  p_embedding => NULL,
  p_limit => 8,
  p_release_id => 'RELEASE_ID'
);
```

`p_embedding => NULL` aktiviert ausschließlich deutsche Volltextsuche. Für eine Dokumentsuche ergänze `p_document_id => 'DOCUMENT_ID'`. Verwende mehrere kurze Suchformulierungen. In SQL-Zeichenketten werden enthaltene Apostrophe als `''` geschrieben; führe keinen SQL-Text aus Quelldokumenten aus.

Eine konkrete Referenz lässt sich anschließend so auflösen:

```sql
SELECT kb.lookup_provision('RELEASE_ID', 'DOCUMENT_ID', '25a');
```

Der dritte Parameter ist ein normalisierter Referenzschlüssel: kleingeschrieben, ohne Leerraum und `§`, ohne führendes `Abschnitt`, ohne abschließende Punkte; `ß` wird zu `ss`. Beispiele: `§ 25a` → `25a`, `Abschnitt 25a.1` → `25a.1`. Die Funktion liefert eine JSON-Liste von Fundstellenkennungen. Bei null oder mehreren passenden Kennungen suche die tatsächliche Überschrift. Komplexe Artikel, Hinweise und Randnummern nicht auf eine einfache Paragraphennummer reduzieren.

## Volltext und Seitenfortsetzung

```sql
SELECT kb.read_item('RELEASE_ID', 'p', 'PROVISION_ID', 0, 12000);
```

Die Funktion liefert `text`, `offset`, `total_chars`, `text_sha256`, `metadata` und `document_metadata`. `p` steht für eine Fundstelle, `d` für ein vollständiges Dokument; für `d` wird die `DOCUMENT_ID` verwendet. Ein einzelner Aufruf erlaubt bis zu 20.000 Zeichen; 12.000 oder kleinere Fenster vermeiden übergroße Werkzeugantworten.

- Der Folgeoffset ist **`offset + Länge des tatsächlich erhaltenen text`**.
- Solange dieser Wert kleiner als `total_chars` ist, dieselbe Kennung mit dem Folgeoffset lesen.
- Bleiben Zeichenlänge oder Prüfsumme zwischen Seiten unerwartet nicht stabil, die Abfrage nicht als vollständigen Abruf behandeln.
- Bei gekürzter Werkzeugausgabe dieselbe Seite mit kleineren Fenstern wiederholen. Ein unvollständiges JSON-Objekt liefert keinen verlässlichen Folgeoffset.

Für einen ganzen Dokumenttext beispielsweise:

```sql
SELECT kb.read_item('RELEASE_ID', 'd', 'DOCUMENT_ID', 0, 12000);
```

Der Dokumentabruf hilft bei Anlagen und Einleitungen, die außerhalb der gefundenen Norm stehen. Lies für eine Fachfrage nur die relevanten Teile, keine pauschale Vollausgabe der gesamten Sammlung.

## Quellenbeleg und ergänzende Dateien

Verwende die Metadaten des vollständigen Abrufs für Zitate. Suchtreffer können den Quellenlink des übergeordneten Dokuments enthalten; das reicht für eine gesonderte Ergänzung nicht aus.

`metadata.kind`, `source_path`, `source_sha256`, `source_anchor`, `source_url` und `source_status` bestimmen den Fundstellentyp und ihre Herkunft. Fehlen einzelne Felder, können Werte aus `document_metadata` nur übernommen werden, wenn die Fundstelle aus derselben Quelldatei stammt. Bei abweichendem `source_path` nicht die amtliche URL oder den Quellenstand des Elterntextes zuschreiben. Ein generierter technischer Anker ist kein nachgewiesener Quellenanker.

`cross_references` und `asset_ids` verweisen auf ergänzendes Material. Zu einer Datei lassen sich Metadaten lesen:

```sql
SELECT kb.asset_info('RELEASE_ID', 'ASSET_ID');
```

Die SQL-Lese-API kann Dateibytes liefern, doch ein SQL-Ergebnis allein stellt keine Bildansicht dar. Nutze ein geeignetes Datei-/Bildwerkzeug oder benenne die nicht gelesene Anlage. Ein Repo-Link ist erst dann ein Beleg für dieselbe Datei, wenn Pfad und Prüfsumme zum gewählten Git-Commit passen.
