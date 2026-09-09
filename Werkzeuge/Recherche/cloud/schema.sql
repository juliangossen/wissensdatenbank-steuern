-- Wissensdatenbank: vorbereitete Migration 1 für ein neues Supabase-Projekt.
-- PostgreSQL >= 16, pgvector im Schema extensions. Einmalig als Projekt-Administrator.
-- Keine Passwörter, keine öffentliche Data API. Originaldateien werden privat
-- als bytea in derselben Transaktion wie die Texte gespeichert.
-- Nach Veröffentlichung sind Release-Inhalte unveränderlich. Administratoren bleiben
-- technisch privilegiert; dies ist kein WORM-Speicher gegen den Datenbankeigentümer.
BEGIN;

CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_extension e JOIN pg_namespace n ON n.oid=e.extnamespace
    WHERE e.extname='vector' AND n.nspname='extensions'
  ) THEN RAISE EXCEPTION 'pgvector muss im Schema extensions installiert sein'; END IF;
END $$;

-- Neue Rollen; bestehende gleichnamige Rollen sind ein Konflikt, keine stille Übernahme.
CREATE ROLE kb_importer NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE kb_mcp NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
-- Der Einrichtungszugang muss diese Rollen für Import und Berechtigungstests
-- ausdrücklich übernehmen können, erbt ihre Rechte aber nicht automatisch.
GRANT kb_importer,kb_mcp TO CURRENT_USER WITH SET TRUE, INHERIT FALSE;
CREATE SCHEMA kb;
REVOKE ALL ON SCHEMA kb FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA kb, extensions TO kb_importer, kb_mcp;
ALTER DEFAULT PRIVILEGES IN SCHEMA kb REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

CREATE TABLE kb.schema_migrations (
  version text PRIMARY KEY,
  sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  installed_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE kb.schema_migrations ENABLE ROW LEVEL SECURITY;

CREATE TABLE kb.releases (
  release_id text PRIMARY KEY CHECK (length(release_id) BETWEEN 1 AND 200),
  manifest_sha256 text NOT NULL CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  embedding_model text,
  embedding_revision text,
  embedding_dimensions integer NOT NULL DEFAULT 384 CHECK (embedding_dimensions=384),
  expected_documents bigint NOT NULL CHECK (expected_documents>0),
  expected_provisions bigint NOT NULL CHECK (expected_provisions>0),
  expected_chunks bigint NOT NULL CHECK (expected_chunks>=0),
  expected_assets bigint NOT NULL CHECK (expected_assets>=0),
  expected_embeddings bigint NOT NULL CHECK (expected_embeddings>=0 AND expected_embeddings<=expected_chunks),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata)='object'),
  sealed_at timestamptz,
  CHECK (expected_embeddings=0 OR (embedding_model IS NOT NULL AND embedding_revision IS NOT NULL))
);

CREATE TABLE kb.documents (
  release_id text NOT NULL REFERENCES kb.releases(release_id),
  document_id text NOT NULL,
  title text NOT NULL CHECK (length(title)>0),
  abbreviation text NOT NULL,
  legal_area text NOT NULL,
  document_type text NOT NULL,
  source_path text NOT NULL,
  source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
  import_date date NOT NULL,
  source_status jsonb NOT NULL CHECK (jsonb_typeof(source_status)='array'),
  source_url text,
  body_markdown text NOT NULL,
  valid_from date DEFAULT NULL,
  valid_to date DEFAULT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata)='object'),
  PRIMARY KEY (release_id,document_id),
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_to>=valid_from)
);
COMMENT ON COLUMN kb.documents.import_date IS 'Technisches Importdatum; kein Rechtsstand oder Gültigkeitsdatum.';
COMMENT ON COLUMN kb.documents.valid_from IS 'Nur ausdrücklich belegtes Gültigkeitsdatum; sonst NULL.';
COMMENT ON COLUMN kb.documents.valid_to IS 'Nur ausdrücklich belegtes Ende der Gültigkeit; sonst NULL. Keine Ableitung aus Importdatum.';

