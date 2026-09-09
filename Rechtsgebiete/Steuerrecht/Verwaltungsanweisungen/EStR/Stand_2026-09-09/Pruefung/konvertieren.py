"""Quellentreue Gliederung der EStR-2012-Webkopie mit EStH 2025."""
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from markdown_it import MarkdownIt
from tabellen import TABLE_RANGES, render_table

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'Quellen/EStR_2012_Webkopie.txt'
TARGET = BASE / 'EStR_2012.md'
MD = MarkdownIt('commonmark', {'html': True}).enable('table')
REF = re.compile(r'\[(\d+)\]')
DEFINITION = re.compile(r'^\[(\d+)\]\s*$')
GROUP = re.compile(r'^Zu § \d+[a-z]? EStG(?:\[\d+\])*$')
# Zeilen nach manueller Prüfung: zitierte frühere Richtlinien und bloße Verweise.
HISTORIC = {743, 1324, 7072, 7084, 12036, 12796, 13545, 14253, 18595, 13552, 18614}
PROSE_REFS = {1669, 3036, 7070, 7082, 7902, 8275, 8446, 8459}
ANNEXES = {19068: 1, 19130: 2, 19340: 3, 19341: 4, 19562: 5, 19563: 6}


class Visible(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def canon(value):
    return re.sub(r'\s+', '', value)


def text_of(value):
    parsed = Visible()
    parsed.feed(MD.render(value))
    return canon(''.join(parsed.parts))


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    raw = SOURCE.read_bytes()
    lines = raw.decode('utf-8-sig').splitlines()
    assert len(lines) == 20085 and sha(raw) == '08d3c8ad5bf40cb5b2b1bbbb32979e458b1c42eebf7eb3ce36d4105ee8173ef3'
    assert lines[32] == 'Einkommensteuer-Richtlinien 2012'
    assert lines[39] == 'Mit den Einkommensteuer-Hinweisen 2025'
    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    sections = {i: line for i, line in enumerate(lines)
                if re.match(r'^[RH] \d', line) and i + 1 not in HISTORIC | PROSE_REFS}
    assert sum(value.startswith('R ') for value in sections.values()) == 302
    assert sum(value.startswith('H ') for value in sections.values()) == 344
    groups = {i for i, line in enumerate(lines) if GROUP.fullmatch(line)}
    assert len(groups) == 118
    defs = defaultdict(list)
    for i, line in enumerate(lines):
        match = DEFINITION.fullmatch(line)
        if match:
            defs[match[1]].append(i)
    references = {}
    for i, line in enumerate(lines):
        if DEFINITION.fullmatch(line):
            continue
        for match in REF.finditer(line):
            candidates = defs[match[1]]
            position = bisect_right(candidates, i)
            assert position < len(candidates), (i + 1, match[1])
            references[i, match.start()] = candidates[position]
    assert len(references) == 507
    assert Counter(references.values()) == Counter({i: 1 for values in defs.values() for i in values})

    def inline(i, heading=False):
        value = lines[i]
        definition = DEFINITION.fullmatch(value)
        if definition:
            return f'<a id="fn-z{i + 1}"></a><strong>{escape(value.strip())}</strong>'
        cursor = 0
        result = []
        for match in REF.finditer(value):
            result.append(escape(value[cursor:match.start()]))
            result.append(f'<a href="#fn-z{references[i, match.start()] + 1}">[{match[1]}]</a>')
            cursor = match.end()
        result.append(escape(value[cursor:]))
        content = ''.join(result)
        return content.replace('*', '\\*').replace('_', '\\_') if heading else content

    parts = ['# Einkommensteuer-Richtlinien 2012 mit Einkommensteuer-Hinweisen 2025\n\n'
             '**Richtlinien:** Fassung der EStÄR 2012 vom 25. März 2013. '
             '**Hinweise:** EStH 2025; in der bereitgestellten Kopie genannter Redaktionsschluss 20. Januar 2026. '
             '**Erfassung und Quellenprüfung:** 9. September 2026.\n\n'
             'Diese Datei verbindet die in der Webkopie enthaltenen Richtlinien (**R**) und Hinweise (**H**) '
             'in ihrer ursprünglichen Reihenfolge. R und H sowie ausdrücklich zitierte frühere Fassungen bleiben '
             'unterscheidbar. Sie ist keine Neufassung „EStR 2025“ und kein vollständiges amtliches Einkommensteuer-Handbuch.\n\n'
             'Die bibliografischen Angaben, Sachtexte, Anmerkungen und Anlagen der gelieferten beck-online-Kopie '
             'sind vollständig übernommen. Website-Navigation und doppelte Kopfangaben bleiben in der '
             '[unveränderten Textquelle](Quellen/EStR_2012_Webkopie.txt) erhalten. Fußnoten der Webquelle '
             'sind verlinkt; nur dort ausdrücklich amtlich bezeichnete Anmerkungen werden als solche eingeordnet.\n\n'
             '**Quellenergänzungen:** Die in Anlage 4 fehlenden Formularabbildungen werden mit dem zur Kopie '
             'gehörenden historischen Stand 2013/2014 aus amtlichen Quellen ergänzt. Die amtlichen Vergleichsübersichten '
             '2025 zu Anlagen 2 und 6 sind gesondert verlinkt; abweichende Fassungen werden nicht vermischt. '
             'Schreibweisen und mögliche Fehler der Kopie werden nicht stillschweigend korrigiert.\n\n'
             '[Prüfbericht](Pruefung/Pruefbericht.md) · [Quellenabgleich](Quellen/Onlineabgleich/Abgleich.json) · '
             '[Anlagen](#anlagen)\n\n## Inhaltsverzeichnis']
    # Das Inhaltsverzeichnis ist neu erzeugt; seine Bezeichnungen sind keine zusätzlichen Quellblöcke.
    toc = []
    for i in sorted(groups | sections.keys()):
        label = escape(REF.sub('', lines[i]))
        if i in groups:
            toc.append(f'- <a href="#gruppe-z{i + 1}">{label}</a>')
        else:
            toc.append(f'  - <a href="#rh-z{i + 1}">{label}</a>')
    toc.extend(f'- [Anlage {number}](#anlage-{number})' for number in ANNEXES.values())
    parts.append('\n'.join(toc))
    parts.append('## Bibliografische Angaben und Einführung')
    blocks = []
    covered = Counter()
    aliases = set()

    def add(a, b, content, kind='absatz'):
        expected = canon('\n'.join(lines[a:b]))
        assert text_of(content) == expected, (a + 1, b, kind)
        for index in range(a, b):
            if lines[index].strip():
                covered[index] += 1
        block_id = f'z{a + 1}-{b}'
        parts.append(f'<!-- quelle:{block_id} -->\n{content}\n<!-- /quelle:{block_id} -->')
        blocks.append({'id': block_id, 'zeile_von': a + 1, 'zeile_bis': b, 'art': kind,
                       'sha256_sichtbarer_quelltext': sha(expected.encode('utf-8'))})

    def heading(index, level, anchor=None, extra=''):
        body = (f'<a id="{anchor}"></a>\n\n' if anchor else '') + extra
        body += '#' * level + ' ' + inline(index, True)
        add(index, index + 1, body, 'ueberschrift')

    def image_blocks(index):
        for item in online.get('abbildungen', []):
            if item.get('quellzeile') != index + 1:
                continue
            path = item['datei']
            assert (BASE / path).is_file(), path
            parts.append('**Amtliche Ergänzung zur fehlenden Formularabbildung – Stand 2013/2014:**\n\n'
                         f'![{escape(item.get("titel", "Formularseite"))}]({path})')

    i = 32
    active = None
    while i < len(lines):
        text = lines[i]
        if not text.strip():
            i += 1
            continue
        if i in TABLE_RANGES:
            end = TABLE_RANGES[i]
            add(i, end, render_table(i, lines, inline), 'tabelle')
            i = end
            continue
        if i + 1 in ANNEXES:
            number = ANNEXES[i + 1]
            if number == 1:
                parts.append('<a id="anlagen"></a>\n\n## Anlagen der kopierten Fassung')
            heading(i, 2, f'anlage-{number}')
            active = None
            if number in (2, 6):
                parts.append('> **Abweichender Vergleichsstand:** Die hier übernommene Übersicht stammt aus der gelieferten '
                             'Kopie. Sie weicht von der im amtlichen EStH 2025 enthaltenen Übersicht ab. '
                             f'Diese liegt gesondert unter [Anlage {number} – amtliche Vergleichsfassung 2025]'
                             f'(Ergaenzungen/Anlage_{number}_BMF_2025.md).')
            i += 1
            continue
        if i in groups:
            heading(i, 2, f'gruppe-z{i + 1}')
            active = None
            i += 1
            continue
        if i in sections:
            # Wiederholte Absatz-Teilstücke erhalten eigene Zeilenanker; die erste Position zusätzlich eine Kurzadresse.
            match = re.match(r'^([RH]) (\d+[a-z]?(?:\.\d+[a-z]?)?)', text)
            alias = match[1].lower() + '-' + match[2].replace('.', '-')
            extra = ''
            if alias not in aliases:
                extra = f'<a id="{alias}"></a>\n\n'
                aliases.add(alias)
            heading(i, 3, f'rh-z{i + 1}', extra)
            active = f'rh-z{i + 1}'
            i += 1
            continue
        if i + 1 in HISTORIC:
            parts.append('> Historischer Bezug der kopierten Quelle; der in der folgenden Überschrift bezeichnete Jahrgang bleibt maßgeblich.')
            heading(i, 4, f'historisch-z{i + 1}')
            i += 1
            continue
        if i == 43:
            heading(i, 2, 'einfuehrung')
            i += 1
            continue
        if 19414 <= i < 19478 and re.fullmatch(r'Muster \d+', text):
            heading(i, 3, 'muster-' + text.split()[-1])
            i += 1
            continue
        if i == 19478:
            heading(i, 3, 'bmf-zuwendungsbestaetigungen')
            i += 1
            continue
        if (len(text) < 200 and re.match(r'^[A-ZÄÖÜ]', text) and not text.endswith(('.', ':'))
                and i + 1 < len(lines) and re.match(r'^\(\d+[a-z]?\)', lines[i + 1])) or re.match(r'^Beispiel(?: \d+)?(?:\[\d+\])*:', text):
            heading(i, 4)
            i += 1
            continue
        j = i + 1
        while j < len(lines) and lines[j].strip():
            if j in sections or j in groups or j in TABLE_RANGES or j + 1 in ANNEXES or j + 1 in HISTORIC:
                break
            if re.match(r'^\(\d+[a-z]?\)', lines[j]) or j == 19478 or re.fullmatch(r'Muster \d+', lines[j]):
                break
            # Bildbeschriftungen bleiben einzeln, damit Ergänzungen exakt zugeordnet werden können.
            if 19414 <= i < 19478:
                break
            j += 1
        paragraph = re.match(r'^\((\d+[a-z]?)\)', text)
        if paragraph and active:
            anchor = active + '-abs-' + paragraph[1]
            if anchor not in aliases:
                parts.append(f'<a id="{anchor}"></a>')
                aliases.add(anchor)
        add(i, j, '<p>' + '<br>\n'.join(inline(index) for index in range(i, j)) + '</p>')
        for index in range(i, j):
            image_blocks(index)
        i = j

    expected_lines = {i for i in range(32, len(lines)) if lines[i].strip()}
    assert covered == Counter({i: 1 for i in expected_lines})
    assert len(covered) == 10924
    image_paths = {item['datei'] for item in online.get('abbildungen', [])}
    output = '\n\n'.join(parts) + '\n'
    assert all(f']({path})' in output for path in image_paths), 'Nicht eingebundene Formularabbildung.'
    TARGET.write_text(output, encoding='utf-8')
    (BASE / 'Pruefung/Quellbloecke.json').write_text(json.dumps(blocks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'pruefung_erfolgreich': True, 'sha256_original_quelle': sha(raw), 'sha256_markdown': sha(TARGET.read_bytes()),
              'quellzeilen_gesamt': len(lines), 'quellzeilen_sachinhalt_nichtleer': len(covered),
              'quellbloecke': len(blocks), 'richtlinienbloecke': 302, 'hinweisbloecke': 344,
              'paragraphengruppen': len(groups), 'historische_ueberschriften': len(HISTORIC),
              'fussnoten': 507, 'anlagenpositionen': 6, 'nicht_belegte_anlagen': [3, 5],
              'ergaenzte_abbildungen': len(image_paths),
              'umfang': 'Alle nichtleeren Sachtextzeilen 33 bis 20085 genau einmal; vollständiger sichtbarer Textrückvergleich pro Quellblock.',
              'einschraenkung': 'Die kombinierte Webkopie ist keine aktuelle Neufassung der EStR und kein vollständiges EStH. Amtlicher Stand-/Strukturvergleich und gekennzeichnete Ergänzungen; kein vollständiger Wortidentitätsvergleich der gesamten Kopie mit BMF-Inhalten.'}
    (BASE / 'Pruefung/Vollstaendigkeitspruefung.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
