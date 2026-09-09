"""Strukturiert die bereitgestellte ErbStDV-Webkopie mit vollständigem Textrückvergleich.

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
SOURCE = BASE / 'Quellen/ErbStDV_Webkopie.txt'
MAIN = 'ErbStDV.md'
SOURCE_SHA256 = 'dbb708bb0865ed7a3edd3de4a141eb4d6af7cef9f2cd14a7f22fc493de3c7c08'
FIRST = 1      # 0-basiert; Zeile 2: „Erbschaftsteuer-Durchführungsverordnung“ (Zeile 1 ist die Tab-Metazeile)
BODY = 11      # Zeile 12: „Zu § 33 ErbStG“
ANNEX = 284    # Zeile 285: „Muster 1[1]“
LAST = 1112    # Zeile 1113: Fußnotentext zu Muster 6 (letzte Zeile, ohne Zeilenende)

GROUP = re.compile(r'^Zu § (\d+) ErbStG$')
CHAPTER = re.compile(r'^Schlußvorschriften$')
PARA = re.compile(r'^§ (\d+)((?:\[\d+\])*) (\S.*)$')
PARA_NOT_TITLE = re.compile(r'^(?:Abs\.|Satz|Sätze|Nr\.|neu gef\.|geänd\.|eingef\.|angef\.)')
ABS = re.compile(r'^\((\d+)\)((?:\[\d+\])*) ')
LIST = re.compile(r'^(\d{1,2}[a-z]?\.)((?:\[\d+\])*)(?=[^\s\d.\[])')
DEF = re.compile(r'^\[(\d+)\]\s*$')
REF = re.compile(r'\[(\d{1,2})\]')
SENT = re.compile(r'(?:(?<=\s)|^)(\d{1,2})(?=[A-ZÄÖÜ§„])')
MUSTER = re.compile(r'^Muster (\d)((?:\[\d+\])*)$')
MUSTER_REF = re.compile(r'^\((?:zu )?§ (\d+) ErbStDV\)$')
FORM_TITLE = re.compile(r'^(?:Anzeige|Totenliste|Fehlanzeige|Anleitung für .+)$')
PAGE = re.compile(r'^\(Seite \d\)$')
FORM_POS = re.compile(r'^\d+\.$')
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


def main():
    data = SOURCE.read_bytes()
    assert digest(data) == SOURCE_SHA256, 'Andere Webkopie: Strukturgrenzen neu prüfen.'
    lines = data.decode('utf-8').splitlines()
    assert len(lines) == 1113 and not data.endswith(b'\n'), 'Andere Webkopie: Strukturgrenzen neu prüfen.'
    assert lines[0].startswith('ErbStDV\t[Erbschaftsteuer-Durchführungsverordnung]\tText gilt vom 30.12.2025')
    assert lines[FIRST] == 'Erbschaftsteuer-Durchführungsverordnung'
    assert lines[FIRST + 1] == '(ErbStDV)[1]'
    assert lines[FIRST + 5].startswith('Zuletzt geändert durch Art. 11 ')
    assert DEF.fullmatch(lines[8]) and lines[9] == 'Zur Anwendung siehe § 12.'
    assert lines[BODY] == 'Zu § 33 ErbStG'
    assert lines[ANNEX] == 'Muster 1[1]'
    assert lines[LAST].startswith('Muster 6 geänd. durch VO v. 17.11.2010')

    def next_index(index):
        index += 1
        while index <= LAST and not lines[index].strip():
            index += 1
        return index

    def prev_index(index):
        index -= 1
        while index > 0 and not lines[index].strip():
            index -= 1
        return index

    # Gliederung: Gruppen, Abschnitt, Paragraphen (nur wenn die Vorzeile keine Fußnotendefinition ist), Muster.
    groups = {}
    for index in range(BODY, ANNEX):
        if GROUP.match(lines[index]):
            groups[index] = 'zu-' + GROUP.match(lines[index])[1] + '-erbstg'
        elif CHAPTER.match(lines[index]):
            groups[index] = 'schlussvorschriften'
    assert list(groups) == [11, 66, 262], groups
    sections = {}
    for index in range(BODY, ANNEX):
        match = PARA.match(lines[index])
        if match and not DEF.fullmatch(lines[prev_index(index)]) and not PARA_NOT_TITLE.match(match[3]):
            sections[index] = 'par-' + match[1]
    assert [int(a.split('-')[1]) for a in sections.values()] == list(range(1, 14)), sections
    assert sum(1 for i in range(BODY, ANNEX) if PARA.match(lines[i])) == 13 + 33, 'Fußnotentexte mit § am Anfang neu zählen.'
    annexes = {index: 'muster-' + MUSTER.match(lines[index])[1]
               for index in range(ANNEX, LAST + 1) if MUSTER.match(lines[index])}
    assert list(annexes) == [284, 432, 596, 788, 838, 1010], annexes
    assert all(MUSTER_REF.match(lines[index + 1]) for index in annexes)
    assert not any(PARA.match(lines[i]) or GROUP.match(lines[i]) for i in range(FIRST, BODY))
    absatz_lines = [i for i in range(BODY, ANNEX) if ABS.match(lines[i])]
    assert len(absatz_lines) == 28, len(absatz_lines)

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
    assert len(references) == 40, len(references)
    assert all(lines[i + 1].strip() and (i + 2 > LAST or not lines[i + 2].strip()) for i in all_definitions), \
        'Fußnotentext ist nicht genau eine Zeile.'

    def structural(index):
        text = lines[index]
        return bool(index in groups or index in sections or index in annexes or DEF.fullmatch(text)
                    or ABS.match(text) or LIST.match(text))

    def text_segment(value):
        return SENT.sub(lambda m: '<sup>' + m[1] + '</sup>', escape(value))

    sentence_numbers = Counter()

    def inline(index, heading=False, list_item=False, bold_position=False):
        line = lines[index]
        definition = DEF.fullmatch(line)
        if definition:
            return f'<a id="fn-z{index + 1}"></a><strong>{escape(line.strip())}</strong>'
        if list_item:
            # Angeklebtes Aufzählungszeichen („1.wenn“, „2.[2]wenn“) bleibt Text; nur ein Leerzeichen wird eingefügt.
            line = LIST.sub(lambda m: m[1] + m[2] + ' ', line, count=1)
        parts = []
        cursor = 0
        for ordinal, match in enumerate(REF.finditer(line)):
            parts.append(text_segment(line[cursor:match.start()]))
            resolved = references[(index, ordinal)]
            parts.append(f'<a href="#fn-z{resolved + 1}">[{match[1]}]</a>')
            cursor = match.end()
        parts.append(text_segment(line[cursor:]))
        value = ''.join(parts)
        sentence_numbers[index] += value.count('<sup>')
        if bold_position:
            value = f'<strong>{value}</strong>'
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

    def paragraph(a, b, kind='absatz', css=None):
        opening = '<p>' if css is None else f'<p class="{css}">'
        add(a, b, opening + '<br>\n'.join(inline(i) for i in range(a, b) if lines[i].strip()) + '</p>', kind)

    def heading(index, level, anchor=None, kind='ueberschrift'):
        if anchor:
            outputs.append(f'<a id="{anchor}"></a>')
        add(index, index + 1, '#' * level + ' ' + inline(index, heading=True), kind)
        decisions.append({'zeile': index + 1, 'art': kind, 'ebene': level, 'sprungmarke': anchor, 'text': lines[index]})

    def block_end(index, limit):
        end = index + 1
        while end < limit and lines[end].strip() and not structural(end):
            end += 1
        return end

    outputs.append('# Erbschaftsteuer-Durchführungsverordnung (ErbStDV)\n\n'
        '**Quellenstand der Kopie: „Text gilt vom 30.12.2025 bis unbestimmt“, zuletzt geändert durch Art. 11 G v. 22.6.2026 '
        '(BGBl. 2026 I Nr. 192) · Übernahme und amtlicher Abgleich: 9. September 2026.**\n\n'
        'Rechtsverordnung des Bundes vom 8. September 1998 (BGBl. I S. 2658) zu §§ 33 und 34 ErbStG. Grundlage ist die '
        'bereitgestellte Textkopie aus beck-online. Alle kopierten Sachtexte werden unverändert übernommen; die Tab-Metazeile '
        'der Kopie bleibt in der [Originalkopie](Quellen/ErbStDV_Webkopie.txt) erhalten. Die Fußnoten der Webquelle sind '
        'verlinkt; sie enthalten die Änderungsnachweise des Anbieters und sind nicht Teil des amtlichen Verordnungstexts. '
        'Die hochgestellten Satznummern geben die Zählung der Kopie wieder; die amtliche Fassung enthält keine Satznummern.\n\n'
        f'**Struktur:** {len(groups)} Gliederungsgruppen („Zu § 33 ErbStG“, „Zu § 34 ErbStG“, „Schlußvorschriften“), '
        f'{len(sections)} Paragraphen mit {len(absatz_lines)} nummerierten Absätzen und {len(annexes)} Muster (Vordrucke). '
        'Paragraphen, Absätze und nummerierte Aufzählungspunkte tragen Sprungmarken. Angeklebte Aufzählungszeichen der Kopie '
        '(„1.wenn …“) bleiben Text; nur ein Leerzeichen wird eingefügt. Die Muster 1 bis 6 sind in der Kopie zellenweise '
        'abgeflacht (jede Zelle eine Zeile); sie bleiben als Formularblöcke in Originalreihenfolge erhalten, verlorene '
        'Spaltenzuordnungen werden nicht rekonstruiert. Schreibweisen, Sonderleerzeichen und mögliche Kopierfehler sind nicht '
        'redaktionell korrigiert; Abweichungen vom amtlichen Wortlaut sind im Prüfbericht dokumentiert.\n\n'
        '[Prüfbericht](Pruefung/Pruefbericht.md) · [Amtlicher Wortlautabgleich](Quellen/Onlineabgleich/Abgleich.json) · '
        '[Amtliche XML-Gesamtausgabe](Quellen/Onlineabgleich/BJNR265800998.xml) · '
        '[Amtliche PDF-Gesamtausgabe](Quellen/Onlineabgleich/GII_ErbStDV.pdf)\n\n'
        '## Navigation\n\n[Inhaltsübersicht](#inhaltsuebersicht) · [Verordnungstext](#verordnungstext) · [Muster](#muster)')

    # Dokumentkopf mit Fundstelle, Änderungsvermerk und Kopffußnote.
    heading(FIRST, 2, kind='dokumentkopf')
    paragraph(FIRST + 1, FIRST + 6, 'dokumentkopf')
    index = FIRST + 6
    while index < BODY:
        if not lines[index].strip():
            index += 1
            continue
        end = block_end(index, BODY)
        paragraph(index, end, 'fussnote' if DEF.fullmatch(lines[index]) else 'einleitung')
        index = end

    # Redaktionelle Gesamtübersicht.
    rows = ['| Position | Überschrift |', '| --- | --- |']
    for index in sorted(groups.keys() | sections.keys()):
        if index in groups:
            rows.append(f'| **[{escape(lines[index])}](#{groups[index]})** | |')
        else:
            match = PARA.match(lines[index])
            rows.append(f'| [§ {match[1]}](#{sections[index]}) | {escape(MARKERS.sub("", match[3]).strip())} |')
    for index, anchor in annexes.items():
        rows.append(f'| [Muster {MUSTER.match(lines[index])[1]}](#{anchor}) | {escape(lines[index + 1])} |')
    outputs.append('<a id="inhaltsuebersicht"></a>\n\n## Inhaltsübersicht (redaktionell)\n\n'
                   'Die Webkopie enthält kein Inhaltsverzeichnis; die Übersicht ist aus den Überschriften erzeugt.\n\n'
                   + '\n'.join(rows))
    outputs.append('<a id="verordnungstext"></a>\n\n## Verordnungstext')

    # Verordnungstext.
    anchors_used = set()
    owner = None
    current = None
    kinds_extra = Counter()
    index = BODY
    while index < ANNEX:
        text = lines[index]
        if not text.strip():
            index += 1
            continue
        if index in groups:
            heading(index, 3, groups[index], 'gliederungsgruppe')
            owner = current = None
            index += 1
            continue
        if index in sections:
            owner = current = sections[index]
            heading(index, 4, owner, 'paragraph')
            index += 1
            continue
        if DEF.fullmatch(text):
            end = block_end(index, ANNEX)
            paragraph(index, end, 'fussnote')
            index = end
            continue
        match = ABS.match(text)
        if match:
            assert owner, index + 1
            current = owner + '-abs-' + match[1]
            assert current not in anchors_used, current
            anchors_used.add(current)
            outputs.append(f'<a id="{current}"></a>')
            end = block_end(index, ANNEX)
            paragraph(index, end, 'absatz')
            index = end
            continue
        if LIST.match(text):
            assert current, index + 1
            items = [index]
            end = index + 1
            while True:
                following = next_index(end - 1)
                if following < ANNEX and LIST.match(lines[following]):
                    items.append(following)
                    end = following + 1
                else:
                    break
            entries = []
            for item in items:
                number = LIST.match(lines[item])[1].rstrip('.')
                anchor = current + '-nr-' + number
                assert anchor not in anchors_used, anchor
                anchors_used.add(anchor)
                entries.append(f'<li id="{anchor}">' + inline(item, list_item=True) + '</li>')
            add(index, end, '<ul class="original-aufzaehlung" style="list-style:none;padding-left:1.5em">\n'
                + '\n'.join(entries) + '\n</ul>', 'aufzaehlung')
            kinds_extra['aufzaehlungspunkte'] += len(items)
            index = end
            continue
        # Absatztext ohne Absatznummer (Paragraphen ohne Absätze) oder Fortsetzung nach einer Aufzählung.
        end = block_end(index, ANNEX)
        paragraph(index, end, 'absatztext')
        index = end

    # Muster 1 bis 6: zellenweise abgeflachte Vordrucke als Formularblöcke.
    outputs.append('<a id="muster"></a>\n\n## Muster (Anlagen)\n\n'
                   'Die Vordrucke sind in der Kopie zellenweise abgeflacht; jede Zelle steht auf einer eigenen Zeile. '
                   'Die Blöcke folgen den Positionsnummern und Binnentiteln der Kopie; Spaltenköpfe, Spaltennummern, '
                   'Punktlinien und Ankreuzkästchen bleiben Textzeilen in Originalreihenfolge.')
    index = ANNEX
    while index <= LAST:
        text = lines[index]
        if not text.strip():
            index += 1
            continue
        if index in annexes:
            heading(index, 3, annexes[index], 'anlage')
            index += 1
            continue
        if MUSTER_REF.match(text):
            paragraph(index, index + 1, 'anlage_bezug', 'anlage-bezug')
            index += 1
            continue
        if DEF.fullmatch(text):
            end = block_end(index, LAST + 1)
            paragraph(index, end, 'fussnote')
            index = end
            continue
        if FORM_TITLE.match(text):
            heading(index, 4, kind='formulartitel')
            index += 1
            continue
        if PAGE.match(text):
            add(index, index + 1, '<p class="seitenmarker">' + inline(index) + '</p>', 'seitenmarker')
            decisions.append({'zeile': index + 1, 'art': 'seitenmarker', 'ebene': None, 'sprungmarke': None, 'text': text})
            index += 1
            continue
        # Formularblock bis zur nächsten Positionsnummer, zum nächsten Binnentitel, Seitenmarker oder zur Fußnote.
        end = index + 1
        last_content = index
        while end <= LAST:
            following = lines[end]
            if following.strip():
                if (FORM_POS.match(following) or FORM_TITLE.match(following) or PAGE.match(following)
                        or DEF.fullmatch(following) or end in annexes):
                    break
                last_content = end
            end += 1
        end = last_content + 1
        cells = [i for i in range(index, end) if lines[i].strip()]
        body = '<p class="formular">' + '<br>\n'.join(
            inline(i, bold_position=bool(FORM_POS.match(lines[i]))) for i in cells) + '</p>'
        add(index, end, body, 'formularblock')
        decisions.append({'zeile': index + 1, 'art': 'formularblock', 'ebene': None, 'sprungmarke': None,
                          'zeile_bis': end, 'zellen': len(cells), 'text': text})
        index = end

    expected_lines = {index for index in range(FIRST, LAST + 1) if lines[index].strip()}
    assert set(coverage) == expected_lines, ('Fehlende/zusätzliche Quellzeilen', sorted(expected_lines - coverage.keys())[:20])
    assert all(value == 1 for value in coverage.values()), 'Doppelt übernommene Quellzeilen.'
    output = '\n\n'.join(outputs) + '\n'
    ids = re.findall(r'id="([^"]+)"', output)
    assert len(ids) == len(set(ids)), 'Doppelte Sprungmarken.'
    (BASE / MAIN).write_text(output, encoding='utf-8')
    (BASE / 'Pruefung/Quellbloecke.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (BASE / 'Pruefung/Gliederungsentscheidungen.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    kinds = Counter(record['art'] for record in records)
    total_sentences = sum(sentence_numbers.values())
    report = {'pruefung_erfolgreich': True, 'sha256_original_quelle': digest(data),
              'sha256_markdown': digest((BASE / MAIN).read_bytes()),
              'quellzeilen_gesamt': len(lines), 'quellzeilen_sachinhalt_nichtleer': len(coverage),
              'quellbloecke': len(records), 'gliederungsgruppen': len(groups), 'gliederungspositionen': len(sections),
              'absaetze': kinds['absatz'], 'absatztexte_ohne_nummer': kinds['absatztext'],
              'aufzaehlungen': kinds['aufzaehlung'], 'aufzaehlungspunkte': kinds_extra['aufzaehlungspunkte'],
              'satznummern': total_sentences, 'zeilen_mit_satznummern': sum(1 for v in sentence_numbers.values() if v),
              'anlagen': len(annexes), 'fussnoten': len(references),
              'formularbloecke': kinds['formularblock'], 'formulartitel': kinds['formulartitel'],
              'seitenmarker': kinds['seitenmarker'], 'sprungmarken': len(ids),
              'sprungmarken_absaetze_und_nummern': len(anchors_used),
              'uebernahme': f'Alle nichtleeren Sachtextzeilen {FIRST + 1} bis {LAST + 1} genau einmal; vollständiger sichtbarer Textrückvergleich pro Quellblock. Zeile 1 (Tab-Metazeile) wird nicht als Text übernommen.',
              'einschraenkung': 'Vollständigkeit der übernommenen Textkopie geprüft. Der Wortlautvergleich mit der amtlichen XML-Gesamtausgabe von Gesetze im Internet ist in Quellen/Onlineabgleich/Abgleich.json und Wortlautabgleich.json dokumentiert (Pruefung/wortlautabgleich.py). Die Blockbildung der abgeflachten Muster ist eine redaktionelle Strukturentscheidung.'}
    (BASE / 'Pruefung/Vollstaendigkeitspruefung.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
