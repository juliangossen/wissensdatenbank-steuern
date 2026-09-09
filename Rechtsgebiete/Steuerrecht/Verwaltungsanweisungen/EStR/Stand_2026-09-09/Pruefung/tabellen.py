"""Geprüfte Tabellenbereiche der unveränderten EStR-/EStH-Textkopie.

Indizes in TABLE_RANGES sind nullbasiert; das Ende ist exklusiv. `lines`
ist die vollständige, mit splitlines() gelesene Quelldatei. `inline(index)`
liefert den bereits HTML-escaped Inline-Inhalt einer Originalzeile.

Anlage 1 folgt der vierteiligen Zellstruktur der gesicherten amtlichen Seite
Quellen/Onlineabgleich/EStH_2025_R_4_6_Anlage.html. Es wird ausschließlich
der Wortlaut der Kopie übernommen; amtliche Zusatzfußnoten werden nicht
in die Kopie eingemischt.

Anlage 6 erhält je Staat/Gebiet eine Zeile mit Name und Steuerbezeichnungen.
Die 77 Grenzen wurden gegen die Länderüberschriften der amtlichen Seite
Quellen/Onlineabgleich/EStH_2025_Anhang_12_II_1.html geprüft. Diese enthält
zusätzlich Andorra und inhaltliche Aktualisierungen; beides wird nicht
in die Kopie eingemischt. Das Quellenende bei Uganda ist bestätigt.

Anlage 2 (Zeilen 19132 bis 19338) ist absichtlich NICHT eingetragen:
verbundene Zellen und die zusammenkopierten Unterfälle 7a/7b lassen sich
aus dem Text nicht eindeutig rekonstruieren. Die gesicherte amtliche
EStH_2025_Anhang_01_I_2.html weicht zudem bei erster und letzter Zeile ab.
Der Hauptkonverter erhält diesen Bereich daher als Originaltext.
"""

from html.parser import HTMLParser
import re


TABLE_RANGES = {
    19069: 19122,  # Anlage 1: Originalzeilen 19070 bis 19122.
    19564: 20085,  # Anlage 6: Originalzeilen 19565 bis 20085.
}

# Einbasierte Originalzeilen, keine aus Wortmustern geratenen Ländergrenzen.
COUNTRY_LINES = (
    19565, 19573, 19583, 19587, 19591, 19595, 19599, 19603, 19609,
    19613, 19623, 19627, 19631, 19639, 19645, 19649, 19653, 19659,
    19663, 19673, 19683, 19689, 19693, 19697, 19701, 19705, 19719,
    19727, 19731, 19737, 19745, 19749, 19757, 19763, 19767, 19771,
    19779, 19789, 19803, 19809, 19815, 19823, 19829, 19833, 19843,
    19849, 19863, 19875, 19879, 19885, 19891, 19899, 19903, 19911,
    19923, 19939, 19945, 19955, 19967, 19977, 19981, 19987, 19999,
    20003, 20007, 20011, 20017, 20021, 20027, 20031, 20037, 20041,
    20053, 20057, 20063, 20073, 20077,
)


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def _without_whitespace(text):
    return re.sub(r"\s+", "", text)


def render_table(start, lines, inline):
    """Rendere eine Tabelle und prüfe exakt den sichtbaren Quellenwortlaut."""
    end = TABLE_RANGES[start]
    if len(lines) < end:
        raise ValueError("Quelldatei endet vor dem registrierten Tabellenbereich.")
    used = []

    def cell(numbers=(), tag="td", attrs=""):
        pieces = []
        for number in numbers:
            index = number - 1
            if not start <= index < end or not lines[index].strip():
                raise ValueError(f"Ungültige Tabellen-Quellzeile: {number}")
            used.append(index)
            pieces.append(inline(index))
        return f"<{tag}{attrs}>" + "<br/>".join(pieces) + f"</{tag}>"

    def row(*cells):
        return "<tr>" + "".join(cells) + "</tr>"

    rows = []
    if start == 19069:
        if lines[start] != "Übergang" or lines[19073] != "1.":
            raise ValueError("Anlage 1 hat nicht mehr die geprüfte Zeilenstruktur.")
        rows.append(row(
            cell((19070,), "th", ' colspan="2"'),
            cell((19072,), "th", ' colspan="2"'),
        ))
        rows.append(row(
            cell((19074,)), cell((19076,)),
            cell((19078,), attrs=' colspan="2"'),
        ))
        for operator, description in (
            (19080, 19082), (19084, 19086), (19088, 19090),
            (19092, 19094), (19096, 19098),
        ):
            rows.append(row(cell(), cell(), cell((operator,)), cell((description,))))
        rows.append(row(
            cell((19100,)), cell((19102,)),
            cell((19104,), attrs=' colspan="2"'),
        ))
        for operator, description in (
            (19106, 19108), (19110, 19112),
            (19114, 19116), (19118, 19120),
        ):
            rows.append(row(cell(), cell(), cell((operator,)), cell((description,))))
        rows.append(row(cell(), cell(), cell((19122,), attrs=' colspan="2"')))
    elif start == 19564:
        if lines[start] != "Afghanistan" or lines[20076] != "Uganda":
            raise ValueError("Anlage 6 hat nicht mehr die geprüfte Zeilenstruktur.")
        boundaries = COUNTRY_LINES + (end + 1,)
        for country, next_country in zip(boundaries, boundaries[1:]):
            values = tuple(
                number for number in range(country + 1, next_country)
                if lines[number - 1].strip()
            )
            if not values:
                raise ValueError(f"Land ohne Steuerbezeichnung: Zeile {country}")
            rows.append(row(cell((country,), "th", ' scope="row"'), cell(values)))
    else:
        raise ValueError(f"Unbekannter Tabellenbeginn: {start}")

    expected_indices = [i for i in range(start, end) if lines[i].strip()]
    if used != expected_indices:
        raise AssertionError("Tabellenzeilen fehlen, sind doppelt oder umgeordnet.")
    result = "<table>\n<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>"
    parser = _VisibleText()
    parser.feed(result)
    parser.close()
    actual = _without_whitespace("".join(parser.parts))
    expected = _without_whitespace("".join(lines[start:end]))
    if actual != expected:
        raise AssertionError("Sichtbarer Tabellenwortlaut weicht von der Quelle ab.")
    return result
