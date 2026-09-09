"""Integrity and completeness tests for the registered provision importer."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    from . import parser
except ImportError:
    import parser


SOURCE = """# Testgesetz

## Navigation

- [§ 1 Vorsteuer](#p-1)
- [§ 2 Folge](#p-2)

<a id="p-1"></a>

### § 1 Vorsteuer

**(1)** Vollständiger Wortlaut mit <a href="#fn-1">[1]</a>.

#### Ausnahme

**(2)** Absatz mit Verweis auf § 2 Absatz 3 UStG.

<table><tr><td rowspan="2">10</td><td>20</td></tr>
<tr><td>30</td></tr></table>

![Schaubild](Quellen/grafik.png)

<a id="p-2"></a>

### § 2 Folge

**(1)** Eine andere Vorschrift.

## Globale Fußnoten

<p><a id="fn-1"></a><strong>[1]</strong><br>Erster Teil.</p>

<p>Rechtlich notwendiger Fortsetzungsabsatz.</p>

<a id="fn-2"></a>Andere Fußnote.
"""


class ParserFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.relative = "Rechtsgebiete/Steuerrecht/Gesetze/TestG/Stand_2026-09-09/TestG.md"
        self.source = self.root / self.relative
        self.source.parent.mkdir(parents=True)
        (self.source.parent / "Quellen").mkdir()
        (self.source.parent / "Quellen/grafik.png").write_bytes(b"test-image")
        (self.root / "Original.pdf").write_bytes(b"original bytes")
        self.entry = {
            "kuerzel": "TestG", "titel": "Testgesetz", "typ": "Gesetz/Verordnung",
            "markdown": self.relative, "original_pdf": "Original.pdf",
            "sha256_original_pdf": hashlib.sha256(b"original bytes").hexdigest(),
            "bearbeitungsstatus": "in_markdown_umgewandelt",
            "quellenabgleich": "2026-09-09", "quellenstand": ["Historische Testfassung"],
            "quelle": "https://example.invalid/testg/",
        }
        self.write_source(SOURCE)

    def write_source(self, markdown: str) -> None:
        data = markdown.encode("utf-8")
        self.source.write_bytes(data)
        self.entry["sha256_markdown"] = hashlib.sha256(data).hexdigest()
        self.write_register()

    def write_register(self) -> None:
        (self.root / "Bestand.json").write_text(
            json.dumps({"eintraege": [self.entry]}, ensure_ascii=False), encoding="utf-8")

    def parse(self) -> dict:
        return parser.parse_collection(self.root, ["TestG"])

    def test_preserves_original_and_complete_provision(self) -> None:
        result = self.parse()
        self.assertEqual(result["documents"][0]["markdown"], SOURCE)
        self.assertEqual(sum(p["kind"] == "provision" for p in result["provisions"]), 2)
        provision = result["provisions"][0]
        original_part = SOURCE[provision["source_start"]:provision["source_end"]]
        self.assertTrue(provision["markdown"].startswith(original_part))
        self.assertIn('rowspan="2"', provision["markdown"])
        self.assertIn("#### Ausnahme", provision["markdown"])
        self.assertIn("Rechtlich notwendiger Fortsetzungsabsatz.", provision["markdown"])
        self.assertNotIn("Andere Fußnote", provision["markdown"])
        self.assertNotIn("Navigation", provision["search_text"])
        self.assertIn("§ 2 Absatz 3 UStG", provision["cross_references"])
        self.assertEqual(provision["asset_ids"], [result["assets"][0]["asset_id"]])

    def test_import_date_does_not_claim_validity(self) -> None:
        doc = self.parse()["documents"][0]
        self.assertEqual(doc["import_date"], "2026-09-09")
        self.assertIsNone(doc["valid_from"])
        self.assertIsNone(doc["valid_to"])
        self.assertEqual(doc["source_status"], ["Historische Testfassung"])
        self.assertEqual(doc["document_type"], "Gesetz")

    def test_modified_markdown_is_rejected(self) -> None:
        self.source.write_text(SOURCE + "Geänderte Quelle", encoding="utf-8")
        with self.assertRaisesRegex(parser.ParseError, "Prüfsumme"):
            self.parse()

    def test_modified_original_is_rejected(self) -> None:
        (self.root / "Original.pdf").write_bytes(b"changed")
        with self.assertRaisesRegex(parser.ParseError, "Prüfsumme"):
            self.parse()

    def test_missing_footnote_is_rejected(self) -> None:
        self.write_source(SOURCE.replace('id="fn-1"', 'id="fn-removed"'))
        with self.assertRaisesRegex(parser.ParseError, "Unaufgelöste Fußnote"):
            self.parse()

    def test_missing_image_is_rejected(self) -> None:
        (self.source.parent / "Quellen/grafik.png").unlink()
        with self.assertRaisesRegex(parser.ParseError, "Quelldatei fehlt"):
            self.parse()

    def test_asset_cannot_escape_version_folder(self) -> None:
        self.write_source(SOURCE.replace("Quellen/grafik.png", "../grafik.png"))
        with self.assertRaisesRegex(parser.ParseError, "Unsicherer Quellpfad"):
            self.parse()

    def test_register_cannot_use_absolute_path(self) -> None:
        self.entry["markdown"] = "C:/private/secret.md"
        self.write_register()
        with self.assertRaisesRegex(parser.ParseError, "Unsicherer Quellpfad"):
            self.parse()

    def test_missing_or_duplicate_document_selection_is_rejected(self) -> None:
        with self.assertRaisesRegex(parser.ParseError, "fehlen im Register"):
            parser.parse_collection(self.root, ["NichtVorhanden"])
        with self.assertRaisesRegex(parser.ParseError, "doppelte"):
            parser.parse_collection(self.root, ["TestG", "testg"])

    def test_ambiguous_source_anchor_is_rejected(self) -> None:
        self.write_source(SOURCE.replace('id="p-2"', 'id="p-1"'))
        with self.assertRaisesRegex(parser.ParseError, "Doppelte Quellanker"):
            self.parse()

    def test_registered_metadata_changed_during_import_is_rejected(self) -> None:
        original = parser._parse_document

        def mutate_register(*args):
            result = original(*args)
            self.entry["quellenstand"] = ["Andere Fassung"]
            self.write_register()
            return result

        with patch.object(parser, "_parse_document", side_effect=mutate_register):
            with self.assertRaisesRegex(parser.ParseError, "Registereinträge.*geändert"):
                self.parse()

    def test_adjacent_alias_anchors_and_provenance_comments_are_preserved(self) -> None:
        self.write_source("""# Erlass
<a id="abschnitt-23-1"></a>
<a id="abschnitt-23-2"></a>
<a id="abschnitt-23-3"></a>
<a id="abschnitt-23-4"></a>

<!-- quelle:z10-10 -->
### 23.1–23.4 [aufgehoben]
<!-- /quelle:z10-10 -->
""")
        provision = self.parse()["provisions"][0]
        self.assertEqual(provision["reference"], "23.1–23.4")
        self.assertEqual(provision["anchor"], "abschnitt-23-1")
        self.assertEqual(len(provision["anchor_aliases"]), 4)
        self.assertEqual(provision["reference_aliases"], ["23.1", "23.2", "23.3", "23.4"])
        self.assertIn('id="abschnitt-23-4"', provision["markdown"])

    def test_multilevel_references_remain_distinct(self) -> None:
        refs = ["4.12.1", "4.12.2", "4.12.10", "1.11", "11.1", "15.2a", "4.12.1a"]
        self.write_source("# Erlass\n\n" + "\n\n".join(
            f'<a id="abschnitt-{reference.replace(".", "-")}"></a>\n\n'
            f"### {reference} Abschnitt\n\nVolltext zu Abschnitt {reference}."
            for reference in refs))
        provisions = self.parse()["provisions"]
        provisions = [p for p in provisions if p["kind"] == "provision"]
        self.assertEqual([p["reference"] for p in provisions], refs)
        for provision, reference in zip(provisions, refs):
            self.assertIn("Abschnitt " + reference, provision["cross_references"])
            self.assertEqual(provision["reference_aliases"], [])

    def test_grouped_statute_range_has_bounded_aliases(self) -> None:
        self.write_source('''# Gesetz

<a id="xxxx-33-bis-48a-33"></a>

### §§ 33 bis 48a (weggefallen)

<a id="xxxx-68-und-69-50"></a>

### §§ 68 und 69 (weggefallen)
''')
        provisions = self.parse()["provisions"]
        self.assertEqual(provisions[0]["reference"], "§§ 33 bis 48a")
        for reference in ["§ 33", "§ 40", "§ 48", "§ 48a"]:
            self.assertIn(reference, provisions[0]["reference_aliases"])
        self.assertNotIn("§ 33a", provisions[0]["reference_aliases"])
        self.assertEqual(provisions[1]["reference_aliases"], ["§ 68", "§ 69"])

    def test_duplicate_reference_with_different_anchors_is_rejected(self) -> None:
        self.write_source(SOURCE.replace("### § 2 Folge", "### § 1 Zweite Auslegung"))
        with self.assertRaisesRegex(parser.ParseError, "Mehrdeutige Vorschriftenreferenz"):
            self.parse()

    def test_default_import_selects_every_registered_document_and_checks_declared_total(self) -> None:
        collection = parser.parse_collection(self.root)
        self.assertEqual([d["abbreviation"] for d in collection["documents"]], ["TestG"])
        register = {"dokumente": 2, "eintraege": [self.entry]}
        (self.root / "Bestand.json").write_text(json.dumps(register), encoding="utf-8")
        with self.assertRaisesRegex(parser.ParseError, "Dokumentzahl"):
            parser.parse_collection(self.root)

    def test_preamble_unrecognized_text_and_global_notes_are_searchable(self) -> None:
        self.write_source(SOURCE.replace("## Navigation", "Ein rechtserheblicher Vorspann.\n\n## Navigation"))
        collection = self.parse()
        bodies = "\n".join(p["search_text"] for p in collection["provisions"])
        self.assertIn("Ein rechtserheblicher Vorspann.", bodies)
        self.assertIn("Andere Fußnote.", bodies)
        for start, end in parser._uncovered_ranges(len(collection["documents"][0]["markdown"]),
                                                  collection["provisions"]):
            self.assertFalse(parser.readable_text(collection["documents"][0]["markdown"][start:end]).strip())

    def test_roman_annex_keeps_quoted_article_heading_and_eu_note(self) -> None:
        self.write_source('''# Verordnung
<a id="art-7"></a>
## Artikel 7
Artikelwortlaut mit <a href="#ntr1-test">1</a>.
<a id="anhang-I"></a>
## ANHANG I
### Artikel 7 der vorliegenden Verordnung
Eigenständiger Inhalt des Anhangs.
<a id="ntr1-test"></a>Entscheidende amtliche Fußnote.
''')
        collection = self.parse()
        article = next(p for p in collection["provisions"] if p["reference"] == "Artikel 7")
        annex = next(p for p in collection["provisions"] if p["reference"] == "ANHANG I")
        self.assertIn("Entscheidende amtliche Fußnote", article["markdown"])
        self.assertIn("### Artikel 7 der vorliegenden Verordnung", annex["markdown"])
        self.assertNotIn("Eigenständiger Inhalt", article["markdown"])

    def test_source_with_no_named_norm_is_still_imported_completely(self) -> None:
        self.write_source("# Erlass\n\nEin vollständiger unnummerierter Erlasstext.\n")
        collection = self.parse()
        self.assertEqual(len(collection["provisions"]), 1)
        self.assertEqual(collection["provisions"][0]["markdown"], collection["documents"][0]["markdown"])

    def test_linked_supplement_keeps_distinct_source_and_dependent_asset(self) -> None:
        supplements = self.source.parent / "Ergaenzungen"
        supplements.mkdir()
        extra = b"# Vergleichsfassung 2025\r\n\r\n![Tabelle](../Quellen/grafik.png)\r\nNeuer Text.\r\n"
        (supplements / "Vergleich.md").write_bytes(extra)
        self.write_source(SOURCE + "\n[Gesonderte Fassung](Ergaenzungen/Vergleich.md)\n")
        collection = self.parse()
        supplement = next(p for p in collection["provisions"] if p["kind"] == "supplement")
        self.assertEqual(supplement["markdown"], extra.decode())
        self.assertEqual(supplement["source_sha256"], hashlib.sha256(extra).hexdigest())
        self.assertTrue(supplement["source_path"].endswith("Ergaenzungen/Vergleich.md"))
        self.assertEqual(len(supplement["asset_ids"]), 2)

    def test_unlinked_archival_sources_are_kept_but_programs_are_excluded(self) -> None:
        (self.source.parent / "Quellen/unverlinkte-quelle.zip").write_bytes(b"official source")
        (self.source.parent / "Quellen/import.py").write_text("raise RuntimeError('must not execute')")
        (self.source.parent / "README.md").write_text("Nachweis und Fassung.", encoding="utf-8")
        collection = self.parse()
        assets = {a["relative_path"] for a in collection["assets"]}
        self.assertIn("Quellen/unverlinkte-quelle.zip", assets)
        self.assertIn("README.md", assets)
        self.assertNotIn("Quellen/import.py", assets)

    def test_margin_context_uses_only_source_headings_and_never_previous_margins(self) -> None:
        self.write_source('''# Erlass
<a id="teil-a"></a>
## Erster Sachabschnitt
<a id="rn-01-01"></a>
<p class="randnummer"><strong>01.01</strong>Erster Text.</p>
<a id="rn-01-02"></a>
<p class="randnummer"><strong>01.02</strong>Zweiter Text.</p>
<a id="teil-b"></a>
## Zweiter Sachabschnitt
<a id="rn-02-01"></a>
<p class="randnummer"><strong>02.01</strong>Dritter Text.</p>
''')
        margins = [p for p in self.parse()["provisions"] if p["reference"].startswith("Rn. ")]
        self.assertEqual([p["title"] for p in margins], [
            "Rn. 01.01 – Erster Sachabschnitt", "Rn. 01.02 – Erster Sachabschnitt",
            "Rn. 02.01 – Zweiter Sachabschnitt"])


class ActualCollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        if not (cls.root / "Bestand.json").is_file():
            raise unittest.SkipTest("Pilotquellen sind in dieser Umgebung nicht vorhanden.")
        cls.collection = parser.parse_collection(cls.root)

    def find(self, doc_id: str, reference: str) -> dict:
        return next(p for p in self.collection["provisions"]
                    if p["doc_id"] == doc_id and p["reference"] == reference)

    def test_ustg_full_section_and_application_notes(self) -> None:
        provision = self.find("ustg", "§ 15")
        self.assertIn("Vorsteuerabzug", provision["title"])
        self.assertIn("**(1)**", provision["markdown"])
        self.assertIn("**(5)**", provision["markdown"])
        self.assertIn("Fußnote", provision["markdown"])
        self.assertNotIn("### § 15a", provision["markdown"])

    def test_ustae_sections_with_letter_suffix_and_footnotes(self) -> None:
        provision = self.find("ustae", "15.2a")
        self.assertIn("Ordnungsmäßige Rechnung", provision["title"])
        self.assertIn('id="fn-z16016"', provision["markdown"])
        self.assertEqual(provision["anchor"], "abschnitt-15-2a")

    def test_bewg_complex_tables_and_images_survive(self) -> None:
        provision = self.find("bewg", "Anlage 24")
        self.assertIn("<table", provision["markdown"])
        self.assertIn("rowspan=", provision["markdown"])
        self.assertIn("<img", provision["markdown"])
        self.assertTrue(provision["asset_ids"])
        self.assertIn("Fußnote", provision["markdown"])

    def test_all_original_provision_slices_are_kept(self) -> None:
        docs = {d["doc_id"]: d for d in self.collection["documents"]}
        for provision in self.collection["provisions"]:
            raw = ((self.root / provision["source_path"]).read_bytes().decode("utf-8-sig")
                   if provision["kind"] == "supplement" else docs[provision["doc_id"]]["markdown"])
            body = raw[provision["source_start"]:provision["source_end"]]
            self.assertTrue(provision["markdown"].startswith(body), provision["provision_id"])

    def test_all_pilot_references_and_aliases_are_unique_per_document(self) -> None:
        seen = {}
        for provision in self.collection["provisions"]:
            for reference in [provision["reference"], *provision["reference_aliases"]]:
                key = (provision["doc_id"], reference)
                self.assertNotIn(key, seen, (key, seen.get(key), provision["provision_id"]))
                seen[key] = provision["provision_id"]
        # 11.1 is not present in this UStAE copy; its collision with 1.11 is
        # covered by the synthetic parser and Store fixtures instead.
        for reference in ["4.12.1", "4.12.2", "4.12.10", "1.11"]:
            provision = self.find("ustae", reference)
            self.assertEqual(provision["anchor"], "abschnitt-" + reference.replace(".", "-"))

    def test_every_registered_main_source_original_and_text_are_present(self) -> None:
        register = json.loads((self.root / "Bestand.json").read_text(encoding="utf-8-sig"))
        docs = self.collection["documents"]
        self.assertEqual(len(docs), register["dokumente"])
        self.assertEqual({d["source_path"] for d in docs}, {e["markdown"] for e in register["eintraege"]})
        assets = {a["asset_id"]: a for a in self.collection["assets"]}
        for doc in docs:
            self.assertEqual(doc["markdown"], (self.root / doc["source_path"]).read_bytes().decode("utf-8-sig"))
            self.assertTrue(doc["original_asset_ids"])
            self.assertTrue(all(asset_id in assets for asset_id in doc["original_asset_ids"]))
            items = [p for p in self.collection["provisions"]
                     if p["doc_id"] == doc["doc_id"] and p["kind"] != "supplement"]
            for start, end in parser._uncovered_ranges(len(doc["markdown"]), items):
                self.assertFalse(parser.readable_text(doc["markdown"][start:end]).strip(), doc["doc_id"])

    def test_cloud_anchors_are_unique_and_generated_anchors_are_identified(self) -> None:
        seen = set()
        for item in self.collection["provisions"]:
            self.assertTrue(item["anchor"])
            key = item["doc_id"], item["anchor"]
            self.assertNotIn(key, seen)
            seen.add(key)
            if item["kind"] in {"source_part", "supplement"}:
                self.assertTrue(item["generated_anchor"])
                self.assertIn("source_anchor", item)

    def test_regulations_are_not_classified_from_the_law_folder(self) -> None:
        docs = {d["abbreviation"]: d for d in self.collection["documents"]}
        for abbreviation in ["KassenSichV", "LStDV", "GewStDV", "KStDV", "FzgLiefgMeldV"]:
            self.assertEqual(docs[abbreviation]["document_type"], "Verordnung")
        for abbreviation in ["DSGVO", "DVO (EU) 282/2011"]:
            self.assertEqual(docs[abbreviation]["document_type"], "EU-Verordnung")
        self.assertEqual(docs["BattDG"]["document_type"], "Gesetz")

    def test_every_stand_data_file_is_archived_or_a_registered_main_source(self) -> None:
        covered = {a["source_path"] for a in self.collection["assets"]}
        covered.update(d["source_path"] for d in self.collection["documents"])
        for doc in self.collection["documents"]:
            for path in (self.root / doc["source_path"]).parent.rglob("*"):
                if path.is_file() and path.suffix.lower() in parser._ARCHIVE_SUFFIXES:
                    self.assertIn(path.relative_to(self.root).as_posix(), covered)

    def test_egbgb_articles_and_nested_paragraphs_keep_complete_context(self) -> None:
        article = self.find("egbgb", "Art 250")
        nested = self.find("egbgb", "Art 250 / § 1")
        self.assertIn(nested["markdown"].rstrip(), article["markdown"])
        self.assertIn("Form und Zeitpunkt", nested["title"])
        self.assertNotEqual(self.find("egbgb", "Art 234")["provision_id"],
                            self.find("egbgb", "Art 234 / §§ 8 und 9")["provision_id"])

    def test_admin_guidance_and_historical_rules_remain_distinguishable(self) -> None:
        aeao = self.find("aeao", "AEAO zu § 8")
        self.assertIn("6.1. Auslandsaufenthalt", aeao["markdown"])
        self.assertIn("Wohnsitz", aeao["title"])
        self.find("estr-2012-esth-2025", "R 3.40")
        historical = self.find("estr-2012-esth-2025", "R 3.40 EStR 2008")
        self.assertIn("2008", historical["title"])
        self.find("erbstr-2019-erbsth-2019", "H E 3.1 (1)")
        self.find("erbstr-2019-erbsth-2019", "H E 3.1 (2)")

    def test_all_umwste_margin_numbers_and_gobd_changes_are_retrievable(self) -> None:
        margins = [p for p in self.collection["provisions"]
                   if p["doc_id"] == "umwste-2025" and p["reference"].startswith("Rn. ")]
        self.assertEqual(len(margins), 572)
        self.assertIn("class=\"randnummer\"", self.find("umwste-2025", "Rn. 01.01")["markdown"])
        change = self.find("zweite-gobd-anderung-vom-14-07-2025", "Abschnitt 11")
        self.assertIn("Randziffer 185", change["markdown"])
        grouped = self.find("umwste-2025", "Rn. 27.09 bis 27.11")
        self.assertEqual(grouped["reference_aliases"], ["Rn. 27.09", "Rn. 27.10", "Rn. 27.11"])
        self.assertIn("einstweilen frei", grouped["markdown"])


if __name__ == "__main__":
    unittest.main()
