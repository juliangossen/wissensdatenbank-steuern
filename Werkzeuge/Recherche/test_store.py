"""Release integrity and read-only research regression tests with synthetic data.

FakeEmbedder is deliberately test-only. It avoids network/model dependencies and
does not represent or evaluate the quality of the real semantic model.
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from store import Store, digest, reference_key


class FakeEmbedder:
    model_name = "TEST-ONLY-deterministic-three-dimensions"
    model_revision = "fixture-v1"
    dimensions = 3

    def __init__(self, fail=False):
        self.fail = fail
        self.queries = []

    def chunk_text(self, text, title=""):
        return [text] if text.strip() else []

    @staticmethod
    def _vector(text):
        lowered = text.casefold()
        if any(word in lowered for word in ("vorsteuer", "einkauf", "abzug")):
            return [1.0, 0.0, 0.0]
        if any(word in lowered for word in ("grundstück", "bodenwert")):
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def embed_documents(self, texts):
        if self.fail:
            raise RuntimeError("Absichtlich unterbrochener Testimport")
        return [self._vector(text) for text in texts]

    def embed_query(self, text):
        self.queries.append(text)
        return self._vector(text)


class StoreIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.root = self.directory / "sources"
        self.root.mkdir()
        self.data = self.directory / "data"
        self.embedder = FakeEmbedder()
        self.store = Store(self.data / "recherche.sqlite3", self.embedder)
        self.collection = self.make_collection("Erste Fassung")
        self.first = self.store.import_collection(self.collection, self.root, progress=lambda _: None)
        self.first_id = self.first["release_id"]

    def tearDown(self):
        # SQLite connections are explicitly closed by normal read operations;
        # collect any context-managed connections promptly on Windows as well.
        self.store._vectors.clear()
        import gc
        gc.collect()
        self.temporary.cleanup()

    def make_collection(self, edition, *, refs=("§ 15", "§ 20"), abbreviation="TestG"):
        provisions = []
        bodies = [
            f'## {refs[0]} Vorsteuerabzug\n\n{edition}: Abzug der Vorsteuer. '
            'Fußnotenverweis [^1]. ÄÖÜ – vollständiger Wortlaut.\n\n'
            '[^1]: Vollständige Fußnote mit § 20 und Anlage.\n',
            f'## {refs[1]} Grundstück\n\n{edition}: Der Bodenwert des Grundstücks.\n',
        ]
        markdown = "# Testgesetz\n\n" + "\n".join(bodies)
        path = self.root / "gesetz.md"
        path.write_text(markdown, encoding="utf-8")
        for index, body in enumerate(bodies):
            provisions.append({
                "provision_id": f"test-p{index}", "doc_id": "test-doc",
                "reference": refs[index], "title": refs[index] + (" Vorsteuerabzug" if index == 0 else " Grundstück"),
                "anchor": f"p-{index}", "markdown": body, "search_text": body,
                "cross_references": ["§ 20"] if index == 0 else [],
                "asset_ids": [],
            })
        return {
            "parser_version": "TEST-ONLY-parser-v1", "assets": [],
            "documents": [{
                "doc_id": "test-doc", "abbreviation": abbreviation,
                "document_type": "Gesetz", "source_path": "gesetz.md",
                "source_sha256": digest(path.read_bytes()), "markdown": markdown,
                "source_url": "https://example.invalid/testgesetz",
                "source_status": [edition], "import_date": "2026-09-09",
                "valid_from": None, "valid_to": None,
            }],
            "provisions": provisions,
        }

    def active_id(self):
        return next(v["release_id"] for v in self.store.list_versions()["versions"] if v["active"])

    def test_embedding_failure_preserves_active_release_and_old_fetch(self):
        old = self.store.fetch(f"{self.first_id}::p::test-p0")["text"]
        changed = self.make_collection("Geänderte Fassung für Abbruch")
        self.store.embedder = FakeEmbedder(fail=True)
        with self.assertRaisesRegex(RuntimeError, "Testimport"):
            self.store.import_collection(changed, self.root, progress=lambda _: None)
        self.assertEqual(self.active_id(), self.first_id)
        self.assertEqual(len(self.store.list_versions()["versions"]), 1)
        self.assertEqual(self.store.fetch(f"{self.first_id}::p::test-p0")["text"], old)

    def test_database_failure_rolls_back_whole_release(self):
        changed = self.make_collection("Fassung mit absichtlich doppelter ID")
        changed["provisions"][1]["provision_id"] = changed["provisions"][0]["provision_id"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.import_collection(changed, self.root, progress=lambda _: None)
        self.assertEqual(self.active_id(), self.first_id)
        self.assertEqual(len(self.store.list_versions()["versions"]), 1)
        self.assertIn("Erste Fassung", self.store.fetch(f"{self.first_id}::p::test-p0")["text"])

    def test_changed_source_hash_cannot_activate_new_release(self):
        changed = self.make_collection("Neue Fassung")
        (self.root / "gesetz.md").write_text("Quelle nach Prüfung geändert", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.store.import_collection(changed, self.root, progress=lambda _: None)
        self.assertEqual(self.active_id(), self.first_id)
        self.assertEqual(len(self.store.list_versions()["versions"]), 1)

    def test_reused_release_is_checked_before_reactivation(self):
        changed = self.make_collection("Zweite Fassung")
        second = self.store.import_collection(changed, self.root, progress=lambda _: None)
        # The old in-memory collection no longer matches the source on disk.
        with self.assertRaises(ValueError):
            self.store.import_collection(self.collection, self.root, progress=lambda _: None)
        self.assertEqual(self.active_id(), second["release_id"])

    def test_successful_update_keeps_original_fetch_id_immutable(self):
        old = self.store.fetch(f"{self.first_id}::p::test-p0")
        changed = self.make_collection("Zweite Fassung")
        second = self.store.import_collection(changed, self.root, progress=lambda _: None)
        self.assertNotEqual(second["release_id"], self.first_id)
        self.assertEqual(self.active_id(), second["release_id"])
        self.assertEqual(self.store.fetch(old["id"])["text"], old["text"])
        self.assertIn("Zweite Fassung", self.store.get_provision("TestG", "§ 15")["text"])
        self.assertIn("Erste Fassung", self.store.get_provision("TestG", "§ 15", self.first_id)["text"])

    def test_pagination_reconstructs_all_text_including_footnotes(self):
        expected = self.collection["provisions"][0]["markdown"]
        pieces, offset = [], 0
        while True:
            page = self.store.fetch(f"{self.first_id}::p::test-p0", offset, 37)
            self.assertEqual(page["offset"], offset)
            self.assertEqual(page["total_chars"], len(expected))
            self.assertEqual(page["text_sha256"], digest(expected))
            pieces.append(page["text"])
            if not page["has_more"]:
                self.assertIsNone(page["next_offset"])
                break
            self.assertGreater(page["next_offset"], offset)
            offset = page["next_offset"]
        self.assertEqual("".join(pieces), expected)
        self.assertIn("Vollständige Fußnote", "".join(pieces))
        self.assertEqual(self.store.fetch(f"{self.first_id}::p::test-p0", len(expected))["text"], "")
        with self.assertRaises(ValueError):
            self.store.fetch(f"{self.first_id}::p::test-p0", len(expected) + 1)

    def test_sql_and_fetch_path_inputs_cannot_escape_registered_data(self):
        for item in ("' OR 1=1 --", "../../secret", "gesetz.md", "../test-p0"):
            with self.assertRaises(ValueError):
                self.store.fetch(f"{self.first_id}::p::{item}")
            with self.assertRaises(ValueError):
                self.store.asset(self.first_id, item)
        result = self.store.search("' OR 1=1; DROP TABLE releases; --", mode="lexical")
        self.assertIsInstance(result["results"], list)
        self.assertEqual(self.active_id(), self.first_id)
        with self.assertRaises(ValueError):
            self.store.fetch("../../gesetz.md")

    def test_asset_traversal_and_hash_mismatch_cannot_activate_release(self):
        outside = self.directory / "outside.txt"
        outside.write_bytes(b"outside content")
        for path, expected_hash in [("../outside.txt", digest(outside.read_bytes())), ("gesetz.md", "0" * 64)]:
            changed = self.make_collection("Neue Fassung mit unzulässiger Anlage")
            changed["assets"] = [{
                "asset_id": "test-asset", "source_path": path,
                "sha256": expected_hash, "relative_path": path, "mime_type": "text/plain",
            }]
            with self.assertRaises(ValueError):
                self.store.import_collection(changed, self.root, progress=lambda _: None)
            self.assertEqual(self.active_id(), self.first_id)

    def test_lexical_and_semantic_channels_remain_explicit(self):
        lexical = self.store.search("Vorsteuer", mode="lexical")
        self.assertEqual(self.embedder.queries, [])
        self.assertEqual(lexical["results"][0]["matched_by"], ["lexical"])
        self.assertEqual(self.store.search("Einkauf", mode="lexical")["results"], [])
        semantic = self.store.search("Einkauf", mode="semantic")
        self.assertEqual(semantic["results"][0]["id"], f"{self.first_id}::p::test-p0")
        self.assertEqual(semantic["results"][0]["matched_by"], ["semantic"])
        hybrid = self.store.search("Vorsteuer", mode="hybrid")
        self.assertEqual(set(hybrid["results"][0]["matched_by"]), {"lexical", "semantic"})
        no_model = Store(self.store.path)
        with self.assertRaisesRegex(ValueError, "Modell"):
            no_model.search("Einkauf", mode="semantic")
        no_model.search("Vorsteuer", mode="lexical")

    def test_model_revision_mismatch_fails_without_fallback(self):
        self.embedder.model_revision = "incompatible-test-version"
        with self.assertRaisesRegex(ValueError, "Suchmodell"):
            self.store.search("Vorsteuer", mode="hybrid")

    def test_source_part_citations_link_only_to_real_source_anchors(self):
        part = {**self.collection["provisions"][0], "kind": "source_part",
                "anchor": "source-part-derived-id", "generated_anchor": True}
        with self.store.connect() as db:
            for actual in (None, "original-anchor"):
                citation = self.store._citation(db, self.first_id, {**part, "source_anchor": actual})
                self.assertEqual(citation["source_path"], "gesetz.md" + ("#" + actual if actual else ""))
                self.assertEqual(citation["kind"], "source_part")
            without_source_anchor = self.store._citation(db, self.first_id, part)
            self.assertEqual(without_source_anchor["source_path"], "gesetz.md")

    def test_supplement_fetch_and_search_keep_their_own_source_provenance(self):
        changed = copy.deepcopy(self.collection)
        body = "# Ergänzung\n\nVorsteuer und ergänzender Quellenstand 2026.\n"
        relative = "Ergaenzungen/Nachtrag.md"
        source = self.root / relative
        source.parent.mkdir()
        source.write_text(body, encoding="utf-8")
        sha = digest(source.read_bytes())
        changed["documents"][0]["valid_from"] = "2011-01-01"
        changed["provisions"][0].update(
            kind="supplement", title="Ergänzender Quellenstand", reference="Ergänzung: Quellenstand",
            markdown=body, search_text=body, source_path=relative, source_sha256=sha,
            anchor="supplement-derived-id", source_anchor=None, generated_anchor=True,
            asset_ids=["supplement-file"],
        )
        changed["assets"] = [{"asset_id": "supplement-file", "doc_id": "test-doc", "source_path": relative,
                              "relative_path": relative, "sha256": sha, "mime_type": "text/markdown"}]
        imported = self.store.import_collection(changed, self.root, progress=lambda _: None)
        fetched = self.store.fetch(f"{imported['release_id']}::p::test-p0")
        searched = next(hit for hit in self.store.search("ergänzender Quellenstand", mode="lexical")["results"]
                        if hit["id"] == fetched["id"])
        self.assertEqual(fetched["text"], body)
        for citation in (fetched, searched):
            self.assertEqual(citation["source_path"], relative)
            self.assertEqual(citation["source_sha256"], sha)
            self.assertEqual(citation["kind"], "supplement")
            self.assertEqual(citation["document_type"], "Ergänzung")
            self.assertEqual(citation["source_status"], [])
            self.assertIsNone(citation["source_url"])
            self.assertIsNone(citation["valid_from"])

    def test_distinct_ustae_section_numbers_do_not_collide(self):
        self.assertNotEqual(reference_key("1.11"), reference_key("11.1"))
        changed = self.make_collection("UStAE-Test", refs=("1.11", "11.1"), abbreviation="UStAE")
        self.store.import_collection(changed, self.root, progress=lambda _: None)
        self.assertEqual(self.store.get_provision("UStAE", "1.11.")["reference"], "1.11")
        self.assertEqual(self.store.get_provision("UStAE", "Abschnitt 11.1")["reference"], "11.1")

    def test_research_connection_is_read_only(self):
        connection = self.store.connect()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM releases")
        finally:
            connection.close()

    def test_cli_read_commands_preserve_source_and_database_bytes(self):
        source_before = (self.root / "gesetz.md").read_bytes()
        database_before = self.store.path.read_bytes()
        cli = Path(__file__).with_name("cli.py")
        commands = [
            ["versions"], ["search", "Vorsteuer", "--mode", "lexical"],
            ["get", "TestG", "§ 15"], ["fetch", f"{self.first_id}::p::test-p0"],
        ]
        for command in commands:
            process = subprocess.run(
                [sys.executable, "-B", str(cli), "--data", str(self.data), *command],
                capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIsInstance(json.loads(process.stdout), dict)
        self.assertEqual((self.root / "gesetz.md").read_bytes(), source_before)
        self.assertEqual(self.store.path.read_bytes(), database_before)

    def test_mcp_handshake_read_only_tools_and_source_preservation(self):
        from mcp import Client
        from server import create_server

        source_before = (self.root / "gesetz.md").read_bytes()
        database_before = self.store.path.read_bytes()

        async def exercise():
            async with Client(create_server(self.store)) as client:
                response = await client.list_tools()
                tools = response.tools
                self.assertEqual({tool.name for tool in tools}, {
                    "search", "fetch", "get_provision", "list_versions", "fetch_asset",
                })
                for tool in tools:
                    self.assertTrue(tool.annotations.read_only_hint)
                    self.assertFalse(tool.annotations.destructive_hint)
                result = await client.call_tool("search", {"query": "Vorsteuer"})
                self.assertFalse(result.is_error)
                payload = result.structured_content
                self.assertEqual(payload["release_id"], self.first_id)
                result = await client.call_tool("fetch", {"id": payload["results"][0]["id"]})
                self.assertFalse(result.is_error)
                self.assertIn("Vollständige Fußnote", result.structured_content["text"])
                rejected = await client.call_tool("fetch", {"id": "../../gesetz.md"})
                self.assertTrue(rejected.is_error)

        asyncio.run(exercise())
        self.assertEqual((self.root / "gesetz.md").read_bytes(), source_before)
        self.assertEqual(self.store.path.read_bytes(), database_before)


if __name__ == "__main__":
    unittest.main()
