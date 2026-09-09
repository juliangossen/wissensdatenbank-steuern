"""Integritäts- und Wiederaufnahmetests mit ausschließlich temporären Testdaten."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import sync_core as sync


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="wissensdatenbank-sync-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "source"
        self.target = self.base / "target"
        self.stand = "Rechtsgebiete/Testrecht/TG/Stand_2026-09-09"
        self.md = self.stand + "/TG.md"
        self.pdf = "PDF_Archiv/02_In_Markdown_umgewandelt/Stand_2026-09-09/Testrecht/TG.pdf"
        self.report = self.stand + "/Pruefung/Pruefbericht.md"
        self._write(self.md, "# Testgesetz\n\n§ 1 Erster Stand.\n".encode("utf-8"))
        self._write(self.pdf, b"%PDF-fixture\nOriginal bytes\n")
        self._write(self.stand + "/Quellen/TG.pdf", self._read(self.pdf))
        self._write(self.stand + "/Quellen/abbildung.png", b"figure-fixture")
        self._write(self.report, b"# Test-Pruefbericht\n")
        self._write(self.stand + "/Pruefung/Quellbloecke.json", b"[{\"text\": \"Test\"}]")
        self._register()

    def _write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def _read(self, relative):
        return (self.root / relative).read_bytes()

    def _register(self):
        pdf_hash = hashlib.sha256(self._read(self.pdf)).hexdigest()
        md_hash = hashlib.sha256(self._read(self.md)).hexdigest()
        self.entry = {
            "kuerzel": "TG", "titel": "Testgesetz", "bereich": "Testrecht",
            "original_pdf": self.pdf, "markdown": self.md, "pruefbericht": self.report,
            "pdf_archivversion": "Stand_2026-09-09", "quellenabgleich": "2026-09-09",
            "bearbeitungsstatus": "in_markdown_umgewandelt", "pdf_seiten": 1,
            "sha256_original_pdf": pdf_hash, "sha256_markdown": md_hash}
        inventory = {"quellenabgleich": "2026-09-09", "dokumente": 1, "eintraege": [self.entry],
                     "unbearbeitete_pdfs": ["PDF_Archiv/01_Unbearbeitet/neues.pdf"]}
        archive_entry = {
            "pdf": self.pdf, "markdown": self.md, "pruefbericht": self.report,
            "archivversion": "Stand_2026-09-09", "quellenabgleich": "2026-09-09",
            "status": "in_markdown_umgewandelt", "pdf_seiten": 1,
            "sha256_pdf": pdf_hash, "sha256_markdown": md_hash}
        self._write("Bestand.json", sync._json(inventory))
        self._write("PDF_Archiv/Archivregister.json", sync._json({"eintraege": [archive_entry]}))
        self._write(self.stand + "/Pruefung/Vollstaendigkeitspruefung.json",
                    sync._json({"sha256_pdf": pdf_hash, "sha256_markdown": md_hash,
                                "alle_textbloecke_identisch": True}))

    def _add_web_copy(self):
        stand = "Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/UStAE/Stand_2026-09-09"
        self.web_source = "Web_Archiv/02_In_Markdown_umgewandelt/Stand_2026-09-09/Steuerrecht/UStAE.txt"
        self.web_md = stand + "/UStAE.md"
        self.web_report = stand + "/Pruefung/Pruefbericht.md"
        self.web_proof = stand + "/Pruefung/Vollstaendigkeitspruefung.json"
        self._write(self.web_source, "1.1. Testabschnitt\n(1) Originaltext.\n".encode("utf-8"))
        self._write(self.web_md, "# UStAE\n\n## 1.1. Testabschnitt\n\n(1) Originaltext.\n".encode("utf-8"))
        self._write(self.web_report, b"# Test-Pruefung einer Textkopie\n")
        self._write(stand + "/Quellen/UStAE.txt", self._read(self.web_source))
        self.web_entry = {
            "kuerzel": "UStAE", "titel": "Umsatzsteuer-Anwendungserlass",
            "original_quelle": self.web_source, "markdown": self.web_md, "pruefbericht": self.web_report,
            "archivversion": "Stand_2026-09-09", "quellenabgleich": "2026-09-09", "erfasst_am": "2026-09-09",
            "quellenstand": ["Webkopie: Text gilt seit 02.06.2026"], "quellformat": "Webkopie (TXT)",
            "vollstaendigkeit": "Vollständig gegenüber bereitgestellter Textkopie.",
            "bearbeitungsstatus": sync.DONE,
            "sha256_original_quelle": hashlib.sha256(self._read(self.web_source)).hexdigest(),
            "sha256_markdown": hashlib.sha256(self._read(self.web_md)).hexdigest()}
        registered = dict(self.web_entry)
        registered["status"] = registered.pop("bearbeitungsstatus")
        self._write("Web_Archiv/Archivregister.json", sync._json({"eintraege": [registered]}))
        inventory = json.loads(self._read("Bestand.json"))
        inventory["eintraege"] = [self.entry, self.web_entry]
        inventory["dokumente"] = 2
        inventory["unbearbeitete_webquellen"] = ["Web_Archiv/01_Unbearbeitet/neuer_text.txt"]
        self._write("Bestand.json", sync._json(inventory))
        self._write(self.web_proof, sync._json({
            "sha256_original_quelle": self.web_entry["sha256_original_quelle"],
            "sha256_markdown": self.web_entry["sha256_markdown"], "pruefung_erfolgreich": True}))

    def test_mixed_sources_export_originals_without_inventing_pdf_and_keep_source_unchanged(self):
        self._add_web_copy()
        self._write("Web_Archiv/01_Unbearbeitet/neuer_text.txt", b"not reviewed")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = sync.publish(self.root, self.target)
        snapshot = Path(result["snapshot"])
        self.assertEqual(result["documents"], 2)
        for relative in (self.web_source, self.web_md, self.web_report, self.web_proof, self.pdf):
            self.assertEqual((snapshot / relative).read_bytes(), self._read(relative))
        self.assertFalse((snapshot / "Web_Archiv/01_Unbearbeitet").exists())
        exported = json.loads((snapshot / "Bestand.json").read_text(encoding="utf-8"))
        self.assertEqual(exported["unbearbeitete_webquellen"], [])
        self.assertNotIn("original_pdf", exported["eintraege"][1])
        self.assertNotIn("pdf_seiten", exported["eintraege"][1])
        self.assertIn("[Textkopie]", (snapshot / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(len(json.loads((snapshot / "Web_Archiv/Archivregister.json").read_bytes())["eintraege"]), 1)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_web_source_requires_register_and_successful_current_proof(self):
        self._add_web_copy()
        register = "Web_Archiv/Archivregister.json"
        originals = {p: self._read(p) for p in (register, self.web_proof, self.web_source, self.web_report)}
        failed = json.loads(originals[self.web_proof])
        failed["pruefung_erfolgreich"] = False
        stale = dict(failed, pruefung_erfolgreich=True, sha256_original_quelle="0" * 64)
        mismatch = json.loads(originals[register])
        mismatch["eintraege"][0]["markdown"] = self.md
        cases = [(register, None), (register, sync._json(mismatch)),
                 (self.web_proof, None), (self.web_proof, sync._json(failed)),
                 (self.web_proof, sync._json(stale)), (self.web_source, b"unreviewed change"),
                 (self.web_report, None)]
        for relative, modified in cases:
            with self.subTest(relative=relative, modified=modified):
                if modified is None:
                    (self.root / relative).unlink()
                else:
                    self._write(relative, modified)
                with self.assertRaises(sync.SyncError):
                    sync.publish(self.root, self.target)
                self.assertFalse(self.target.exists())
                self._write(relative, originals[relative])

    def test_plan_excludes_inbox_and_foreign_project_files(self):
        self._write("PDF_Archiv/01_Unbearbeitet/neues.pdf", b"not approved")
        self._write("private.txt", b"private")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        plan = sync.inspect_source(self.root)
        self.assertEqual(plan["documents"], 1)
        self.assertFalse(self.target.exists())
        result = sync.publish(self.root, self.target)
        snapshot = Path(result["snapshot"])
        self.assertFalse((snapshot / "private.txt").exists())
        self.assertFalse((snapshot / "PDF_Archiv/01_Unbearbeitet").exists())
        self.assertTrue((snapshot / self.stand / "Quellen/abbildung.png").is_file())
        self.assertEqual(json.loads((snapshot / "Bestand.json").read_text(encoding="utf-8"))["unbearbeitete_pdfs"], [])
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_bad_hash_fails_before_first_write(self):
        self._write(self.md, b"unreviewed edit")
        with self.assertRaisesRegex(sync.SyncError, "Prüfsumme"):
            sync.publish(self.root, self.target)
        self.assertFalse(self.target.exists())

    def test_stale_proof_blocks_updated_manifest(self):
        old_report = self._read(self.stand + "/Pruefung/Vollstaendigkeitspruefung.json")
        self._write(self.md, b"updated")
        self._register()
        self._write(self.stand + "/Pruefung/Vollstaendigkeitspruefung.json", old_report)
        with self.assertRaisesRegex(sync.SyncError, "Prüfnachweis"):
            sync.publish(self.root, self.target)
        self.assertFalse(self.target.exists())

    def test_interrupted_run_has_no_current_and_can_resume(self):
        def interrupted(message):
            if message.startswith("Kopiert:"):
                raise RuntimeError("simulated interruption")

        with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
            sync.publish(self.root, self.target, interrupted)
        cloud = self.target / sync.CLOUD_NAME
        self.assertFalse((cloud / sync.CURRENT).exists())
        partial = next((cloud / "Fassungen").iterdir())
        self.assertFalse((partial / sync.MANIFEST).exists())
        self.assertFalse((partial / "README.md").exists())
        result = sync.publish(self.root, self.target)
        self.assertEqual(Path(result["snapshot"]), partial)
        self.assertGreater(result["unchanged"], 0)
        self.assertTrue((partial / sync.MANIFEST).is_file())
        self.assertTrue((cloud / sync.CURRENT).is_file())

    def test_same_content_is_idempotent_and_all_manifest_bytes_match(self):
        first = sync.publish(self.root, self.target)
        cloud = self.target / sync.CLOUD_NAME
        current_before = (cloud / sync.CURRENT).read_bytes()
        second = sync.publish(self.root, self.target)
        self.assertEqual(first["snapshot"], second["snapshot"])
        self.assertEqual(second["copied"], 0)
        self.assertEqual(second["unchanged"], second["files"])
        self.assertEqual((cloud / sync.CURRENT).read_bytes(), current_before)
        self.assertEqual(second["state"], "lokal_bereitgestellt")
        self.assertEqual(second["cloud_upload"], "unbekannt")
        self.assertEqual(len(list((cloud / "Fassungen").iterdir())), 1)
        manifest = json.loads((Path(first["snapshot"]) / sync.MANIFEST).read_text(encoding="utf-8"))
        for entry in manifest["entries"]:
            data = (Path(first["snapshot"]) / entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
            self.assertEqual(len(data), entry["bytes"])

    def test_changed_snapshot_is_never_repaired_or_overwritten(self):
        result = sync.publish(self.root, self.target)
        snapshot = Path(result["snapshot"])
        (snapshot / self.md).write_bytes(b"remote changed")
        cloud = self.target / sync.CLOUD_NAME
        pointer = (cloud / sync.CURRENT).read_bytes()
        with self.assertRaisesRegex(sync.SyncError, "nicht überschrieben"):
            sync.publish(self.root, self.target)
        self.assertEqual((snapshot / self.md).read_bytes(), b"remote changed")
        self.assertEqual((cloud / sync.CURRENT).read_bytes(), pointer)

    def test_missing_file_in_complete_snapshot_is_not_silently_repaired(self):
        result = sync.publish(self.root, self.target)
        missing = Path(result["snapshot"]) / self.md
        missing.unlink()
        with self.assertRaises(sync.SyncError):
            sync.publish(self.root, self.target)
        self.assertFalse(missing.exists())

    def test_new_revision_preserves_all_previous_bytes(self):
        first = sync.publish(self.root, self.target)
        old = Path(first["snapshot"])
        old_bytes = {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()}
        self._write(self.md, b"# Testgesetz\nNew reviewed version\n")
        self._register()
        second = sync.publish(self.root, self.target)
        self.assertNotEqual(first["snapshot"], second["snapshot"])
        self.assertEqual(old_bytes, {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()})
        pointer = json.loads((self.target / sync.CLOUD_NAME / sync.CURRENT).read_text(encoding="utf-8"))
        self.assertTrue(pointer["snapshot"].endswith(second["version"]))

    def test_interruption_preserves_old_current(self):
        sync.publish(self.root, self.target)
        pointer = self.target / sync.CLOUD_NAME / sync.CURRENT
        before = pointer.read_bytes()
        self._write(self.md, b"second version")
        self._register()

        def interrupted(message):
            if message.startswith("Kopiert:"):
                raise RuntimeError("interrupted")

        with self.assertRaises(RuntimeError):
            sync.publish(self.root, self.target, interrupted)
        self.assertEqual(pointer.read_bytes(), before)

    def test_recursive_destinations_rejected(self):
        for destination in (self.root, self.root / "output", self.root.parent):
            if destination == self.root.parent:
                continue  # A sibling cloud directory is valid.
            with self.subTest(destination=destination), self.assertRaises(sync.SyncError):
                sync.publish(self.root, destination)
        with self.assertRaises(sync.SyncError):
            sync.publish(self.target / sync.CLOUD_NAME / "source", self.target)

    def test_unowned_cloud_directory_is_not_adopted(self):
        cloud = self.target / sync.CLOUD_NAME
        cloud.mkdir(parents=True)
        (cloud / "user.txt").write_bytes(b"keep")
        with self.assertRaises(sync.SyncError):
            sync.publish(self.root, self.target)
        self.assertEqual(list(cloud.iterdir()), [cloud / "user.txt"])

    def test_archive_mismatch_and_escaping_paths_fail_before_write(self):
        archive_path = self.root / "PDF_Archiv/Archivregister.json"
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
        archive["eintraege"][0]["markdown"] = "../outside.md"
        archive_path.write_bytes(sync._json(archive))
        with self.assertRaises(sync.SyncError):
            sync.publish(self.root, self.target)
        self.assertFalse(self.target.exists())
        for path in ("../outside.md", "C:/outside.md", "/absolute.md", "a\\b.md"):
            with self.subTest(path=path), self.assertRaises(sync.SyncError):
                sync._inside(self.root, path)


if __name__ == "__main__":
    unittest.main()
