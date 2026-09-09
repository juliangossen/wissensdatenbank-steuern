"""Read-only PostgreSQL adapter for server.create_server.

The caller supplies a dedicated reader connection and an optional local embedder.
No account discovery, credential storage, import, network model service or arbitrary
SQL tool is provided here. Install schema.sql and read_api.sql first.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import math
import re
import time
from urllib.parse import quote

import psycopg

VERSION_NOTICE = "Importdatum ist kein Geltungsdatum. Ein belegter Geltungszeitraum ist in diesem Bestand nicht hinterlegt."
NEXT_STEP = "Passende Treffer mit fetch vollständig nachladen; bei has_more=true next_offset verwenden. Querverweise prüfen. Suchrang ist keine rechtliche Bewertung."

# These statements are application constants. User values are bound parameters.
VERSIONS = "SELECT kb.list_versions()"
LOOKUP = "SELECT kb.lookup_provision(%s,%s,%s)"
READ_ITEM = "SELECT kb.read_item(%s,%s,%s,%s,%s)"
READ_ITEMS = "SELECT kb.read_item(%s,'p',x.pid,0,1) FROM pg_catalog.unnest(%s::text[]) AS x(pid)"
SEARCH = "SELECT to_jsonb(hit) FROM kb.hybrid_search(%s,%s::extensions.vector,%s,%s,%s,%s,%s) AS hit"
ASSET_INFO = "SELECT kb.read_asset_info(%s,%s)"
ASSET_BYTES = "SELECT kb.fetch_asset_bytes(%s,%s,%s,%s)"


def reference_key(value):
    return re.sub(r"[\s§]", "", value.casefold()).removeprefix("abschnitt").rstrip(".")


class PostgresStore:
    def __init__(self, parameters: dict, embedder=None):
        allowed = {"host", "port", "dbname", "user", "password", "sslmode", "sslrootcert"}
        if not isinstance(parameters, dict) or set(parameters) - allowed:
            raise ValueError("Nur feste Datenbank-Verbindungsparameter sind erlaubt.")
        if not all(parameters.get(k) for k in ("host", "dbname", "user", "sslrootcert")):
            raise ValueError("Host, Datenbank, Leserbenutzer und Root-Zertifikat sind erforderlich.")
        if parameters.get("sslmode", "verify-full") != "verify-full":
            raise ValueError("Die Cloud-Leseverbindung benötigt sslmode=verify-full.")
        self._parameters = {**parameters, "sslmode": "verify-full"}
        self.embedder = embedder

    @contextmanager
    def _connection(self):
        try:
            with psycopg.connect(
                **self._parameters, connect_timeout=15, prepare_threshold=None,
                options="-c default_transaction_read_only=on -c statement_timeout=30000",
            ) as db:
                yield db
        except psycopg.Error:
            # Driver errors can contain a DSN, host, user or secret. Never forward.
            raise RuntimeError("Die Cloud-Leseabfrage ist fehlgeschlagen. Verbindung und eingerichtete Lese-API prüfen.") from None

    @staticmethod
    def _json(db, sql, params=()):
        row = db.execute(sql, params).fetchone()
        return row[0] if row else None

    def _versions(self, db):
        result = self._json(db, VERSIONS)
        if not isinstance(result, dict) or not isinstance(result.get("versions"), list):
            raise RuntimeError("Die Cloud-Lese-API liefert keine gültige Fassungsübersicht.")
        return result

    def _release(self, db, release_id=None):
        versions = self._versions(db)["versions"]
        matches = [v for v in versions if v["release_id"] == release_id] if release_id else [v for v in versions if v["active"]]
        if len(matches) != 1:
            raise ValueError("Keine passende importierte Fassung vorhanden.")
        return matches[0]

    @staticmethod
    def _document(release, document):
        if not isinstance(document, str) or not document.strip():
            raise ValueError("Eine Dokumentabkürzung ist erforderlich.")
        matches = [d for d in release["documents"] if d["abbreviation"].casefold() == document.casefold()]
        if len(matches) != 1:
            raise ValueError("Dokument ist in dieser Fassung nicht vorhanden oder nicht eindeutig.")
        return matches[0]

    def list_versions(self):
        with self._connection() as db:
            result = self._versions(db)
        return {**result, "version_notice": VERSION_NOTICE}

    @staticmethod
    def _citation(release_id, provision, document):
        pid = provision["provision_id"]
        source = provision.get("source_path", document["source_path"])
        separate_source = source != document["source_path"]
        kind = provision.get("kind", "provision")
        anchor = provision.get("source_anchor", "" if provision.get("generated_anchor") else provision.get("anchor", ""))
        return {
            "id": f"{release_id}::p::{pid}",
            "title": f'{document["abbreviation"]} {provision["title"]}',
            "reference": provision["reference"], "document": document["abbreviation"], "kind": kind,
            "document_type": provision.get("document_type", "Ergänzung" if kind == "supplement" else document["document_type"]),
            "source_url": provision.get("source_url", None if separate_source else document.get("source_url")),
            "url": f'knowledge://{release_id}/provision/{quote(pid, safe="")}',
            "source_path": source + ("#" + anchor if anchor else ""),
            "source_sha256": provision.get("source_sha256", document["source_sha256"]),
            "source_status": provision.get("source_status", [] if separate_source else document["source_status"]),
            "import_date": provision.get("import_date", document["import_date"]),
            "valid_from": provision.get("valid_from", None if separate_source else document.get("valid_from")),
            "valid_to": provision.get("valid_to", None if separate_source else document.get("valid_to")),
            "release_id": release_id,
        }

    @staticmethod
    def _window(offset, max_chars):
        if type(offset) is not int or not 0 <= offset <= 2147483647 or type(max_chars) is not int or not 1 <= max_chars <= 50000:
            raise ValueError("offset muss >=0 und max_chars zwischen 1 und 50000 sein.")

    def _fetch(self, db, release_id, kind, item_id, offset, max_chars):
        first = self._json(db, READ_ITEM, (release_id, kind, item_id, offset, min(max_chars, 20000)))
        if first is None:
            raise ValueError("Fundstelle in dieser Fassung nicht vorhanden.")
        total = first["total_chars"]
        if offset > total:
            raise ValueError("Offset liegt hinter dem Textende.")
        fragments = [first["text"]]
        end = offset + len(first["text"])
        target = min(offset + max_chars, total)
        while end < target:
            part = self._json(db, READ_ITEM, (release_id, kind, item_id, end, min(target - end, 20000)))
            if not part or part["text_sha256"] != first["text_sha256"] or part["total_chars"] != total or not part["text"]:
                raise RuntimeError("Die Textfortsetzung stimmt nicht mit der unveränderlichen Fundstelle überein.")
            fragments.append(part["text"])
            end += len(part["text"])
        metadata = first["metadata"]
        result = self._citation(release_id, metadata, first["document_metadata"]) if kind == "p" else {"id": f"{release_id}::d::{item_id}", **metadata, "release_id": release_id}
        text = "".join(fragments)
        if len(text) != target - offset:
            raise RuntimeError("Die Cloud-Lese-API lieferte ein unvollständiges Textfenster.")
        if offset == 0 and end == total and hashlib.sha256(text.encode("utf-8")).hexdigest() != first["text_sha256"]:
            raise RuntimeError("Die Text-Prüfsumme stimmt nicht.")
        result.update({
            "text": text, "offset": offset, "next_offset": end if end < total else None,
            "has_more": end < total, "total_chars": total, "text_sha256": first["text_sha256"],
            "cross_references": metadata.get("cross_references", []), "asset_ids": metadata.get("asset_ids", []),
            "metadata": metadata, "document_metadata": first["document_metadata"], "version_notice": VERSION_NOTICE,
        })
        return result

    def fetch(self, id, offset=0, max_chars=12000):
        self._window(offset, max_chars)
        parts = id.split("::", 2) if isinstance(id, str) else []
        if len(parts) != 3 or parts[1] not in ("p", "d") or not parts[0] or not parts[2]:
            raise ValueError("Ungültige Fundstellen-ID. ID aus search oder list_versions verwenden.")
        with self._connection() as db:
            return self._fetch(db, *parts, offset, max_chars)

    def get_provision(self, document, reference, release_id=None, offset=0, max_chars=12000):
        self._window(offset, max_chars)
        if not isinstance(reference, str) or not reference.strip() or len(reference) > 1000:
            raise ValueError("Eine konkrete Vorschriftsreferenz ist erforderlich.")
        with self._connection() as db:
            release = self._release(db, release_id)
            doc = self._document(release, document)
            rid = release["release_id"]
            matches = self._json(db, LOOKUP, (rid, doc["doc_id"], reference_key(reference)))
            if not isinstance(matches, list) or len(matches) != 1:
                raise ValueError("Fundstelle fehlt oder ist nicht eindeutig. Mit search nach der genauen Überschrift suchen; kein Ersatz aus einer anderen Fassung.")
            return self._fetch(db, rid, "p", matches[0], offset, max_chars)

    def search(self, query, limit=8, document=None, release_id=None, mode="hybrid"):
        if not isinstance(query, str) or not query.strip() or len(query) > 8000:
            raise ValueError("Suchfrage muss zwischen 1 und 8000 Zeichen haben.")
        if mode not in ("hybrid", "lexical") or type(limit) is not int or not 1 <= limit <= 30:
            raise ValueError("Cloud-Suchmodus muss hybrid oder lexical sein; Trefferzahl 1–30.")
        started = time.perf_counter()
        with self._connection() as db:
            release = self._release(db, release_id)
            rid = release["release_id"]
            docs = [self._document(release, document)] if document is not None else release["documents"]
            if not docs:
                raise ValueError("Dokument ist in dieser Fassung nicht vorhanden.")
            vector, model, revision = None, None, None
            if mode == "hybrid":
                if self.embedder is None:
                    raise ValueError("Semantisches Modell nicht geladen; keine stille Ersatzsuche.")
                model, revision = self.embedder.model_name, self.embedder.model_revision
                if (model, revision) != (release["embedding_model"], release["embedding_revision"]):
                    raise ValueError("Suchmodell stimmt nicht mit dem gespeicherten Index überein.")
                values = [float(x) for x in self.embedder.embed_query(query)]
                if len(values) != 384 or not all(math.isfinite(x) and abs(x) <= 3.402823466e38 for x in values) or not any(values):
                    raise ValueError("Ungültiger Suchvektor.")
                norm = math.sqrt(sum(x * x for x in values))
                vector = "[" + ",".join(format(x / norm, ".9g") for x in values) + "]"
            params = (query, vector, model, revision, 30, rid, docs[0]["doc_id"] if document is not None else None)
            candidates = {}
            for row in db.execute(SEARCH, params).fetchall():
                hit = row[0]
                if hit["release_id"] != rid:
                    raise RuntimeError("Suchtreffer gehört nicht zur angeforderten Fassung.")
                pid = hit["provision_id"]
                if pid not in candidates or hit["score"] > candidates[pid]["score"]:
                    candidates[pid] = {**hit, "matched_by": [mode]}
            # Deterministic explicit citations, as in the local Store.search.
            refs = {reference_key(x) for x in re.findall(r"§\s*\d+[a-z]?|\b\d+[a-z]?(?:\.\d+[a-z]?)+\.?", query, re.I)}
            for doc in docs:
                if document or re.search(r"\b" + re.escape(doc["abbreviation"]) + r"\b", query, re.I):
                    for ref in sorted(refs):
                        matches = self._json(db, LOOKUP, (rid, doc["doc_id"], ref))
                        for pid in matches or []:
                            hit = candidates.setdefault(pid, {"provision_id": pid, "score": 0, "excerpt": "", "matched_by": []})
                            if "exact" not in hit["matched_by"]:
                                hit["score"] += 1
                                hit["matched_by"].append("exact")
            selected = sorted(candidates.values(), key=lambda x: (-x["score"], x["provision_id"]))[:limit]
            metadata = {}
            if selected:
                for row in db.execute(READ_ITEMS, (rid, [h["provision_id"] for h in selected])).fetchall():
                    item = row[0]
                    if item is not None:
                        metadata[item["item_id"]] = item
            results = []
            for hit in selected:
                item = metadata.get(hit["provision_id"])
                if item is None:
                    raise RuntimeError("Metadaten einer Suchfundstelle fehlen.")
                citation = self._citation(rid, item["metadata"], item["document_metadata"])
                citation.update({"excerpt": (hit["excerpt"] or item["metadata"]["title"])[:1400],
                                 "excerpt_is_partial": True, "score": round(hit["score"], 6), "matched_by": hit["matched_by"]})
                results.append(citation)
        return {"results": results, "release_id": rid, "mode": mode,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
                "version_notice": VERSION_NOTICE, "next_step": NEXT_STEP}

    def asset(self, release_id, asset_id):
        if not isinstance(release_id, str) or not release_id or not isinstance(asset_id, str) or not asset_id:
            raise ValueError("Fassungskennung und registrierte Anlagen-ID sind erforderlich.")
        with self._connection() as db:
            metadata = self._json(db, ASSET_INFO, (release_id, asset_id))
            if metadata is None:
                raise ValueError("Anlage nicht in dieser Fassung registriert.")
            total = metadata["byte_size"]
            fragments, offset = [], 0
            while offset < total:
                raw = self._json(db, ASSET_BYTES, (release_id, asset_id, offset, min(8388608, total - offset)))
                if raw is None or not raw:
                    raise RuntimeError("Die gespeicherte Anlage ist unvollständig.")
                block = bytes(raw)
                fragments.append(block)
                offset += len(block)
            blob = b"".join(fragments)
            if len(blob) != total or hashlib.sha256(blob).hexdigest() != metadata["sha256"]:
                raise ValueError("Anlagen-Prüfsumme stimmt nicht.")
            return metadata, blob
