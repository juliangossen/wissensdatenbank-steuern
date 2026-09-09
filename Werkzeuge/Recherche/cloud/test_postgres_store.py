"""Offline contract tests: no database, model download or credential access."""
import copy
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent))
import postgres_store as pg

RID = "r-test"
DOC = {
    "doc_id": "d-ustg", "abbreviation": "UStG", "title": "Umsatzsteuergesetz",
    "document_type": "Gesetz", "source_url": "https://example.invalid/ustg",
    "source_path": "Rechtsgebiete/UStG.md", "source_sha256": "a" * 64,
    "source_status": ["Quellenstand aus dem Original"], "import_date": "2026-09-09",
    "valid_from": None, "valid_to": None, "metadata": {"original": "unverändert"},
}
PARAMS = {"host": "reader.invalid", "dbname": "postgres", "user": "kb_reader",
          "password": "DO_NOT_PRINT_SYNTHETIC_SECRET", "sslrootcert": "dummy-root.crt"}


class Cursor:
    def __init__(self, rows): self.rows = rows
    def fetchone(self): return self.rows[0] if self.rows else None
    def fetchall(self): return self.rows


class FakeDB:
    def __init__(self):
        self.calls = []
        self.lookup = ["p-15"]
        self.bad_hash = False
        self.blob = b"registered-image"
        self.text = "§ 15 Vorsteuer\n" + "ä🙂|Fußnote|\n" * 6000
        self.metadata = {"provision_id": "p-15", "doc_id": DOC["doc_id"], "title": "§ 15 Vorsteuer",
                         "reference": "§ 15", "anchor": "par-15", "asset_ids": ["a-form"],
                         "cross_references": [{"reference": "§ 14", "extra": "unverändert"}],
                         "reference_aliases": ["Abschnitt 15"], "ordinal": 15}
        self.version = {"release_id": RID, "active": True, "created_at": "2026-09-09T00:00:00Z",
                        "documents": [DOC], "counts": {"document_count": 1},
                        "embedding_model": "dummy", "embedding_revision": "v1", "embedding_dimensions": 384}
        self.hits = [{"release_id": RID, "provision_id": "p-15", "document_id": DOC["doc_id"], "excerpt": "Vorsteuer", "score": 0.03},
                     {"release_id": RID, "provision_id": "p-15", "document_id": DOC["doc_id"], "excerpt": "Doppelter Chunk", "score": 0.02}]

    def __enter__(self): return self
    def __exit__(self, *args): return False

    def item(self, rid, kind, ident, offset, chars):
        if rid != RID or (kind == "p" and ident != "p-15") or (kind == "d" and ident != DOC["doc_id"]): return None
        return {"release_id": rid, "kind": kind, "item_id": ident,
                "metadata": copy.deepcopy(self.metadata if kind == "p" else DOC), "document_metadata": copy.deepcopy(DOC),
                "text": self.text[offset:offset + chars], "offset": offset, "total_chars": len(self.text),
                "text_sha256": hashlib.sha256(self.text.encode()).hexdigest()}

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if sql == pg.VERSIONS: value = {"versions": [copy.deepcopy(self.version)]}
        elif sql == pg.LOOKUP: value = self.lookup if params[0] == RID else []
        elif sql == pg.READ_ITEM: value = self.item(*params)
        elif sql == pg.READ_ITEMS: return Cursor([(self.item(params[0], "p", pid, 0, 1),) for pid in params[1]])
        elif sql == pg.SEARCH: return Cursor([(copy.deepcopy(hit),) for hit in self.hits])
        elif sql == pg.ASSET_INFO:
            value = {"asset_id": "a-form", "doc_id": DOC["doc_id"], "source_path": "original/form.png",
                     "relative_path": "form.png", "mime_type": "image/png", "storage_backend": "postgres",
                     "byte_size": len(self.blob), "sha256": "0" * 64 if self.bad_hash else hashlib.sha256(self.blob).hexdigest()}
        elif sql == pg.ASSET_BYTES: value = self.blob[params[2]:params[2] + params[3]]
        else: raise AssertionError("Unexpected SQL; adapter must only call fixed read functions")
        return Cursor([(value,)])


class DummyEmbedder:
    model_name = "dummy"
    model_revision = "v1"
    def embed_query(self, text): return [1.0] + [0.0] * 383


class PostgresStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB()
        self.connect = patch.object(pg.psycopg, "connect", return_value=self.db).start()
        self.addCleanup(patch.stopall)
        self.store = pg.PostgresStore(PARAMS, DummyEmbedder())

    def test_full_unicode_pagination_metadata_and_document_fetch(self):
        pages, offset = [], 0
        while True:
            result = self.store.fetch(f"{RID}::p::p-15", offset, 50000)
            pages.append(result["text"])
            self.assertEqual(result["metadata"], self.db.metadata)
            self.assertEqual(result["document_metadata"], DOC)
            self.assertEqual(result["asset_ids"], ["a-form"])
            self.assertEqual(result["cross_references"], self.db.metadata["cross_references"])
            self.assertIsNone(result["valid_from"])
            if not result["has_more"]: break
            offset = result["next_offset"]
        self.assertEqual("".join(pages), self.db.text)
        self.assertTrue(all(args[4] <= 20000 for sql, args in self.db.calls if sql == pg.READ_ITEM))
        document = self.store.fetch(f"{RID}::d::{DOC['doc_id']}")
        self.assertEqual(document["metadata"], DOC)
        self.assertEqual(document["text"], self.db.text[:12000])

    def test_exact_lookup_is_normalized_and_ambiguous_matches_fail(self):
        result = self.store.get_provision("ustg", "§ 15")
        self.assertEqual(result["id"], f"{RID}::p::p-15")
        self.assertIn((pg.LOOKUP, (RID, DOC["doc_id"], "15")), self.db.calls)
        self.db.lookup = ["p-15", "p-other"]
        with self.assertRaisesRegex(ValueError, "nicht eindeutig"):
            self.store.get_provision("UStG", "§ 15")

    def test_generated_identifiers_are_not_fabricated_source_fragments(self):
        self.db.metadata.update(kind="source_part", anchor="source-part-derived-id", generated_anchor=True)
        for actual in (None, "real-source-anchor"):
            self.db.metadata["source_anchor"] = actual
            result = self.store.fetch(f"{RID}::p::p-15")
            self.assertEqual(result["source_path"], DOC["source_path"] + ("#" + actual if actual else ""))
            self.assertEqual(result["kind"], "source_part")

    def test_supplement_fetch_and_search_keep_own_source_and_unknown_legal_status(self):
        self.db.metadata.update(kind="supplement", anchor="supplement-derived-id", generated_anchor=True,
                                source_anchor=None, source_path="Ergaenzungen/Nachtrag.md", source_sha256="b" * 64)
        fetched = self.store.fetch(f"{RID}::p::p-15")
        searched = self.store.search("Vorsteuer", mode="lexical")["results"][0]
        for result in (fetched, searched):
            self.assertEqual(result["source_path"], "Ergaenzungen/Nachtrag.md")
            self.assertEqual(result["source_sha256"], "b" * 64)
            self.assertEqual(result["kind"], "supplement")
            self.assertEqual(result["document_type"], "Ergänzung")
            self.assertEqual(result["source_status"], [])
            self.assertIsNone(result["source_url"])
            self.assertIsNone(result["valid_from"])
        self.assertEqual(fetched["document_metadata"], DOC)
        self.assertEqual(fetched["metadata"], self.db.metadata)

    def test_search_binds_query_deduplicates_and_preserves_source_fields(self):
        query = "Vorsteuer'; DROP TABLE kb.documents; --"
        result = self.store.search(query)
        self.assertEqual(len(result["results"]), 1)
        hit = result["results"][0]
        self.assertEqual(hit["source_status"], DOC["source_status"])
        self.assertEqual(hit["source_sha256"], DOC["source_sha256"])
        sql, args = next(call for call in self.db.calls if call[0] == pg.SEARCH)
        self.assertNotIn(query, sql)
        self.assertEqual(args[0], query)
        self.assertEqual(args[5], RID)
        self.assertEqual(len(args[1].strip("[]").split(",")), 384)

    def test_exact_reference_boost_and_no_historical_substitution(self):
        result = self.store.search("UStG § 15")
        self.assertIn("exact", result["results"][0]["matched_by"])
        self.assertGreater(result["results"][0]["score"], 1)
        with self.assertRaisesRegex(ValueError, "Fassung"):
            self.store.get_provision("UStG", "§ 15", "r-absent")

    def test_models_must_match_and_lexical_is_explicit(self):
        self.db.version["embedding_revision"] = "other"
        with self.assertRaisesRegex(ValueError, "Suchmodell"):
            self.store.search("Vorsteuer")
        self.store.embedder = None
        self.assertEqual(self.store.search("Vorsteuer", mode="lexical")["mode"], "lexical")
        with self.assertRaisesRegex(ValueError, "keine stille"):
            self.store.search("Vorsteuer")

    def test_asset_bytes_are_paginated_and_hash_checked(self):
        self.db.blob = b"a" * (8388608 + 7)
        metadata, data = self.store.asset(RID, "a-form")
        self.assertEqual(data, self.db.blob)
        self.assertEqual(metadata["source_path"], "original/form.png")
        calls = [args for sql, args in self.db.calls if sql == pg.ASSET_BYTES]
        self.assertEqual(len(calls), 2)
        self.db.bad_hash = True
        with self.assertRaisesRegex(ValueError, "Prüfsumme"):
            self.store.asset(RID, "a-form")

    def test_connection_is_readonly_tls_verified_and_errors_are_sanitized(self):
        self.store.list_versions()
        args = self.connect.call_args.kwargs
        self.assertEqual(args["sslmode"], "verify-full")
        self.assertIn("default_transaction_read_only=on", args["options"])
        self.connect.side_effect = psycopg.OperationalError(PARAMS["password"])
        with self.assertRaises(RuntimeError) as error:
            self.store.list_versions()
        self.assertNotIn(PARAMS["password"], str(error.exception))
        with self.assertRaises(ValueError): pg.PostgresStore({**PARAMS, "options": "arbitrary"})
        with self.assertRaises(ValueError): pg.PostgresStore({**PARAMS, "sslmode": "disable"})

    def test_invalid_ids_windows_and_vectors_are_rejected(self):
        for ident in [None, "path/to/source.md", "r::sql::x"]:
            with self.assertRaises(ValueError): self.store.fetch(ident)
        for offset, size in [(-1, 1), (False, 1), (2147483648, 1), (0, 50001)]:
            with self.assertRaises(ValueError): self.store.fetch(f"{RID}::p::p-15", offset, size)
        self.store.embedder.embed_query = lambda text: [float("nan")] * 384
        with self.assertRaisesRegex(ValueError, "Suchvektor"): self.store.search("Vorsteuer")


if __name__ == "__main__":
    unittest.main()
