"""Reproduzierbare, verlustfrei geprüfte UStG-Konvertierung aus dem GII-XML.

Aufruf: py konvertieren.py
Benötigt für den Rückvergleich: markdown-it-py (GFM-Tabellenerweiterung).
Die archivierte XML-Datei wird gelesen; es erfolgen keine Netzwerkzugriffe.
"""
from pathlib import Path
import hashlib
from html.parser import HTMLParser
import json
import re
import xml.etree.ElementTree as ET

from markdown_it import MarkdownIt

BASE = Path(__file__).resolve().parent.parent
XML = BASE / 'Quellen/XML/BJNR119530979.xml'
ROOT = ET.parse(XML).getroot()
PARSER = MarkdownIt('commonmark', {'html': True}).enable('table')
SYNTHETIC_HEADERS = {'AbschnittVorschriftInhalt', 'RechenzeichenRechengröße'}


def norm(s):
    return re.sub(r'\s+', '', s)


def tidy(s):
    return re.sub(r'\s+', ' ', s).strip()


def source_text(el):
    return ''.join(el.itertext()) if el is not None else ''


def md_text(s):
    s = re.sub(r'\s+', ' ', s or '')
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    s = re.sub(r'([\\`*_\[\]|])', r'\\\1', s)
    return re.sub(r'-{3,}', lambda m: m.group().replace('-', '\\-'), s)


def mixed(el, cell=False):
    out = md_text(el.text)
    for child in el:
        out += render(child, cell)
        out += md_text(child.tail)
    return out


def dl(el, cell=False):
    children = list(el)
    assert len(children) % 2 == 0
    items = []
    for i in range(0, len(children), 2):
        dt, dd = children[i:i + 2]
        assert dt.tag == 'DT' and dd.tag == 'DD'
        prefix = '**' + mixed(dt, cell).strip() + '** '
        body = mixed(dd, cell).strip()
        if cell:
            items.append(prefix + body)
        else:
            lines = (prefix.rstrip() + '\n\n' + body if body.startswith('- ') else prefix + body).splitlines()
            items.append('- ' + lines[0] + ''.join('\n  ' + s if s else '\n' for s in lines[1:]))
    if cell:
        return '<br>' + '<br>'.join(items) + '<br>'
    return '\n\n' + '\n\n'.join(items) + '\n\n'


def cell_text(el):
    return re.sub(r'(?:<br>\s*)+$', '', re.sub(r'^(?:\s*<br>)+', '', mixed(el, True).strip()))


def anchor(enbez):
    enbez = tidy(enbez)
    if enbez.startswith('§'):
        return 'ustg-' + enbez.replace('§', '').strip()
    if enbez.startswith('Anlage'):
        return 'anlage-' + re.search(r'\d+', enbez).group()
    return 'inhaltsuebersicht'


def table(el):
    group = el.find('tgroup')
    cols = int(group.get('cols'))
    colnames = {x.get('colname'): i for i, x in enumerate(group.findall('colspec'))}
    rows = list(group.findall('thead/row')) + list(group.findall('tbody/row'))
    spans = {}
    grid = []
    for ri, row in enumerate(rows):
        cells = [''] * cols
        used = {i for i, last in spans.items() if last >= ri}
        pos = 0
        for entry in row.findall('entry'):
            if entry.get('namest'):
                pos = colnames[entry.get('namest')]
            elif entry.get('colname'):
                pos = colnames[entry.get('colname')]
            else:
                while pos in used:
                    pos += 1
            assert pos < cols
            end = colnames[entry.get('nameend')] if entry.get('nameend') else pos
            cells[pos] = cell_text(entry)
            for ci in range(pos, end + 1):
                used.add(ci)
                if entry.get('morerows'):
                    spans[ci] = ri + int(entry.get('morerows'))
            pos = end + 1
        grid.append(cells)
    is_toc = el is TOC_TABLE
    if is_toc:
        for row in grid:
            first_plain = row[0].replace('**', '')
            if re.fullmatch(r'[IVX]+\.', first_plain):
                row[2], row[1] = row[1], ''
            elif first_plain.startswith('Anlage '):
                annex = re.match(r'(Anlage\s+\d+)\s*(.*)', first_plain)
                row[:] = ['', '**' + annex.group(1) + '**', annex.group(2)]
            elif not row[0] and row[1] and not row[2]:
                row[2], row[1] = row[1], ''
            for ci, value in enumerate(row):
                plain = re.sub(r'\*\*', '', value)
                match = re.match(r'^(§\s*\d+[a-z]?|Anlage\s+\d+)(?=\s|$)', plain)
                if match:
                    row[ci] = '[' + value + '](#' + anchor(match.group()) + ')'
                roman = re.fullmatch(r'\*\*([IVX]+)\.\*\*', value)
                if roman:
                    row[ci] = '[' + value + '](#abschnitt-' + str(ROMANS.index(roman.group(1)) + 1) + ')'
        header = ['Abschnitt', 'Vorschrift', 'Inhalt']
    elif cols == 2:
        header = ['Rechenzeichen', 'Rechengröße']
    else:
        header = grid.pop(0)
    return '\n\n' + '\n'.join([
        '| ' + ' | '.join(header) + ' |',
        '| ' + ' | '.join(['---'] * cols) + ' |',
        *['| ' + ' | '.join(row) + ' |' for row in grid],
    ]) + '\n\n'


