"""Verify Store.export research-export-1 and prepare local PostgreSQL import rows.

No database connection, uploads, credentials or source edits. Standard library only.
Usage: py -B normalize_export.py EXPORT_DIRECTORY NEW_TARGET_DIRECTORY
The output manifest is written last; without it the output is incomplete.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

SCHEMA_VERSION = 'research-postgres-1'
HASH = re.compile(r'[0-9a-f]{64}\Z')


class ExportError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ExportError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Doppelter JSON-Schlüssel: {key}')
        result[key] = value
    return result


def decode(data):
    def invalid(value):
        raise ExportError(f'Nicht endlicher JSON-Wert: {value}')
    return json.loads(data, object_pairs_hook=json_object, parse_constant=invalid)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def safe_relative(value):
    require(isinstance(value, str) and bool(value), 'Leerer oder ungültiger relativer Pfad')
    path = PurePosixPath(value)
    require(bool(path.parts) and not path.is_absolute() and str(path) == value and '..' not in path.parts
            and '\\' not in value and ':' not in value and not any(ord(c) < 32 for c in value),
            f'Unsicherer relativer Pfad: {value!r}')
    return path


def inside(base, relative):
    path = base.joinpath(*safe_relative(relative).parts)
    cursor = path
    while cursor != base:
        require(not cursor.is_symlink() and not getattr(cursor, 'is_junction', lambda: False)(),
                f'Verknüpfung als Quelle unzulässig: {relative}')
        cursor = cursor.parent
    require(path.resolve().is_relative_to(base) and path.is_file(), f'Quelldatei fehlt: {relative}')
    return path


def hash_file(path):
    hasher = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            hasher.update(block)
            size += len(block)
    return hasher.hexdigest(), size


def actual_files(base):
    result = set()
    stack = [base]
    while stack:
        directory = stack.pop()
        for entry in directory.iterdir():
            require(not entry.is_symlink() and not getattr(entry, 'is_junction', lambda: False)(),
                    f'Verknüpfung im Export: {entry.name}')
            if entry.is_dir():
                stack.append(entry)
            elif entry.is_file():
                result.add(entry.relative_to(base).as_posix())
            else:
                raise ExportError('Export enthält eine besondere Dateisystemdatei')
    return result


def text(value, name, allow_empty=False):
    require(isinstance(value, str) and (allow_empty or bool(value)), f'Ungültiger Text: {name}')
    require('\x00' not in value, f'NUL-Zeichen: {name}')
    return value


def number(value, name):
    require(type(value) is int and value >= 0, f'Ungültiger Zählwert: {name}')
    return value


def legal_date(value, name, nullable=True):
    if value is None and nullable:
        return None
    require(isinstance(value, str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)), f'Ungültiges Datum: {name}')
    require(date.fromisoformat(value).isoformat() == value, f'Ungültiges Datum: {name}')
    return value


def validity(metadata):
    start = legal_date(metadata.get('valid_from'), 'valid_from')
    end = legal_date(metadata.get('valid_to'), 'valid_to')
    require(start is None or end is None or start <= end, 'Gültigkeitsende liegt vor dem Anfang')
    return {'valid_from': start, 'valid_to': end}


def prepare(source):
    raw_source = Path(source).absolute()
    require(not raw_source.is_symlink() and not getattr(raw_source, 'is_junction', lambda: False)(), 'Exportordner ist eine Verknüpfung')
    base = raw_source.resolve()
    require(base.is_dir(), 'Exportordner fehlt')
    manifest_path = inside(base, 'manifest.json')
    manifest_bytes = manifest_path.read_bytes()
    manifest = decode(manifest_bytes)
    require(manifest.get('format') == 'research-export-1', 'Nicht unterstütztes Exportformat')
    release_id = text(manifest.get('release_id'), 'release_id')
    require(bool(re.fullmatch(r'r-[0-9a-f]{24}', release_id)), 'Ungültige Release-ID')
    metadata = manifest.get('metadata')
    require(isinstance(metadata, dict), 'Release-Metadaten fehlen')
    require(metadata.get('dimensions') == 384, 'Cloud-Schema benötigt genau 384 Dimensionen')
    model = text(metadata.get('model'), 'model')
    revision = text(metadata.get('model_revision'), 'model_revision')
    files = {}
    require(isinstance(manifest.get('files'), list), 'Manifest-Dateiliste fehlt')
    for item in manifest['files']:
        require(isinstance(item, dict), 'Ungültiger Manifest-Eintrag')
        relative = str(safe_relative(item.get('path')))
        require(relative not in files and relative != 'manifest.json', f'Doppelter Manifest-Pfad: {relative}')
        expected_hash = item.get('sha256')
        require(isinstance(expected_hash, str) and HASH.fullmatch(expected_hash), f'Ungültige Prüfsumme: {relative}')
        size = number(item.get('size'), 'size')
        path = inside(base, relative)
        require(hash_file(path) == (expected_hash, size), f'Prüfsumme/Dateigröße weicht ab: {relative}')
        files[relative] = {'path': path, 'sha256': expected_hash, 'size': size}
    required = {name + '.jsonl' for name in ('documents', 'provisions', 'chunks', 'assets')}
    require(required <= files.keys(), 'JSONL-Dateien fehlen')
    require(actual_files(base) == set(files) | {'manifest.json'}, 'Nicht registrierte oder fehlende Dateien im Export')
    tables = {}
    for name in ('documents', 'provisions', 'chunks', 'assets'):
        data = files[name + '.jsonl']['path'].read_bytes()
        require(digest(data) == files[name + '.jsonl']['sha256'], 'Export während des Lesens geändert')
        rows = [decode(line) for line in data.decode('utf-8').splitlines() if line.strip()]
        require(all(isinstance(row, dict) and row.get('release_id') == release_id for row in rows), 'Fremde Release-ID oder ungültige JSONL-Zeile')
        fields = {'documents': {'release_id', 'id', 'metadata', 'markdown'},
                  'provisions': {'release_id', 'id', 'doc_id', 'ref_key', 'metadata', 'markdown'},
                  'chunks': {'release_id', 'id', 'provision_id', 'text', 'vector'},
                  'assets': {'release_id', 'id', 'metadata', 'object_path'}}[name]
        require(all(set(row) == fields for row in rows), f'Nicht unterstützte Felder in {name}')
        require(len({str(row.get('id')) for row in rows}) == len(rows), f'Doppelte IDs in {name}')
        tables[name] = rows
    for table, count_key in [('documents', 'document_count'), ('provisions', 'provision_count'), ('chunks', 'chunk_count'), ('assets', 'asset_count')]:
        require(len(tables[table]) == number(metadata.get(count_key), count_key), f'Manifest-Anzahl weicht ab: {table}')
    require(tables['documents'] and tables['provisions'] and tables['chunks'], 'Leerer Recherchebestand')

    output = {name: [] for name in ('releases', 'documents', 'provisions', 'search_chunks', 'assets')}
    doc_ids = set()
    for row in tables['documents']:
        m = row.get('metadata')
        require(isinstance(m, dict) and row['id'] == m.get('doc_id'), 'Dokument-ID widerspricht Metadaten')
        ident = text(row['id'], 'document_id')
        markdown = text(row.get('markdown'), 'document markdown')
        source_hash = m.get('source_sha256')
        require(isinstance(source_hash, str) and HASH.fullmatch(source_hash), 'Dokument-Prüfsumme fehlt')
        # parser.py entfernt einen gegebenenfalls vorhandenen UTF-8-BOM beim Dekodieren.
        require(source_hash in {digest(markdown.encode('utf-8')), digest(b'\xef\xbb\xbf' + markdown.encode('utf-8'))}, 'Markdown stimmt nicht mit registrierter Quellprüfsumme überein')
        status = m.get('source_status')
        require(isinstance(status, list) and all(isinstance(x, str) for x in status), 'source_status muss unverändert als Liste vorliegen')
        source_path = str(safe_relative(m.get('source_path')))
        source_url = text(m.get('source_url', ''), 'source_url', True)
        require(not source_url or (urlsplit(source_url).scheme in ('http', 'https') and bool(urlsplit(source_url).netloc)), 'Ungültige Quellen-URL')
        entry = m.get('metadata', {})
        require(isinstance(entry, dict), 'Ungültige Registermetadaten')
        output['documents'].append({
            'release_id': release_id, 'document_id': ident, 'title': text(m.get('title'), 'title'),
            'abbreviation': text(m.get('abbreviation'), 'abbreviation'),
            'legal_area': text(entry.get('bereich', ''), 'legal_area', True),
            'document_type': text(m.get('document_type', ''), 'document_type', True),
            'source_path': source_path, 'source_sha256': source_hash,
            'import_date': legal_date(m.get('import_date'), 'import_date', False),
            'source_status': status, 'source_url': source_url or None, 'body_markdown': markdown,
            **validity(m), 'metadata': m,
        })
        doc_ids.add(ident)
    provisions = {}
    anchors = set()
    for row in tables['provisions']:
        m = row.get('metadata')
        require(isinstance(m, dict) and row['id'] == m.get('provision_id') and row.get('doc_id') == m.get('doc_id'), 'Vorschriftsmetadaten widersprechen IDs')
        require(row['doc_id'] in doc_ids, 'Vorschrift ohne Dokument')
        ident = text(row['id'], 'provision_id')
        anchor = text(m.get('anchor'), 'anchor')
        require((row['doc_id'], anchor) not in anchors, 'Mehrdeutiger Dokumentanker')
        anchors.add((row['doc_id'], anchor))
        output['provisions'].append({
            'release_id': release_id, 'provision_id': ident, 'document_id': row['doc_id'],
            'anchor': anchor, 'label': text(m.get('reference'), 'reference'),
            'heading': text(m.get('title'), 'heading'), 'body_markdown': text(row.get('markdown'), 'provision markdown'),
            'ref_key': text(row.get('ref_key'), 'ref_key'), 'ordinal': number(m.get('ordinal'), 'ordinal'),
            **validity(m), 'metadata': m,
        })
        provisions[ident] = m
    require(doc_ids == {p['document_id'] for p in output['provisions']}, 'Dokument ohne Vorschriftsblöcke')
    ordinals = Counter()
    for row in tables['chunks']:
        require(type(row.get('id')) is int and row['id'] > 0, 'Ungültige Chunk-ID')
        pid = row.get('provision_id')
        require(pid in provisions, 'Suchabschnitt ohne Vorschrift')
        vector = row.get('vector')
        require(isinstance(vector, list) and len(vector) == 384
                and all(type(x) in (int, float) and abs(x) <= 3.402823466e38 and math.isfinite(x) for x in vector), 'Ungültiger 384-dimensionaler Vektor')
        require(sum(x*x for x in vector) > 0, 'Nullvektor ist kein Embedding')
        output['search_chunks'].append({
            'release_id': release_id, 'chunk_id': str(row['id']), 'provision_id': pid,
            'document_id': provisions[pid]['doc_id'], 'ordinal': ordinals[pid],
            'body_text': text(row.get('text'), 'chunk text'), 'embedding': vector,
            'embedding_model': model, 'embedding_revision': revision,
        })
        ordinals[pid] += 1
    assets_used = set()
    associations = defaultdict(list)
    for pid, m in provisions.items():
        require(isinstance(m.get('asset_ids', []), list), 'Ungültige Asset-Verweise')
        for asset_id in m.get('asset_ids', []):
            associations[asset_id].append(pid)
    asset_ids = set()
    for row in tables['assets']:
        m = row.get('metadata')
        require(isinstance(m, dict) and row['id'] == m.get('asset_id'), 'Asset-ID widerspricht Metadaten')
        require(m.get('doc_id') in doc_ids, 'Asset ohne Dokument')
        ident = text(row['id'], 'asset_id')
        expected_hash = m.get('sha256')
        require(isinstance(expected_hash, str) and HASH.fullmatch(expected_hash), 'Asset-Prüfsumme fehlt')
        object_path = row.get('object_path')
        require(object_path == 'assets/' + expected_hash and object_path in files, 'Asset-Pfad widerspricht Content-Hash oder Manifest')
        require(files[object_path]['sha256'] == expected_hash, 'Asset-Hash widerspricht Objektbytes')
        refs = associations.get(ident, [])
        require(all(provisions[pid]['doc_id'] == m['doc_id'] for pid in refs), 'Asset wird aus einem fremden Dokument referenziert')
        output['assets'].append({
            'release_id': release_id, 'asset_id': ident, 'document_id': m['doc_id'],
            'provision_id': refs[0] if len(refs) == 1 else None,
            'relative_path': str(safe_relative(m.get('relative_path'))),
            'object_key': f'releases/{release_id}/assets/{expected_hash}',
            'sha256': expected_hash, 'mime_type': text(m.get('mime_type'), 'mime_type'),
            'byte_size': files[object_path]['size'], 'storage_bucket': 'knowledge-assets',
            'verified_at': None, 'metadata': m,
        })
        assets_used.add(object_path)
        asset_ids.add(ident)
    require(set(associations) <= asset_ids, 'Vorschrift referenziert fehlendes Asset')
    require(set(files) == required | assets_used, 'Nicht verwendete oder fremde Dateien im Exportmanifest')
    output['releases'].append({
        'release_id': release_id, 'manifest_sha256': digest(manifest_bytes),
        'embedding_model': model, 'embedding_revision': revision, 'embedding_dimensions': 384,
        'expected_documents': len(output['documents']), 'expected_provisions': len(output['provisions']),
        'expected_chunks': len(output['search_chunks']), 'expected_assets': len(output['assets']),
        'expected_embeddings': len(output['search_chunks']), 'metadata': metadata,
    })
    return base, manifest_bytes, files, assets_used, output


def normalize(source, target):
    target = Path(target).absolute()
    require(not target.exists(), 'Ziel existiert bereits; neuen Ordner verwenden')
    base, source_manifest, files, assets, rows = prepare(source)
    require(not target.resolve().is_relative_to(base), 'Ausgabe darf nicht im unveränderlichen Quellexport liegen')
    target.mkdir(parents=True, exist_ok=False)
    manifest = {'format': SCHEMA_VERSION, 'release_id': rows['releases'][0]['release_id'],
                'source_manifest_sha256': digest(source_manifest), 'files': [],
                'cloud_uploaded': False, 'assets_verified_in_cloud': False,
                'note': 'Lokale Vorbereitung; keine Verbindung, kein Upload, keine Aktivierung.'}

    def write(relative, content):
        path = target.joinpath(*safe_relative(relative).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        manifest['files'].append({'path': relative, 'sha256': digest(content), 'size': len(content)})

    for table, records in rows.items():
        write(table + '.jsonl', b''.join(encode(r) + b'\n' for r in records))
    write('source_manifest.json', source_manifest)
    for name in sorted(assets):
        source_path = inside(base, name)
        content = source_path.read_bytes()
        require((digest(content), len(content)) == (files[name]['sha256'], files[name]['size']), 'Asset während Vorbereitung geändert')
        write(name, content)
    require(inside(base, 'manifest.json').read_bytes() == source_manifest, 'Quellmanifest während Vorbereitung geändert')
    # JSONL-Dateien nochmals überprüfen, bevor der Abschlussmarker erscheint.
    for name, item in files.items():
        require(hash_file(inside(base, name)) == (item['sha256'], item['size']), 'Quellexport während Vorbereitung geändert')
    (target / 'manifest.json').write_bytes(encode(manifest) + b'\n')
    return {'target': str(target.resolve()), 'release_id': manifest['release_id'],
            'documents': len(rows['documents']), 'provisions': len(rows['provisions']),
            'chunks': len(rows['search_chunks']), 'assets': len(rows['assets']), 'cloud_uploaded': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export_directory', type=Path)
    parser.add_argument('new_target_directory', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(normalize(args.export_directory, args.new_target_directory), ensure_ascii=False, indent=2))
    except (ExportError, KeyError, ValueError, OSError) as error:
        raise SystemExit(f'Vorbereitung abgebrochen: {error}') from None
