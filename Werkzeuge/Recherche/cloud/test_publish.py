"""Corpus-wide publication checks; no network, credentials or cloud writes."""
from copy import deepcopy
import json
import re
import struct
import unittest
from unittest.mock import patch

import publish


class Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0]


def corpus():
    """Deliberately contains neither UStG, UStAE nor BewG."""
    documents = [{"document_id": doc, "abbreviation": doc.upper()} for doc in ("ao", "gobd", "hgb", "erbr")]
    provisions, chunks = [], []
    for doc in documents:
        for ordinal in range(5):
            ident = f"{doc['document_id']}:{ordinal}"
            provisions.append({"document_id": doc["document_id"], "provision_id": ident,
                               "ref_key": str(ordinal), "ordinal": ordinal,
                               "metadata": {"reference_aliases": ["Abschnitt 7.2a."] if ordinal == 3 else []}})
            chunks.append({"document_id": doc["document_id"], "provision_id": ident,
                           "body_text": f"Vollständige Rechnungslegung {doc['abbreviation']} Nummer {ordinal}."})
    return {"release": {"release_id": "r-fixture"},
            "rows": {"documents": documents, "provisions": provisions, "search_chunks": chunks, "assets": []}}


class ReadDB:
    def __init__(self, package):
        self.package = package
        self.calls = []
        self.missing_document = None
        self.wrong_document = False
        self.missing_alias = False

    def execute(self, query, parameters):
        self.calls.append((query, parameters))
        if "hybrid_search" in query:
            term, rid, doc = parameters
            if doc == self.missing_document:
                return Result([])
            return Result([(rid, "other" if self.wrong_document else doc, f"{doc}:0")])
        if "lookup_provision" in query:
            result = []
            for probe in parameters[1].obj:
                matches = [] if self.missing_alias and probe["ref_key"] == "7.2a" else [probe["provision_id"]]
                result.append((probe["document_id"], probe["ref_key"], matches))
            return Result(list(reversed(result)))
        raise AssertionError(query)


class CorpusReaderTests(unittest.TestCase):
    def setUp(self):
        self.package = corpus()
        self.db = ReadDB(self.package)

    def test_every_document_is_searched_with_its_own_expected_text(self):
        checked = publish.verify_lexical_search(self.db, self.package)
        self.assertEqual(checked, [doc["document_id"] for doc in self.package["rows"]["documents"]])
        for sql, values in self.db.calls:
            self.assertIn("Rechnungslegung", values[0])
            self.assertNotIn(values[0], sql)
            self.assertEqual(values[1], "r-fixture")

    def test_missing_fourth_document_cannot_pass_the_corpus_check(self):
        self.db.missing_document = "erbr"
        with self.assertRaisesRegex(ValueError, "ERBR"):
            publish.verify_lexical_search(self.db, self.package)

    def test_search_cannot_return_a_different_document(self):
        self.db.wrong_document = True
        with self.assertRaisesRegex(ValueError, "Volltextsuche"):
            publish.verify_lexical_search(self.db, self.package)

    def test_document_without_search_chunks_is_not_silently_skipped(self):
        self.package["rows"]["search_chunks"] = [r for r in self.package["rows"]["search_chunks"] if r["document_id"] != "gobd"]
        with self.assertRaisesRegex(ValueError, "GOBD"):
            publish.lexical_queries(self.package)

    def test_exact_samples_cover_every_document_and_all_aliases(self):
        probes = publish.reference_probes(self.package)
        for doc in self.package["rows"]["documents"]:
            keys = {p["ref_key"] for p in probes if p["document_id"] == doc["document_id"]}
            self.assertEqual(keys, {"0", "2", "3", "4", "7.2a"})
        self.assertEqual(publish.verify_exact_references(self.db, self.package),
                         {"exact_reference_probes": 20, "exact_documents": 4})

    def test_missing_nonpilot_alias_is_rejected(self):
        self.db.missing_alias = True
        with self.assertRaisesRegex(ValueError, "7.2a"):
            publish.verify_exact_references(self.db, self.package)

    def test_no_assets_does_not_index_first_asset_or_activate_early(self):
        publish.insert_and_verify_assets(self.db, self.package)
        self.assertEqual(self.db.calls, [])


class RowDB:
    def __init__(self, rows):
        self.rows = deepcopy(rows)
        self.group_sizes = []

    def execute(self, query, parameters):
        statement = query.as_string()
        table = re.search(r'kb\."([a-z_]+)"', statement)[1]
        if "count(*)" in statement:
            return Result([(len(self.rows[table]),)])
        ids = set(parameters[1])
        self.group_sizes.append(len(ids))
        key = publish.TABLE_KEYS[table]
        return Result([(row,) for row in reversed(self.rows[table]) if row[key] in ids])


class ExhaustiveRowTests(unittest.TestCase):
    def setUp(self):
        vector = [struct.unpack("<f", struct.pack("<f", 0.123456789))[0]] + [0.0] * 383
        self.rows = {"search_chunks": [{"release_id": "r-fixture", "chunk_id": str(i),
                                         "body_text": f"Unveränderter Volltext {i}", "embedding": vector}
                                        for i in range(2 * publish.BATCH_ROWS + 3)]}
        self.package = {"release": {"release_id": "r-fixture"}, "rows": self.rows}
        self.db = RowDB(self.rows)

    def test_every_row_and_float32_value_is_compared_in_bounded_groups(self):
        for row in self.db.rows["search_chunks"]:
            row["embedding"] = json.dumps(row["embedding"])
        with patch.object(publish, "log"):
            self.assertEqual(publish.verify_rows(self.db, self.package), {"search_chunks": 503})
        self.assertEqual(self.db.group_sizes, [250, 250, 3])

    def test_corruption_in_last_group_is_rejected(self):
        self.db.rows["search_chunks"][-1]["body_text"] = "Gekürzter Text"
        with self.assertRaisesRegex(ValueError, "body_text"):
            publish.verify_rows(self.db, self.package)

    def test_vector_corruption_is_rejected(self):
        self.db.rows["search_chunks"][-1]["embedding"] = [1.0] + [0.0] * 383
        with self.assertRaisesRegex(ValueError, "embedding"):
            publish.verify_rows(self.db, self.package)

    def test_extra_cloud_row_is_rejected_before_content_comparison(self):
        self.db.rows["search_chunks"].append({"chunk_id": "unexpected"})
        with self.assertRaisesRegex(ValueError, "Zeilenzahl"):
            publish.verify_rows(self.db, self.package)


if __name__ == "__main__":
    unittest.main()
