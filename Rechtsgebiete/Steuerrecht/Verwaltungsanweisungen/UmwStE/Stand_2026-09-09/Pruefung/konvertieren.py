"""Strukturiert die bereitgestellte UmwStE-2025-Webkopie mit vollständigem Textrückvergleich.

Jede Zielzeile stammt aus einem Quellblock der Textkopie. Der sichtbare Text des
gerenderten Markdown muss nach Entfernung von Leerraum zeichengenau mit dem
Quellblock übereinstimmen. Es wird nichts berichtigt, ergänzt oder weggelassen.
Die Kopie enthält keine Fußnotenverweise und keine Satznummern; beide Mechanismen
der AEAO-Vorlage entfallen deshalb. Die Zuordnung der Fußnoten ist redaktionell
erschlossen (fussnoten.py) und wird als solche gekennzeichnet.
"""
from collections import Counter
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

from markdown_it import MarkdownIt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fussnoten import eintraege as fussnoten_eintraege  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'Quellen/UmwStE_2025_Webkopie.txt'
MAIN = 'UmwStE_2025.md'
SHA_SOURCE = '251239a3caa3d78675c3b0d0e2da8ff828ed04c58377554c2c4c1739c4e3254b'
META = 1        # 0-basiert; Zeile 2: Tab-getrennte beck-online-Metazeile (nicht übernommen)
TITLE = 2       # Zeile 3: „Schreiben betr. Anwendung des Umwandlungssteuergesetzes …“
INTRO = 8       # Zeile 9: Einleitungssatz
TOC = 10        # Zeile 11: „Inhaltsverzeichnis“; Zeile 12: Spaltenkopf „Rn.“
TOC_END = 1352  # exklusiv; Zeile 1353 leer
BODY = 1353     # Zeile 1354: „Erstes Kapitel: Anwendungsregelungen“
LAST = 7495     # Zeile 7496: letzter Beispielsatz zu Rn. K.19
FN = 7497       # Zeile 7498: „[1] “
END = 7777      # Zeile 7778: „BeckVerw 574870.zurück zum Text“

RN = re.compile(r'^(?!31\.12)((?:\d{2}|E \d{2}|Org|K|S)\.\d{2}[a-z]?(?: bis 27\.11)?)')
RN_FIRST = re.compile(r'^((?:\d{2}|E \d{2}|Org|K|S)\.\d{2}[a-z]?)')
LEVELS = [
    ('kapitel', re.compile(r'^(?:Erstes|Zweites) Kapitel: \S'), 2),
    ('teil', re.compile(r'^(?:Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebter|Achter|Neunter|Zehnter) Teil\. \S|^Besonderer Teil zum UmwStG$'), 3),
    ('buchstabe', re.compile(r'^[A-H]\. \S'), 4),
    ('roemisch', re.compile(r'^[IVX]+a?\. \S'), 5),
    ('arabisch', re.compile(r'^\d{1,2}\. (?!Schritt$)\S'), 6),
    ('kleinbuchstabe', re.compile(r'^[a-e]\) \S'), 7),
    ('doppelbuchstabe', re.compile(r'^[a-e]{2}\) \S'), 8),
    ('klammerziffer', re.compile(r'^\(\d\) \S'), 9),
]
DEF = re.compile(r'^\[(\d+)\] $')
BEISPIEL = re.compile(r'^(?:(?:Gegen)?Beispiel(?: \d+)?(?: \([^)]+\)| zu [^:]+)?|Lösung(?: Abwandlung(?: \d)?)?|Abwandlung(?: \d)?):$')
LIST = re.compile(r'^(–(?=\S)|[a-e]{1,2}\)(?=\S)|\d\.(?=[A-Za-zÄÖÜäöü]))')
NAVIGATION = 'zurück zum Text'
# Zeilen nach manueller Prüfung (0-basiert). Zeile 6645 ist Aufzählungspunkt „b) …“ mit Leerzeichen
# (Gegenstück Zeile 6631 „a)In den Fällen …“), kein Gliederungstitel.
LIST_SPACED = {6644}
# Strichzeilen, die Zwischenüberschriften sind (Großbuchstabe, kein Satzende; in der PDF Aufzählungszeichen ● vor fett gesetztem Titel).
DASH_HEADINGS = {2704, 2710, 3005, 3009, 3015, 3023, 3027, 3033, 3039, 3043, 3047}
# Zwischentitel mit Doppelpunkt in Lösungen (Beteiligtenbezeichnungen, Feststellungsblock).
COLON_TITLES = {2895, 2901, 2909, 4038, 4230, 4434, 4630}
# Inhaltsverzeichniseinträge, deren Titel vom Text abweicht (Index der Bezeichnungszeile -> Index der Textüberschrift).
TOC_TITLE_DIFFERENCES = {46: 1378, 126: 2814, 639: 5077, 969: 6208}
# Amtliche Seitendarstellungen (PDF vom 2.1.2025) der in der Kopie abgeflachten Umwandlungsmatrizen; Randnummer -> PDF-Seiten.
SUPPLEMENTS = {'01.10': [11], '01.12': [11, 12], '01.17': [12], '01.19': [13]}
IMAGE = 'Quellen/Abbildungen/BMF_2025-01-02_Seite-{}.png'
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


