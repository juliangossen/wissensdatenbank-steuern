"""Geprüfte Tabellenbereiche der unveränderten ErbStR-2019-Webkopie (Anlagen 1 und 2).

Indizes in TABLE_RANGES sind nullbasiert; das Ende ist exklusiv. `lines` ist die
vollständige, mit splitlines() gelesene Quelldatei. `inline(index)` liefert den
bereits HTML-escaped Inline-Inhalt einer Originalzeile (mit verlinkten Fußnoten).

Anlage 1 (zu R B 160.2 und 163) ist in der Kopie als Zweispalter abgeflacht:
je Tabellenzeile zuerst alle Zellen der Spalte „Anbauflächen bzw. Tierarten“,
danach die Zelle „Produktionszweig“. Die Zeilengrenzen wurden an der amtlichen
PDF-Seite 183 (Quellen/Onlineabgleich/ErbStR_2019_BMF.pdf) geprüft. Die Kopie
teilt die amtliche Zeile „Futterbau“ in zwei Zeilen (Weidevieh / davon Rinder für
die Milcherzeugung); diese Teilung wird beibehalten, es wird nichts umgeordnet.

Anlage 2 (zu R B 163) besteht aus sieben Regionalblöcken. Jeder Block ist in der
Kopie zellenweise abgeflacht: Blockkopf, Regionsnamen, „Code“, Merkmalzeile, dann
je Zeile Code, Merkmal und genau N Werte. N ergibt sich aus der Zahl der
Wertspalten des Blocks; die Spaltenköpfe (Länder mit Regierungsbezirken) wurden an
den amtlichen PDF-Seiten 184 bis 190 geprüft, auf denen die Anlage nur als Bild
vorliegt. Jede Zeile muss genau N Zahlenzellen haben; andernfalls bricht die
Konvertierung ab. Es werden nur Zellen der Kopie verwendet, nichts wird ergänzt.
"""

from html.parser import HTMLParser
import re


ANLAGE_1_START = 27753   # Zeile 27754: „Anbauflächen bzw. Tierarten“
ANLAGE_1_END = 27798     # Zeile 27798: „Veredlung“ (letzte Zelle)

# Nullbasierter Beginn jedes Regionalblocks der Anlage 2 (Zeile „Standarddeckungsbeiträge“)
# mit den an den amtlichen Seiten geprüften Spaltenköpfen. Reihenfolge in der Kopie:
# zuerst alle Länder der oberen Kopfzeile, dann die Regierungsbezirke der unteren Kopfzeile.
ANLAGE_2_BLOCKS = {
    27817: ('184', (('Schleswig-Holstein', ()), ('Niedersachsen', ('Braunschweig', 'Hannover', 'Lüneburg', 'Weser-Ems')))),
    28611: ('185', (('Nordrhein-Westfalen', ('Düsseldorf', 'Köln', 'Münster', 'Detmold', 'Arnsberg')),)),
    29405: ('186', (('Hessen', ('Darmstadt', 'Gießen', 'Kassel')), ('Rheinland-Pfalz', ()), ('Saarland', ()))),
    30199: ('187', (('Baden-Württemberg', ('Stuttgart', 'Karlsruhe', 'Freiburg', 'Tübingen')),)),
    30881: ('188', (('Bayern', ('Oberbayern', 'Niederbayern', 'Oberpfalz', 'Oberfranken', 'Mittelfranken', 'Unterfranken', 'Schwaben')),)),
    31899: ('189', (('Brandenburg', ()), ('Mecklenburg-Vorpommern', ()), ('Sachsen', ('Chemnitz', 'Dresden', 'Leipzig')))),
    32693: ('190', (('Sachsen-Anhalt', ('Dessau', 'Halle', 'Magdeburg')), ('Thüringen', ()), ('Stadtstaaten', ()))),
}
ANLAGE_2_END = 33484     # exklusiv; Zeile 33484 „4 003“ ist die letzte Zelle

TABLE_RANGES = {ANLAGE_1_START: ANLAGE_1_END}
_starts = sorted(ANLAGE_2_BLOCKS)
for _start, _next in zip(_starts, _starts[1:] + [ANLAGE_2_END]):
    TABLE_RANGES[_start] = _next

CODE = re.compile(r'^(?:J/\d+[a-z]*|Jm|Ja|D/\d+[a-z]*|F/\d+)$')
VALUE = re.compile(r'^[\s  ]*\d[\d  .,]*\s*$')


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def _without_whitespace(text):
    return re.sub(r'\s+', '', text)


