-- Migration 003: ursprüngliche Assetmetadaten für den lesenden MCP erhalten.
-- Ergänzt die bereits installierte read_api.sql; verändert keine Quelleninhalte.
BEGIN;

CREATE FUNCTION kb.read_asset_info(p_release_id text,p_asset_id text) RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT a.metadata || kb.asset_info(a.release_id,a.asset_id)
 FROM kb.assets a JOIN kb.releases r USING(release_id)
 WHERE a.release_id=p_release_id AND a.asset_id=p_asset_id AND r.sealed_at IS NOT NULL
$$;

REVOKE ALL ON FUNCTION kb.read_asset_info(text,text) FROM PUBLIC,anon,authenticated,kb_importer,kb_mcp;
GRANT EXECUTE ON FUNCTION kb.read_asset_info(text,text) TO kb_mcp;
COMMIT;
