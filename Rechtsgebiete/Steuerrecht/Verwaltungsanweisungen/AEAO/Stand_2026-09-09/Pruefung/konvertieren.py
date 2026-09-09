"""Strukturiert die bereitgestellte AEAO-Webkopie mit vollständigem Textrückvergleich.

Jede Zielzeile stammt aus einem Quellblock der Textkopie. Der sichtbare Text des
gerenderten Markdown muss nach Entfernung von Leerraum zeichengenau mit dem
Quellblock übereinstimmen. Es wird nichts berichtigt, ergänzt oder weggelassen.
"""
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
SOURCE = BASE / 'Quellen/AEAO_Webkopie.txt'
MAIN = 'AEAO.md'
FIRST = 86      # 0-basiert; Zeile 87: „Anwendungserlass zur Abgabenordnung“
BODY = 104      # Zeile 105: „AEAO zu § 1 – Anwendungsbereich:“
ANNEX = 18297   # Zeile 18298: „Anlage 1[1] Abtretungs-/Verpfändungsanzeige“
LAST = 18403    # Zeile 18404: „(Unterschrift des Ordensobern)“

HEAD = re.compile(r'^AEAO((?:\[\d+\])*) (zu|vor) (§§?) ([^–:]+?)(?: – (.*?))?:((?:\[\d+\])*)\s*$')
ANNEX_HEAD = re.compile(r'^Anlage (\d)((?:\[\d+\])*) (?!zu\b)(\S.*)$')
DEF = re.compile(r'^\[(\d+)\]\s*$')
REF = re.compile(r'\[(\d{1,2})\]')
NUM = re.compile(r'^(\d+(?:\.\d+)*)\.((?:\[\d+\])*)\s+(\S.*)$')
LIST = re.compile(r'^(\d{1,2}\.(?=[^\s\d.])|[a-z]{1,2}\)(?=\S)|[–•])\s*')
SENT = re.compile(r'(?:(?<=\s)|^)(\d{1,2})(?=[A-ZÄÖÜ§„])')
SENT_START = re.compile(r'^\d{1,2}[A-ZÄÖÜ§„]')
TOC = re.compile(r'^Inhaltsübersicht\s*(?:\[\d+\])*\s*$')
TOC_NUMBER = re.compile(r'^\d+(?:\.\d+)*\.?$')
ZU = re.compile(r'^Zu §§? [^:]{1,80}:(?:\[\d+\])*$')
BEISPIEL = re.compile(r'^(?:Gegen)?Beispiele?(?: \d+)?(?: \([^)]{1,60}\))?(?: für [^:]{1,80})?:(?:\[\d+\])*$')
PARAGRAPH_SIGN = re.compile(r'^§ \d+$')
MARKERS = re.compile(r'(?:\[\d+\])+$')
FRAGMENT_END = re.compile(r'\b(als|wer|und|oder|wenn|sowie|bzw|wie|dass|ob)$')
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


def slug(value):
    return re.sub(r'[^0-9a-z]+', '-', value.lower()).strip('-')