def render_table(start, lines, inline):
    """Rendere eine Tabelle und prüfe exakt den sichtbaren Quellenwortlaut."""
    end = TABLE_RANGES[start]
    if len(lines) < end:
        raise ValueError('Quelldatei endet vor dem registrierten Tabellenbereich.')
    used = []

    def cell(numbers=(), tag='td', attrs=''):
        pieces = []
        for number in numbers:
            index = number - 1
            if not start <= index < end or not lines[index].strip():
                raise ValueError(f'Ungültige Tabellen-Quellzeile: {number}')
            used.append(index)
            pieces.append(inline(index))
        return f'<{tag}{attrs}>' + '<br>'.join(pieces) + f'</{tag}>'

    def row(*cells):
        return '<tr>' + ''.join(cells) + '</tr>'

    rows = []
    description = {}
    if start == ANLAGE_1_START:
        if lines[start] != 'Anbauflächen bzw. Tierarten' or lines[27769] != 'Ackerbau' \
                or lines[27781] != 'Futterbau' or lines[27797] != 'Veredlung':
            raise ValueError('Anlage 1 hat nicht mehr die geprüfte Zeilenstruktur.')
        rows.append(row(cell((27754,), 'th'), cell((27756,), 'th')))
        rows.append(row(cell((27758, 27760, 27762, 27764, 27766, 27768)), cell((27770,))))
        rows.append(row(cell((27772, 27774, 27776, 27778, 27780)), cell((27782, 27784))))
        rows.append(row(cell((27786, 27788, 27790)), cell()))
        rows.append(row(cell((27792, 27794, 27796)), cell((27798,))))
        description = {'anlage': 1, 'zeilen': 4, 'spalten': 2, 'amtliche_seite': '183'}
    elif start in ANLAGE_2_BLOCKS:
        page, layout = ANLAGE_2_BLOCKS[start]
        tokens = [i for i in range(start, end) if lines[i].strip()]
        if lines[tokens[0]] != 'Standarddeckungsbeiträge' or lines[tokens[1]] != 'nach der EU-Typologie':
            raise ValueError(f'Anlage 2, Block ab Zeile {start + 1}: Blockkopf weicht ab.')
        expected_names = [name for name, _ in layout] + [sub for _, subs in layout for sub in subs]
        names = tokens[2:2 + len(expected_names)]
        if [lines[i] for i in names] != expected_names:
            raise ValueError(f'Anlage 2, Block ab Zeile {start + 1}: Spaltenköpfe weichen ab.')
        code_index = tokens[2 + len(expected_names)]
        merkmal_index = tokens[3 + len(expected_names)]
        if lines[code_index] != 'Code' or not lines[merkmal_index].startswith('Merkmal ('):
            raise ValueError(f'Anlage 2, Block ab Zeile {start + 1}: Kopfzeile „Code/Merkmal“ fehlt.')
        columns = sum(max(1, len(subs)) for _, subs in layout)
        top = [cell((tokens[0] + 1, tokens[1] + 1), 'th', ' rowspan="2" colspan="2"')]
        position = 2
        for name, subs in layout:
            attrs = f' colspan="{len(subs)}"' if subs else ' rowspan="2"'
            top.append(cell((tokens[position] + 1,), 'th', attrs))
            position += 1
        bottom = []
        for _, subs in layout:
            for _ in subs:
                bottom.append(cell((tokens[position] + 1,), 'th'))
                position += 1
        rows.append(row(*top))
        rows.append(row(*bottom))
        rows.append(row(cell((code_index + 1,), 'th'), cell((merkmal_index + 1,), 'th', f' colspan="{columns + 1}"')))
        position = 4 + len(expected_names)
        code_rows = section_rows = average_rows = 0
        while position < len(tokens):
            index = tokens[position]
            text = lines[index]
            if CODE.match(text):
                values = tokens[position + 2:position + 2 + columns]
                if len(values) != columns or not all(VALUE.match(lines[v]) for v in values) \
                        or (position + 2 + columns < len(tokens) and VALUE.match(lines[tokens[position + 2 + columns]])):
                    raise ValueError(f'Anlage 2, Zeile {index + 1}: nicht genau {columns} Werte.')
                rows.append(row(cell((index + 1,)), cell((tokens[position + 1] + 1,)),
                                *[cell((v + 1,)) for v in values]))
                position += 2 + columns
                code_rows += 1
            elif text.startswith('Merkmal '):
                rows.append(row(cell((index + 1,), attrs=f' colspan="{columns + 2}"')))
                position += 1
                section_rows += 1
            elif text.startswith('Durchschnittlicher Standarddeckung'):
                values = tokens[position + 1:position + 1 + columns]
                if len(values) != columns or not all(VALUE.match(lines[v]) for v in values):
                    raise ValueError(f'Anlage 2, Zeile {index + 1}: Durchschnittszeile ohne {columns} Werte.')
                rows.append(row(cell((index + 1,), attrs=' colspan="2"'), *[cell((v + 1,)) for v in values]))
                position += 1 + columns
                average_rows += 1
            else:
                raise ValueError(f'Anlage 2, Zeile {index + 1}: unerwartete Zelle {text!r}.')
        if (code_rows, section_rows, average_rows) != (54, 2, 1):
            raise ValueError(f'Anlage 2, Block ab Zeile {start + 1}: Zeilenzahl weicht ab ({code_rows}, {section_rows}, {average_rows}).')
        description = {'anlage': 2, 'block_ab_zeile': start + 1, 'wertspalten': columns, 'merkmalzeilen': code_rows,
                       'amtliche_seite': page}
    else:
        raise ValueError(f'Unbekannter Tabellenbeginn: {start}')

    expected_indices = [i for i in range(start, end) if lines[i].strip()]
    if used != expected_indices:
        raise AssertionError('Tabellenzeilen fehlen, sind doppelt oder umgeordnet.')
    result = '<table>\n<tbody>\n' + '\n'.join(rows) + '\n</tbody>\n</table>'
    parser = _VisibleText()
    parser.feed(result)
    parser.close()
    actual = _without_whitespace(''.join(parser.parts))
    expected = _without_whitespace(''.join(lines[start:end]))
    if actual != expected:
        raise AssertionError('Sichtbarer Tabellenwortlaut weicht von der Quelle ab.')
    return result, description
