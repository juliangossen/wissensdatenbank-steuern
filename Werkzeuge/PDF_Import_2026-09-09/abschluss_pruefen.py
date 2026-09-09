"""Lesende Abschlussprüfung der registrierten neuen PDF-Dokumente und Links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
from markdown_it import MarkdownIt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MD = MarkdownIt('commonmark', {'html': True}).enable('table')


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == 'id':
                self.ids.append(value)
            elif key in {'href', 'src'}:
                self.links.append(value)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    imported = json.loads((HERE / 'Importabschluss.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / 'Bestand.json').read_text(encoding='utf-8'))
    by_md = {entry['markdown']: entry for entry in inventory['eintraege']}
    parsed = {}
    linked = 0

    def parse(path):
        if path not in parsed:
            source = path.read_text(encoding='utf-8')
            result = Links()
            result.feed(MD.render(source))
            assert len(result.ids) == len(set(result.ids)), f'Doppelte Anker: {path}'
            parsed[path] = result
        return parsed[path]

    documents = []
    for entry in imported['eintraege']:
        pdf = ROOT / entry['pdf']
        md = ROOT / entry['markdown']
        assert sha(pdf) == entry['sha256_pdf']
        assert sha(md) == entry['sha256_markdown']
        assert by_md[entry['markdown']]['sha256_markdown'] == sha(md)
        assert by_md[entry['markdown']]['original_pdf'] == entry['pdf']
        assert by_md[entry['markdown']]['sha256_original_pdf'] == sha(pdf)
        assert by_md[entry['markdown']]['pdf_seiten'] == entry['pdf_seiten']
        for path in [md, md.parent / 'README.md', md.parent.parent / 'README.md', ROOT / entry['pruefbericht']]:
            assert path.is_file(), path
            result = parse(path)
            for value in result.links:
                link = urlsplit(value)
                if link.scheme or link.netloc:
                    continue
                target = (path.parent / unquote(link.path)).resolve() if link.path else path.resolve()
                assert target.is_relative_to(ROOT), f'Link außerhalb der Datenbank: {path}: {value}'
                assert target.exists(), f'Linkziel fehlt: {path}: {value}'
                if link.fragment and target.suffix.lower() == '.md':
                    assert unquote(link.fragment) in parse(target).ids, f'Anker fehlt: {path}: {value}'
                linked += 1
        documents.append({'kuerzel': entry['kuerzel'], 'pdf_seiten': entry['pdf_seiten'],
                          'pdf_unveraendert': True, 'markdown_unveraendert': True,
                          'im_bestand_registriert': True, 'lokale_links_gueltig': True})
    output = {'pruefung_erfolgreich': True, 'neue_dokumente': len(documents),
              'neue_pdf_seiten': sum(d['pdf_seiten'] for d in documents),
              'gepruefte_lokale_links': linked, 'bestand_dokumente': inventory['dokumente'],
              'unbearbeitete_pdfs': inventory['unbearbeitete_pdfs'], 'dokumente': documents}
    (HERE / 'Abschlusspruefung.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in output.items() if k != 'dokumente'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
