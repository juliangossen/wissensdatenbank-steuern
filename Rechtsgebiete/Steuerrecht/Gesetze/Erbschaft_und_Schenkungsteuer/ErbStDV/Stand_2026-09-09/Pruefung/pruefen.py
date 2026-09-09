"""Unabhängiger lesender Rückvergleich der gespeicherten ErbStDV-Markdown-Datei.

Liest ausschließlich die abgelegten Dateien: Quellkopie, Archivkopie, Markdown, Quellblockliste,
Vollständigkeitsprüfung, amtlichen Abgleich und Wortlautabgleich. Es wird nichts geschrieben.
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
ROOT = next(path for path in BASE.parents if (path / 'Bestand.json').is_file())
ARCHIVE_COPY = ROOT / 'Web_Archiv/02_In_Markdown_umgewandelt/Stand_2026-09-09/Steuerrecht/Gesetze/Erbschaft_und_Schenkungsteuer/ErbStDV/ErbStDV.txt'
MD = MarkdownIt('commonmark', {'html': True}).enable('table')
FIRST, LAST = 1, 1112


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
    source = BASE / 'Quellen/ErbStDV_Webkopie.txt'
    markdown = BASE / 'ErbStDV.md'
    assert proof['pruefung_erfolgreich'] is True
    assert sha(source) == proof['sha256_original_quelle'] == 'dbb708bb0865ed7a3edd3de4a141eb4d6af7cef9f2cd14a7f22fc493de3c7c08'
    assert ARCHIVE_COPY.is_file() and ARCHIVE_COPY.read_bytes() == source.read_bytes(), 'Archivkopie weicht ab.'
    assert sha(markdown) == proof['sha256_markdown']
    raw = source.read_bytes()
    lines = raw.decode('utf-8').splitlines()
    assert len(lines) == proof['quellzeilen_gesamt'] == 1113 and not raw.endswith(b'\n')
    content = markdown.read_text(encoding='utf-8')
    found = list(re.finditer(r'<!-- quelle:([^ ]+) -->\n(.*?)\n<!-- /quelle:\1 -->', content, re.S))
    assert len(found) == len({match[1] for match in found})
    blocks = {match[1]: match[2] for match in found}
    coverage = Counter()
    kinds = Counter()
    for record in records:
        assert record['datei'] == 'ErbStDV.md'
        body = blocks.pop(record['id'])
        expected = canon('\n'.join(lines[record['zeile_von'] - 1:record['zeile_bis']]))
        parser = Parsed()
        parser.feed(MD.render(body))
        assert canon(''.join(parser.text)) == expected, record['id']
        assert hashlib.sha256(expected.encode('utf-8')).hexdigest() == record['sha256_sichtbarer_quelltext']
        for index in range(record['zeile_von'] - 1, record['zeile_bis']):
            if lines[index].strip():
                coverage[index] += 1
        kinds[record['art']] += 1
    assert not blocks, 'Quellblöcke ohne Registrierung.'
    assert coverage == Counter({i: 1 for i in range(FIRST, LAST + 1) if lines[i].strip()})
    assert len(records) == proof['quellbloecke'] and len(coverage) == proof['quellzeilen_sachinhalt_nichtleer']
    assert kinds['paragraph'] == proof['gliederungspositionen'] == 13
    assert kinds['gliederungsgruppe'] == proof['gliederungsgruppen'] == 3
    assert kinds['anlage'] == proof['anlagen'] == 6
    assert kinds['absatz'] == proof['absaetze'] and kinds['aufzaehlung'] == proof['aufzaehlungen']
    assert kinds['formularblock'] == proof['formularbloecke'] and kinds['formulartitel'] == proof['formulartitel']
    assert kinds['fussnote'] == proof['fussnoten'] == 40
    assert content.count('<sup>') == proof['satznummern']
    assert sum(1 for line in lines if line.startswith('(') and re.match(r'^\(\d+\)', line)) == proof['absaetze']

    parser = Parsed()
    parser.feed(MD.render(content))
    assert len(parser.ids) == len(set(parser.ids)), 'Doppelte Sprungmarken.'
    ids = set(parser.ids)
    assert len(ids) == proof['sprungmarken']
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
    assert {f'par-{n}' for n in range(1, 14)} <= ids
    assert {f'muster-{n}' for n in range(1, 7)} <= ids
    assert {'zu-33-erbstg', 'zu-34-erbstg', 'schlussvorschriften', 'inhaltsuebersicht', 'verordnungstext', 'muster'} <= ids
    assert sum(1 for i in ids if '-abs-' in i and '-nr-' not in i) == proof['absaetze']
    assert sum(1 for i in ids if '-nr-' in i) == proof['aufzaehlungspunkte'] == 40

    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    for item in online['dateien']:
        path = BASE / item['datei']
        assert path.is_file() and sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], item['datei']
    assert online['stand_stimmt_ueberein'] is True and online['wortlautabgleich_durchgefuehrt'] is True
    comparison = json.loads((BASE / 'Quellen/Onlineabgleich/Wortlautabgleich.json').read_text(encoding='utf-8'))
    assert comparison['webkopie']['sha256'] == proof['sha256_original_quelle']
    assert comparison['amtliche_xml']['sha256'] == sha(BASE / 'Quellen/Onlineabgleich/BJNR265800998.xml')
    assert comparison['rahmen']['stand_stimmt_ueberein'] is True
    assert comparison['ergebnis']['paragraphen_gesamt'] == 13
    assert comparison['ergebnis']['text_abweichend'] == online['paragraphen_mit_abweichungen']
    print(f'OK: {len(records)} Quellblöcke, {len(coverage)} Sachtextzeilen, {len(footnotes)} Fußnoten, '
          f'{len(ids)} Sprungmarken, {links} lokale Links und {len(online["dateien"])} Abgleichdateien geprüft; '
          f'Wortlautabgleich: {len(comparison["ergebnis"]["text_identisch"])} von 13 Paragraphen zeichenidentisch.')


if __name__ == '__main__':
    main()
