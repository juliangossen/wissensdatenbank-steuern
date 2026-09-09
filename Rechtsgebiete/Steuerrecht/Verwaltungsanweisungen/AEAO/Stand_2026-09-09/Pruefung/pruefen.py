"""Unabhängiger lesender Rückvergleich der gespeicherten AEAO-Markdown-Datei.

Liest ausschließlich die abgelegten Dateien: Quellkopie, Markdown, Quellblockliste,
Vollständigkeitsprüfung und amtlichen Abgleich. Es wird nichts geschrieben.
"""
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
FIRST, LAST = 86, 18403


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
    source = BASE / 'Quellen/AEAO_Webkopie.txt'
    markdown = BASE / 'AEAO.md'
    assert proof['pruefung_erfolgreich'] is True
    assert sha(source) == proof['sha256_original_quelle']
    assert sha(markdown) == proof['sha256_markdown']
    lines = source.read_text(encoding='utf-8-sig').splitlines()
    assert len(lines) == proof['quellzeilen_gesamt']
    content = markdown.read_text(encoding='utf-8')
    found = list(re.finditer(r'<!-- quelle:([^ ]+) -->\n(.*?)\n<!-- /quelle:\1 -->', content, re.S))
    assert len(found) == len({match[1] for match in found})
    blocks = {match[1]: match[2] for match in found}
    coverage = Counter()
    for record in records:
        assert record['datei'] == 'AEAO.md'
        body = blocks.pop(record['id'])
        expected = canon('\n'.join(lines[record['zeile_von'] - 1:record['zeile_bis']]))
        parser = Parsed()
        parser.feed(MD.render(body))
        assert canon(''.join(parser.text)) == expected, record['id']
        assert hashlib.sha256(expected.encode('utf-8')).hexdigest() == record['sha256_sichtbarer_quelltext']
        for index in range(record['zeile_von'] - 1, record['zeile_bis']):
            if lines[index].strip():
                coverage[index] += 1
    assert not blocks, 'Quellblöcke ohne Registrierung.'
    assert coverage == Counter({i: 1 for i in range(FIRST, LAST + 1) if lines[i].strip()})
    assert len(records) == proof['quellbloecke'] and len(coverage) == proof['quellzeilen_sachinhalt_nichtleer']

    parser = Parsed()
    parser.feed(MD.render(content))
    assert len(parser.ids) == len(set(parser.ids)), 'Doppelte Sprungmarken.'
    ids = set(parser.ids)
    links = 0
    for link in parser.links:
        value = urlsplit(link)
        if value.scheme or value.netloc:
            continue
        target = (markdown.parent / unquote(value.path)).resolve() if value.path else markdown
        assert target.exists(), link
        if value.fragment and target == markdown:
            assert unquote(value.fragment) in ids, link
        links += 1
    footnotes = [i for i in parser.ids if i.startswith('fn-z')]
    assert len(footnotes) == proof['fussnoten'] == len(re.findall(r'href="#fn-z\d+"', content))
    assert sum(1 for i in ids if i.startswith('aeao-') and '-nr-' not in i) == proof['gliederungspositionen']
    assert {'anlage-1', 'anlage-2', 'anlage-3', 'inhaltsuebersicht', 'erlasstext', 'anlagen'} <= ids
    assert sum(1 for i in ids if '-nr-' in i) == proof['sprungmarken_nummerierte_punkte']

    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    for item in online['dateien']:
        path = BASE / item['datei']
        assert path.is_file() and sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], item['datei']
    assert online['abschnitte_stimmen_ueberein'] is True
    print(f'OK: {len(records)} Quellblöcke, {len(coverage)} Sachtextzeilen, {len(footnotes)} Fußnoten, '
          f'{links} lokale Links und {len(online["dateien"])} Abgleichdateien geprüft.')


if __name__ == '__main__':
    main()
