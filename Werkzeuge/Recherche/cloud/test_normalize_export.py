"""Meaningful local contract/negative tests; no database, cloud or model needed."""
from pathlib import Path
import json
import tempfile
import unittest
from normalize_export import normalize, prepare, digest, encode, ExportError

HERE = Path(__file__).resolve().parent


def fixture(base, change=None):
    base.mkdir()
    rid = 'r-' + 'a' * 24
    markdown = '# Beispiel\n\n## § 1 Inhalt\n\nDer Wert beträgt −12,5 %.\n'
    blob = b'%PDF-1.7\nfixture only\n'
    asset_sha = digest(blob)
    document = {'doc_id': 'demo', 'abbreviation': 'Demo', 'title': 'Beispiel', 'document_type': 'Gesetz',
                'source_path': 'Rechtsgebiete/Demo/Stand_2026-09-09/Demo.md', 'source_sha256': digest(markdown.encode()),
                'source_url': 'https://example.invalid/amtlich', 'source_status': ['Historische Fassung 2011'],
                'import_date': '2026-09-09', 'valid_from': None, 'valid_to': None, 'metadata': {'bereich': 'Steuerrecht'}}
    provision = {'provision_id': 'demo:p-1', 'doc_id': 'demo', 'reference': '§ 1', 'title': '§ 1 Inhalt',
                 'anchor': 'p-1', 'ordinal': 0, 'asset_ids': ['demo:a-1']}
    asset = {'asset_id': 'demo:a-1', 'doc_id': 'demo', 'relative_path': 'Quellen/Demo.pdf',
             'source_path': 'Rechtsgebiete/Demo/Quellen/Demo.pdf', 'sha256': asset_sha, 'mime_type': 'application/pdf'}
    records = {
        'documents': [{'release_id': rid, 'id': 'demo', 'metadata': document, 'markdown': markdown}],
        'provisions': [{'release_id': rid, 'id': 'demo:p-1', 'doc_id': 'demo', 'ref_key': '1', 'metadata': provision, 'markdown': markdown}],
        'chunks': [{'release_id': rid, 'id': 1, 'provision_id': 'demo:p-1', 'text': 'Der Wert beträgt −12,5 %.', 'vector': [1.0] + [0.0] * 383}],
        'assets': [{'release_id': rid, 'id': 'demo:a-1', 'metadata': asset, 'object_path': 'assets/' + asset_sha}],
    }
    if change:
        change(records)
    files = []
    for table, rows in records.items():
        data = b''.join(encode(row) + b'\n' for row in rows)
        path = table + '.jsonl'
        (base / path).write_bytes(data)
        files.append({'path': path, 'size': len(data), 'sha256': digest(data)})
    (base / 'assets').mkdir()
    (base / 'assets' / asset_sha).write_bytes(blob)
    files.append({'path': 'assets/' + asset_sha, 'size': len(blob), 'sha256': asset_sha})
    manifest = {'format': 'research-export-1', 'release_id': rid,
                'metadata': {'model': 'fixture-model', 'model_revision': 'fixture-revision', 'dimensions': 384,
                             'document_count': 1, 'provision_count': 1, 'chunk_count': 1, 'asset_count': 1}, 'files': files}
    (base / 'manifest.json').write_bytes(encode(manifest))
    return manifest


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='test-normalize-', dir=HERE)
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_full_mapping_and_unknown_validity(self):
        source = self.base / 'source'
        fixture(source)
        output = self.base / 'output'
        result = normalize(source, output)
        self.assertFalse(result['cloud_uploaded'])
        d = json.loads((output / 'documents.jsonl').read_text(encoding='utf-8'))
        self.assertEqual(d['source_status'], ['Historische Fassung 2011'])
        self.assertEqual(d['import_date'], '2026-09-09')
        self.assertIsNone(d['valid_from'])
        self.assertIsNone(d['valid_to'])
        self.assertIn('−12,5 %', d['body_markdown'])
        a = json.loads((output / 'assets.jsonl').read_text(encoding='utf-8'))
        self.assertIsNone(a['verified_at'])
        self.assertTrue((output / 'manifest.json').is_file())

    def test_corrupted_file_is_rejected_before_output(self):
        source = self.base / 'source'
        fixture(source)
        (source / 'documents.jsonl').write_text('tampered', encoding='utf-8')
        with self.assertRaises(ExportError):
            normalize(source, self.base / 'output')
        self.assertFalse((self.base / 'output').exists())

    def test_traversal_manifest_is_rejected(self):
        source = self.base / 'source'
        m = fixture(source)
        m['files'][0]['path'] = '../documents.jsonl'
        (source / 'manifest.json').write_bytes(encode(m))
        with self.assertRaises(ExportError):
            prepare(source)

    def test_wrong_vector_dimensions_are_rejected(self):
        source = self.base / 'source'
        fixture(source, lambda r: r['chunks'][0]['vector'].append(1.0))
        with self.assertRaises(ExportError):
            prepare(source)

    def test_zero_vector_is_rejected(self):
        source = self.base / 'source'
        fixture(source, lambda r: r['chunks'][0].update(vector=[0.0] * 384))
        with self.assertRaises(ExportError):
            prepare(source)

    def test_cross_release_or_missing_provision_is_rejected(self):
        source = self.base / 'source'
        fixture(source, lambda r: r['chunks'][0].update(provision_id='missing'))
        with self.assertRaises(ExportError):
            prepare(source)

    def test_asset_hash_mismatch_is_rejected(self):
        source = self.base / 'source'
        fixture(source, lambda r: r['assets'][0]['metadata'].update(sha256='0' * 64))
        with self.assertRaises(ExportError):
            prepare(source)

    def test_existing_output_is_not_overwritten(self):
        source = self.base / 'source'
        fixture(source)
        output = self.base / 'output'
        output.mkdir()
        (output / 'user-file').write_text('preserve', encoding='utf-8')
        with self.assertRaises(ExportError):
            normalize(source, output)
        self.assertEqual((output / 'user-file').read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()
