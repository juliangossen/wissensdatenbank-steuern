"""Strukturiert die bereitgestellte UStAE-Webkopie mit vollständigem Textrückvergleich."""
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from markdown_it import MarkdownIt

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'Quellen/UStAE_Webkopie.txt'
MAIN = 'UStAE.md'
SYN = 'Ergaenzungen/Beck_Synopse_UStR_2008_UStAE.md'
NUMBER = r'\d{1,2}[a-z]?(?:\.\d{1,2}[a-z]?){1,2}'
SECTION = re.compile(r'^(' + NUMBER + r')(?:\[\d+\])*\s+')
REF = re.compile(r'\[(\d+)\]')
DEFINITION = re.compile(r'^\[(\d+)\]\s*$')
MD = MarkdownIt('commonmark', {'html': True}).enable('table')


class Visible(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def canon(value):
    return re.sub(r'\s+', '', value)


def visible(value):
    parser = Visible()
    parser.feed(MD.render(value))
    return canon(''.join(parser.parts))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main():
    data = SOURCE.read_bytes()
    lines = data.decode('utf-8-sig').splitlines()
    assert len(lines) == 27139, 'Andere Webkopie: Strukturgrenzen neu prüfen.'
    assert lines[292] == 'Umsatzsteuer-Anwendungserlass'
    assert lines[1839 + 1] == 'Abkürzungsverzeichnis'
    assert lines[2866] == '1.1 Leistungsaustausch'
    assert lines[22315].startswith('Gegenüberstellung UStR 2008')
    assert lines[26285].startswith('Anlage 1 ')
    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    toc_numbers = {line.strip() for line in lines[304:1837] if re.fullmatch(NUMBER, line.strip())}
    assert len(toc_numbers) == 432
    section_lines = {}
    for index in range(2865, 22315):
        match = SECTION.match(lines[index])
        if match and match[1] in toc_numbers:
            assert match[1] not in section_lines, match[1]
            section_lines[match[1]] = index
    assert len(section_lines) == 427
    assert toc_numbers - section_lines.keys() == {'23.1', '23.2', '23.3', '23.4', '25d.1'}
    definitions = defaultdict(list)
    for index, line in enumerate(lines):
        match = DEFINITION.fullmatch(line)
        if match:
            definitions[match[1]].append(index)
    references = {}
    for index, line in enumerate(lines):
        if DEFINITION.fullmatch(line):
            continue
        for match in REF.finditer(line):
            candidates = definitions[match[1]]
            pos = bisect_right(candidates, index)
            assert pos < len(candidates), (index + 1, match[1])
            references[(index, match.start())] = candidates[pos]
    assert len(references) == 829
    assert set(references.values()) == {i for values in definitions.values() for i in values}
    assert all(count == 1 for count in Counter(references.values()).values())

    def destination(index):
        return SYN if 22315 <= index < 26285 else MAIN

    def inline(index, target, heading=False):
        line = lines[index]
        definition = DEFINITION.fullmatch(line)
        if definition:
            return f'<a id="fn-z{index + 1}"></a><strong>{escape(line.strip())}</strong>'
        parts = []
        cursor = 0
        for match in REF.finditer(line):
            parts.append(escape(line[cursor:match.start()]))
            resolved = references[(index, match.start())]
            file = destination(resolved)
            prefix = '' if file == target else ('../' + MAIN if target == SYN else SYN)
            parts.append(f'<a href="{prefix}#fn-z{resolved + 1}">[{match[1]}]</a>')
            cursor = match.end()
        parts.append(escape(line[cursor:]))
        value = ''.join(parts)
        if heading:
            value = value.replace('*', '\\*').replace('_', '\\_')
        return value

    outputs = {MAIN: [], SYN: []}
    records = []
    coverage = Counter()

    def add(a, b, body, kind='absatz', target=MAIN):
        expected = canon('\n'.join(lines[a:b]))
        assert visible(body) == expected, ('Textabweichung', a + 1, b, kind)
        for index in range(a, b):
            if lines[index].strip():
                coverage[index] += 1
        block_id = f'z{a + 1}-{b}'
        outputs[target].append(f'<!-- quelle:{block_id} -->\n{body}\n<!-- /quelle:{block_id} -->')
        records.append({'id': block_id, 'zeile_von': a + 1, 'zeile_bis': b, 'datei': target,
                        'art': kind, 'sha256_sichtbarer_quelltext': digest(expected.encode('utf-8'))})

    def paragraph(a, b, target=MAIN):
        add(a, b, '<p>' + '<br>\n'.join(inline(i, target) for i in range(a, b)) + '</p>', target=target)

    def heading(index, level, anchor=None, target=MAIN):
        body = ('<a id="' + anchor + '"></a>\n\n' if anchor else '')
        body += '#' * level + ' ' + inline(index, target, heading=True)
        add(index, index + 1, body, 'ueberschrift', target)

    def sid(number):
        return 'abschnitt-' + number.replace('.', '-')

    def supplements(key):
        mappings = [item for item in online.get('abbildungen', [])
                    if item.get('abschnitt') == key or ('anlage' in item and key == 'anlage-' + str(item['anlage']))]
        if not mappings:
            return
        outputs[MAIN].append('#### Ergänzung aus der amtlichen BMF-Fassung\n\n'
            'Die folgenden Seitendarstellungen sichern die in der Textkopie fehlenden Schaubilder, Formulare '
            'oder Tabellenbeziehungen. Sie stammen aus der amtlichen PDF mit demselben Stand 2. Juni 2026; '
            'gegebenenfalls wiederholter Begleittext gehört zur vollständigen Originalseite.')
        for item in mappings:
            path = item['datei']
            assert (BASE / path).is_file(), path
            outputs[MAIN].append(f'**Amtliche PDF, Seite {item["pdf_seite"]}:**\n\n'
                                 f'![Originalseite {item["pdf_seite"]} des UStAE – {key}]({path})')

    outputs[MAIN].append('# Umsatzsteuer-Anwendungserlass (UStAE)\n\n'
        '**Quellenstand: 2. Juni 2026 · Übernahme und Quellenabgleich: 9. September 2026.**\n\n'
        'Verwaltungsanweisung des Bundesministeriums der Finanzen. Grundlage ist die bereitgestellte '
        'Textkopie aus beck-online. Alle kopierten Sachtexte werden unverändert übernommen; '
        'die Website-Navigation bleibt in der [Originalkopie](Quellen/UStAE_Webkopie.txt) erhalten. '
        'Die Fußnoten der Webquelle sind verlinkt. Nur ausdrücklich mit „Amtl. Anm.“ gekennzeichnete '
        'Anmerkungen sind als amtlich bezeichnet. Die [redaktionelle Synopse](Ergaenzungen/Beck_Synopse_UStR_2008_UStAE.md) '
        'ist als gesonderte Ergänzung abgelegt.\n\n'
        '**Ergänzungen:** Fehlende Schaubilder und Formularseiten sowie die aufgehobene Position 25d.1 '
        'werden aus der amtlichen BMF-Fassung ergänzt und ausdrücklich gekennzeichnet. In der Textkopie '
        'abgeflachte Tabellen bleiben als Text erhalten; die amtlichen Seitendarstellungen sichern ihre Anordnung. '
        'Satznummern, Schreibweisen und Trennzeichen der Kopie sind nicht redaktionell korrigiert.\n\n'
        '[Prüfbericht](Pruefung/Pruefbericht.md) · [Quellenabgleich](Quellen/Onlineabgleich/Abgleich.json) · '
        '[Amtliche PDF](' + online['pdf_datei'] + ')\n\n'
        '## Navigation\n\n[Inhaltsübersicht](#inhaltsuebersicht) · [Abkürzungen](#abkuerzungen) · '
        '[Erlasstext](#erlasstext) · [Anlagen](#anlagen)')
    outputs[SYN].append('# Redaktionelle Gegenüberstellung UStR 2008 – UStAE\n\n'
        'Diese Ergänzung stammt aus der vom Nutzer bereitgestellten beck-online-Textkopie. '
        'Die Quelle bezeichnet sie ausdrücklich als redaktionell erstellte Synopse. '
        'Sie ist kein zusätzlicher amtlicher Erlasstext. Die kopierte Reihenfolge aller Tabellenangaben '
        'bleibt erhalten; verlorene Zellenverbindungen werden nicht geraten.\n\n[Zum UStAE](../UStAE.md)')

    # Einleitung, einschließlich aller Angaben zur Fundstelle.
    heading(292, 2)
    paragraph(293, 298)
    paragraph(299, 300)
    paragraph(301, 302)

    heading(303, 2, 'inhaltsuebersicht')
    tokens = [i for i in range(304, 1837) if lines[i].strip()]
    rows = []
    position = 0
    while position < len(tokens):
        index = tokens[position]
        value = lines[index].strip()
        if re.fullmatch(NUMBER, value) or re.fullmatch(r'Anlage \d', value):
            assert position + 1 < len(tokens)
            title_index = tokens[position + 1]
            anchor = sid(value) if value in toc_numbers else 'anlage-' + value.split()[-1]
            rows.append(f'<tr><td><a href="#{anchor}">{inline(index, MAIN)}</a></td><td>{inline(title_index, MAIN)}</td></tr>')
            position += 2
        else:
            rows.append(f'<tr><td colspan="2">{inline(index, MAIN)}</td></tr>')
            position += 1
    add(304, 1837, '<table>\n' + '\n'.join(rows) + '\n</table>', 'inhaltsverzeichnis')
    paragraph(1837, 1839)

    heading(1840, 2, 'abkuerzungen')
    tokens = [i for i in range(1841, 2864) if lines[i].strip()]
    rows = []
    position = 0
    while position < len(tokens):
        start = tokens[position]
        equal = position + 1 < len(tokens) and lines[tokens[position + 1]].strip() == '='
        count = 3 if equal else 2
        selected = tokens[position:position + count]
        assert len(selected) == count
        cells = [inline(selected[0], MAIN), inline(selected[1], MAIN) if equal else '', inline(selected[-1], MAIN)]
        rows.append('<tr>' + ''.join('<td>' + cell + '</td>' for cell in cells) + '</tr>')
        position += count
    assert len(rows) == 171
    add(1841, 2864, '<table>\n' + '\n'.join(rows) + '\n</table>', 'abkuerzungstabelle')

    # Originalblöcke: Abschnitte, Zwischentitel, Beispiele, Absätze, Fußnoten.
    outputs[MAIN].append('<a id="erlasstext"></a>\n\n## Erlasstext')
    current_section = None
    current_annex = None
    body_headings = {index: number for number, index in section_lines.items()}
    paragraph_anchors = Counter()
    i = 2865
    while i < len(lines):
        target = destination(i)
        text = lines[i]
        if not text.strip():
            i += 1
            continue
        if i == 22315:
            if current_section:
                supplements(current_section)
                current_section = None
            heading(i, 2, 'synopse', target=SYN)
            # Die flache Synopse bleibt in gut lesbaren Quellzeilen erhalten.
            # Alle nummerierten Zuordnungen und Pfeile sind unverändert enthalten.
            nonempty = [n for n in range(i + 1, 26285) if lines[n].strip()]
            add(i + 1, 26285, '<div class="synopse-quellzeilen">\n' + '\n'.join(
                '<p>' + inline(n, SYN) + '</p>' for n in nonempty) + '\n</div>', 'redaktionelle_synopse', SYN)
            i = 26285
            continue
        if i == 26285:
            outputs[MAIN].append('<a id="anlagen"></a>\n\n## Anlagen')
        if i == 26804:
            # Spaltenzuordnung an den amtlichen Seiten 883–885 visuell geprüft.
            starts = [26819, 26833, 26847, 26861, 26875, 26889, 26903, 26907,
                      26921, 26935, 26953, 26967, 26981, 26995, 27009, 27023,
                      27037, 27051, 27065, 27079, 27093, 27107, 27121]
            headers = [n for n in range(26804, 26817) if lines[n].strip()]
            assert len(headers) == 7
            table = ['<table>', '<thead><tr>' + ''.join('<th>' + inline(n, MAIN) + '</th>' for n in headers) + '</tr></thead>', '<tbody>']
            for row, start in enumerate(starts):
                end = starts[row + 1] - 1 if row + 1 < len(starts) else 27133
                cells = [n for n in range(start - 1, end) if lines[n].strip()]
                if lines[start - 1].startswith('Gälisch'):
                    assert len(cells) == 2
                    values = [inline(cells[0], MAIN), '', inline(cells[1], MAIN), '', '', '', '']
                elif lines[start - 1] == 'Kroatisch':
                    assert len(cells) == 9
                    values = [inline(cells[0], MAIN), inline(cells[1], MAIN),
                              '<br>'.join(inline(n, MAIN) for n in cells[2:5]),
                              *[inline(n, MAIN) for n in cells[5:]]]
                else:
                    assert len(cells) == 7, (start, cells)
                    values = [inline(n, MAIN) for n in cells]
                table.append('<tr>' + ''.join('<td>' + value + '</td>' for value in values) + '</tr>')
            table += ['</tbody>', '</table>']
            add(i, 27133, '\n'.join(table), 'sprachentabelle_anlage_8')
            i = 27133
            continue
        annex = re.match(r'^Anlage ([1-8])(?:\[\d+\])* ', text) if i >= 26285 else None
        if annex and ' zu A ' not in text:
            if current_annex:
                supplements('anlage-' + str(current_annex))
            current_annex = int(annex[1])
            heading(i, 2, 'anlage-' + annex[1])
            i += 1
            continue
        if i in body_headings:
            if current_section:
                supplements(current_section)
            current_section = body_headings[i]
            heading(i, 3, sid(current_section))
            i += 1
            continue
        if text.startswith('23.1–23.4 [aufgehoben]'):
            outputs[MAIN].append('\n'.join('<a id="' + sid(number) + '"></a>' for number in ['23.1', '23.2', '23.3', '23.4']))
            heading(i, 3)
            i += 1
            continue
        if re.match(r'^Zu §§? \d', text) and 'UStG' in text and len(text) < 150:
            if current_section:
                supplements(current_section)
                current_section = None
            if text.startswith('Zu § 25e UStG'):
                outputs[MAIN].append('## Zu § 25d UStG\n\n<a id="abschnitt-25d-1"></a>\n\n### 25d.1. - gestrichen -\n\n'
                    '> Ergänzung aus der amtlichen BMF-PDF, Seite 849. Diese gestrichene Position ist im '
                    'Inhaltsverzeichnis der Webkopie genannt, fehlt aber in ihrem Erlasstext. Es wird kein '
                    'früherer Regelungstext eingefügt.')
            heading(i, 2)
            i += 1
            continue
        if 2865 <= i < 22315 and ((len(text) < 200 and re.match(r'^[A-ZÄÖÜ]', text)
                and not text.endswith(('.', ':')) and i + 1 < len(lines)
                and re.match(r'^\(\d+[a-z]?\)', lines[i + 1])) or re.match(r'^Beispiel(?: \d+)?(?:\[\d+\])*:', text)):
            heading(i, 4)
            i += 1
            continue
        j = i + 1
        while j < len(lines) and lines[j].strip():
            if j in body_headings or j == 22315 or j == 26285 or re.match(r'^Anlage [1-8](?:\[\d+\])* ', lines[j]):
                break
            if re.match(r'^Zu §§? \d', lines[j]) or re.match(r'^\(\d+[a-z]?\)', lines[j]):
                break
            if re.match(r'^Beispiel(?: \d+)?(?:\[\d+\])*:', lines[j]):
                break
            j += 1
        paragraph_match = re.match(r'^\((\d+[a-z]?)\)', text)
        if paragraph_match and current_section:
            anchor = sid(current_section) + '-abs-' + paragraph_match[1]
            paragraph_anchors[anchor] += 1
            if paragraph_anchors[anchor] == 1:
                outputs[MAIN].append('<a id="' + anchor + '"></a>')
        paragraph(i, j, target)
        i = j
    if current_annex:
        supplements('anlage-' + str(current_annex))

    expected_lines = {index for index in range(292, len(lines)) if lines[index].strip()}
    assert set(coverage) == expected_lines, ('Fehlende/zusätzliche Quellzeilen', sorted(expected_lines - coverage.keys()))
    assert all(value == 1 for value in coverage.values()), 'Doppelt übernommene Quellzeilen.'
    for file, parts in outputs.items():
        (BASE / file).parent.mkdir(parents=True, exist_ok=True)
        (BASE / file).write_text('\n\n'.join(parts) + '\n', encoding='utf-8')
    (BASE / 'Pruefung/Quellbloecke.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'pruefung_erfolgreich': True, 'sha256_original_quelle': digest(data),
              'sha256_markdown': digest((BASE / MAIN).read_bytes()),
              'sha256_redaktionelle_synopse': digest((BASE / SYN).read_bytes()),
              'quellzeilen_gesamt': len(lines), 'quellzeilen_sachinhalt_nichtleer': len(coverage),
              'quellbloecke': len(records), 'abschnittsbloecke_kopie': 428,
              'amtliche_abschnittspositionen': 432, 'anlagen': 8, 'abkuerzungen': 171,
              'fussnoten': len(references), 'uebernahme': 'Alle nichtleeren Sachtextzeilen 293 bis 27139 genau einmal; vollständiger sichtbarer Textrückvergleich pro Quellblock.',
              'ergaenzung_25d_1': '25d.1. - gestrichen -; amtliche PDF Seite 849',
              'abbildungen': len(online.get('abbildungen', [])),
              'einschraenkung': 'Vollständigkeit der übernommenen Textkopie geprüft; kein vollständiger Wortlautvergleich Webkopie gegen amtliche PDF. Redaktionelle Hinweise bleiben als solche erkennbar.'}
    (BASE / 'Pruefung/Vollstaendigkeitspruefung.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
