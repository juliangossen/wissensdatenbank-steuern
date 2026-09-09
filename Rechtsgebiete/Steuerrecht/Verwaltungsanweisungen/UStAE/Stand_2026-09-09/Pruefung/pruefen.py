"""Unabhängiger lesender Rückvergleich der gespeicherten UStAE-Markdown-Dateien."""
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from markdown_it import MarkdownIt

BASE = Path(__file__).resolve().parent.parent
MD = MarkdownIt('commonmark', {'html': True}).enable('table')


class Parsed(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text, self.ids, self.links = [], [], []

    def handle_data(self, data):
        self.text.append(data)

    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key == 'id':
                self.ids.append(value)
            if key in ('href', 'src'):
                self.links.append(value)


def canon(text):
    return re.sub(r'\s+', '', text)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proof = json.loads((BASE / 'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    records = json.loads((BASE / 'Pruefung/Quellbloecke.json').read_text(encoding='utf-8'))
    source = BASE / 'Quellen/UStAE_Webkopie.txt'
    assert sha(source) == proof['sha256_original_quelle']
    assert sha(BASE / 'UStAE.md') == proof['sha256_markdown']
    assert sha(BASE / 'Ergaenzungen/Beck_Synopse_UStR_2008_UStAE.md') == proof['sha256_redaktionelle_synopse']
    lines = source.read_text(encoding='utf-8-sig').splitlines()
    texts = {file: (BASE / file).read_text(encoding='utf-8') for file in {record['datei'] for record in records}}
    blocks = {}
    for file, content in texts.items():
        found = list(re.finditer(r'<!-- quelle:([^ ]+) -->\n(.*?)\n<!-- /quelle:\1 -->', content, re.S))
        assert len(found) == len({match[1] for match in found}), file
        blocks[file] = {match[1]: match[2] for match in found}
    coverage = Counter()
    for record in records:
        body = blocks[record['datei']].pop(record['id'])
        expected = canon('\n'.join(lines[record['zeile_von'] - 1:record['zeile_bis']]))
        parser = Parsed()
        parser.feed(MD.render(body))
        assert canon(''.join(parser.text)) == expected, record['id']
        assert hashlib.sha256(expected.encode('utf-8')).hexdigest() == record['sha256_sichtbarer_quelltext']
        for index in range(record['zeile_von'] - 1, record['zeile_bis']):
            if lines[index].strip():
                coverage[index] += 1
    assert all(not value for value in blocks.values())
    assert coverage == Counter({i: 1 for i in range(292, len(lines)) if lines[i].strip()})
    parsed = {}
    for file, content in texts.items():
        parser = Parsed()
        parser.feed(MD.render(content))
        assert len(parser.ids) == len(set(parser.ids)), file
        parsed[(BASE / file).resolve()] = parser
    links = 0
    for file, parser in parsed.items():
        for link in parser.links:
            value = urlsplit(link)
            if value.scheme or value.netloc:
                continue
            target = (file.parent / unquote(value.path)).resolve() if value.path else file
            assert target.exists(), (file.name, link)
            if value.fragment and target in parsed:
                assert unquote(value.fragment) in parsed[target].ids, (file.name, link)
            links += 1
    anchors = parsed[(BASE / 'UStAE.md').resolve()].ids
    assert len([v for parser in parsed.values() for v in parser.ids if v.startswith('fn-z')]) == 829
    assert all('abschnitt-' + num in anchors for num in ['23-1', '23-2', '23-3', '23-4', '25d-1'])
    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    assert sha(BASE / online['pdf_datei']) == online['pdf_sha256']
    for image in online['abbildungen']:
        assert sha(BASE / image['datei']) == image['sha256']
    print(f'OK: {len(records)} Quellblöcke, {len(coverage)} Sachtextzeilen, 829 Fußnoten, {links} lokale Links und {len(online["abbildungen"])} Abbildungen geprüft.')


if __name__ == '__main__':
    main()