def main():
    data = SOURCE.read_bytes()
    lines = data.decode('utf-8-sig').splitlines()
    assert len(lines) == 18428, 'Andere Webkopie: Strukturgrenzen neu prüfen.'
    assert lines[FIRST] == 'Anwendungserlass zur Abgabenordnung'
    assert lines[FIRST + 1] == '(AEAO)[1][2][3]'
    assert lines[BODY] == 'AEAO zu § 1 – Anwendungsbereich:'
    assert lines[ANNEX].startswith('Anlage 1[1] ')
    assert lines[LAST] == '(Unterschrift des Ordensobern)'
    assert lines[LAST + 3].strip() == 'zum Seitenanfang'

    def next_index(index):
        index += 1
        while index <= LAST and not lines[index].strip():
            index += 1
        return index

    def prev_index(index, floor):
        index -= 1
        while index > floor and not lines[index].strip():
            index -= 1
        return index

    # Gliederungspositionen und Anlagen.
    sections = {}
    for index in range(BODY, ANNEX):
        match = HEAD.match(lines[index])
        if match:
            key = re.sub(r'\[\d+\]', '', match[4]).strip()
            anchor = 'aeao-' + match[2] + '-' + slug(key)
            assert anchor not in sections.values(), anchor
            sections[index] = anchor
    assert len(sections) == 224, len(sections)
    annexes = {index: 'anlage-' + ANNEX_HEAD.match(lines[index])[1]
               for index in range(ANNEX, LAST + 1) if ANNEX_HEAD.match(lines[index])}
    assert list(annexes) == [18297, 18307, 18366], annexes
    assert all(not HEAD.match(lines[i]) for i in range(FIRST, BODY))

    # Fußnoten: jeder Verweis gehört zur nächsten folgenden Definition derselben Nummer.
    definitions = defaultdict(list)
    for index in range(FIRST, LAST + 1):
        match = DEF.fullmatch(lines[index])
        if match:
            definitions[match[1]].append(index)
    references = {}
    for index in range(FIRST, LAST + 1):
        if DEF.fullmatch(lines[index]):
            continue
        for ordinal, match in enumerate(REF.finditer(lines[index])):
            candidates = definitions[match[1]]
            pos = bisect_right(candidates, index)
            assert pos < len(candidates), (index + 1, match[1])
            references[(index, ordinal)] = candidates[pos]
    all_definitions = {i for values in definitions.values() for i in values}
    assert set(references.values()) == all_definitions
    assert all(count == 1 for count in Counter(references.values()).values())
    assert len(references) == 983, len(references)

    # Strukturentscheidungen.
    def structural(index):
        text = lines[index]
        return bool(index in sections or index in annexes or DEF.fullmatch(text) or NUM.match(text)
                    or LIST.match(text) or TOC.match(text) or ZU.match(text) or BEISPIEL.match(text)
                    or PARAGRAPH_SIGN.match(text))

    def numbered_is_title(index):
        rest = NUM.match(lines[index])[3]
        if re.match(r'^\d', rest):
            return False
        core = MARKERS.sub('', rest).rstrip()
        if len(core) >= 140:
            return False
        if core.endswith(('n.F.', 'a.F.')) and len(core) < 80:
            return True
        if core.endswith(':'):
            label = core[:-1].strip()
            return bool(re.match(r'^(?:Gegen)?Beispiel|^Variante$|^Schritt$|^Einzelfragen$|^Schattenveranlagung\b', label))
        if core.endswith(('.', ';', ',', '!', '?', '“', '”')):
            return False
        following = next_index(index)
        if following <= LAST and LIST.match(lines[following]):
            return False
        if FRAGMENT_END.search(core):
            return False
        return True

    def cell_like(index):
        text = lines[index].strip()
        return len(text) < 80 and not text.endswith('.') and not structural(index) and not HEAD.match(text)

    def free_heading(index, floor):
        text = lines[index].strip()
        core = MARKERS.sub('', text).rstrip()
        if len(core) >= 120 or not re.match(r'^[A-ZÄÖÜ]', core) or '€' in core:
            return False
        if core.endswith(('.', ';', ',', ':')) or FRAGMENT_END.search(core):
            return False
        following = next_index(index)
        if following > LAST:
            return False
        after = lines[following]
        if not (NUM.match(after) or SENT_START.match(after) or (len(after) >= 100 and not LIST.match(after))):
            return False
        before = prev_index(index, floor)
        if before > floor and cell_like(before):
            return False
        return True

    # Erster Durchlauf: Sprungmarken nummerierter Gliederungspunkte je Position.
    number_anchor = {}
    owner = None
    for index in range(BODY, LAST + 1):
        if index in sections:
            owner = sections[index]
        elif index in annexes:
            owner = annexes[index]
        match = NUM.match(lines[index])
        if match and owner:
            anchor = owner + '-nr-' + match[1].replace('.', '-')
            number_anchor.setdefault(anchor, index)

    def text_segment(value):
        return SENT.sub(lambda m: '<sup>' + m[1] + '</sup>', escape(value))

    def inline(index, heading=False, bold_number=False, list_item=False):
        line = lines[index]
        definition = DEF.fullmatch(line)
        if definition:
            return f'<a id="fn-z{index + 1}"></a><strong>{escape(line.strip())}</strong>'
        if list_item:
            line = LIST.sub(lambda m: m[1] + ' ', line, count=1)
        parts = []
        cursor = 0
        for ordinal, match in enumerate(REF.finditer(line)):
            parts.append(text_segment(line[cursor:match.start()]))
            resolved = references[(index, ordinal)]
            parts.append(f'<a href="#fn-z{resolved + 1}">[{match[1]}]</a>')
            cursor = match.end()
        parts.append(text_segment(line[cursor:]))
        value = ''.join(parts)
        if bold_number:
            value = re.sub(r'^(\d+(?:\.\d+)*\.)', r'<strong>\1</strong>', value, count=1)
        if heading:
            value = value.replace('*', '\\*').replace('_', '\\_')
        return value

    outputs = []
    records = []
    coverage = Counter()
    decisions = []

    def add(a, b, body, kind='absatz'):
        expected = canon('\n'.join(lines[a:b]))
        assert visible(body) == expected, ('Textabweichung', a + 1, b, kind)
        for index in range(a, b):
            if lines[index].strip():
                coverage[index] += 1
        block_id = f'z{a + 1}-{b}'
        outputs.append(f'<!-- quelle:{block_id} -->\n{body}\n<!-- /quelle:{block_id} -->')
        records.append({'id': block_id, 'zeile_von': a + 1, 'zeile_bis': b, 'datei': MAIN,
                        'art': kind, 'sha256_sichtbarer_quelltext': digest(expected.encode('utf-8'))})

    def paragraph(a, b, kind='absatz', bold_number=False, css=None):
        opening = '<p>' if css is None else f'<p class="{css}">'
        add(a, b, opening + '<br>\n'.join(inline(i, bold_number=bold_number and i == a) for i in range(a, b)
                                         if lines[i].strip()) + '</p>', kind)

    def heading(index, level, anchor=None, kind='ueberschrift'):
        if anchor:
            outputs.append(f'<a id="{anchor}"></a>')
        add(index, index + 1, '#' * level + ' ' + inline(index, heading=True), kind)
        decisions.append({'zeile': index + 1, 'art': kind, 'ebene': level, 'text': lines[index]})

    outputs.append('# Anwendungserlass zur Abgabenordnung (AEAO)\n\n'
        '**Quellenstand: 2. Juli 2026 · Übernahme und Quellenabgleich: 9. September 2026.**\n\n'
        'Verwaltungsanweisung des Bundesministeriums der Finanzen (BMF-Schreiben vom 31. Januar 2014, '
        'BStBl. 2014 I S. 290; zuletzt geändert durch BMF-Schreiben vom 2. Juli 2026, BStBl. I S. 950). '
        'Grundlage ist die bereitgestellte Textkopie aus beck-online mit der Angabe „Text gilt seit 02.07.2026“. '
        'Alle kopierten Sachtexte werden unverändert übernommen; Website-Navigation und die Liste der '
        'Geltungszeiträume bleiben in der [Originalkopie](Quellen/AEAO_Webkopie.txt) erhalten. Die Fußnoten '
        'der Webquelle sind verlinkt; sie enthalten Änderungsnachweise und Hinweise des Anbieters und sind '
        'nicht Teil des amtlichen Erlasstexts. Nach Fußnote 2 des Dokumentkopfs ist die Satzzählung nicht '
        'amtlich; die hochgestellten Satznummern geben diese Zählung der Kopie wieder.\n\n'
        '**Struktur:** 224 Gliederungspositionen („AEAO zu § …“, „AEAO vor §§ …“) und drei Anlagen. '
        'Nummerierte Gliederungspunkte tragen Sprungmarken; die in der Kopie enthaltenen Inhaltsübersichten '
        'einzelner Positionen sind verlinkt. Nicht nummerierte Zwischenüberschriften wurden nach Form und '
        'Kontext erkannt; alle Entscheidungen stehen in [Gliederungsentscheidungen.json](Pruefung/Gliederungsentscheidungen.json). '
        'In der Kopie abgeflachte Tabellen (Berechnungsbeispiele, Anschriftenbeispiele) bleiben als Textzeilen '
        'erhalten; die beiden Formularseiten der Anlage 1 sind in der Textkopie nur als Platzhalterzeilen enthalten. '
        'Schreibweisen, Satznummern und mögliche Kopierfehler sind nicht redaktionell korrigiert.\n\n'
        '[Prüfbericht](Pruefung/Pruefbericht.md) · [Amtlicher Standabgleich](Quellen/Onlineabgleich/Abgleich.json) · '
        '[BMF-Änderungsschreiben vom 2.7.2026](Quellen/Onlineabgleich/2026-07-02-aenderung-aeao-51-52-usw.pdf)\n\n'
        '## Navigation\n\n[Inhaltsübersicht](#inhaltsuebersicht) · [Erlasstext](#erlasstext) · [Anlagen](#anlagen)')

    # Dokumentkopf mit Fundstelle, Kopffußnoten und Einleitungssatz.
    heading(FIRST, 2, kind='dokumentkopf')
    paragraph(FIRST + 1, FIRST + 6, 'dokumentkopf')
    index = FIRST + 6
    while index < BODY:
        if not lines[index].strip():
            index += 1
            continue
        end = index + 1
        while end < BODY and lines[end].strip():
            end += 1
        paragraph(index, end, 'fussnote' if DEF.fullmatch(lines[index]) else 'einleitung')
        index = end

    # Redaktionelle Gesamtübersicht der Gliederungspositionen.
    rows = ['| Position | Regelungsgegenstand |', '| --- | --- |']
    for index, anchor in sections.items():
        match = HEAD.match(lines[index])
        label = f'AEAO {match[2]} {match[3]} ' + re.sub(r'\[\d+\]', '', match[4]).strip()
        title = re.sub(r'\[\d+\]', '', match[5] or '').strip()
        rows.append(f'| [{label}](#{anchor}) | {escape(title)} |')
    for index, anchor in annexes.items():
        match = ANNEX_HEAD.match(lines[index])
        rows.append(f'| [Anlage {match[1]}](#{anchor}) | {escape(re.sub(r"\[\d+\]", "", match[3]).strip())} |')
    outputs.append('<a id="inhaltsuebersicht"></a>\n\n## Inhaltsübersicht (redaktionell)\n\n'
                   'Die Webkopie enthält kein Gesamtinhaltsverzeichnis; die Übersicht ist aus den '
                   'Positionsüberschriften erzeugt.\n\n' + '\n'.join(rows))
    outputs.append('<a id="erlasstext"></a>\n\n## Erlasstext')

    anchor_used = Counter()
    owner = None
    floor = BODY - 1
    index = BODY
    while index <= LAST:
        text = lines[index]
        if not text.strip():
            index += 1
            continue
        if index == ANNEX:
            outputs.append('<a id="anlagen"></a>\n\n## Anlagen')
        if index in sections:
            owner = sections[index]
            floor = index
            heading(index, 3, owner, 'gliederungsposition')
            index += 1
            continue
        if index in annexes:
            owner = annexes[index]
            floor = index
            heading(index, 3, owner, 'anlage')
            index += 1
            continue
        if TOC.match(text):
            heading(index, 4, kind='inhaltsuebersicht_position')
            end = index + 1
            while end <= LAST and not (NUM.match(lines[end]) or end in sections or end in annexes):
                end += 1
            tokens = [i for i in range(index + 1, end) if lines[i].strip()]
            rows = []
            position = 0
            while position < len(tokens):
                token = tokens[position]
                value = lines[token].strip()
                if TOC_NUMBER.fullmatch(value) and position + 1 < len(tokens):
                    target = owner + '-nr-' + value.rstrip('.').replace('.', '-')
                    cell = inline(token)
                    if target in number_anchor:
                        cell = f'<a href="#{target}">{cell}</a>'
                    rows.append(f'<tr><td>{cell}</td><td>{inline(tokens[position + 1])}</td></tr>')
                    position += 2
                else:
                    rows.append(f'<tr><td colspan="2">{inline(token)}</td></tr>')
                    position += 1
            add(index + 1, end, '<table>\n' + '\n'.join(rows) + '\n</table>', 'inhaltsuebersicht_tabelle')
            index = end
            continue
        if DEF.fullmatch(text):
            end = index + 1
            while end <= LAST and lines[end].strip() and not structural(end):
                end += 1
            paragraph(index, end, 'fussnote')
            index = end
            continue
        match = NUM.match(text)
        if match:
            anchor = owner + '-nr-' + match[1].replace('.', '-')
            anchor_used[anchor] += 1
            first = anchor_used[anchor] == 1 and number_anchor.get(anchor) == index
            if numbered_is_title(index):
                depth = match[1].count('.') + 1
                heading(index, min(3 + depth, 6), anchor if first else None, 'nummerierte_ueberschrift')
                index += 1
                continue
            if first:
                outputs.append(f'<a id="{anchor}"></a>')
            end = index + 1
            while end <= LAST and lines[end].strip() and not structural(end):
                end += 1
            paragraph(index, end, 'nummerierter_absatz', bold_number=True)
            index = end
            continue
        if LIST.match(text):
            items = [index]
            end = index + 1
            while True:
                following = next_index(end - 1)
                if following <= LAST and LIST.match(lines[following]) and not NUM.match(lines[following]) \
                        and following not in sections:
                    items.append(following)
                    end = following + 1
                else:
                    break
            add(index, end, '<ul class="original-aufzaehlung" style="list-style:none;padding-left:1.5em">\n'
                + '\n'.join('<li>' + inline(i, list_item=True) + '</li>' for i in items) + '\n</ul>', 'aufzaehlung')
            index = end
            continue
        if ZU.match(text) or BEISPIEL.match(text) or PARAGRAPH_SIGN.match(text):
            heading(index, 4, kind='zwischenueberschrift_form')
            index += 1
            continue
        if free_heading(index, floor):
            heading(index, 4, kind='zwischenueberschrift_kontext')
            index += 1
            continue
        if cell_like(index):
            cells = [index]
            end = index + 1
            while True:
                following = next_index(end - 1)
                if following <= LAST and cell_like(following) and following not in sections \
                        and not free_heading(following, floor):
                    cells.append(following)
                    end = following + 1
                else:
                    break
            if len(cells) >= 3:
                add(index, end, '<p class="quellzeilen">' + '<br>\n'.join(inline(i) for i in cells) + '</p>',
                    'kurze_quellzeilen')
                index = end
                continue
        end = index + 1
        while end <= LAST and lines[end].strip() and not structural(end) and not free_heading(end, floor):
            end += 1
        paragraph(index, end)
        index = end

    expected_lines = {index for index in range(FIRST, LAST + 1) if lines[index].strip()}
    assert set(coverage) == expected_lines, ('Fehlende/zusätzliche Quellzeilen', sorted(expected_lines - coverage.keys())[:20])
    assert all(value == 1 for value in coverage.values()), 'Doppelt übernommene Quellzeilen.'
    (BASE / MAIN).write_text('\n\n'.join(outputs) + '\n', encoding='utf-8')
    (BASE / 'Pruefung/Quellbloecke.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (BASE / 'Pruefung/Gliederungsentscheidungen.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    kinds = Counter(record['art'] for record in records)
    report = {'pruefung_erfolgreich': True, 'sha256_original_quelle': digest(data),
              'sha256_markdown': digest((BASE / MAIN).read_bytes()),
              'quellzeilen_gesamt': len(lines), 'quellzeilen_sachinhalt_nichtleer': len(coverage),
              'quellbloecke': len(records), 'gliederungspositionen': len(sections), 'anlagen': len(annexes),
              'fussnoten': len(references), 'nummerierte_ueberschriften': kinds['nummerierte_ueberschrift'],
              'nummerierte_absaetze': kinds['nummerierter_absatz'],
              'zwischenueberschriften': kinds['zwischenueberschrift_form'] + kinds['zwischenueberschrift_kontext'],
              'inhaltsuebersichten_je_position': kinds['inhaltsuebersicht_tabelle'],
              'aufzaehlungen': kinds['aufzaehlung'], 'kurze_quellzeilenbloecke': kinds['kurze_quellzeilen'],
              'sprungmarken_nummerierte_punkte': len(number_anchor),
              'uebernahme': f'Alle nichtleeren Sachtextzeilen {FIRST + 1} bis {LAST + 1} genau einmal; vollständiger sichtbarer Textrückvergleich pro Quellblock.',
              'einschraenkung': 'Vollständigkeit der übernommenen Textkopie geprüft; kein Wortlautvergleich mit einer amtlichen Gesamtfassung. Gliederungsebenen nicht nummerierter Zwischenüberschriften und die Zuordnung abgeflachter Tabellenzeilen sind redaktionelle Strukturentscheidungen.'}
    (BASE / 'Pruefung/Vollstaendigkeitspruefung.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
