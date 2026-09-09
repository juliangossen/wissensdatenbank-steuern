"""Unabhängiger lesender Rückvergleich der gespeicherten ErbStR-2019-Markdown-Datei.

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
FIRST, LAST = 33, 33483
SECTION_ID = re.compile(r'^(?:r-[eb]-\d+[a-z]?(?:-\d+)?|h-[eb]-\d+[a-z]?(?:-\d+)?(?:-abs-\d+)?)$')


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
    source = BASE / 'Quellen/ErbStR_2019_Webkopie.txt'
    markdown = BASE / 'ErbStR_2019.md'
    assert proof['pruefung_erfolgreich'] is True
    assert sha(source) == proof['sha256_original_quelle']
    assert sha(markdown) == proof['sha256_markdown']
    raw = source.read_bytes()
    assert raw[:3] != b'\xef\xbb\xbf' and b'\r\n' in raw
    lines = raw.decode('utf-8').splitlines()
    assert len(lines) == proof['quellzeilen_gesamt']
    content = markdown.read_text(encoding='utf-8')
    assert not content.startswith('---'), 'Kein YAML-Frontmatter erwartet.'
    found = list(re.finditer(r'<!-- quelle:([^ ]+) -->\n(.*?)\n<!-- /quelle:\1 -->', content, re.S))
    assert len(found) == len({match[1] for match in found})
    blocks = {match[1]: match[2] for match in found}
    coverage = Counter()
    for record in records:
        assert record['datei'] == 'ErbStR_2019.md'
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
    assert all(not lines[i].strip() for i in range(LAST + 1, len(lines)))

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
    assert Counter(re.findall(r'href="#(fn-z\d+)"', content)) == Counter({i: 1 for i in footnotes}), 'Fußnoten nicht bijektiv.'
    assert all(int(i[4:]) - 1 in range(FIRST, LAST + 1) and re.fullmatch(r'\[\d+\]\s*', lines[int(i[4:]) - 1]) for i in footnotes)
    sections = [i for i in ids if SECTION_ID.match(i)]
    assert len(sections) == proof['gliederungspositionen'], len(sections)
    assert sum(1 for i in ids if i.startswith('zu-')) == proof['paragraphengruppen']
    assert {'teil-i', 'teil-ii', 'teil-iii', 'teil-iii-a', 'teil-iii-b', 'teil-iii-c', 'teil-iii-d', 'teil-iii-e', 'teil-iii-f',
            'anlage-1', 'anlage-2', 'inhaltsuebersicht', 'erlasstext', 'anlagen', 'einfuehrung-abs-1'} <= ids
    assert sum(1 for i in ids if '-nr-' in i or '-bst-' in i) == proof['sprungmarken_nummerierte_punkte']
    assert sum(1 for i in ids if '-beispiel' in i) == proof['sprungmarken_beispiele']
    headings = Counter(len(m[1]) for m in re.finditer(r'^(#{1,6}) ', content, re.M))
    assert headings[5] == proof['gliederungspositionen'] and headings[4] == proof['paragraphengruppen']
    assert headings[6] == proof['beispiele'] and headings[3] == proof['teilueberschriften_bewg']
    assert content.count('<table>') == proof['tabellen'] == 8
    assert 'zum Seitenanfang' not in content and 'beck-online' not in content.split('<!-- quelle:')[1]

    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    for item in online['dateien']:
        path = BASE / item['datei']
        assert path.is_file() and sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], item['datei']
    assert online['strukturvergleich']['richtlinien_ueberschriften_im_amtlichen_text_gefunden'] == online['strukturvergleich']['richtlinien_ueberschriften_kopie']
    assert online['strukturvergleich']['hinweis_ueberschriften_im_amtlichen_text_gefunden'] == online['strukturvergleich']['hinweis_ueberschriften_kopie']
    assert online['strukturvergleich']['gliederung_stimmt_ueberein'] is True
    assert online['textvergleich']['durchgefuehrt'] is True
    print(f'OK: {len(records)} Quellblöcke, {len(coverage)} Sachtextzeilen, {len(sections)} R-/H-Blöcke, {len(footnotes)} Fußnoten, '
          f'{links} lokale Links und {len(online["dateien"])} Abgleichdateien geprüft.')


if __name__ == '__main__':
    main()
