"""Strukturiert die bereitgestellte ErbStR-2019-Webkopie (mit ErbStH 2019) mit vollständigem Textrückvergleich.

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

from tabellen import TABLE_RANGES, render_table

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'Quellen/ErbStR_2019_Webkopie.txt'
MAIN = 'ErbStR_2019.md'
SOURCE_SHA256 = 'cf27a1a4edce887a670bce6ae01dd603dfd4dcd9461a753004d5d21e592822de'
FIRST = 33      # 0-basiert; Zeile 34: „Allgemeine Verwaltungsvorschrift …“
INTRO = 47      # Zeile 48: „I. Einführung“
ANNEX = 27750   # Zeile 27751: „Anlage 1“
LAST = 33483    # Zeile 33484: „4 003“ (letzte Zelle der Anlage 2)

ROMAN = re.compile(r'^(I|II|III)\. (Einführung|Erbschaftsteuer- und Schenkungsteuergesetz|Bewertungsgesetz)$')
PART = re.compile(r'^([A-F])\. (\S.*)$')
GROUP = re.compile(r'^Zu §§? (\d+[a-z]?(?: (?:bis|und) \d+[a-z]?)?) (ErbStG|BewG)((?:\[\d+\])*)$')
RH = re.compile(r'^([RH]) ([EB]) (\d+[a-z]?(?:\.\d+)?)((?:\[\d+\])*)(?: \((\d+)\))?((?:\[\d+\])*)(?: (\S.*))?$')
ANNEX_HEAD = re.compile(r'^Anlage (\d)$')
DEF = re.compile(r'^\[(\d+)\]\s*$')
REF = re.compile(r'\[(\d{1,2})\]')
ABS = re.compile(r'^\((\d+)\)((?:\[\d+\])*)\s')
LIST = re.compile(r'^(\d{1,2}\.(?=[^\s\d.])|\d{1,2}\.(?=\d{1,2}[A-ZÄÖÜ§„])|[a-z]\)(?=\S)|–(?=\S))')
BEISPIEL = re.compile(r'^Beispiel(e?)(?: (\d+))?(?: Abwandlung)?(?: \([^)]{1,120}\))?(?: [^:]{1,120})?:?((?:\[\d+\])*)$')
LOESUNG = re.compile(r'^(Lösung|Abwandlung):?$')
UNBESETZT = re.compile(r'^– unbesetzt –$')
SENT = re.compile(r'(?:(?<=\s)|^)(\d{1,2})(?=[A-ZÄÖÜ§„])')
MARKERS = re.compile(r'\[\d+\]')
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
    assert digest(data) == SOURCE_SHA256, 'Andere Webkopie: Strukturgrenzen neu prüfen.'
    lines = data.decode('utf-8').splitlines()
    assert len(lines) == 33485
    assert lines[FIRST] == 'Allgemeine Verwaltungsvorschrift zur Anwendung des Erbschaftsteuer- und Schenkungsteuerrechts'
    assert lines[FIRST + 1] == '(Erbschaftsteuer-Richtlinien 2019 – ErbStR 2019)[1]'
    assert lines[FIRST + 4] == 'Mit den Erbschaftsteuer-Hinweisen 2019[2]'
    assert lines[FIRST + 12].startswith('Nach Artikel 108 Absatz 7 des Grundgesetzes')
    assert lines[INTRO] == 'I. Einführung'
    assert lines[ANNEX] == 'Anlage 1' and lines[ANNEX + 1] == '(zu R B 160.2 und 163)'
    assert lines[LAST] == '4 003' and not lines[LAST + 1].strip()
    assert lines[32] == 'ErbStR 2019\tErbschaftsteuer-Richtlinien 2019\t\tBund', 'Tab-Metazeile fehlt.'
    assert all(not lines[i].strip() for i in range(LAST + 1, len(lines)))

    def next_index(index):
        index += 1
        while index <= LAST and not lines[index].strip():
            index += 1
        return index

    # Fußnoten: Definitionszeile „[n] “, Text auf den Folgezeilen; jeder Verweis gehört zur
    # nächsten folgenden Definition derselben Nummer. Die Nummerierung beginnt je Block neu.
    definitions = defaultdict(list)
    for index in range(FIRST, LAST + 1):
        match = DEF.fullmatch(lines[index])
        if match:
            definitions[match[1]].append(index)
    definition_lines = {i for values in definitions.values() for i in values}
    footnote_text_lines = {i + 1 for i in definition_lines}
    references = {}
    for index in range(FIRST, LAST + 1):
        if index in definition_lines:
            continue
        for ordinal, match in enumerate(REF.finditer(lines[index])):
            candidates = definitions[match[1]]
            pos = bisect_right(candidates, index)
            assert pos < len(candidates), (index + 1, match[1])
            references[(index, ordinal)] = candidates[pos]
    assert set(references.values()) == definition_lines, 'Definition ohne Verweis.'
    assert all(count == 1 for count in Counter(references.values()).values()), 'Definition mehrfach referenziert.'
    assert len(references) == 224, len(references)
    official_notes = sum(1 for i in definition_lines if lines[i + 1].startswith('[Amtl. Anm.:]'))

    # Gliederung: Hauptteile, Teilüberschriften des BewG-Teils, Paragraphengruppen, R-/H-Blöcke, Anlagen.
    heads = {}
    romans, parts, groups, sections, annexes = {}, {}, {}, {}, {}
    for index in range(INTRO, LAST + 1):
        text = lines[index]
        if not text.strip() or index in definition_lines or index in footnote_text_lines:
            continue
        if ROMAN.match(text):
            romans[index] = 'teil-' + ROMAN.match(text)[1].lower()
        elif PART.match(text) and index > 17264 and index < ANNEX and lines[index + 1].strip():
            parts[index] = 'teil-iii-' + PART.match(text)[1].lower()
        elif GROUP.match(text):
            match = GROUP.match(text)
            groups[index] = slug('zu-' + match[1] + '-' + match[2])
        elif RH.match(text) and index < ANNEX:
            match = RH.match(text)
            assert (match[7] is None) == (match[1] == 'H'), (index + 1, text)
            anchor = slug(match[1] + '-' + match[2] + '-' + match[3])
            if match[5]:
                anchor += '-abs-' + match[5]
            sections[index] = anchor
        elif index >= ANNEX and ANNEX_HEAD.match(text) and lines[index + 1].startswith('(zu R B '):
            annexes[index] = 'anlage-' + ANNEX_HEAD.match(text)[1]
    assert list(romans) == [47, 66, 17264], romans
    assert list(parts) == [17265, 17711, 18368, 18889, 22316, 27563], parts
    assert len(groups) == 90 and len(set(groups.values())) == 90
    assert len(sections) == 529 and len(set(sections.values())) == 529
    assert list(annexes) == [27750, 27814], annexes
    for mapping in (romans, parts, groups, sections, annexes):
        heads.update(mapping)
    kinds = Counter(lines[i][:3] for i in sections)
    assert kinds == Counter({'R E': 146, 'H E': 137, 'R B': 135, 'H B': 111}), kinds
    assert not any(RH.match(lines[i]) for i in range(FIRST, INTRO))
    assert sum(1 for i in range(INTRO, LAST + 1) if BEISPIEL.match(lines[i])) == 243
    assert sum(1 for i in range(INTRO, LAST + 1) if i not in heads and re.match(r'^R [EB] \d', lines[i])) == 1  # Fußnotentext Zeile 18460

    # Zwischenüberschriften: Die Kopie setzt nach einer Überschrift keine Leerzeile. Eine Zeile,
    # der unmittelbar eine nichtleere Zeile folgt, ist deshalb eine Überschrift der Kopie.
    def heading_candidate(index):
        text = lines[index]
        if index in heads or index in definition_lines or index in footnote_text_lines:
            return False
        if index >= LAST or not text.strip() or not lines[index + 1].strip():
            return False
        if any(start <= index < end for start, end in TABLE_RANGES.items()):
            return False
        if LIST.match(text) or ABS.match(text) or BEISPIEL.match(text):
            return False
        core = MARKERS.sub('', text).strip()
        return len(core) < 120 and '→' not in core and not core.endswith((',', ';'))

    subheadings = {i for i in range(INTRO, LAST + 1) if heading_candidate(i)}
    for index in subheadings:
        assert index + 1 not in heads, index + 1

    def structural(index):
        text = lines[index]
        return bool(index in heads or index in definition_lines or index in subheadings or index in TABLE_RANGES
                    or LIST.match(text) or ABS.match(text) or BEISPIEL.match(text) or LOESUNG.match(text)
                    or UNBESETZT.match(text))

    def cell_like(index):
        # Kurze Zeile ohne Satzschluss; Abkürzungszellen wie „Jg.“ (kein Leerzeichen) zählen als Zelle.
        text = lines[index].strip()
        return len(text) < 80 and not (text.endswith(('.', ':', ';')) and ' ' in text) and not structural(index)

    def text_segment(value):
        return SENT.sub(lambda m: '<sup>' + m[1] + '</sup>', escape(value))

    def inline(index, heading=False, list_item=False):
        line = lines[index]
        if index in definition_lines:
            return f'<a id="fn-z{index + 1}"></a><strong>{escape(line.strip())}</strong>'
        if list_item:
            line = LIST.sub(lambda m: m[1] + ' ', line, count=1)
        parts_ = []
        cursor = 0
        for ordinal, match in enumerate(REF.finditer(line)):
            parts_.append(text_segment(line[cursor:match.start()]))
            resolved = references[(index, ordinal)]
            parts_.append(f'<a href="#fn-z{resolved + 1}">[{match[1]}]</a>')
            cursor = match.end()
        parts_.append(text_segment(line[cursor:]))
        value = ''.join(parts_)
        if heading:
            value = value.replace('*', '\\*').replace('_', '\\_')
        return value

    outputs = []
    records = []
    coverage = Counter()
    decisions = []
    tables = []
    anchor_used = Counter()

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

    def claim(anchor):
        anchor_used[anchor] += 1
        return anchor if anchor_used[anchor] == 1 else None

    def paragraph(a, b, kind='absatz', css=None, anchor=None, strong=False):
        opening = '<p>' if css is None else f'<p class="{css}">'
        content = '<br>\n'.join(inline(i) for i in range(a, b) if lines[i].strip())
        if strong:
            content = '<strong>' + content + '</strong>'
        prefix = f'<a id="{anchor}"></a>' if anchor else ''
        add(a, b, opening + prefix + content + '</p>', kind)

    def heading(index, level, anchor=None, kind='ueberschrift'):
        body = (f'<a id="{anchor}"></a>\n\n' if anchor else '') + '#' * level + ' ' + inline(index, heading=True)
        add(index, index + 1, body, kind)
        decisions.append({'zeile': index + 1, 'art': kind, 'ebene': level, 'sprungmarke': anchor, 'text': lines[index]})

    def footnote_block(a, b):
        groups_ = []
        for index in range(a, b):
            if not lines[index].strip():
                continue
            if groups_ and groups_[-1][-1] == index - 1:
                groups_[-1].append(index)
            else:
                groups_.append([index])
        assert len(groups_) <= 3 and sum(len(g) for g in groups_) <= 4, (a + 1, b)
        add(a, b, '\n'.join('<p>' + '<br>\n'.join(inline(i) for i in group) + '</p>' for group in groups_), 'fussnote')

    def footnote_end(index):
        end = index + 1
        while end <= LAST and end not in definition_lines and end not in heads and end not in TABLE_RANGES:
            end += 1
        while not lines[end - 1].strip():
            end -= 1
        return end

    counts = {'hauptteile': len(romans), 'teilueberschriften_bewg': len(parts), 'paragraphengruppen': len(groups),
              'richtlinien_erbstg': kinds['R E'], 'hinweise_erbstg': kinds['H E'],
              'richtlinien_bewg': kinds['R B'], 'hinweise_bewg': kinds['H B'], 'anlagen': len(annexes)}
    outputs.append('# Erbschaftsteuer-Richtlinien 2019 mit Erbschaftsteuer-Hinweisen 2019\n\n'
        '**Quellenstand: Richtlinien und Hinweise vom 16. Dezember 2019 (BStBl. I 2019 Sondernummer 1) · '
        'Übernahme und Quellenabgleich: 9. September 2026.**\n\n'
        'Allgemeine Verwaltungsvorschrift zur Anwendung des Erbschaftsteuer- und Schenkungsteuerrechts '
        '(Erbschaftsteuer-Richtlinien 2019 – ErbStR 2019, BStBl. I 2019 Sondernummer 1 S. 2) mit den '
        'Erbschaftsteuer-Hinweisen 2019 (gleich lautende Erlasse der obersten Finanzbehörden der Länder vom '
        '16. Dezember 2019, BStBl. I 2019 Sondernummer 1 S. 151). Grundlage ist die bereitgestellte Textkopie aus '
        'beck-online, die Richtlinien (**R E**, **R B**) und Hinweise (**H E**, **H B**) in ihrer ursprünglichen '
        'Reihenfolge verbindet. Alle kopierten Sachtexte werden unverändert übernommen; Website-Navigation und '
        'Tab-Metazeile bleiben in der [Originalkopie](Quellen/ErbStR_2019_Webkopie.txt) erhalten. Die Fußnoten der '
        f'Webquelle sind verlinkt; von den {len(references)} Fußnoten sind nur die {official_notes} mit „[Amtl. Anm.:]“ '
        'gekennzeichneten amtlich, die übrigen sind Hinweise des Anbieters auf spätere Rechtsänderungen, Erlasse und '
        'Rechtsprechung (Rechtsstand der Anmerkungen bis 2025). Der Richtlinien- und Hinweistext selbst hat den '
        'Stand vom 16. Dezember 2019; die durch das JStG 2020 veranlassten gleich lautenden Ländererlasse vom '
        '13. September 2021 (BStBl. I 2021 S. 1837) und vom 13. Dezember 2021 (BStBl. I 2022 S. 38) sind nur in '
        'Fußnoten der Kopie zitiert und nicht in den Text eingearbeitet. Die mit „Redaktionelle Ergänzung:“ '
        'bezeichnete Fortführung der Anwendungsliste in H E 37 stammt aus der Webquelle, nicht aus dem amtlichen Text. '
        'Die hochgestellten Satznummern geben die Zählung der Kopie wieder.\n\n'
        f'**Struktur:** {counts["hauptteile"]} Hauptteile (I. Einführung, II. Erbschaftsteuer- und Schenkungsteuergesetz, '
        f'III. Bewertungsgesetz mit den Teilen A bis F), {counts["paragraphengruppen"]} Paragraphengruppen („Zu § … ErbStG/BewG“), '
        f'{counts["richtlinien_erbstg"]} Richtlinienblöcke R E, {counts["hinweise_erbstg"]} Hinweisblöcke H E, '
        f'{counts["richtlinien_bewg"]} Richtlinienblöcke R B, {counts["hinweise_bewg"]} Hinweisblöcke H B und '
        f'{counts["anlagen"]} Anlagen. Hauptteile, Gruppen, R-/H-Blöcke, Absätze, nummerierte Punkte in Richtlinien und '
        'Beispiele tragen Sprungmarken. Zwischenüberschriften wurden an der Form der Kopie erkannt (Überschriftzeilen '
        'stehen ohne Leerzeile vor ihrer Folgezeile); alle Entscheidungen stehen in '
        '[Gliederungsentscheidungen.json](Pruefung/Gliederungsentscheidungen.json). In der Kopie abgeflachte Tabellen '
        '(DBA-Übersicht, Berechnungsbeispiele, Vervielfältiger- und Pachtpreisübersichten) bleiben als Textzeilen in '
        'Originalreihenfolge erhalten; nur die Anlagen 1 und 2 sind nach dem am amtlichen PDF geprüften Spaltenaufbau '
        'als Tabellen dargestellt. Die Kopie enthält keine Inhaltsübersicht, keinen Artikel 2 (Aufhebung der ErbStR 2011), '
        'keine Schlussformel und keine Unterschriften des amtlichen Textes; Schreibweisen, Satznummern und mögliche '
        'Kopierfehler sind nicht redaktionell korrigiert.\n\n'
        '[Prüfbericht](Pruefung/Pruefbericht.md) · [Amtlicher Abgleich](Quellen/Onlineabgleich/Abgleich.json) · '
        '[Amtliche ErbStR 2019 (PDF)](Quellen/Onlineabgleich/ErbStR_2019_BMF.pdf) · '
        '[Amtliche ErbStH 2019 (PDF)](Quellen/Onlineabgleich/ErbStH_2019_BMF.pdf)\n\n'
        '## Navigation\n\n[Inhaltsübersicht](#inhaltsuebersicht) · [Erlasstext](#erlasstext) · [Anlagen](#anlagen)')

    # Dokumentkopf: Titel, Fundstelle, zwei Kopffußnoten und Erlassformel.
    heading(FIRST, 2, kind='dokumentkopf')
    paragraph(FIRST + 1, FIRST + 5, 'dokumentkopf')
    assert FIRST + 6 in definition_lines and FIRST + 9 in definition_lines
    footnote_block(FIRST + 6, FIRST + 8)
    footnote_block(FIRST + 9, FIRST + 11)
    paragraph(FIRST + 12, FIRST + 13, 'einleitung')

    # Redaktionell erzeugte Gesamtübersicht (die Kopie enthält keine Inhaltsübersicht).
    toc = []
    for index in sorted(heads):
        label = escape(MARKERS.sub('', lines[index]).strip())
        anchor = heads[index]
        if index in romans:
            depth = 0
        elif index in parts:
            depth = 1
        elif index in groups:
            depth = 2 if index > 17264 else 1
        elif index in sections:
            depth = 3 if index > 17264 else 2
        else:
            depth = 0
            label += ' ' + escape(lines[index + 1])
        toc.append('  ' * depth + f'- <a href="#{anchor}">{label}</a>')
    outputs.append('<a id="inhaltsuebersicht"></a>\n\n## Inhaltsübersicht (redaktionell)\n\n'
                   'Die Webkopie enthält keine Inhaltsübersicht; die Übersicht ist aus den Überschriften der Kopie erzeugt.\n\n'
                   + '\n'.join(toc))
    outputs.append('<a id="erlasstext"></a>')

    section = None       # Sprungmarke des aktuellen R-/H-Blocks bzw. „einfuehrung“
    in_rules = False     # Absatz- und Punktanker nur in Richtlinienblöcken und der Einführung
    abs_scope = None
    nr_scope = None
    index = INTRO
    while index <= LAST:
        text = lines[index]
        if not text.strip():
            index += 1
            continue
        if index == ANNEX:
            outputs.append('<a id="anlagen"></a>')
        if index in TABLE_RANGES:
            end = TABLE_RANGES[index]
            body, description = render_table(index, lines, inline)
            add(index, end, body, 'tabelle')
            description.update({'zeile_von': index + 1, 'zeile_bis': end})
            tables.append(description)
            decisions.append({'zeile': index + 1, 'art': 'tabelle', 'ebene': None, 'sprungmarke': None,
                              'text': lines[index], 'umfang': description})
            index = end
            continue
        if index in romans:
            heading(index, 2, romans[index], 'hauptteil')
            section = 'einfuehrung' if index == INTRO else None
            in_rules = index == INTRO
            abs_scope = nr_scope = None
            index += 1
            continue
        if index in parts:
            heading(index, 3, parts[index], 'teilueberschrift')
            section = None
            index += 1
            continue
        if index in groups:
            heading(index, 4, groups[index], 'paragraphengruppe')
            section = None
            index += 1
            continue
        if index in sections:
            section = sections[index]
            in_rules = text.startswith('R ')
            abs_scope = nr_scope = None
            heading(index, 5, section, 'richtlinie' if in_rules else 'hinweis')
            index += 1
            continue
        if index in annexes:
            section = annexes[index]
            in_rules = False
            abs_scope = nr_scope = None
            heading(index, 2, section, 'anlage')
            index += 1
            continue
        if index in definition_lines:
            end = footnote_end(index)
            footnote_block(index, end)
            index = end
            continue
        if BEISPIEL.match(text):
            match = BEISPIEL.match(text)
            anchor = None
            if section:
                anchor = claim(section + '-beispiel' + ('-' + match[2] if match[2] else ''))
            heading(index, 6, anchor, 'beispiel')
            index += 1
            continue
        if LOESUNG.match(text):
            paragraph(index, index + 1, 'loesung', strong=True)
            decisions.append({'zeile': index + 1, 'art': 'loesung', 'ebene': None, 'sprungmarke': None, 'text': text})
            index += 1
            continue
        if UNBESETZT.match(text):
            paragraph(index, index + 1, 'unbesetzt')
            index += 1
            continue
        if index in subheadings:
            paragraph(index, index + 1, 'zwischenueberschrift', strong=True)
            decisions.append({'zeile': index + 1, 'art': 'zwischenueberschrift', 'ebene': None, 'sprungmarke': None,
                              'text': text, 'signal': 'Folgezeile ohne Leerzeile'})
            index += 1
            continue
        if LIST.match(text):
            items = []
            end = index
            following = index
            while following <= LAST and LIST.match(lines[following]) and following not in heads \
                    and following not in definition_lines and following not in subheadings and following not in TABLE_RANGES:
                items.append(following)
                end = following + 1
                following = next_index(following)
            rendered = []
            for item in items:
                marker = LIST.match(lines[item])[1]
                anchor = None
                if in_rules and section:
                    scope = abs_scope or section
                    if marker[0].isdigit():
                        nr_scope = scope + '-nr-' + marker.rstrip('.')
                        anchor = claim(nr_scope)
                    elif marker[0].isalpha():
                        anchor = claim((nr_scope or scope) + '-bst-' + marker[0])
                prefix = f'<a id="{anchor}"></a>' if anchor else ''
                rendered.append('<li>' + prefix + inline(item, list_item=True) + '</li>')
            add(index, end, '<ul class="original-aufzaehlung" style="list-style:none;padding-left:1.5em">\n'
                + '\n'.join(rendered) + '\n</ul>', 'aufzaehlung')
            index = end
            continue
        if ABS.match(text):
            number = ABS.match(text)[1]
            anchor = None
            if in_rules and section:
                abs_scope = section + '-abs-' + number
                nr_scope = None
                anchor = claim(abs_scope)
            end = index + 1
            while end <= LAST and lines[end].strip() and not structural(end):
                end += 1
            paragraph(index, end, 'absatz_nummeriert', anchor=anchor)
            index = end
            continue
        if cell_like(index):
            cells = [index]
            end = index + 1
            following = next_index(index)
            while following <= LAST and cell_like(following):
                cells.append(following)
                end = following + 1
                following = next_index(following)
            if len(cells) >= 3:
                add(index, end, '<p class="quellzeilen">' + '<br>\n'.join(inline(i) for i in cells) + '</p>',
                    'kurze_quellzeilen')
                index = end
                continue
        end = index + 1
        while end <= LAST and lines[end].strip() and not structural(end):
            end += 1
        paragraph(index, end)
        index = end

    expected_lines = {index for index in range(FIRST, LAST + 1) if lines[index].strip()}
    assert set(coverage) == expected_lines, ('Fehlende/zusätzliche Quellzeilen', sorted(expected_lines - coverage.keys())[:20])
    assert all(value == 1 for value in coverage.values()), 'Doppelt übernommene Quellzeilen.'
    output = '\n\n'.join(outputs) + '\n'
    (BASE / MAIN).write_text(output, encoding='utf-8')
    (BASE / 'Pruefung/Quellbloecke.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (BASE / 'Pruefung/Gliederungsentscheidungen.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    kinds_out = Counter(record['art'] for record in records)
    ids = re.findall(r'<a id="([^"]+)"></a>', output)
    assert len(ids) == len(set(ids)), 'Doppelte Sprungmarken.'
    report = {'pruefung_erfolgreich': True, 'sha256_original_quelle': digest(data),
              'sha256_markdown': digest((BASE / MAIN).read_bytes()),
              'quellzeilen_gesamt': len(lines), 'quellzeilen_sachinhalt_nichtleer': len(coverage),
              'quellbloecke': len(records), **counts,
              'gliederungspositionen': len(sections), 'fussnoten': len(references), 'fussnoten_amtlich': official_notes,
              'beispiele': kinds_out['beispiel'], 'zwischenueberschriften': kinds_out['zwischenueberschrift'],
              'loesungen': kinds_out['loesung'], 'unbesetzte_positionen': kinds_out['unbesetzt'],
              'nummerierte_absaetze': kinds_out['absatz_nummeriert'], 'aufzaehlungen': kinds_out['aufzaehlung'],
              'kurze_quellzeilenbloecke': kinds_out['kurze_quellzeilen'], 'tabellen': kinds_out['tabelle'],
              'tabellenbeschreibung': tables,
              'sprungmarken_absaetze': sum(1 for i in ids if '-abs-' in i and not i.startswith('h-') and '-nr-' not in i and '-bst-' not in i),
              'sprungmarken_nummerierte_punkte': sum(1 for i in ids if '-nr-' in i or '-bst-' in i),
              'sprungmarken_beispiele': sum(1 for i in ids if '-beispiel' in i),
              'satznummern': output.count('<sup>'),
              'uebernahme': f'Alle nichtleeren Sachtextzeilen {FIRST + 1} bis {LAST + 1} genau einmal; vollständiger sichtbarer Textrückvergleich pro Quellblock.',
              'einschraenkung': 'Vollständigkeit der übernommenen Textkopie geprüft. Die Kopie enthält keine Inhaltsübersicht, keinen Artikel 2, keine Schlussformel/Unterschriften der ErbStR 2019 und keinen Länderministerienblock der ErbStH 2019. Gliederungsebenen, Zwischenüberschriften und die Zuordnung abgeflachter Tabellenzeilen sind dokumentierte Strukturentscheidungen; nur Anlage 1 und 2 sind nach amtlich geprüftem Spaltenaufbau als Tabellen gesetzt.'}
    (BASE / 'Pruefung/Vollstaendigkeitspruefung.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
