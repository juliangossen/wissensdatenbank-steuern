"""Local, immutable research releases. SQLite is the development adapter.

The cloud target is PostgreSQL/pgvector; no database credentials are needed here.
Only import_collection writes source releases. Research methods are read-only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import numpy as np

STORE_VERSION = "research-local-1"
VERSION_NOTICE = "Importdatum ist kein Geltungsdatum. Ein belegter Geltungszeitraum ist in diesem Bestand nicht hinterlegt."


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def reference_key(value):
    return re.sub(r"[\s§]", "", value.casefold()).removeprefix("abschnitt").rstrip(".")


def terms(value):
    # Unicode word boundaries; SQL FTS operators are never accepted from callers.
    return re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE)


class ManagedConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class Store:
    def __init__(self, path: Path, embedder=None):
        self.path = Path(path)
        self.embedder = embedder
        self._vectors = {}

    def connect(self, *, writable=False):
        if writable:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(self.path, timeout=60, factory=ManagedConnection)
        else:
            db = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=60, factory=ManagedConnection)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def initialize(self):
        with self.connect(writable=True) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS releases(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, metadata TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS active(singleton INTEGER PRIMARY KEY CHECK(singleton=1), release_id TEXT REFERENCES releases(id));
            CREATE TABLE IF NOT EXISTS documents(release_id TEXT REFERENCES releases(id), id TEXT, metadata TEXT NOT NULL, markdown TEXT NOT NULL, PRIMARY KEY(release_id,id));
            CREATE TABLE IF NOT EXISTS provisions(release_id TEXT REFERENCES releases(id), id TEXT, doc_id TEXT, ref_key TEXT, metadata TEXT NOT NULL, markdown TEXT NOT NULL, PRIMARY KEY(release_id,id), FOREIGN KEY(release_id,doc_id) REFERENCES documents(release_id,id));
            CREATE INDEX IF NOT EXISTS provision_lookup ON provisions(release_id,doc_id,ref_key);
            CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, release_id TEXT NOT NULL, provision_id TEXT NOT NULL, text TEXT NOT NULL, vector BLOB NOT NULL, FOREIGN KEY(release_id,provision_id) REFERENCES provisions(release_id,id));
            CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(title,body, tokenize='unicode61 remove_diacritics 2');
            CREATE TABLE IF NOT EXISTS assets(release_id TEXT REFERENCES releases(id), id TEXT, metadata TEXT NOT NULL, content BLOB NOT NULL, PRIMARY KEY(release_id,id));
            CREATE TABLE IF NOT EXISTS embedding_cache(key TEXT PRIMARY KEY, vector BLOB NOT NULL);
            """)

    def import_collection(self, collection, root: Path, progress=print):
        if self.embedder is None:
            raise ValueError("Für den Import ist das lokale Embedding-Modell erforderlich.")
        self.initialize()
        root = root.resolve()

        def validate_sources():
            if collection["parser_version"].startswith("registered-provisions-"):
                register = json.loads((root / "Bestand.json").read_text(encoding="utf-8-sig"))
                for d in collection["documents"]:
                    entries = [e for e in register.get("eintraege", []) if e.get("kuerzel", "").casefold() == d["abbreviation"].casefold()]
                    if len(entries) != 1 or entries[0] != d["metadata"]:
                        raise ValueError(f'Registrierte Quellenangaben während Import geändert: {d["abbreviation"]}')
            for d in collection["documents"]:
                path = (root / d["source_path"]).resolve()
                if not path.is_relative_to(root) or digest(path.read_bytes()) != d["source_sha256"]:
                    raise ValueError(f'Quelle während Import geändert: {d["source_path"]}')
            for a in collection["assets"]:
                path = (root / a["source_path"]).resolve()
                if not path.is_relative_to(root) or digest(path.read_bytes()) != a["sha256"]:
                    raise ValueError(f'Asset während Import geändert: {a["source_path"]}')

        validate_sources()
        identity = {
            "store_version": STORE_VERSION, "parser_version": collection["parser_version"],
            "model": self.embedder.model_name, "model_revision": self.embedder.model_revision,
            "documents": sorted((d["doc_id"], d["source_sha256"], digest(canonical({k:v for k,v in d.items() if k != "markdown"}))) for d in collection["documents"]),
            "provisions": digest(canonical(collection["provisions"])),
            "assets": sorted((a["asset_id"], a["sha256"]) for a in collection["assets"]),
        }
        release_id = "r-" + digest(canonical(identity))[:24]
        with self.connect() as db:
            existing = db.execute("SELECT metadata FROM releases WHERE id=?", (release_id,)).fetchone()
        if existing:
            with self.connect(writable=True) as db:
                db.execute("INSERT INTO active VALUES(1,?) ON CONFLICT(singleton) DO UPDATE SET release_id=excluded.release_id", (release_id,))
            return {"release_id": release_id, "reused": True, **json.loads(existing[0])}

        docs = {d["doc_id"]: d for d in collection["documents"]}
        chunks = []
        for number, p in enumerate(collection["provisions"], 1):
            title = f'{docs[p["doc_id"]]["abbreviation"]} {p["title"]}'
            for body in self.embedder.chunk_text(p["search_text"], title=title):
                text = title + "\n" + body
                key = digest(canonical([identity["model"], identity["model_revision"], text]))
                chunks.append({"provision_id": p["provision_id"], "title": title, "text": text, "key": key})
            if number % 500 == 0 or number == len(collection["provisions"]):
                progress(f'Suchabschnitte vorbereiten: {number}/{len(collection["provisions"])} Fundstellen, {len(chunks)} Abschnitte.')
        if not chunks:
            raise ValueError("Import ohne Suchabschnitte wird nicht aktiviert.")
        cache = {}
        with self.connect() as db:
            for c in chunks:
                row = db.execute("SELECT vector FROM embedding_cache WHERE key=?", (c["key"],)).fetchone()
                if row:
                    cache[c["key"]] = row[0]
        missing = list({c["key"]: c for c in chunks if c["key"] not in cache}.values())
        progress(f'{len(collection["documents"])} Dokumente, {len(collection["provisions"])} Fundstellen, {len(chunks)} Suchabschnitte; {len(missing)} neue Embeddings.')
        batches = (missing[start:start + 32] for start in range(0, len(missing), 32))
        inputs = ([c["text"] for c in missing[start:start + 32]] for start in range(0, len(missing), 32))
        parallel = getattr(self.embedder, "embed_document_batches", None)
        results = parallel(inputs) if callable(parallel) else (self.embedder.embed_documents(texts) for texts in inputs)
        completed = 0
        try:
            for batch, vectors in zip(batches, results, strict=True):
                if len(vectors) != len(batch):
                    raise ValueError("Embedding-Anzahl stimmt nicht mit dem Import überein.")
                with self.connect(writable=True) as db:
                    for c, vector in zip(batch, vectors):
                        array = np.asarray(vector, dtype="<f4")
                        if array.shape != (self.embedder.dimensions,) or not np.isfinite(array).all() or np.linalg.norm(array) == 0:
                            raise ValueError("Ungültiger Embedding-Vektor.")
                        blob = (array / np.linalg.norm(array)).astype("<f4").tobytes()
                        cache[c["key"]] = blob
                        db.execute("INSERT OR IGNORE INTO embedding_cache VALUES(?,?)", (c["key"], blob))
                completed += len(batch)
                progress(f'Embeddings: {completed}/{len(missing)}')
        finally:
            close = getattr(results, "close", None)
            if callable(close):
                close()

        # Read and verify assets before publication. Concurrent source edits abort.
        asset_data = []
        for a in collection["assets"]:
            path = (root / a["source_path"]).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Asset außerhalb des Bestands.")
            blob = path.read_bytes()
            if digest(blob) != a["sha256"]:
                raise ValueError(f'Asset während Import geändert: {a["source_path"]}')
            asset_data.append((a, blob))
        validate_sources()
        metadata = {**identity, "document_count": len(docs), "provision_count": len(collection["provisions"]), "chunk_count": len(chunks), "asset_count": len(asset_data), "dimensions": self.embedder.dimensions, "version_notice": VERSION_NOTICE}
        with self.connect(writable=True) as db:
            db.execute("INSERT INTO releases VALUES(?,?,?)", (release_id, datetime.now(timezone.utc).isoformat(), canonical(metadata)))
            for d in collection["documents"]:
                db.execute("INSERT INTO documents VALUES(?,?,?,?)", (release_id, d["doc_id"], canonical({k:v for k,v in d.items() if k != "markdown"}), d["markdown"]))
            for p in collection["provisions"]:
                db.execute("INSERT INTO provisions VALUES(?,?,?,?,?,?)", (release_id, p["provision_id"], p["doc_id"], reference_key(p["reference"]), canonical({k:v for k,v in p.items() if k not in ("markdown", "search_text")}), p["markdown"]))
            for c in chunks:
                cursor = db.execute("INSERT INTO chunks(release_id,provision_id,text,vector) VALUES(?,?,?,?)", (release_id, c["provision_id"], c["text"], cache[c["key"]]))
                db.execute("INSERT INTO chunk_fts(rowid,title,body) VALUES(?,?,?)", (cursor.lastrowid, c["title"], c["text"]))
            for a, blob in asset_data:
                db.execute("INSERT INTO assets VALUES(?,?,?,?)", (release_id, a["asset_id"], canonical(a), blob))
            db.execute("INSERT INTO active VALUES(1,?) ON CONFLICT(singleton) DO UPDATE SET release_id=excluded.release_id", (release_id,))
        return {"release_id": release_id, "reused": False, **metadata}

    def _release(self, db, release_id=None):
        row = db.execute("SELECT id,metadata FROM releases WHERE id=?", (release_id,)).fetchone() if release_id else db.execute("SELECT r.id,r.metadata FROM releases r JOIN active a ON r.id=a.release_id").fetchone()
        if not row:
            raise ValueError("Keine passende importierte Fassung vorhanden.")
        return row[0], json.loads(row[1])

    def list_versions(self):
        with self.connect() as db:
            active, _ = self._release(db)
            releases = []
            for row in db.execute("SELECT * FROM releases ORDER BY created_at DESC"):
                docs = [json.loads(d[0]) for d in db.execute("SELECT metadata FROM documents WHERE release_id=? ORDER BY id", (row["id"],))]
                releases.append({"release_id": row["id"], "active": row["id"] == active, "created_at": row["created_at"], "documents": docs, "counts": {k:v for k,v in json.loads(row["metadata"]).items() if k.endswith("_count")}})
            return {"versions": releases, "version_notice": VERSION_NOTICE}

    def _citation(self, db, release_id, p):
        d = json.loads(db.execute("SELECT metadata FROM documents WHERE release_id=? AND id=?", (release_id, p["doc_id"])).fetchone()[0])
        source = p.get("source_path", d["source_path"])
        separate_source = source != d["source_path"]
        kind = p.get("kind", "provision")
        anchor = p.get("source_anchor", "" if p.get("generated_anchor") else p.get("anchor", ""))
        return {
            "id": f'{release_id}::p::{p["provision_id"]}',
            "title": f'{d["abbreviation"]} {p["title"]}', "reference": p["reference"],
            "document": d["abbreviation"], "kind": kind,
            "document_type": p.get("document_type", "Ergänzung" if kind == "supplement" else d["document_type"]),
            "source_url": p.get("source_url", None if separate_source else d.get("source_url")),
            "url": f'knowledge://{release_id}/provision/{quote(p["provision_id"], safe="")}',
            "source_path": source + ("#" + anchor if anchor else ""),
            "source_sha256": p.get("source_sha256", d["source_sha256"]),
            "source_status": p.get("source_status", [] if separate_source else d["source_status"]),
            "import_date": p.get("import_date", d["import_date"]),
            "valid_from": p.get("valid_from", None if separate_source else d.get("valid_from")),
            "valid_to": p.get("valid_to", None if separate_source else d.get("valid_to")),
            "release_id": release_id,
        }

    def search(self, query, limit=8, document=None, release_id=None, mode="hybrid"):
        if not isinstance(query, str) or not query.strip() or len(query) > 8000:
            raise ValueError("Suchfrage muss zwischen 1 und 8000 Zeichen haben.")
        if mode not in ("hybrid", "lexical", "semantic") or not 1 <= limit <= 30:
            raise ValueError("Ungültiger Suchmodus oder Trefferzahl (1–30).")
        started = time.perf_counter()
        with self.connect() as db:
            release_id, release = self._release(db, release_id)
            doc_rows = list(db.execute("SELECT id,metadata FROM documents WHERE release_id=?", (release_id,)))
            allowed = {r["id"] for r in doc_rows if document is None or json.loads(r["metadata"])["abbreviation"].casefold() == document.casefold()}
            if not allowed:
                raise ValueError("Dokument ist in dieser Fassung nicht vorhanden.")
            prov = {r["id"]: json.loads(r["metadata"]) for r in db.execute("SELECT id,doc_id,metadata FROM provisions WHERE release_id=?", (release_id,)) if r["doc_id"] in allowed}
            scores, snippets, channels = {}, {}, {}
            if mode in ("hybrid", "lexical"):
                words = list(dict.fromkeys(terms(query)))[:100]
                expression = " OR ".join('"' + w + '"' for w in words)
                placeholders = ",".join("?" for _ in allowed)
                rows = db.execute(f"SELECT c.provision_id,c.text,bm25(chunk_fts,4.0,1.0) AS rank FROM chunk_fts JOIN chunks c ON c.id=chunk_fts.rowid JOIN provisions p ON p.release_id=c.release_id AND p.id=c.provision_id WHERE chunk_fts MATCH ? AND c.release_id=? AND p.doc_id IN ({placeholders}) ORDER BY rank LIMIT 500", (expression, release_id, *sorted(allowed))).fetchall() if expression else []
                seen = set()
                for row in rows:
                    pid = row["provision_id"]
                    if pid not in prov or pid in seen:
                        continue
                    seen.add(pid)
                    scores[pid] = scores.get(pid, 0) + 1 / (60 + len(seen))
                    snippets[pid] = row["text"]
                    channels.setdefault(pid, []).append("lexical")
                    if len(seen) >= 80:
                        break
            if mode in ("hybrid", "semantic"):
                if self.embedder is None:
                    raise ValueError("Semantisches Modell nicht geladen; keine stille Ersatzsuche.")
                if (release["model"], release["model_revision"]) != (self.embedder.model_name, self.embedder.model_revision):
                    raise ValueError("Suchmodell stimmt nicht mit dem gespeicherten Index überein.")
                if release_id not in self._vectors:
                    rows = db.execute("SELECT provision_id,text,vector FROM chunks WHERE release_id=? ORDER BY id", (release_id,)).fetchall()
                    self._vectors[release_id] = (rows, np.stack([np.frombuffer(r["vector"], dtype="<f4") for r in rows]))
                rows, vectors = self._vectors[release_id]
                q = np.asarray(self.embedder.embed_query(query), dtype="float32")
                if q.shape != (release["dimensions"],) or not np.isfinite(q).all() or np.linalg.norm(q) == 0:
                    raise ValueError("Ungültiger Suchvektor.")
                similarities = vectors @ (q / np.linalg.norm(q))
                seen = set()
                for index in np.argsort(-similarities):
                    row = rows[int(index)]
                    pid = row["provision_id"]
                    if pid not in prov or pid in seen:
                        continue
                    seen.add(pid)
                    scores[pid] = scores.get(pid, 0) + 1 / (60 + len(seen))
                    snippets.setdefault(pid, row["text"])
                    channels.setdefault(pid, []).append("semantic")
                    if len(seen) >= 80:
                        break
            # Explicit citations are deterministic candidates, independent of vectors.
            for d in doc_rows:
                meta = json.loads(d["metadata"])
                if d["id"] not in allowed:
                    continue
                if document or re.search(r"\b" + re.escape(meta["abbreviation"]) + r"\b", query, re.I):
                    refs = re.findall(r"§\s*\d+[a-z]?|\b\d+[a-z]?(?:\.\d+[a-z]?)+\.?", query, re.I)
                    keys = {reference_key(x) for x in refs}
                    for pid, p in prov.items():
                        if p["doc_id"] == d["id"] and reference_key(p["reference"]) in keys:
                            scores[pid] = scores.get(pid, 0) + 1
                            snippets.setdefault(pid, p["title"])
                            channels.setdefault(pid, []).append("exact")
            results = []
            for pid in sorted(scores, key=lambda x: (-scores[x], x))[:limit]:
                result = self._citation(db, release_id, prov[pid])
                result.update({"excerpt": snippets[pid][:1400], "excerpt_is_partial": True, "score": round(scores[pid], 6), "matched_by": channels[pid]})
                results.append(result)
            return {"results": results, "release_id": release_id, "mode": mode, "elapsed_ms": round((time.perf_counter() - started) * 1000, 1), "version_notice": VERSION_NOTICE, "next_step": "Passende Treffer mit fetch vollständig nachladen; bei has_more=true next_offset verwenden. Querverweise prüfen. Suchrang ist keine rechtliche Bewertung."}

    def get_provision(self, document, reference, release_id=None, offset=0, max_chars=12000):
        with self.connect() as db:
            release_id, _ = self._release(db, release_id)
            doc_id = next((r["id"] for r in db.execute("SELECT id,metadata FROM documents WHERE release_id=?", (release_id,)) if json.loads(r["metadata"])["abbreviation"].casefold() == document.casefold()), None)
            rows = db.execute("SELECT id FROM provisions WHERE release_id=? AND doc_id=? AND ref_key=?", (release_id, doc_id, reference_key(reference))).fetchall()
            if not rows:
                rows = [r for r in db.execute("SELECT id,metadata FROM provisions WHERE release_id=? AND doc_id=?", (release_id, doc_id)) if reference_key(reference) in {reference_key(alias) for alias in json.loads(r["metadata"]).get("reference_aliases", [])}]
            if len(rows) != 1:
                raise ValueError("Fundstelle fehlt oder ist nicht eindeutig. Mit search nach der genauen Überschrift suchen; kein Ersatz aus einer anderen Fassung.")
        return self.fetch(f'{release_id}::p::{rows[0][0]}', offset, max_chars)

    def fetch(self, id, offset=0, max_chars=12000):
        if not isinstance(offset, int) or offset < 0 or not 1 <= max_chars <= 50000:
            raise ValueError("offset muss >=0 und max_chars zwischen 1 und 50000 sein.")
        parts = id.split("::", 2)
        if len(parts) != 3 or parts[1] not in ("p", "d"):
            raise ValueError("Ungültige Fundstellen-ID. ID aus search oder list_versions verwenden.")
        release_id, kind, item_id = parts
        with self.connect() as db:
            self._release(db, release_id)
            table = "provisions" if kind == "p" else "documents"
            row = db.execute(f"SELECT metadata,markdown FROM {table} WHERE release_id=? AND id=?", (release_id, item_id)).fetchone()
            if not row:
                raise ValueError("Fundstelle in dieser Fassung nicht vorhanden.")
            metadata, text = json.loads(row[0]), row[1]
            if offset > len(text):
                raise ValueError("Offset liegt hinter dem Textende.")
            result = self._citation(db, release_id, metadata) if kind == "p" else {"id": id, **metadata, "release_id": release_id}
            end = min(offset + max_chars, len(text))
            result.update({"text": text[offset:end], "offset": offset, "next_offset": end if end < len(text) else None, "has_more": end < len(text), "total_chars": len(text), "text_sha256": digest(text), "cross_references": metadata.get("cross_references", []), "asset_ids": metadata.get("asset_ids", []), "version_notice": VERSION_NOTICE})
            return result

    def asset(self, release_id, asset_id):
        with self.connect() as db:
            self._release(db, release_id)
            row = db.execute("SELECT metadata,content FROM assets WHERE release_id=? AND id=?", (release_id, asset_id)).fetchone()
            if not row:
                raise ValueError("Anlage nicht in dieser Fassung registriert.")
            meta, blob = json.loads(row[0]), bytes(row[1])
            if digest(blob) != meta["sha256"]:
                raise ValueError("Anlagen-Prüfsumme stimmt nicht.")
            return meta, blob

    def export(self, target: Path, release_id=None):
        """Portable, complete local export; no network requests or credentials."""
        target = Path(target)
        if target.exists():
            raise ValueError("Exportziel existiert bereits. Einen neuen Ordner wählen.")
        with self.connect() as db:
            release_id, metadata = self._release(db, release_id)
            target.mkdir(parents=True)
            manifest = {"format": "research-export-1", "release_id": release_id, "metadata": metadata, "files": []}
            def write(name, content):
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                manifest["files"].append({"path": name, "sha256": digest(content), "size": len(content)})
            for table in ("documents", "provisions", "chunks", "assets"):
                records = []
                for row in db.execute(f"SELECT * FROM {table} WHERE release_id=?", (release_id,)):
                    record = dict(row)
                    if "metadata" in record:
                        record["metadata"] = json.loads(record["metadata"])
                    if table == "chunks":
                        record["vector"] = np.frombuffer(record["vector"], dtype="<f4").tolist()
                    if table == "assets":
                        blob = bytes(record.pop("content"))
                        name = "assets/" + record["metadata"]["sha256"]
                        record["object_path"] = name
                        if not (target / name).exists():
                            write(name, blob)
                    records.append(canonical(record))
                write(table + ".jsonl", ("\n".join(records) + "\n").encode("utf-8"))
            # Manifest is the completion marker and is written last.
            (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"target": str(target.resolve()), "release_id": release_id, "file_count": len(manifest["files"])}