CREATE TABLE kb.provisions (
  release_id text NOT NULL,
  provision_id text NOT NULL,
  document_id text NOT NULL,
  anchor text NOT NULL,
  label text NOT NULL,
  heading text NOT NULL,
  body_markdown text NOT NULL,
  ref_key text NOT NULL,
  ordinal integer NOT NULL CHECK (ordinal>=0),
  valid_from date DEFAULT NULL,
  valid_to date DEFAULT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata)='object'),
  PRIMARY KEY (release_id,provision_id),
  UNIQUE (release_id,document_id,provision_id),
  UNIQUE (release_id,document_id,anchor),
  FOREIGN KEY (release_id,document_id) REFERENCES kb.documents(release_id,document_id),
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_to>=valid_from)
);
CREATE INDEX provisions_document_order ON kb.provisions(release_id,document_id,ordinal);
CREATE INDEX provisions_reference ON kb.provisions(release_id,document_id,ref_key);

CREATE TABLE kb.search_chunks (
  release_id text NOT NULL,
  chunk_id text NOT NULL,
  provision_id text NOT NULL,
  document_id text NOT NULL,
  ordinal integer NOT NULL CHECK (ordinal>=0),
  body_text text NOT NULL CHECK (length(body_text)>0),
  embedding extensions.vector(384),
  embedding_model text,
  embedding_revision text,
  fts tsvector GENERATED ALWAYS AS (to_tsvector('pg_catalog.german'::regconfig,body_text)) STORED,
  PRIMARY KEY (release_id,chunk_id),
  UNIQUE (release_id,provision_id,ordinal),
  FOREIGN KEY (release_id,document_id,provision_id)
    REFERENCES kb.provisions(release_id,document_id,provision_id),
  CHECK ((embedding IS NULL AND embedding_model IS NULL AND embedding_revision IS NULL)
      OR (embedding IS NOT NULL AND embedding_model IS NOT NULL AND embedding_revision IS NOT NULL)),
  CHECK (embedding IS NULL OR extensions.vector_norm(embedding)>0)
);
CREATE INDEX chunks_fts ON kb.search_chunks USING gin(fts);
CREATE INDEX chunks_document ON kb.search_chunks(release_id,document_id);
-- Zunächst exakter Vektorvergleich in einem vorgefilterten Release. Ein ungeprüfter
-- globaler HNSW-Index mit anschließendem Releasefilter kann Treffer verlieren.

CREATE TABLE kb.assets (
  release_id text NOT NULL,
  asset_id text NOT NULL,
  document_id text NOT NULL,
  provision_id text,
  relative_path text NOT NULL,
  object_key text NOT NULL,
  sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  mime_type text NOT NULL,
  byte_size bigint NOT NULL CHECK (byte_size>=0),
  storage_bucket text NOT NULL DEFAULT 'knowledge-assets' CHECK (storage_bucket='knowledge-assets'),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata)='object'),
  -- Setzt der Importer erst nach Upload UND Download-/Hashprüfung der Objektbytes.
  verified_at timestamptz,
  PRIMARY KEY (release_id,asset_id),
  FOREIGN KEY (release_id,document_id) REFERENCES kb.documents(release_id,document_id),
  FOREIGN KEY (release_id,document_id,provision_id)
    REFERENCES kb.provisions(release_id,document_id,provision_id),
  CHECK (object_key !~ '(^/|(^|/)\.\.(/|$)|[\\])'),
  CHECK (relative_path !~ '(^/|(^|/)\.\.(/|$)|[\\])')
);

CREATE TABLE kb.active_release (
  singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
  release_id text NOT NULL REFERENCES kb.releases(release_id),
  activated_at timestamptz NOT NULL
);