def rn_anchors(label):
    if label.startswith('27.09 bis 27.11'):
        return ['rn-27-09', 'rn-27-10', 'rn-27-11']
    return ['rn-' + slug(label)]


def main():
    data = SOURCE.read_bytes()
    assert digest(data) == SHA_SOURCE, 'Andere Webkopie: Strukturgrenzen neu prüfen.'
    lines = data.decode('utf-8').splitlines()
    assert len(lines) == 7778 and END == len(lines) - 1
    assert lines[0] == '' and lines[META].startswith('[BMF 2.1.2025 IV C 2 - S 1978/00035/020/040]\t')
    assert lines[TITLE].startswith('Schreiben betr. Anwendung des Umwandlungssteuergesetzes')
    assert lines[TITLE + 1] == 'Vom 2. Januar 2025' and lines[TITLE + 4].startswith('Geänd. durch BMF v. 1.8.2025')
    assert lines[7] == '' and lines[INTRO].startswith('Unter Bezugnahme') and lines[9] == ''
    assert lines[TOC] == 'Inhaltsverzeichnis' and lines[TOC + 1] == 'Rn.' and lines[TOC_END] == ''
    assert lines[BODY] == 'Erstes Kapitel: Anwendungsregelungen'
    assert lines[LAST].startswith('A verschmilzt Anfang 2025') and lines[LAST + 1] == ''
    assert lines[FN] == '[1] ' and lines[END].startswith('BeckVerw 574870.')
    assert all(lines[i].strip() == '' for i in (1352,)) and lines[TOC_END + 1] == lines[BODY]
    assert lines[6644].startswith('b) In den Fällen des § 23 Abs. 3 Satz 1 Nr. 2 UmwStG')
    assert all(lines[i].startswith('–') and lines[i][1:2].isupper() for i in DASH_HEADINGS)
    assert all(lines[i].endswith(':') for i in COLON_TITLES)

    def next_index(index):
        index += 1
        while index <= LAST and not lines[index].strip():
            index += 1
        return index

    def heading_of(index):
        text = lines[index]
        if index in LIST_SPACED:
            return None
        for kind, pattern, level in LEVELS:
            if pattern.match(text):
                return kind, level
        return None

    def is_list_item(index):
        return index in LIST_SPACED or (bool(LIST.match(lines[index])) and index not in DASH_HEADINGS)

    def structural(index):
        return bool(RN.match(lines[index]) or heading_of(index) or BEISPIEL.match(lines[index])
                    or index in DASH_HEADINGS or index in COLON_TITLES or is_list_item(index))

    def cell_like(index, inside_run=False):
        text = lines[index].strip()
        if not text or len(text) >= 80 or text.endswith(':') or structural(index):
            return False
        if text.endswith('.'):
            # Zellen mit Abkürzungspunkt („Gebietskörpersch.“) nur innerhalb eines Laufs kurzer Zeilen,
            # wenn auch die folgende Zeile eine Zelle ist; kurze Sätze bleiben Absätze.
            following = next_index(index)
            return inside_run and len(text) < 40 and following <= LAST and cell_like(following)
        return True

    # Randnummern und Gliederungspositionen des Erlasstexts (erster Durchlauf).
    rn_lines = {}
    rn_anchor_lines = {}
    for index in range(BODY, LAST + 1):
        match = RN.match(lines[index])
        if match:
            assert match[1] not in rn_lines, match[1]
            rn_lines[match[1]] = index
            for anchor in rn_anchors(match[1]):
                assert anchor not in rn_anchor_lines, anchor
                rn_anchor_lines[anchor] = index
    assert len(rn_lines) == 572 and len(rn_anchor_lines) == 574
    assert all(not RN.match(lines[i]) for i in range(TITLE, TOC))
    section_lines = [i for i in range(BODY, LAST + 1) if heading_of(i)]
    assert len(section_lines) == 338, len(section_lines)
    assert all(not any(pattern.match(lines[i]) for _, pattern, _ in LEVELS) for i in range(TITLE, TOC))

    # Inhaltsverzeichnis der Kopie: Dreizeiler Bezeichnung/Titel/Randnummern, Zweizeiler ohne Randnummern.
    entries = []
    entry = []
    for index in range(TOC + 1, TOC_END):
        if lines[index].strip():
            entry.append(index)
        elif entry:
            entries.append(entry)
            entry = []
    if entry:
        entries.append(entry)
    assert entries[0] == [TOC + 1] and entries[-1][-1] == TOC_END - 1
    entries = entries[1:]
    assert len(entries) == len(section_lines) == 338
    for entry, target in zip(entries, section_lines):
        label = lines[entry[0]]
        full = label if len(entry) == 1 else label + ' ' + lines[entry[1]]
        assert len(entry) in (1, 2, 3), entry
        assert lines[target].startswith(label), (entry[0] + 1, target + 1)
        if entry[0] in TOC_TITLE_DIFFERENCES:
            assert TOC_TITLE_DIFFERENCES[entry[0]] == target and full != lines[target], entry[0] + 1
        else:
            assert full == lines[target], (entry[0] + 1, full, target + 1, lines[target])

    def inline(index, heading=False, list_item=False):
        line = lines[index]
        if list_item:
            line = LIST.sub(lambda m: m[1] + ' ', line, count=1)
        value = escape(line)
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
        if level <= 6:
            add(index, index + 1, '#' * level + ' ' + inline(index, heading=True), kind)
        else:
            add(index, index + 1, f'<p class="gliederung-{level}"><strong>{inline(index)}</strong></p>', kind)
        decisions.append({'zeile': index + 1, 'art': kind, 'ebene': level, 'text': lines[index]})

    def bold_paragraph(index, kind, css):
        add(index, index + 1, f'<p class="{css}"><strong>{inline(index)}</strong></p>', kind)
        decisions.append({'zeile': index + 1, 'art': kind, 'ebene': None, 'text': lines[index]})

    # Dokumentkopf mit Fundstelle, Änderungsvermerk und Einleitungssatz.
    outputs.append('<a id="dokumentkopf"></a>')
    heading(TITLE, 2, kind='dokumentkopf')
    paragraph(TITLE + 1, TITLE + 5, 'dokumentkopf', css='dokumentkopf')
    outputs.append('<a id="einleitung"></a>')
    paragraph(INTRO, INTRO + 1, 'einleitung')

    # Inhaltsverzeichnis der Kopie als verlinkte Tabelle (Spaltenkopf „Rn.“ ist Quellzeile 12).
    heading(TOC, 2, 'inhaltsverzeichnis', 'inhaltsverzeichnis')
    rows = [f'<tr><th></th><th></th><th>{inline(TOC + 1)}</th></tr>']
    for entry, target in zip(entries, section_lines):
        anchor = f'gliederung-z{target + 1}'
        label = f'<a href="#{anchor}">{inline(entry[0])}</a>'
        if len(entry) == 1:
            rows.append(f'<tr><td colspan="3">{label}</td></tr>')
        elif len(entry) == 2:
            rows.append(f'<tr><td>{label}</td><td colspan="2"><a href="#{anchor}">{inline(entry[1])}</a></td></tr>')
        else:
            first = RN_FIRST.match(lines[entry[2]])
            assert first, lines[entry[2]]
            rn_anchor = rn_anchors(first[1])[0]
            assert rn_anchor in rn_anchor_lines, (entry[2] + 1, first[1])
            rows.append(f'<tr><td>{label}</td><td><a href="#{anchor}">{inline(entry[1])}</a></td>'
                        f'<td><a href="#{rn_anchor}">{inline(entry[2])}</a></td></tr>')
    add(TOC + 1, TOC_END, '<table class="inhaltsverzeichnis">\n' + '\n'.join(rows) + '\n</table>', 'inhaltsverzeichnis_tabelle')

    # Erlasstext.
    outputs.append('<a id="erlasstext"></a>\n\n## Erlasstext')
    pending = []
    images = []

    def flush_supplement():
        # Amtliche Seitendarstellung nach dem letzten Block der Randnummer, deren Tabelle in der Kopie abgeflacht ist.
        if not pending:
            return
        label, pages = pending.pop()
        parts = [f'> **Ergänzung aus der amtlichen BMF-Fassung:** Die folgende Seitendarstellung sichert die Zeilen- und '
                 f'Spaltenzuordnung der in der Textkopie abgeflachten Tabelle zu Rn. {label}. Sie stammt aus der amtlichen '
                 'PDF vom 2.1.2025 (Ursprungsfassung; diese Tabelle ist vom Änderungsschreiben vom 1.8.2025 nicht betroffen). '
                 'Der übrige Text der Seite gehört zur vollständigen Originalseite und ist kein zusätzlicher Quellblock.']
        for page in pages:
            path = IMAGE.format(page)
            assert (BASE / path).is_file(), path
            images.append(path)
            parts.append(f'**Amtliche PDF, Seite {page}:**\n\n![Seite {page} der BMF-PDF vom 2.1.2025 – Tabelle zu Rn. {label}]({path})')
        outputs.append('\n\n'.join(parts))

    index = BODY
    while index <= LAST:
        text = lines[index]
        if not text.strip():
            index += 1
            continue
        if RN.match(text) or heading_of(index):
            flush_supplement()
        match = RN.match(text)
        if match:
            label = match[1]
            rest = text[match.end():]
            if label in SUPPLEMENTS:
                pending.append((label, SUPPLEMENTS[label]))
            for anchor in rn_anchors(label):
                outputs.append(f'<a id="{anchor}"></a>')
            body = f'<p class="randnummer"><strong>{escape(label)}</strong>'
            body += f'<strong>{escape(rest)}</strong>' if rest == 'Beispiel:' else escape(rest)
            add(index, index + 1, body + '</p>', 'randnummer')
            index += 1
            continue
        if is_list_item(index):
            items = [index]
            end = index + 1
            while True:
                following = next_index(end - 1)
                if following <= LAST and is_list_item(following):
                    items.append(following)
                    end = following + 1
                else:
                    break
            add(index, end, '<ul class="original-aufzaehlung" style="list-style:none;padding-left:1.5em">\n'
                + '\n'.join('<li>' + inline(i, list_item=True) + '</li>' for i in items) + '\n</ul>', 'aufzaehlung')
            index = end
            continue
        head = heading_of(index)
        if head:
            heading(index, head[1], f'gliederung-z{index + 1}', head[0])
            index += 1
            continue
        if BEISPIEL.match(text):
            bold_paragraph(index, 'beispiel_ueberschrift', 'beispiel')
            index += 1
            continue
        if index in DASH_HEADINGS:
            bold_paragraph(index, 'zwischenueberschrift_strich', 'zwischenueberschrift')
            index += 1
            continue
        if index in COLON_TITLES:
            bold_paragraph(index, 'zwischentitel', 'zwischenueberschrift')
            index += 1
            continue
        if cell_like(index):
            cells = [index]
            end = index + 1
            while True:
                following = next_index(end - 1)
                if following <= LAST and cell_like(following, inside_run=True):
                    cells.append(following)
                    end = following + 1
                else:
                    break
            if len(cells) >= 3:
                add(index, end, '<p class="quellzeilen">' + '<br>\n'.join(inline(i) for i in cells) + '</p>', 'kurze_quellzeilen')
                decisions.append({'zeile': index + 1, 'zeile_bis': end, 'art': 'kurze_quellzeilen', 'zellen': len(cells), 'text': lines[index]})
                index = end
                continue
        end = index + 1
        while end <= LAST and lines[end].strip() and not structural(end):
            end += 1
        paragraph(index, end)
        index = end
    flush_supplement()
    assert len(images) == sum(len(pages) for pages in SUPPLEMENTS.values()) == 5

    # Fußnoten der Webkopie mit redaktionell erschlossener Zuordnung.
    assignments = fussnoten_eintraege(lines)
    definition_lines = []
    index = FN
    while index <= END:
        match = DEF.fullmatch(lines[index])
        assert match and int(match[1]) == len(definition_lines) + 1 and lines[index + 1].strip(), index + 1
        assert index + 1 == END or lines[index + 2] == '', index + 1
        definition_lines.append(index)
        index += 3
    assert len(definition_lines) == 94 and [e['definition_zeile'] for e in assignments] == [i + 1 for i in definition_lines]
    status = Counter(e['status'] for e in assignments)
    kinds_fn = Counter(e['art'] for e in assignments)
    outputs.append('<a id="fussnoten"></a>\n\n## Fußnoten der Webkopie\n\n'
        'Die Webkopie enthält am Dateiende 94 Fußnotendefinitionen, im Text aber keine Verweiszeichen: Die '
        'Fußnotenmarker sind beim Kopieren entfernt worden; nur in Tabellenzellen blieben Leerzeichenreste. Die '
        'folgende Zuordnung ist deshalb **redaktionell erschlossen** – aus der Reihenfolge der Fußnoten, den zitierten '
        'Verwaltungsanweisungen (jede BeckVerw-Dokumentnummer entspricht durchgehend genau einem zitierten Schreiben), '
        'den amtlichen Fußnoten der [BMF-PDF](Quellen/Onlineabgleich/2025-01-02-umwStE.pdf) und den Leerzeichenresten '
        'der Kopie (Einzelheiten in [Pruefung/fussnoten.py](Pruefung/fussnoten.py) und '
        '[Fussnotenzuordnung.json](Pruefung/Fussnotenzuordnung.json)). Sie ist kein Bestandteil der Kopie. '
        f'{status["erschlossen"]} Fußnoten sind auf eine Zeile bezogen, {status["erschlossen_ohne_zelle"]} nur auf eine '
        f'Randnummer, {status["offen"]} bleibt offen. Nur die {kinds_fn["amtliche Anmerkung"]} mit „[Amtl. Anm.:]“ '
        'gekennzeichneten Fußnoten sind amtliche Anmerkungen; die übrigen sind Hinweise des Anbieters. Das an jede '
        'Fußnote angeklebte „zurück zum Text“ ist Website-Navigation der Kopie und bleibt als Textbestandteil erhalten.')
    rows = ['| Fußnote | Art | Bezugsstelle (erschlossen) | Grundlage |', '| --- | --- | --- | --- |']
    for item, def_index in zip(assignments, definition_lines):
        link = f'[[{item["fussnote"]}]](#fn-z{def_index + 1})'
        if item['randnummer'] in ('Dokumentkopf', 'Einleitung'):
            target = f'[{item["randnummer"]}](#{item["randnummer"].lower()}), Zeile {item["zeile"]}: {item["stelle"]}'
        elif item['randnummer'] and item['zeile']:
            target = f'[Rn. {item["randnummer"]}](#{rn_anchors(item["randnummer"])[0]}), Zeile {item["zeile"]}: {item["stelle"]}'
        elif item['randnummer']:
            target = f'[Rn. {item["randnummer"]}](#{rn_anchors(item["randnummer"])[0]}), Zelle nicht identifizierbar: {item["stelle"]}'
        else:
            target = f'offen: {item["stelle"]}'
        rows.append(f'| {link} | {escape(item["art"])} | {escape(target, quote=False)} | {escape(item["grundlage"], quote=False)} |')
    outputs.append('\n'.join(rows))
    for def_index in definition_lines:
        text = lines[def_index + 1]
        assert text.endswith(NAVIGATION), def_index + 2
        body = (f'<p class="fussnote"><a id="fn-z{def_index + 1}"></a><strong>{escape(lines[def_index].strip())}</strong><br>\n'
                f'{escape(text[:-len(NAVIGATION)])}<span class="kopie-navigation">{NAVIGATION}</span></p>')
        add(def_index, def_index + 2, body, 'fussnote')

    expected_lines = {index for index in range(TITLE, END + 1) if lines[index].strip()}
    assert set(coverage) == expected_lines, ('Fehlende/zusätzliche Quellzeilen', sorted(expected_lines ^ coverage.keys())[:20])
    assert all(value == 1 for value in coverage.values()), 'Doppelt übernommene Quellzeilen.'
    kinds = Counter(record['art'] for record in records)
    levels = Counter(d['ebene'] for d in decisions if d['art'] in {k for k, _, _ in LEVELS})

    outputs.insert(0, '# Umwandlungssteuererlass 2025 (UmwStE 2025)\n\n'
        '**Quellenstand: BMF-Schreiben vom 2. Januar 2025 (BStBl. I S. 92), geändert durch BMF-Schreiben vom '
        '1. August 2025 (BStBl. I S. 1591) · Übernahme und Quellenabgleich: 9. September 2026.**\n\n'
        'Verwaltungsanweisung des Bundesministeriums der Finanzen zur Anwendung des Umwandlungssteuergesetzes '
        '(IV C 2 - S 1978/00035/020/040). Grundlage ist die bereitgestellte Textkopie aus beck-online (BeckVerw 647650) '
        'in der Fassung des Bundessteuerblatts. Alle kopierten Sachtexte werden unverändert übernommen; die Metazeile der '
        'Kopie bleibt in der [Originalkopie](Quellen/UmwStE_2025_Webkopie.txt) erhalten. Die 94 Fußnoten der Webquelle '
        'stehen am Ende der Datei; ihre Verweisstellen sind in der Kopie nicht erhalten und wurden redaktionell '
        'erschlossen. Nur mit „[Amtl. Anm.:]“ gekennzeichnete Fußnoten sind amtliche Anmerkungen; die übrigen sind '
        'Hinweise des Anbieters (Dokumentverknüpfungen „BeckVerw“, redaktionelle Anmerkungen, Änderungsvermerke).\n\n'
        f'**Struktur:** Das Inhaltsverzeichnis der Kopie ist als verlinkte Tabelle übernommen ({len(entries)} Einträge). '
        f'{len(rn_lines)} Randnummern („00.01“ bis „K.19“) tragen Sprungmarken `rn-…`; Kapitel, Teile und die Ebenen '
        'A., I., 1. sind Überschriften der Ebenen 2 bis 6, die Ebenen a), aa), (1) sowie Beispiel-, Lösungs- und '
        'Zwischenüberschriften sind hervorgehobene Absätze. In der Kopie abgeflachte Tabellen (Umwandlungsmatrizen, '
        f'Bilanzen, Berechnungen) bleiben als {kinds["kurze_quellzeilen"]} Blöcke kurzer Quellzeilen in Originalreihenfolge '
        f'erhalten; für die vier Umwandlungsmatrizen (Rn. {", ".join(SUPPLEMENTS)}) sichern {len(images)} gekennzeichnete '
        'Seitendarstellungen der amtlichen PDF die Spaltenzuordnung. Aufzählungen behalten ihr Originalzeichen. Die Kopie enthält keine Satznummern. Schreibweisen und '
        'mögliche Kopierfehler sind nicht berichtigt. Alle Gliederungsentscheidungen stehen in '
        '[Gliederungsentscheidungen.json](Pruefung/Gliederungsentscheidungen.json).\n\n'
        '[Prüfbericht](Pruefung/Pruefbericht.md) · [Amtlicher Abgleich](Quellen/Onlineabgleich/Abgleich.json) · '
        '[BMF-PDF vom 2.1.2025](Quellen/Onlineabgleich/2025-01-02-umwStE.pdf) · '
        '[Änderungsschreiben vom 1.8.2025](Quellen/Onlineabgleich/2025-08-01-aenderung-bmf-schreiben-umwste.pdf)\n\n'
        '## Navigation\n\n[Dokumentkopf](#dokumentkopf) · [Inhaltsverzeichnis](#inhaltsverzeichnis) · '
        '[Erlasstext](#erlasstext) · [Fußnoten](#fussnoten)')

    (BASE / MAIN).write_text('\n\n'.join(outputs) + '\n', encoding='utf-8')
    (BASE / 'Pruefung/Quellbloecke.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (BASE / 'Pruefung/Gliederungsentscheidungen.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (BASE / 'Pruefung/Fussnotenzuordnung.json').write_text(json.dumps(assignments, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'pruefung_erfolgreich': True, 'sha256_original_quelle': digest(data),
              'sha256_markdown': digest((BASE / MAIN).read_bytes()),
              'quellzeilen_gesamt': len(lines), 'quellzeilen_sachinhalt_nichtleer': len(coverage),
              'quellbloecke': len(records), 'gliederungspositionen': len(section_lines),
              'gliederungsebenen': {str(level): levels[level] for level in sorted(levels)},
              'inhaltsverzeichnis_eintraege': len(entries), 'randnummern': len(rn_lines),
              'sprungmarken_randnummern': len(rn_anchor_lines), 'anlagen': 0,
              'fussnoten': len(definition_lines), 'fussnotenverweise_in_der_kopie': 0,
              'fussnoten_zuordnung': dict(status), 'fussnoten_arten': dict(kinds_fn),
              'beispiel_ueberschriften': kinds['beispiel_ueberschrift'],
              'zwischenueberschriften': kinds['zwischenueberschrift_strich'] + kinds['zwischentitel'],
              'aufzaehlungen': kinds['aufzaehlung'], 'kurze_quellzeilenbloecke': kinds['kurze_quellzeilen'],
              'absaetze': kinds['absatz'], 'satznummern': 0,
              'ergaenzte_seitendarstellungen': len(images), 'ergaenzte_randnummern': list(SUPPLEMENTS),
              'uebernahme': f'Alle nichtleeren Sachtextzeilen {TITLE + 1} bis {END + 1} genau einmal; vollständiger sichtbarer Textrückvergleich pro Quellblock. Zeile 2 (Metazeile) nicht übernommen.',
              'einschraenkung': 'Vollständigkeit der übernommenen Textkopie geprüft; der Wortlautvergleich mit der amtlichen BMF-PDF steht in Quellen/Onlineabgleich/Abgleich.json. Fußnotenzuordnung, Gliederungsebenen und die Blöcke abgeflachter Tabellen sind redaktionelle Strukturentscheidungen.'}
    (BASE / 'Pruefung/Vollstaendigkeitspruefung.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
