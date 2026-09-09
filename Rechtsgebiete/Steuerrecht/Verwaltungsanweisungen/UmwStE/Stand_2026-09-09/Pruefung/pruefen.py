"""Unabhängiger lesender Rückvergleich der gespeicherten UmwStE-2025-Markdown-Datei.

Liest ausschließlich die abgelegten Dateien: Quellkopie, Markdown, Quellblockliste,
Vollständigkeitsprüfung, Fußnotenzuordnung und amtlichen Abgleich. Es wird nichts geschrieben.
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
TITLE, BODY, LAST, END = 2, 1353, 7495, 7777
RN = re.compile(r'^(?!31\.12)((?:\d{2}|E \d{2}|Org|K|S)\.\d{2}[a-z]?(?: bis 27\.11)?)')


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
    assignments = json.loads((BASE / 'Pruefung/Fussnotenzuordnung.json').read_text(encoding='utf-8'))
    source = BASE / 'Quellen/UmwStE_2025_Webkopie.txt'
    markdown = BASE / 'UmwStE_2025.md'
    assert proof['pruefung_erfolgreich'] is True
    assert sha(source) == proof['sha256_original_quelle']
    assert sha(markdown) == proof['sha256_markdown']
    lines = source.read_text(encoding='utf-8').splitlines()
    assert len(lines) == proof['quellzeilen_gesamt'] == END + 1
    content = markdown.read_text(encoding='utf-8')
    found = list(re.finditer(r'<!-- quelle:([^ ]+) -->\n(.*?)\n<!-- /quelle:\1 -->', content, re.S))
    assert len(found) == len({match[1] for match in found})
    blocks = {match[1]: match[2] for match in found}
    coverage = Counter()
    for record in records:
        assert record['datei'] == 'UmwStE_2025.md'
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
    assert coverage == Counter({i: 1 for i in range(TITLE, END + 1) if lines[i].strip()})
    assert len(records) == proof['quellbloecke'] and len(coverage) == proof['quellzeilen_sachinhalt_nichtleer']
    kinds = Counter(record['art'] for record in records)
    assert kinds['randnummer'] == proof['randnummern'] == 572
    assert kinds['fussnote'] == proof['fussnoten'] == 94
    assert kinds['kurze_quellzeilen'] == proof['kurze_quellzeilenbloecke']
    assert kinds['aufzaehlung'] == proof['aufzaehlungen']
    assert kinds['beispiel_ueberschrift'] == proof['beispiel_ueberschriften']
    assert kinds['zwischenueberschrift_strich'] + kinds['zwischentitel'] == proof['zwischenueberschriften']
    assert kinds['inhaltsverzeichnis_tabelle'] == 1 and kinds['einleitung'] == 1

    # Randnummern der Kopie unabhängig zählen; jede Rn-Zeile ist ein eigener Block „randnummer“.
    rn_lines = {}
    current = None
    rn_of = {}
    for index in range(len(lines)):
        match = RN.match(lines[index]) if BODY <= index <= LAST else None
        if match:
            assert match[1] not in rn_lines
            rn_lines[match[1]] = index
            current = match[1]
        rn_of[index + 1] = current
    assert len(rn_lines) == proof['randnummern']
    rn_blocks = {record['zeile_von'] - 1 for record in records if record['art'] == 'randnummer'}
    assert rn_blocks == set(rn_lines.values())

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
    # Jede Fußnote wird genau einmal aus der Zuordnungstabelle verlinkt; im Text gibt es keine Verweise.
    assert len(footnotes) == proof['fussnoten'] == len(re.findall(r'\]\(#fn-z\d+\)', content))
    assert not re.search(r'href="#fn-z', content)
    assert sum(1 for i in ids if i.startswith('rn-')) == proof['sprungmarken_randnummern'] == 574
    assert sum(1 for i in ids if i.startswith('gliederung-z')) == proof['gliederungspositionen'] == 338
    assert {'dokumentkopf', 'einleitung', 'inhaltsverzeichnis', 'erlasstext', 'fussnoten', 'rn-00-01', 'rn-k-19', 'rn-e-20-01', 'rn-27-11'} <= ids
    assert content.count('<sup>') == proof['satznummern'] == 0

    # Fußnotenzuordnung: 94 Einträge, Bezugszeilen vorhanden und in der angegebenen Randnummer.
    assert [item['fussnote'] for item in assignments] == list(range(1, 95))
    assert Counter(item['status'] for item in assignments) == Counter(proof['fussnoten_zuordnung'])
    for item in assignments:
        assert f'fn-z{item["definition_zeile"]}' in ids
        assert lines[item['definition_zeile'] - 1] == f'[{item["fussnote"]}] '
        if item['zeile'] is not None:
            assert lines[item['zeile'] - 1].strip(), item['fussnote']
            if item['zeile'] > BODY:
                assert rn_of[item['zeile']] == item['randnummer'], item['fussnote']
    assert sum(1 for item in assignments if item['text'].startswith('[Amtl. Anm.:]')) == proof['fussnoten_arten']['amtliche Anmerkung']

    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    for item in online['dateien']:
        path = BASE / item['datei']
        assert path.is_file() and sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], item['datei']
    for image in online['abbildungen']:
        path = BASE / image['datei']
        assert path.is_file() and sha(path) == image['sha256'] and path.stat().st_size == image['bytes'], image['datei']
        assert f']({image["datei"]})' in content, image['datei']
    assert len(online['abbildungen']) == 3 and proof['ergaenzte_seitendarstellungen'] == 5
    assert online['randnummern']['kopie'] == proof['randnummern'] == online['randnummern']['pdf_randmarken']
    assert online['randnummern']['fehlen_in_pdf'] == [] and online['randnummern']['fehlen_in_kopie'] == []
    assert online['randnummern']['gleiche_reihenfolge'] is True
    details = json.loads((BASE / 'Quellen/Onlineabgleich/Randnummernabgleich.json').read_text(encoding='utf-8'))
    assert [item['rn'] for item in details] == list(rn_lines)
    classes = Counter(item['klasse'] for item in details)
    assert sum(online['wortlautvergleich']['klassen'].values()) == len(details) == 572
    assert all(classes[key.split(' ')[0]] == value for key, value in online['wortlautvergleich']['klassen'].items())
    assert online['aenderungsschreiben_2025_08_01']['rn_org_03_aehnlichkeit_neufassung'] >= 0.99
    assert online['aenderungsschreiben_2025_08_01']['rn_15_35a_aehnlichkeit_neufassung'] >= 0.99
    print(f'OK: {len(records)} Quellblöcke, {len(coverage)} Sachtextzeilen, {len(rn_lines)} Randnummern, {len(footnotes)} Fußnoten, '
          f'{links} lokale Links und {len(online["dateien"])} Abgleichdateien geprüft.')


if __name__ == '__main__':
    main()