CREATE TABLE kb.asset_contents (
  release_id text NOT NULL,
  asset_id text NOT NULL,
  content bytea NOT NULL,
  PRIMARY KEY (release_id,asset_id),
  FOREIGN KEY (release_id,asset_id) REFERENCES kb.assets(release_id,asset_id)
);

-- Eine einmal veröffentlichte Fassung ist append-only. Auch Staging-Inhalte sind
-- insert-only: ein fehlerhafter Import erhält eine neue release_id.
CREATE FUNCTION kb.guard_release() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  IF TG_OP='INSERT' THEN
    IF NEW.sealed_at IS NOT NULL THEN RAISE EXCEPTION 'Direkt versiegelter Import verboten'; END IF;
    RETURN NEW;
  END IF;
  IF TG_OP='UPDATE' AND OLD.sealed_at IS NULL AND NEW.sealed_at IS NOT NULL
     AND (to_jsonb(NEW)-'sealed_at')=(to_jsonb(OLD)-'sealed_at') THEN RETURN NEW; END IF;
  RAISE EXCEPTION 'Release-Metadaten sind unveränderlich';
END $$;
CREATE TRIGGER immutable_release BEFORE INSERT OR UPDATE OR DELETE ON kb.releases
FOR EACH ROW EXECUTE FUNCTION kb.guard_release();

CREATE FUNCTION kb.guard_content() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE r kb.releases%ROWTYPE;
BEGIN
  IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Release-Inhalte sind insert-only'; END IF;
  -- Derselbe Zeilenlock wird vom Aktivieren benutzt; konkurrierende Importe können
  -- nach der Versiegelung keine Zeilen mehr einschieben.
  SELECT * INTO r FROM kb.releases WHERE release_id=NEW.release_id FOR UPDATE;
  IF NOT FOUND OR r.sealed_at IS NOT NULL THEN RAISE EXCEPTION 'Release fehlt oder ist versiegelt'; END IF;
  IF TG_OP='UPDATE' THEN
    IF TG_TABLE_NAME='assets' THEN
      IF OLD.verified_at IS NULL AND NEW.verified_at IS NOT NULL
         AND (to_jsonb(NEW)-'verified_at')=(to_jsonb(OLD)-'verified_at') THEN RETURN NEW; END IF;
    END IF;
    RAISE EXCEPTION 'Release-Inhalte sind insert-only; nur die erste Uploadbestätigung ist erlaubt';
  END IF;
  IF TG_TABLE_NAME='assets' THEN
    IF NEW.verified_at IS NOT NULL THEN RAISE EXCEPTION 'Asset muss ungeprüft eingefügt werden'; END IF;
  END IF;
  IF TG_TABLE_NAME='asset_contents' THEN
    IF NOT EXISTS (SELECT 1 FROM kb.assets a WHERE a.release_id=NEW.release_id AND a.asset_id=NEW.asset_id
       AND a.byte_size=octet_length(NEW.content) AND a.sha256=encode(sha256(NEW.content),'hex')) THEN
      RAISE EXCEPTION 'Assetbytes passen nicht zu Größe und Prüfsumme';
    END IF;
  END IF;
  IF TG_TABLE_NAME='search_chunks' THEN
    IF NEW.embedding IS NOT NULL THEN
      IF NEW.embedding_model IS DISTINCT FROM r.embedding_model
         OR NEW.embedding_revision IS DISTINCT FROM r.embedding_revision THEN
        RAISE EXCEPTION 'Embedding-Modell/Revision passt nicht zum Release';
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER immutable_document BEFORE INSERT OR UPDATE OR DELETE ON kb.documents FOR EACH ROW EXECUTE FUNCTION kb.guard_content();
CREATE TRIGGER immutable_provision BEFORE INSERT OR UPDATE OR DELETE ON kb.provisions FOR EACH ROW EXECUTE FUNCTION kb.guard_content();
CREATE TRIGGER immutable_chunk BEFORE INSERT OR UPDATE OR DELETE ON kb.search_chunks FOR EACH ROW EXECUTE FUNCTION kb.guard_content();
CREATE TRIGGER immutable_asset BEFORE INSERT OR UPDATE OR DELETE ON kb.assets FOR EACH ROW EXECUTE FUNCTION kb.guard_content();
CREATE TRIGGER immutable_asset_content BEFORE INSERT OR UPDATE OR DELETE ON kb.asset_contents FOR EACH ROW EXECUTE FUNCTION kb.guard_content();

