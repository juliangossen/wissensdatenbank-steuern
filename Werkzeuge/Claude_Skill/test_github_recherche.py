"""Behavioral checks for the standalone Claude skill GitHub helper; no network."""

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".claude" / "skills" / "steuerrecht-recherche" / "scripts" / "github_recherche.py"
SPEC = importlib.util.spec_from_file_location("github_recherche", SCRIPT)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)
COMMIT = "a" * 40


class Fixture:
    def __init__(self, documents, register_mutator=None):
        self.calls = []
        self.files = {}
        self.entries = []
        for name, data in documents.items():
            path = "Rechtsgebiete/" + name + "/Stand_2026-09-09/" + name + ".md"
            self.files[path] = data
            self.entries.append({"kuerzel": name, "titel": name + " Volltext", "markdown": path,
                                 "sha256_markdown": hashlib.sha256(data).hexdigest(),
                                 "quellenabgleich": "2026-09-09", "quellenstand": ["historische Fassung"],
                                 "quelle": "https://example.org/amtlich", "vollstaendigkeit": "ungeprüfter Wortlaut"})
        self.register = {"dokumente": len(self.entries), "eintraege": self.entries, "quellenabgleich": "2026-09-09"}
        if register_mutator:
            register_mutator(self.register)

    def fetch(self, url, maximum):
        self.calls.append((url, maximum))
        if url == helper.API_ROOT + "/commits/main":
            return (COMMIT + "\n").encode()
        root = helper.RAW_ROOT + "/" + COMMIT + "/"
        if not url.startswith(root):
            raise AssertionError("Mutable or unexpected URL: " + url)
        path = url[len(root):]
        if path == "Bestand.json":
            return json.dumps(self.register, ensure_ascii=False).encode("utf-8")
        return self.files[path]


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def repository(self, documents, mutator=None):
        self.fixture = Fixture(documents, mutator)
        return helper.Repository(COMMIT, self.temp.name, self.fixture.fetch)

    def test_resolve_pins_full_sha_and_catalog_preserves_source_limits(self):
        fixture = Fixture({"UStG": b"test"})
        resolved = helper.resolve(fetch=fixture.fetch)
        repository = helper.Repository(resolved["commit"], self.temp.name, fixture.fetch)
        catalog = repository.catalog()
        self.assertEqual(COMMIT, resolved["commit"])
        self.assertEqual(["historische Fassung"], catalog["documents"][0]["quellenstand"])
        self.assertEqual("ungeprüfter Wortlaut", catalog["documents"][0]["vollstaendigkeit"])
        self.assertIn("/blob/" + COMMIT + "/", catalog["documents"][0]["github_url"])

    def test_hashes_original_crlf_utf8_bytes_without_normalizing(self):
        raw = b"\xef\xbb\xbf" + "# Gesetz\r\n\r\nÜbertrag ß 😀\r\n".encode("utf-8")
        repository = self.repository({"UStG": raw})
        result = repository.read("ustg")
        self.assertTrue(result["sha256_verified"])
        self.assertEqual(raw.decode("utf-8-sig"), result["text"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["source"]["sha256_markdown"])
        self.assertIn("L3: Übertrag", result["numbered_text"])

    def test_mismatched_download_is_not_read_or_cached(self):
        repository = self.repository({"UStG": b"unchanged"})
        self.fixture.files[self.fixture.entries[0]["markdown"]] = b"modified"
        with self.assertRaises(helper.ResearchError) as error:
            repository.read("UStG")
        self.assertEqual("integrity", error.exception.code)
        self.assertFalse(list(Path(self.temp.name).iterdir()))

    def test_cache_is_reverified_and_corruption_refetched(self):
        repository = self.repository({"UStG": b"# Gesetz\nRichtig."})
        repository.read("UStG")
        first_count = len(self.fixture.calls)
        repository.read("UStG")
        self.assertEqual(first_count, len(self.fixture.calls))
        next(Path(self.temp.name).glob("*.bin")).write_bytes(b"forged")
        result = repository.read("UStG")
        self.assertEqual(first_count + 1, len(self.fixture.calls))
        self.assertIn("Richtig", result["text"])

    def test_search_covers_end_of_full_document_and_selected_sources_only(self):
        repository = self.repository({"UStG": ("Intro\n\n" + "x" * 30000 + "\n\nDIFFERENZbesteuerung am Ende.").encode(),
                                      "AO": b"Nicht ausgewahlt"})
        result = repository.search(["UStG"], "differenzbesteuerung")
        self.assertEqual(1, result["total"])
        self.assertGreater(result["results"][0]["read_offset"], 30000)
        self.assertFalse(any("/AO/" in call[0] for call in self.fixture.calls))
        page = repository.read("UStG", result["results"][0]["read_offset"])
        self.assertIn("am Ende", page["text"])

    def test_search_all_any_are_paragraph_based_and_paginate_stably(self):
        repository = self.repository({"UStG": "alpha\n\nbeta\n\nAlpha beta\n\nalpha BETA\n".encode()})
        first = repository.search(["UStG"], "alpha beta", limit=1)
        second = repository.search(["UStG"], "alpha beta", offset=first["next_offset"], limit=1)
        self.assertEqual(2, first["total"])
        self.assertIsNone(second["next_offset"])
        self.assertLess(first["results"][0]["read_offset"], second["results"][0]["read_offset"])
        self.assertEqual(4, repository.search(["UStG"], "alpha beta", mode="any")["total"])

    def test_read_paging_reconstructs_long_lines_unicode_crlf_and_final_line(self):
        original = "# Kopf\r\n" + "ß😀a" * 6000 + "\r\n" + "\n" * 200 + "ENDE ohne Zeilenumbruch"
        repository = self.repository({"UStG": original.encode("utf-8")})
        chunks, offset, previous = [], 0, -1
        while offset is not None:
            self.assertGreater(offset, previous)
            previous = offset
            page = repository.read("UStG", offset, limit=997)
            self.assertLessEqual(page["returned_characters"], 997)
            self.assertLessEqual(page["text"].count("\n"), helper.MAX_READ_LINES)
            self.assertEqual(original.count("\n", 0, offset) + 1, page["start_line"])
            chunks.append(page["text"])
            offset = page["next_offset"]
        self.assertEqual(original, "".join(chunks))

    def test_read_unicode_line_separator_does_not_invent_github_line(self):
        repository = self.repository({"UStG": "a\u2028b\nc".encode("utf-8")})
        result = repository.read("UStG")
        self.assertEqual("L1: a\u2028b\nL2: c", result["numbered_text"])
        self.assertEqual(2, result["end_line"])

    def test_headings_ignore_navigation_links_and_return_readable_offsets(self):
        original = "# Gesetz\n\n- [§ 25a](#p25a)\n\n## § 25a Differenzbesteuerung\nText.\n\n### Tabelle\nTabelle.\n\n## § 26\nWeiter."
        repository = self.repository({"UStG": original.encode("utf-8")})
        result = repository.headings("UStG", "§ 25a")
        self.assertEqual(1, result["total"])
        candidate = result["headings"][0]
        self.assertEqual(2, candidate["level"])
        self.assertTrue(original[candidate["next_heading_offset"]:].startswith("### Tabelle"))
        self.assertTrue(repository.read("UStG", candidate["read_offset"])["text"].startswith("## § 25a"))

    def test_mutable_commits_and_traversal_are_rejected_before_download(self):
        for value in ("main", "a" * 39, "a" * 41, "../main", "https://bad.invalid", None):
            with self.subTest(value=value), self.assertRaises(helper.ResearchError):
                helper.Repository(value, self.temp.name, lambda *_: self.fail("network called"))
        for value in ("../x.md", "/x.md", "a/../x.md", "a\\x.md", "C:/x.md", "a/%2e%2e/x.md", "x.md?token=a"):
            with self.subTest(value=value), self.assertRaises(helper.ResearchError):
                helper.validate_path(value)
        for value in ("../main", "main?x", "main#x", "a//b", "a/../b", "foo.lock", "-main"):
            with self.subTest(value=value), self.assertRaises(helper.ResearchError):
                helper.resolve(value, lambda *_: self.fail("network called"))

    def test_register_errors_fail_closed(self):
        mutations = [lambda reg: reg.update(dokumente=2),
                     lambda reg: reg["eintraege"][0].update(sha256_markdown="missing"),
                     lambda reg: reg["eintraege"][0].update(markdown="../../secrets.md")]
        for mutator in mutations:
            with self.subTest(mutator=mutator), self.assertRaises(helper.ResearchError):
                self.repository({"UStG": b"x"}, mutator)

    def test_bounds_require_specific_documents_and_nonempty_queries(self):
        repository = self.repository({"UStG": b"x"})
        for action in (lambda: repository.select([]), lambda: repository.select(["UStG"] * 6),
                       lambda: repository.search(["UStG"], ""), lambda: repository.search(["UStG"], "a" * 251),
                       lambda: repository.read("UStG", -1), lambda: repository.read("UStG", 2),
                       lambda: repository.read("UStG", limit=12001), lambda: repository.catalog(limit=21)):
            with self.assertRaises(helper.ResearchError):
                action()

    def test_network_failures_have_actionable_messages_without_raw_exception(self):
        errors = [URLError("SECRET_INTERNAL_PROXY"), HTTPError("https://secret", 403, "SECRET_TOKEN", {}, None)]
        for error in errors:
            with self.subTest(error=type(error).__name__), patch.object(helper, "build_opener") as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaises(helper.ResearchError) as caught:
                    helper.fetch_bytes(helper.RAW_ROOT + "/file", 100)
                self.assertIn("Netzwerkfreigabe", str(caught.exception))
                self.assertNotIn("SECRET", str(caught.exception))

    def test_response_oversize_and_incomplete_content_are_rejected(self):
        class Response(io.BytesIO):
            status = 200
            def geturl(self):
                return helper.RAW_ROOT + "/file"
        for content, headers, expected in [(b"x" * 11, {}, "size"), (b"x", {"Content-Length": "11"}, "size"),
                                           (b"x", {"Content-Length": "2"}, "network")]:
            response = Response(content)
            response.headers = headers
            with self.subTest(expected=expected), patch.object(helper, "build_opener") as opener:
                opener.return_value.open.return_value = response
                with self.assertRaises(helper.ResearchError) as caught:
                    helper.fetch_bytes(response.geturl(), 10)
                self.assertEqual(expected, caught.exception.code)

    def test_cli_runtime_error_is_structured_json_without_traceback(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = helper.main(["catalog", "--commit", "main"])
        self.assertEqual(1, code)
        parsed = json.loads(output.getvalue())
        self.assertFalse(parsed["ok"])
        self.assertEqual("commit", parsed["error"]["code"])
        self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()