def render(el, cell=False):
    tag = el.tag
    if tag == 'BR':
        return '<br>' if cell else '  \n'
    if tag == 'DL':
        return dl(el, cell)
    if tag == 'table':
        assert not cell
        return table(el)
    if tag == 'pre':
        def raw(node):
            return (node.text or '') + ''.join(('\n' if c.tag == 'BR' else raw(c)) + (c.tail or '') for c in node)
        return '\n\n```text\n' + raw(el).strip('\n') + '\n```\n\n'
    if tag == 'B':
        return '**' + mixed(el, cell).strip() + '**'
    if tag == 'P':
        content = mixed(el, cell).strip()
        if not content:
            return ''
        if content in {'-', '+', '='}:
            content = '\\' + content
        content = re.sub(r'^\((\d+[a-z]?)\)', r'**(\1)**', content)
        return content + ('<br>' if cell else '\n\n')
    if tag == 'LA':
        return mixed(el, cell) + ('<br>' if cell else '\n\n')
    if tag in {'Content', 'DD', 'DT', 'NB', 'noindex', 'kommentar', 'titel'}:
        return mixed(el, cell)
    raise ValueError('Nicht behandeltes XML-Element: ' + tag)


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.head = None

    def handle_starttag(self, tag, attrs):
        if tag == 'thead':
            self.head = []

    def handle_data(self, data):
        (self.head if self.head is not None else self.parts).append(data)

    def handle_endtag(self, tag):
        if tag == 'thead':
            text = ''.join(self.head)
            if norm(text) not in SYNTHETIC_HEADERS:
                self.parts.append(text)
            self.head = None


def visible(md):
    reader = VisibleText()
    reader.feed(PARSER.render(md))
    return ''.join(reader.parts)


ROMANS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
TOC_TABLE = ROOT[1].find('.//table')
CHECKS = []
PARTS = []


def checked(el, title):
    result = render(el).strip()
    original = norm(source_text(el))
    recovered = norm(visible(result))
    if original != recovered:
        i = next((i for i, pair in enumerate(zip(original, recovered)) if pair[0] != pair[1]), min(len(original), len(recovered)))
        raise AssertionError(f'{title}: Textabweichung bei Zeichen {i}:\nXML: {original[max(0,i-100):i+220]}\nMD: {recovered[max(0,i-100):i+220]}')
    CHECKS.append({'teil': title, 'zeichen_ohne_whitespace': len(original),
                   'sha256_normalisierter_text': hashlib.sha256(original.encode()).hexdigest(),
                   'identisch': True})
    return result


def add(s):
    if s.strip():
        PARTS.append(s.strip())


