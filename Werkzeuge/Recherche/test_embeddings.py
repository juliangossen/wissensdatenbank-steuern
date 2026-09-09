"""Token safety tests; optional real CPU-model integration smoke test."""

import math
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from embeddings import EmbeddingError, LocalEmbedder, chunk_text


class CharacterChunkTests(unittest.TestCase):
    def test_lazy_constructor_does_not_download_or_create_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary) / "not-created"
            embedder = LocalEmbedder(cache)
            self.assertEqual(embedder.dimensions, 384)
            self.assertFalse(cache.exists())

    def test_overlap_keeps_every_character(self):
        text = "Ein Text mit Umlauten: äöü und § 15.\n" * 17
        chunks = chunk_text(text, max_chars=80, overlap_chars=13)
        rebuilt = chunks[0] + "".join(part[13:] for part in chunks[1:])
        self.assertEqual(rebuilt, text)
        self.assertTrue(all(len(part) <= 80 for part in chunks))

    def test_invalid_windows_are_rejected(self):
        for size, overlap in [(0, 0), (8, 8), (8, -1)]:
            with self.assertRaises(ValueError):
                chunk_text("test", size, overlap)

    def test_small_imports_stay_serial_and_worker_count_is_bounded(self):
        embedder = LocalEmbedder(Path("unused-model-cache"))
        with patch.object(embedder, "embed_documents", return_value=[[1.0]]) as serial:
            self.assertEqual(list(embedder.embed_document_batches([["one text"]])), [[[1.0]]])
            serial.assert_called_once_with(["one text"])
        self.assertEqual(list(embedder.embed_document_batches([])), [])
        for workers in [0, 5, -1]:
            with self.assertRaises(ValueError):
                list(embedder.embed_document_batches([["text"]], workers=workers))


@unittest.skipUnless(os.environ.get("RECHERCHE_EMBEDDING_TEST") == "1",
                     "Modelltest bewusst mit RECHERCHE_EMBEDDING_TEST=1 aktivieren")
class RealEmbeddingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.embedder = LocalEmbedder(Path(__file__).parent / ".daten" / "modelle")

    def test_semantic_german_retrieval_uses_real_normalized_vectors(self):
        documents = self.embedder.embed_documents([
            "Vorsteuerabzug: Ein Unternehmer kann die gesetzlich geschuldete Steuer "
            "für Lieferungen und sonstige Leistungen, die für sein Unternehmen "
            "ausgeführt wurden, abziehen.",
            "Das Fahrrad hat zwei Räder und fährt auf dem Radweg im Wald.",
            "Die Bewertung eines unbebauten Grundstücks richtet sich nach dem Bodenrichtwert.",
        ])
        query = self.embedder.embed_query("Kann ich die Umsatzsteuer meiner betrieblichen Einkäufe zurückbekommen?")
        scores = [sum(a * b for a, b in zip(query, vector)) for vector in documents]
        self.assertEqual(max(range(3), key=scores.__getitem__), 0, scores)
        self.assertEqual(len(query), 384)
        self.assertAlmostEqual(math.sqrt(sum(v * v for v in query)), 1, places=5)

    def test_long_provision_tail_is_indexed_and_oversized_input_is_rejected(self):
        title = "UStG § 15 Vorsteuerabzug"
        text = " ".join(
            f"Der Unternehmer Nummer {number} führt Leistungen für sein Unternehmen aus."
            for number in range(200)
        ) + " EindeutigerEndmarker"
        pieces = self.embedder.chunk_text(text, title=title)
        self.assertGreater(len(pieces), 1)
        self.assertTrue(pieces[-1].endswith("EindeutigerEndmarker"))
        self.assertTrue(all(self.embedder.token_count(title + "\n" + part) <= 448 for part in pieces))
        covered = [False] * len(text)
        start = 0
        # Each piece is an exact substring, and the windows cover the whole text.
        for part in pieces:
            position = text.find(part, start)
            self.assertGreaterEqual(position, 0)
            covered[position:position + len(part)] = [True] * len(part)
            start = position + 1
        self.assertTrue(all(covered))
        with self.assertRaisesRegex(ValueError, "Token"):
            self.embedder.embed_documents([title + "\n" + text])

    def test_long_question_is_not_silently_truncated(self):
        question = "Mein Unternehmen kauft betriebliche Waren mit Umsatzsteuer ein. " * 60
        vector = self.embedder.embed_query(question)
        self.assertEqual(len(vector), 384)
        self.assertAlmostEqual(math.sqrt(sum(v * v for v in vector)), 1, places=5)

    def test_parallel_batches_equal_serial_vectors_and_keep_input_order(self):
        batches = [
            ["Vorsteuerabzug bei einem betrieblichen Einkauf.", "Bewertung des Grundstücks nach dem Bodenrichtwert."],
            ["Die elektronische Rechnung dokumentiert eine Lieferung.", "Ein Fahrrad fährt auf einem Waldweg."],
            ["Eine selbständige Tätigkeit kann gewerbesteuerpflichtig sein."],
        ]
        expected = [self.embedder.embed_documents(batch) for batch in batches]
        actual = list(self.embedder.embed_document_batches(batches, workers=3))
        self.assertEqual([len(batch) for batch in actual], [2, 2, 1])
        for expected_batch, actual_batch in zip(expected, actual):
            for expected_vector, actual_vector in zip(expected_batch, actual_batch):
                self.assertEqual(len(actual_vector), 384)
                self.assertLessEqual(max(abs(a - b) for a, b in zip(expected_vector, actual_vector)), 1e-6)

    def test_failed_worker_preserves_previous_release_and_verified_cache_batches(self):
        from store import Store, digest
        from test_store import FakeEmbedder

        class DeliberatelyUnchunked(LocalEmbedder):
            def chunk_text(self, text, title=""):
                return [text]

        def collection(root, edition, count):
            items = []
            for index in range(count):
                body = f"{edition}: Betriebsausgabe Nummer {index}."
                if index == 32:
                    body += " UngekuerzterTesttext" * 1000
                items.append({"provision_id": f"test-{index}", "doc_id": "test",
                              "reference": f"§ {index + 1}", "title": f"Prüftext {index}",
                              "anchor": f"p-{index}", "markdown": body, "search_text": body,
                              "asset_ids": [], "cross_references": []})
            markdown = "\n\n".join(p["markdown"] for p in items)
            (root / "source.md").write_bytes(markdown.encode())
            return {"parser_version": "TEST-ONLY-worker-failure", "assets": [], "provisions": items,
                    "documents": [{"doc_id": "test", "abbreviation": "TestG", "title": "Testquelle",
                                   "document_type": "Gesetz", "source_path": "source.md",
                                   "source_sha256": digest(markdown), "markdown": markdown,
                                   "source_status": [edition], "import_date": "2026-09-09"}]}

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = Store(root / "research.sqlite3", FakeEmbedder())
            old = store.import_collection(collection(root, "Alte Fassung", 1), root, progress=lambda _: None)
            with store.connect() as db:
                before = db.execute("SELECT count(*) FROM embedding_cache").fetchone()[0]
            store.embedder = DeliberatelyUnchunked(self.embedder.cache_dir)
            with self.assertRaisesRegex(EmbeddingError, "Parallele lokale Embedding-Berechnung"):
                store.import_collection(collection(root, "Neue Fassung", 33), root, progress=lambda _: None)
            with store.connect() as db:
                self.assertEqual(db.execute("SELECT release_id FROM active").fetchone()[0], old["release_id"])
                self.assertEqual(db.execute("SELECT count(*) FROM releases").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT count(*) FROM embedding_cache").fetchone()[0], before + 32)
                self.assertEqual(db.execute("SELECT count(*) FROM embedding_cache WHERE length(vector)=?", (384 * 4,)).fetchone()[0], 32)


if __name__ == "__main__":
    unittest.main()