CREATE FUNCTION kb.confirm_asset_upload(p_release_id text,p_asset_id text,p_observed_sha256 text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
  -- Der Importer berechnet observed_sha256 nach dem Rücklesen der gespeicherten
  -- Bytes. Zusätzlich prüft SQL den tatsächlich gespeicherten Inhalt selbst.
  UPDATE kb.assets SET verified_at=clock_timestamp()
    WHERE release_id=p_release_id AND asset_id=p_asset_id AND sha256=p_observed_sha256 AND verified_at IS NULL
      AND EXISTS (SELECT 1 FROM kb.asset_contents c WHERE c.release_id=p_release_id AND c.asset_id=p_asset_id
        AND encode(sha256(c.content),'hex')=p_observed_sha256 AND octet_length(c.content)=kb.assets.byte_size);
  IF NOT FOUND THEN RAISE EXCEPTION 'Asset fehlt, Prüfsumme falsch oder bereits bestätigt'; END IF;
END $$;

CREATE FUNCTION kb.activate_release(p_release_id text,p_manifest_sha256 text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE r kb.releases%ROWTYPE;
BEGIN
  -- Serialisiert alle Pointerwechsel, einschließlich des ersten leeren Pointers.
  PERFORM pg_advisory_xact_lock(78234001);
  SELECT * INTO r FROM kb.releases WHERE release_id=p_release_id FOR UPDATE;
  IF NOT FOUND OR r.manifest_sha256 IS DISTINCT FROM p_manifest_sha256 THEN
    RAISE EXCEPTION 'Release oder Manifest-Prüfsumme stimmt nicht';
  END IF;
  IF r.sealed_at IS NULL THEN
    IF (SELECT count(*) FROM kb.documents WHERE release_id=p_release_id)<>r.expected_documents
       OR (SELECT count(*) FROM kb.provisions WHERE release_id=p_release_id)<>r.expected_provisions
       OR (SELECT count(*) FROM kb.search_chunks WHERE release_id=p_release_id)<>r.expected_chunks
       OR (SELECT count(*) FROM kb.assets WHERE release_id=p_release_id)<>r.expected_assets
       OR (SELECT count(*) FROM kb.asset_contents WHERE release_id=p_release_id)<>r.expected_assets
       OR (SELECT count(*) FROM kb.search_chunks WHERE release_id=p_release_id AND embedding IS NOT NULL)<>r.expected_embeddings THEN
      RAISE EXCEPTION 'Release unvollständig: Manifest-Zählwerte stimmen nicht';
    END IF;
    IF EXISTS (SELECT 1 FROM kb.documents d WHERE d.release_id=p_release_id
               AND NOT EXISTS (SELECT 1 FROM kb.provisions p WHERE p.release_id=d.release_id AND p.document_id=d.document_id)) THEN
      RAISE EXCEPTION 'Dokument ohne Vorschriften-/Textblöcke';
    END IF;
    IF EXISTS (SELECT 1 FROM kb.assets WHERE release_id=p_release_id AND verified_at IS NULL) THEN
      RAISE EXCEPTION 'Private Asset-Uploads sind noch nicht bestätigt';
    END IF;
    UPDATE kb.releases SET sealed_at=clock_timestamp() WHERE release_id=p_release_id;
  END IF;
  INSERT INTO kb.active_release(singleton,release_id,activated_at) VALUES(true,p_release_id,clock_timestamp())
  ON CONFLICT (singleton) DO UPDATE SET release_id=excluded.release_id,activated_at=excluded.activated_at;
  -- Versiegelung und Pointerwechsel werden erst mit demselben COMMIT sichtbar.
END $$;

-- Feste Lesefunktionen. Keine frei eingebbaren SQL-Abfragen; keine dynamischen SQLs.
-- Alle berechtigten Nutzer dieses privaten MCP lesen dieselbe Wissensdatenbank.
-- Die Nutzerzulassung erfolgt vor jedem MCP-Aufruf am OAuth-/Serverrand.
CREATE FUNCTION kb.release_info() RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT jsonb_build_object('release_id',r.release_id,'manifest_sha256',r.manifest_sha256,
   'created_at',r.created_at,'sealed_at',r.sealed_at,'embedding_model',r.embedding_model,
   'embedding_revision',r.embedding_revision,'embedding_dimensions',r.embedding_dimensions,
   'documents',r.expected_documents,'provisions',r.expected_provisions,'chunks',r.expected_chunks,
   'assets',r.expected_assets,'embeddings',r.expected_embeddings)
 FROM kb.active_release a JOIN kb.releases r USING(release_id) WHERE a.singleton AND r.sealed_at IS NOT NULL
$$;

CREATE FUNCTION kb.hybrid_search(
  p_query text,p_embedding extensions.vector DEFAULT NULL,p_embedding_model text DEFAULT NULL,
  p_embedding_revision text DEFAULT NULL,p_limit integer DEFAULT 10,
  p_release_id text DEFAULT NULL,p_document_id text DEFAULT NULL
) RETURNS TABLE(release_id text,document_id text,provision_id text,chunk_id text,
  title text,abbreviation text,label text,heading text,anchor text,excerpt text,
  score double precision,import_date date,source_status jsonb,
  source_url text,valid_from date,valid_to date,document_valid_from date,document_valid_to date)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$
DECLARE rid text; model text; revision text;
BEGIN
  IF p_query IS NULL OR length(btrim(p_query))=0 OR length(p_query)>8000 THEN
    RAISE EXCEPTION 'Suchtext muss 1 bis 8000 Zeichen enthalten';
  END IF;
  IF p_limit IS NULL OR p_limit<1 OR p_limit>30 THEN RAISE EXCEPTION 'Limit muss zwischen 1 und 30 liegen'; END IF;
  SELECT r.release_id,r.embedding_model,r.embedding_revision INTO rid,model,revision
  FROM kb.releases r WHERE r.release_id=coalesce(p_release_id,(SELECT a.release_id FROM kb.active_release a WHERE a.singleton))
    AND r.sealed_at IS NOT NULL;
  IF NOT FOUND THEN RETURN; END IF;
  IF p_embedding IS NOT NULL AND (extensions.vector_dims(p_embedding)<>384 OR extensions.vector_norm(p_embedding)=0
      OR p_embedding_model IS DISTINCT FROM model OR p_embedding_revision IS DISTINCT FROM revision) THEN
    RAISE EXCEPTION 'Suchvektor muss 384 Dimensionen und dasselbe Modell/dieselbe Revision wie das Release verwenden';
  END IF;
  RETURN QUERY
  WITH query AS (SELECT websearch_to_tsquery('pg_catalog.german'::regconfig,p_query) AS terms),
  lexical_candidates AS (
    SELECT c.chunk_id,ts_rank_cd(c.fts,q.terms) AS rank_value
    FROM kb.search_chunks c CROSS JOIN query q
    WHERE c.release_id=rid AND (p_document_id IS NULL OR c.document_id=p_document_id) AND c.fts@@q.terms
    ORDER BY rank_value DESC,c.chunk_id LIMIT p_limit*4
  ),
  lexical AS (SELECT x.chunk_id,row_number() OVER(ORDER BY x.rank_value DESC,x.chunk_id) AS rank_no FROM lexical_candidates x),
  -- Materialisierung grenzt den exakten Vergleich vor der Distanzberechnung ein.
  vector_scope AS MATERIALIZED (
    SELECT c.chunk_id,c.embedding FROM kb.search_chunks c
    WHERE p_embedding IS NOT NULL AND c.release_id=rid AND c.embedding IS NOT NULL
      AND (p_document_id IS NULL OR c.document_id=p_document_id)
  ),
  vector_candidates AS (
    SELECT c.chunk_id,c.embedding OPERATOR(extensions.<=>) p_embedding AS distance FROM vector_scope c
    ORDER BY distance,c.chunk_id LIMIT p_limit*4
  ),
  semantic AS (SELECT x.chunk_id,row_number() OVER(ORDER BY x.distance,x.chunk_id) AS rank_no FROM vector_candidates x),
  fusion AS (
    SELECT coalesce(l.chunk_id,s.chunk_id) AS id,
      (coalesce(1.0/(60+l.rank_no),0.0)+coalesce(1.0/(60+s.rank_no),0.0))::double precision AS rrf
    FROM lexical l FULL JOIN semantic s USING(chunk_id)
  ),
  best_chunks AS (
    SELECT DISTINCT ON (c.provision_id) f.id,f.rrf
    FROM fusion f JOIN kb.search_chunks c ON c.release_id=rid AND c.chunk_id=f.id
    ORDER BY c.provision_id,f.rrf DESC,c.chunk_id
  )
  SELECT c.release_id,c.document_id,c.provision_id,c.chunk_id,d.title,d.abbreviation,
    p.label,p.heading,p.anchor,left(c.body_text,1200),f.rrf,d.import_date,d.source_status,
    d.source_url,p.valid_from,p.valid_to,d.valid_from,d.valid_to
  FROM best_chunks f JOIN kb.search_chunks c ON c.release_id=rid AND c.chunk_id=f.id
  JOIN kb.provisions p ON p.release_id=c.release_id AND p.provision_id=c.provision_id
  JOIN kb.documents d ON d.release_id=c.release_id AND d.document_id=c.document_id
  ORDER BY f.rrf DESC,c.chunk_id LIMIT p_limit;
END $$;

CREATE FUNCTION kb.fetch_provision(p_release_id text,p_provision_id text,p_offset integer DEFAULT 0,p_chars integer DEFAULT 20000)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$
DECLARE answer jsonb;
BEGIN
  IF p_offset IS NULL OR p_offset<0 OR p_chars IS NULL OR p_chars<1 OR p_chars>20000 THEN
    RAISE EXCEPTION 'Ungültiges Textfenster';
  END IF;
  SELECT jsonb_build_object('release_id',p.release_id,'provision_id',p.provision_id,'document_id',p.document_id,
    'title',d.title,'abbreviation',d.abbreviation,'label',p.label,'heading',p.heading,'anchor',p.anchor,
    'body_markdown',substring(p.body_markdown FROM p_offset+1 FOR p_chars),'offset',p_offset,
    'total_chars',length(p.body_markdown),'next_offset',CASE WHEN p_offset+p_chars<length(p.body_markdown) THEN p_offset+p_chars ELSE NULL END,
    'import_date',d.import_date,'source_status',d.source_status,'source_url',d.source_url,
    'document_valid_from',d.valid_from,'document_valid_to',d.valid_to,'provision_valid_from',p.valid_from,'provision_valid_to',p.valid_to)
  INTO answer FROM kb.provisions p JOIN kb.documents d USING(release_id,document_id)
    JOIN kb.releases r USING(release_id)
  WHERE p.release_id=p_release_id AND p.provision_id=p_provision_id AND r.sealed_at IS NOT NULL;
  RETURN answer;
END $$;

CREATE FUNCTION kb.asset_info(p_release_id text,p_asset_id text) RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT jsonb_build_object('release_id',a.release_id,'asset_id',a.asset_id,'document_id',a.document_id,
   'provision_id',a.provision_id,'relative_path',a.relative_path,'storage_bucket',a.storage_bucket,
   'object_key',a.object_key,'storage_backend','postgres','sha256',a.sha256,'mime_type',a.mime_type,'byte_size',a.byte_size)
 FROM kb.assets a JOIN kb.releases r USING(release_id)
 WHERE a.release_id=p_release_id AND a.asset_id=p_asset_id AND r.sealed_at IS NOT NULL
$$;

CREATE FUNCTION kb.fetch_asset_bytes(p_release_id text,p_asset_id text,p_offset integer DEFAULT 0,p_bytes integer DEFAULT 1048576)
RETURNS bytea LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$
DECLARE answer bytea;
BEGIN
  IF p_offset IS NULL OR p_offset<0 OR p_bytes IS NULL OR p_bytes<1 OR p_bytes>8388608 THEN
    RAISE EXCEPTION 'Ungültiges Dateifenster';
  END IF;
  SELECT substring(c.content FROM p_offset+1 FOR p_bytes) INTO answer
    FROM kb.asset_contents c JOIN kb.releases r USING(release_id)
    WHERE c.release_id=p_release_id AND c.asset_id=p_asset_id AND r.sealed_at IS NOT NULL;
  RETURN answer;
END $$;

-- RLS bleibt für öffentliche Supabase-Rollen vollständig geschlossen. Nur der
-- getrennte Backend-Importer darf Zeilen einfügen und seine Importdaten prüfen.
ALTER TABLE kb.releases ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.provisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.search_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.active_release ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.asset_contents ENABLE ROW LEVEL SECURITY;
CREATE POLICY importer_release_read ON kb.releases FOR SELECT TO kb_importer USING(true);
CREATE POLICY importer_release_insert ON kb.releases FOR INSERT TO kb_importer WITH CHECK(sealed_at IS NULL);
CREATE POLICY importer_document_read ON kb.documents FOR SELECT TO kb_importer USING(true);
CREATE POLICY importer_document_insert ON kb.documents FOR INSERT TO kb_importer WITH CHECK(true);
CREATE POLICY importer_provision_read ON kb.provisions FOR SELECT TO kb_importer USING(true);
CREATE POLICY importer_provision_insert ON kb.provisions FOR INSERT TO kb_importer WITH CHECK(true);
CREATE POLICY importer_chunk_read ON kb.search_chunks FOR SELECT TO kb_importer USING(true);
CREATE POLICY importer_chunk_insert ON kb.search_chunks FOR INSERT TO kb_importer WITH CHECK(true);
CREATE POLICY importer_asset_read ON kb.assets FOR SELECT TO kb_importer USING(true);
CREATE POLICY importer_asset_insert ON kb.assets FOR INSERT TO kb_importer WITH CHECK(true);
CREATE POLICY importer_asset_content_read ON kb.asset_contents FOR SELECT TO kb_importer USING(true);
CREATE POLICY importer_asset_content_insert ON kb.asset_contents FOR INSERT TO kb_importer WITH CHECK(true);
REVOKE ALL ON ALL TABLES IN SCHEMA kb FROM PUBLIC,anon,authenticated,kb_mcp;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA kb FROM PUBLIC,anon,authenticated,kb_mcp,kb_importer;
GRANT SELECT,INSERT ON kb.releases,kb.documents,kb.provisions,kb.search_chunks,kb.assets,kb.asset_contents TO kb_importer;
GRANT EXECUTE ON FUNCTION kb.activate_release(text,text) TO kb_importer;
GRANT EXECUTE ON FUNCTION kb.confirm_asset_upload(text,text,text) TO kb_importer;
GRANT EXECUTE ON FUNCTION kb.release_info(),kb.hybrid_search(text,extensions.vector,text,text,integer,text,text),
  kb.fetch_provision(text,text,integer,integer),kb.asset_info(text,text),
  kb.fetch_asset_bytes(text,text,integer,integer) TO kb_mcp;

-- Der Export behält storage_bucket/object_key für eine spätere Storage-Portierung.
-- Tatsächlich gelesen werden die privaten SQL-Bytes über fetch_asset_bytes.

COMMIT;
