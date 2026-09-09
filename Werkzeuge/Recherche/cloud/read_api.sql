-- Zusätzliche feste Lesefunktionen für den MCP-Store-Vertrag.
-- Nach schema.sql als derselbe Eigentümer ausführen; keine Login-Rollen/Secrets.
BEGIN;

CREATE FUNCTION kb.list_versions() RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT jsonb_build_object('versions',coalesce(jsonb_agg(v.item ORDER BY v.created_at DESC,v.release_id),'[]'::jsonb))
 FROM (
   SELECT r.release_id,r.created_at,jsonb_build_object(
     'release_id',r.release_id,'active',EXISTS(SELECT 1 FROM kb.active_release a WHERE a.singleton AND a.release_id=r.release_id),
     'created_at',r.created_at,'metadata',r.metadata,
     'embedding_model',r.embedding_model,'embedding_revision',r.embedding_revision,'embedding_dimensions',r.embedding_dimensions,
     'documents',coalesce((SELECT jsonb_agg(d.metadata ORDER BY d.document_id) FROM kb.documents d WHERE d.release_id=r.release_id),'[]'::jsonb),
     'counts',jsonb_build_object('document_count',r.expected_documents,'provision_count',r.expected_provisions,
                               'chunk_count',r.expected_chunks,'asset_count',r.expected_assets)) AS item
   FROM kb.releases r WHERE r.sealed_at IS NOT NULL
 ) v
$$;

CREATE FUNCTION kb.lookup_provision(p_release_id text,p_document_id text,p_ref_key text) RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 WITH eligible AS (
   SELECT p.provision_id,p.ref_key,p.metadata
   FROM kb.provisions p JOIN kb.releases r USING(release_id)
   WHERE p.release_id=p_release_id AND p.document_id=p_document_id AND r.sealed_at IS NOT NULL
 ), exact AS (SELECT e.provision_id FROM eligible e WHERE e.ref_key=p_ref_key),
 matches AS (
   SELECT e.provision_id FROM exact e
   UNION ALL
   SELECT e.provision_id FROM eligible e
   WHERE NOT EXISTS(SELECT 1 FROM exact)
     AND EXISTS(
       SELECT 1 FROM jsonb_array_elements_text(
         CASE WHEN jsonb_typeof(e.metadata->'reference_aliases')='array'
              THEN e.metadata->'reference_aliases' ELSE '[]'::jsonb END
       ) alias(value)
       WHERE rtrim(regexp_replace(regexp_replace(replace(lower(alias.value),'ß','ss'),
                    '[[:space:]§]','','g'),'^abschnitt',''),'.')=p_ref_key
     )
 )
 SELECT coalesce(jsonb_agg(m.provision_id ORDER BY m.provision_id),'[]'::jsonb) FROM matches m
$$;

CREATE FUNCTION kb.read_item(p_release_id text,p_kind text,p_item_id text,p_offset integer DEFAULT 0,p_chars integer DEFAULT 12000)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$
DECLARE item_metadata jsonb; document_metadata jsonb; body text; total integer;
BEGIN
 IF p_kind IS NULL OR p_kind NOT IN ('p','d') OR p_offset IS NULL OR p_offset<0
    OR p_chars IS NULL OR p_chars<1 OR p_chars>20000 THEN
   RAISE EXCEPTION 'Ungültige Fundstellenart oder ungültiges Textfenster';
 END IF;
 IF p_kind='p' THEN
   SELECT p.metadata,d.metadata,p.body_markdown INTO item_metadata,document_metadata,body
   FROM kb.provisions p JOIN kb.documents d USING(release_id,document_id) JOIN kb.releases r USING(release_id)
   WHERE p.release_id=p_release_id AND p.provision_id=p_item_id AND r.sealed_at IS NOT NULL;
 ELSE
   SELECT d.metadata,d.metadata,d.body_markdown INTO item_metadata,document_metadata,body
   FROM kb.documents d JOIN kb.releases r USING(release_id)
   WHERE d.release_id=p_release_id AND d.document_id=p_item_id AND r.sealed_at IS NOT NULL;
 END IF;
 IF NOT FOUND THEN RETURN NULL; END IF;
 total:=length(body);
 IF p_offset>total THEN RAISE EXCEPTION 'Offset liegt hinter dem Textende'; END IF;
 RETURN jsonb_build_object('release_id',p_release_id,'kind',p_kind,'item_id',p_item_id,
   'metadata',item_metadata,'document_metadata',document_metadata,
   'text',CASE WHEN p_offset=total THEN '' ELSE substring(body FROM p_offset+1 FOR p_chars) END,
   'offset',p_offset,'total_chars',total,'text_sha256',encode(sha256(convert_to(body,'UTF8')),'hex'));
END $$;

REVOKE ALL ON FUNCTION kb.list_versions(),kb.lookup_provision(text,text,text),kb.read_item(text,text,text,integer,integer)
 FROM PUBLIC,anon,authenticated,kb_importer,kb_mcp;
GRANT EXECUTE ON FUNCTION kb.list_versions(),kb.lookup_provision(text,text,text),kb.read_item(text,text,text,integer,integer) TO kb_mcp;
COMMIT;