PDF_HASH = hashlib.sha256((BASE / 'Quellen/UStG.pdf').read_bytes()).hexdigest()
add('''---
titel: "Umsatzsteuergesetz (UStG)"
dokumenttyp: "Gesetzesvolltext"
rechtsgebiet: "Steuerrecht / Umsatzsteuer"
rechtsordnung: "Deutschland / Bundesrecht"
sprache: "de"
ausfertigungsdatum: "1979-11-26"
neufassung: "2005-02-21"
dokumentierter_aenderungsstand: "2026-06-29"
letzte_aenderung: "Artikel 5 des Gesetzes vom 29. Juni 2026 (BGBl. 2026 I Nr. 197)"
quellenabgleich: "2026-09-09"
quelle: "https://www.gesetze-im-internet.de/ustg_1980/BJNR119530979.html"
quelle_xml: "https://www.gesetze-im-internet.de/ustg_1980/xml.zip"
quelle_pdf: "https://www.gesetze-im-internet.de/ustg_1980/UStG.pdf"
xml_builddate: "20260831215512"
umfang_pdf_seiten: 98
---''')
add('# Umsatzsteuergesetz (UStG)')
add('''## Dokumentation der Fassung

**Quellenabgleich: 09.09.2026.** Letzte in der Quelle ausgewiesene Änderung: Artikel 5 des Gesetzes vom 29. Juni 2026 (BGBl. 2026 I Nr. 197). Das Ordnerdatum bezeichnet den Quellenabgleich; das Änderungsdatum ist kein allgemeines Inkrafttretensdatum aller Vorschriften.

Die bereitgestellte [UStG.pdf](Quellen/UStG.pdf) umfasst 98 Seiten und war beim Abruf bytegleich mit der PDF-Gesamtausgabe von [Gesetze im Internet](https://www.gesetze-im-internet.de/ustg_1980/). Für die strukturierte Übernahme wurde die dazugehörige [XML-Gesamtausgabe](Quellen/XML/BJNR119530979.xml) verwendet. Der vollständige Inhalt wurde mit der PDF und der Markdown-Ausgabe abgeglichen; Einzelheiten stehen im [Prüfbericht](Pruefung/Pruefbericht.md).

Die folgende Wiedergabe enthält die Inhaltsübersicht, sämtliche Vorschriften einschließlich weggefallener Vorschriften, alle fünf Anlagen sowie die mitgelieferten Fußnoten, Fundstellen und Anwendungshinweise. Absatz-, Nummern- und Buchstabenkennzeichnungen bleiben erhalten. Zusammengezogene Tabellenzellen werden durch leere Fortsetzungszellen dargestellt. Wiederkehrende PDF-Servicezeilen, Seitennummern und am Seitenumbruch wiederholte Tabellenköpfe entfallen. Metadaten, Navigationslinks und zusätzliche Tabellenüberschriften sind redaktionelle Ergänzungen dieser Wissensdatenbank.

Navigation: [Gesetzeskopf](#gesetzeskopf) · [Inhaltsübersicht](#inhaltsuebersicht) · [Anlagen](#anlagen)

---''')
add('<a id="gesetzeskopf"></a>\n\n## Gesetzeskopf')
add('UStG\n\nAusfertigungsdatum: 26.11.1979')
add('''**Vollzitat:**

"Umsatzsteuergesetz in der Fassung der Bekanntmachung vom 21. Februar 2005 (BGBl. I S. 386), das zuletzt durch Artikel 5 des Gesetzes vom 29. Juni 2026 (BGBl. 2026 I Nr. 197) geändert worden ist"''')
add('**Stand:**\n\n' + '  \n'.join(md_text(x.findtext('standkommentar')) for x in ROOT[0].findall('metadaten/standangabe')))
section = 0
for ni, node in enumerate(ROOT):
    meta = node.find('metadaten')
    enbez = tidy(meta.findtext('enbez', ''))
    group = meta.find('gliederungseinheit')
    if group is not None:
        section += 1
        add(f'<a id="abschnitt-{section}"></a>\n\n## ' + md_text(group.findtext('gliederungsbez')) + ' – ' + md_text(tidy(group.findtext('gliederungstitel'))))
    elif ni > 0:
        if enbez == 'Anlage 1':
            add('<a id="anlagen"></a>\n\n## Anlagen')
        title = meta.find('titel')
        title_md = mixed(title).replace('  \n', ' ').strip() if title is not None else ''
        if title is not None:
            checked(title, enbez + ' / Überschrift')
        level = '##' if enbez == 'Inhaltsübersicht' else '###'
        add(f'<a id="{anchor(enbez)}"></a>\n\n{level} {enbez}' + (' ' + title_md if title_md else ''))
    for kind, heading in [('text', ''), ('fussnoten', 'Fußnote')]:
        content = node.find(f'textdaten/{kind}/Content')
        if content is not None:
            if heading:
                add(('### ' if ni == 0 else '#### ') + heading)
            add(checked(content, (enbez or ('Gesetzeskopf' if ni == 0 else f'Abschnitt {section}')) + ' / ' + kind))

DOCUMENT = '\n\n'.join(PARTS) + '\n'
assert '\ufffd' not in DOCUMENT
ids = re.findall(r'<a id="([^"]+)"', DOCUMENT)
assert len(ids) == len(set(ids)), 'Doppelte Anker'
links = re.findall(r'\]\(#([^)]*)\)', DOCUMENT)
assert set(links) <= set(ids), 'Ungültige Navigationslinks'
(BASE / 'UStG.md').write_text(DOCUMENT, encoding='utf-8', newline='\n')

report = {
    'pruefdatum': '2026-09-09',
    'xml_normdatensaetze': len(ROOT),
    'abschnitte': section,
    'paragraphen': sum(tidy(n.findtext('metadaten/enbez', '')).startswith('§') for n in ROOT),
    'anlagen': sum(tidy(n.findtext('metadaten/enbez', '')).startswith('Anlage') for n in ROOT),
    'tabellen': len(list(ROOT.iter('table'))),
    'tabellenzeilen_einschliesslich_originalkopfzeilen': len(list(ROOT.iter('row'))),
    'tabellenzellen': len(list(ROOT.iter('entry'))),
    'gliederungskennzeichnungen_dt': len(list(ROOT.iter('DT'))),
    'gepruefte_textbloecke': len(CHECKS),
    'textbloecke_ohne_abweichung': all(x['identisch'] for x in CHECKS),
    'interne_links': len(links),
    'alle_linkziele_vorhanden': True,
    'sha256_pdf': PDF_HASH,
    'sha256_xml': hashlib.sha256(XML.read_bytes()).hexdigest(),
    'sha256_markdown': hashlib.sha256(DOCUMENT.encode()).hexdigest(),
    'methode': 'XML-Text gegen gerenderten Markdown-Text je Inhalt/Fußnote/Überschrift; nur Whitespace und redaktionelle Tabellenköpfe ausgenommen. Satzzeichen und alle übrigen Zeichen bleiben vergleichsrelevant.',
    'bloecke': CHECKS,
}
(BASE / 'Pruefung/Vollstaendigkeitspruefung.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'bloecke'}, ensure_ascii=False, indent=2))
