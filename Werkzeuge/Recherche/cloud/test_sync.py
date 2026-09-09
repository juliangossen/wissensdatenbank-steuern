"""Full-register sync selection and publication-pointer integrity."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import sync


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name)
        self.root = self.app / "corpus"
        self.rid = "r-complete"
        self.collection = {"documents": [{"doc_id": str(i)} for i in range(58)]}
        self.store = Mock()
        self.store.import_collection.return_value = {"release_id": self.rid}

        def export(target, rid):
            target.mkdir(parents=True)
            (target / "manifest.json").write_text(json.dumps({"release_id": rid}), encoding="utf-8")

        self.store.export.side_effect = export
        self.parse = patch.object(sync, "parse_collection", return_value=self.collection).start()
        patch.object(sync, "APP", self.app).start()
        patch.object(sync, "ROOT", self.root).start()
        patch.object(sync, "build_store", return_value=self.store).start()
        self.publish = patch.object(sync, "publish", return_value={"release_id": self.rid}).start()
        patch("builtins.print").start()
        self.addCleanup(patch.stopall)

    def test_default_sync_passes_the_entire_register_and_publishes_its_export(self):
        sync.sync()
        self.parse.assert_called_once_with(self.root)
        self.assertIs(self.store.import_collection.call_args.args[0], self.collection)
        self.assertEqual(self.publish.call_args.kwargs, {"apply": True})
        pointer = json.loads((self.app / ".daten/Cloud_Paketpfad.json").read_text(encoding="utf-8"))
        self.assertEqual(pointer["release_id"], self.rid)
        self.assertFalse((Path(pointer["base"]) / "Supabase").exists())
        self.store.list_versions.assert_not_called()

    def test_failed_publication_preserves_previous_cloud_pointer(self):
        pointer = self.app / ".daten/Cloud_Paketpfad.json"
        pointer.parent.mkdir()
        previous = '{"release_id":"r-old","base":"previous-package"}\n'
        pointer.write_text(previous, encoding="utf-8")
        self.publish.side_effect = ValueError("Cloudprüfung fehlgeschlagen")
        with self.assertRaisesRegex(ValueError, "Cloudprüfung"):
            sync.sync()
        self.assertEqual(pointer.read_text(encoding="utf-8"), previous)


if __name__ == "__main__":
    unittest.main()
