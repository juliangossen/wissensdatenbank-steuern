"""Lesende Integritätsprüfung der strukturierten EStR-/EStH-Webkopie."""
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

    def handle_data(self, value):
        self.text.append(value)

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == 'id':
                self.ids.append(value)
            elif key in ('href', 'src'):
                self.links.append(value)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canon(value):
    return re.sub(r'\s+', '', value)


def main():
    source = BASE / 'Quellen/EStR_2012_Webkopie.txt'
    target = BASE / 'EStR_2012.md'
    proof = json.loads((BASE / 'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    records = json.loads((BASE / 'Pruefung/Quellbloecke.json').read_text(encoding='utf-8'))
    assert proof['pruefung_erfolgreich'] is True
    assert sha(source) == proof['sha256_original_quelle']
    assert sha(target) == proof['sha256_markdown']
    lines = source.read_text(encoding='utf-8-sig').splitlines()
    text = target.read_text(encoding='utf-8')
    matches = list(re.finditer(r'<!-- quelle:([^ ]+) -->\n(.*?)\n<!-- /quelle:\1 -->', text, re.S))
    blocks = {match[1]: match[2] for match in matches}
    assert len(matches) == len(blocks) == len(records)
    coverage = Counter()
    for record in records:
        body = blocks.pop(record['id'])
        expected = canon('\n'.join(lines[record['zeile_von'] - 1:record['zeile_bis']]))
        parser = Parsed()
        parser.feed(MD.render(body))
        assert canon(''.join(parser.text)) == expected, record['id']
        assert hashlib.sha256(expected.encode('utf-8')).hexdigest() == record['sha256_sichtbarer_quelltext']
        for index in range(record['zeile_von'] - 1, record['zeile_bis']):
            if lines[index].strip():
                coverage[index] += 1
    assert not blocks
    assert coverage == Counter({i: 1 for i in range(32, len(lines)) if lines[i].strip()})
    parser = Parsed()
    parser.feed(MD.render(text))
    assert len(parser.ids) == len(set(parser.ids)), 'Doppelte Anker'
    assert sum(value.startswith('fn-z') for value in parser.ids) == 507
    footnote_refs = [urlsplit(value).fragment for value in parser.links if value.startswith('#fn-z')]
    assert Counter(footnote_refs) == Counter({value: 1 for value in parser.ids if value.startswith('fn-z')})
    assert sum(value.startswith('rh-z') and '-abs-' not in value for value in parser.ids) == 646
    assert sum(value.startswith('gruppe-z') for value in parser.ids) == 118
    assert all(f'anlage-{i}' in parser.ids for i in range(1, 7))
    for value in parser.links:
        link = urlsplit(value)
        if link.scheme or link.netloc:
            continue
        path = BASE / unquote(link.path) if link.path else target
        assert path.is_file(), value
        if path == target and link.fragment:
            assert unquote(link.fragment) in parser.ids, value
    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    for image in online.get('abbildungen', []):
        assert sha(BASE / image['datei']) == image['sha256'], image['datei']
    for item in online.get('quellen', []):
        if item.get('datei') and item.get('sha256'):
            assert sha(BASE / item['datei']) == item['sha256'], item['datei']
    for item in online.get('ergaenzungen', []):
        assert sha(BASE / item['datei']) == item['sha256'], item['datei']
        assert sha(BASE / item['quelle_datei']) == item['quelle_sha256'], item['quelle_datei']
    print(f'OK: {len(records)} Quellblöcke, {len(coverage)} Sachtextzeilen, 646 R/H-Blöcke, 507 Fußnoten, {len(online.get("abbildungen", []))} Formularabbildungen und alle Hauptdokument-Links geprüft.')


if __name__ == '__main__':
    main()
