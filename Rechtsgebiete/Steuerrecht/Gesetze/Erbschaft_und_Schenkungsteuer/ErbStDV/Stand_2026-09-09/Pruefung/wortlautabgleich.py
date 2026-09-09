"""Wortlautvergleich der ErbStDV-Webkopie mit der amtlichen XML-Gesamtausgabe von Gesetze im Internet.

Liest nur die archivierte Webkopie und die im Ordner Quellen/Onlineabgleich gesicherten amtlichen
Dateien (XML-Gesamtausgabe, pdftotext-Extraktion des BGBl-Auszugs zu Muster 5). Schreibt
Quellen/Onlineabgleich/Wortlautabgleich.json. Es wird nichts an der Kopie oder am Markdown geändert.

Normalisierung für den Vergleich der §§ 1 bis 13 (nur für den Vergleich, nicht für die Übernahme):
- Anbieterfußnoten der Kopie (Definitionszeile „[n] “ und Folgezeile) werden ausgelassen,
- Fußnotenmarker „[n]“ und die Satznummern der Kopie (Ziffer unmittelbar vor Großbuchstabe/§/„) werden entfernt,
- nach angeklebten Aufzählungszeichen („1.wenn“) wird ein Leerzeichen eingefügt,
- U+2004 (Three-per-em space), U+2009 (Thin space) und U+00A0 werden zu Leerzeichen, U+00AD (Soft hyphen) entfällt,
- Leerraum wird auf ein Leerzeichen zusammengezogen.
Muster 1 bis 4 und 6 werden gegen die pre-Blöcke der XML als Wortmengen verglichen (Layoutzeichen der
ASCII-Tabellen entfallen); Muster 5 liegt amtlich nur als PDF vor und wird gegen dessen pdftotext-Extraktion verglichen.
"""
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'Quellen/ErbStDV_Webkopie.txt'
ONLINE = BASE / 'Quellen/Onlineabgleich'
XML = ONLINE / 'BJNR265800998.xml'
MUSTER5_TEXT = ONLINE / 'bgbl1_2025_j0372_0010_pdftotext.txt'
TARGET = ONLINE / 'Wortlautabgleich.json'

PARA = re.compile(r'^§ (\d+)((?:\[\d+\])*) (\S.*)$')
PARA_NOT_TITLE = re.compile(r'^(?:Abs\.|Satz|Sätze|Nr\.|neu gef\.|geänd\.|eingef\.|angef\.)')
GROUP = re.compile(r'^(Zu § \d+ ErbStG|Schlußvorschriften)$')
DEF = re.compile(r'^\[(\d+)\]\s*$')
MARKER = re.compile(r'\[\d+\]')
SENT = re.compile(r'(?:(?<=\s)|^)(\d{1,2})(?=[A-ZÄÖÜ§„])')
LIST = re.compile(r'^(\d{1,2}[a-z]?\.)(?=[^\s\d.])')
MUSTER = re.compile(r'^Muster (\d)((?:\[\d+\])*)$')
WORD = re.compile(r'[0-9A-Za-zÄÖÜäöüß]+')

# Redaktionelle Einordnung der maschinell ermittelten Abweichungen (nach Sichtung der Ausgabe).
BEWERTUNG_PARAGRAPHEN = {
    '§ 2': 'Nur Typografie: Gedankenstrich „–“ der Kopie gegenüber Bindestrich „-“ der XML in Nr. 3.',
    '§ 3': 'Nur Leerzeichen: Kopie „Lebens-(Sterbegeld-)“, XML „Lebens- (Sterbegeld-)“.',
    '§ 10': 'Drei Wortformen weichen ab: Kopie „Anerkennungen“ / XML „Anerkennung“ (Satz 1), Kopie „Rechtsgeschäfte“ / XML „Rechtsgeschäfts“ (Satz 3), Kopie „Erwerben“ / XML „Erwerbern“ (Satz 4 Nr. 4). Die amtliche PDF-Gesamtausgabe lautet wie die XML. Die Kopie wird nicht geändert.',
    '§ 11': 'Eine Wortform weicht ab: Kopie „ihres Zuständigkeitsbereichs“, XML „ihre Zuständigkeitsbereichs“. Die amtliche PDF-Gesamtausgabe lautet wie die XML. Die Kopie wird nicht geändert.',
    '§ 13': 'Die Kopie enthält zusätzlich Satz 2 (Außerkrafttreten der ErbStDV in der Fassung BGBl. III 611-8-1); XML und PDF von Gesetze im Internet enthalten nur Satz 1.',
}
ERWARTETE_ABWEICHUNGEN = ['§ 2', '§ 3', '§ 10', '§ 11', '§ 13']
BEWERTUNG_MUSTER = {
    1: 'Differenzen sind Layoutartefakte der ASCII-Tabelle in der XML: Spaltentrenner „I“ und Silbentrennungen an Zellenumbrüchen („Todes-/tag“, „Rücknahme-/preis“, „Wert-/papiere“, „Wertpapier-/kenn-Nr.“). Kein abweichendes Wort im Formulartext. Bezugszeile: Kopie „(zu § 1 ErbStDV)“, XML-Titel „(§ 1 ErbStDV)“.',
    2: 'Differenzen sind Spaltentrenner „I“ der XML. Sachliche Abweichung: Kopie „als Begünstiger*“ (Zeile 554) gegenüber XML „als Begünstigter“ (Nr. 4). Die Kopie wird nicht geändert.',
    3: 'Differenzen sind Spaltentrenner „I“ und Silbentrennungen der XML („Sterbe-/registers“, „minder-/jährigen“, „Einzelhandels-/geschäft“, „Groß-/handel“, „Handwerks-/betrieb“, „Land-“), die Groß-/Kleinschreibung „Bei/bei minderjährigen“ sowie Verklebungen und eine Wortdopplung der Kopie: „einenWohnsitz“ (Zeile 678), „welchenWert“ (Zeile 760), „angeben angeben“ (Zeile 768); XML „Land-“ gegenüber Kopie „land-“ (Zeile 764). Die Kopie wird nicht geändert.',
    4: 'Einzige Differenz ist die Groß-/Kleinschreibung „Im Standesamtsbezirk“ (Kopie, Zeile 810) gegenüber „im Standesamtsbezirk“ (XML, nach einer Trennlinie). Kein weiteres abweichendes Wort.',
    5: 'Vergleichsgrundlage ist die pdftotext-Extraktion des BGBl-Auszugs (BGBl. 2025 I Nr. 372, S. 9–10) aus dem XML-Paket. Differenzen sind Silbentrennungen an Zeilenumbrüchen der PDF („Testamentsvoll-/streckerzeugnisses“, „Eigentums-/umschreibung“). Sachliche Abweichung: Kopie „Testament­vollstrecker­zeugnisses“ (ohne Fugen-s, mit weichen Trennzeichen, Zeile 934) gegenüber amtlich „Testamentsvollstreckerzeugnisses“. Die Kopie wird nicht geändert.',
    6: 'Differenzen sind Spaltentrenner „I“ der XML. Kein abweichendes Wort im Formulartext.',
}
# Erwartete Wortformen-Differenzen je Muster (nur Kopie, nur amtlich); Änderungen erzwingen eine Neubewertung.
ERWARTETE_MUSTER_DIFFERENZEN = {
    1: ({'Rücknahmepreis', 'Todestag', 'Wertpapiere', 'Wertpapierkenn'},
        {'I', 'Rücknahme', 'Todes', 'Wert', 'Wertpapier', 'kenn', 'papiere', 'preis', 'tag'}),
    2: ({'Begünstiger'}, {'Begünstigter', 'I'}),
    3: ({'Einzelhandelsgeschäft', 'Großhandel', 'Handwerksbetrieb', 'Sterberegisters', 'angeben', 'bei', 'einenWohnsitz',
         'land', 'minderjährigen', 'welchenWert'},
        {'Bei', 'Einzelhandels', 'Groß', 'Handwerks', 'I', 'Land', 'Sterbe', 'Wert', 'Wohnsitz', 'betrieb', 'einen',
         'geschäft', 'handel', 'jährigen', 'minder', 'registers', 'welchen'}),
    4: ({'Im'}, {'im'}),
    5: ({'Eigentumsumschreibung', 'Testamentvollstreckerzeugnisses'}, {'Eigentums', 'Testamentsvoll', 'streckerzeugnisses', 'umschreibung'}),
    6: (set(), {'I'}),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(value):
    value = value.replace(' ', ' ').replace(' ', ' ').replace(' ', ' ').replace('­', '')
    return re.sub(r'\s+', ' ', value).strip()


def copy_norm_line(line):
    line = MARKER.sub('', line)
    line = SENT.sub('', line)
    line = LIST.sub(lambda m: m[1] + ' ', line, count=1)
    return line


def token_diff(a, b):
    """Abweichende Tokenfolgen mit kurzem Kontext, Kopie gegen amtlichen Text."""
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    result = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue
        result.append({'kopie': ' '.join(a[i1:i2]), 'amtlich': ' '.join(b[j1:j2]),
                       'kontext_kopie': ' '.join(a[max(0, i1 - 3):i2 + 3])})
    return result


def words(value):
    return Counter(WORD.findall(value.replace('­', '')))


def main():
    lines = SOURCE.read_bytes().decode('utf-8').splitlines()
    assert len(lines) == 1113
    root = ET.parse(XML).getroot()
    norms = root.findall('norm')
    frame = norms[0].find('metadaten')

    # Kopie: Paragraphen mit Titel und Normtext ohne Anbieterfußnoten.
    def is_section(index):
        match = PARA.match(lines[index])
        if not match or PARA_NOT_TITLE.match(match[3]):
            return False
        prev = index - 1
        while prev > 0 and not lines[prev].strip():
            prev -= 1
        return not DEF.fullmatch(lines[prev])

    first_muster = next(i for i in range(len(lines)) if MUSTER.match(lines[i]))
    section_indices = [i for i in range(11, first_muster) if is_section(i)]
    assert len(section_indices) == 13
    copy_sections = {}
    for position, index in enumerate(section_indices):
        stop = section_indices[position + 1] if position + 1 < len(section_indices) else first_muster
        match = PARA.match(lines[index])
        body = []
        skip = False
        for i in range(index + 1, stop):
            text = lines[i]
            if DEF.fullmatch(text):
                skip = True
                continue
            if not text.strip():
                skip = False
                continue
            if skip or GROUP.match(text):
                continue
            body.append(copy_norm_line(text))
        copy_sections['§ ' + match[1]] = {'titel': normalize(MARKER.sub('', match[3])), 'text': normalize(' '.join(body))}

    # XML: Paragraphen mit Titel und Text (Listen als DT/DD-Folgen).
    xml_sections = {}
    xml_muster = {}
    xml_only = []
    xml_footnotes = {}
    for norm in norms[1:]:
        meta = norm.find('metadaten')
        enbez = meta.findtext('enbez')
        unit = meta.find('gliederungseinheit')
        content = norm.find('textdaten/text/Content')
        notes = norm.find('textdaten/fussnoten')
        if notes is not None and ''.join(notes.itertext()).strip():
            xml_footnotes[enbez or unit.findtext('gliederungsbez')] = normalize(' '.join(notes.itertext()))
        if enbez and enbez.startswith('§ '):
            xml_sections[enbez] = {'titel': normalize(meta.findtext('titel') or ''),
                                   'text': normalize(' '.join(content.itertext()))}
        elif enbez and enbez.startswith('Muster '):
            pre = content.find('.//pre')
            file = content.find('.//FILE')
            xml_muster[int(enbez.split()[1])] = {
                'bezug': normalize(meta.findtext('titel') or ''),
                'pre': normalize(' '.join(pre.itertext())) if pre is not None else None,
                'datei': file.get('SRC') if file is not None else None,
                'fundstelle': normalize(' '.join(content.find('.//kommentar').itertext()))}
        elif enbez:
            xml_only.append({'enbez': enbez, 'text': normalize(' '.join(content.itertext()))})
    assert list(xml_sections) == list(copy_sections), (list(xml_sections), list(copy_sections))

    paragraphs = []
    for key, copy in copy_sections.items():
        official = xml_sections[key]
        copy_tokens, official_tokens = copy['text'].split(' '), official['text'].split(' ')
        differences = token_diff(copy_tokens, official_tokens)
        paragraphs.append({'paragraph': key, 'titel_kopie': copy['titel'], 'titel_identisch': copy['titel'] == official['titel'],
                           'text_identisch': copy['text'] == official['text'],
                           'zeichen_kopie': len(copy['text']), 'zeichen_amtlich': len(official['text']),
                           'abweichungen': differences, 'bewertung': BEWERTUNG_PARAGRAPHEN.get(key, 'Zeichenidentisch nach Normalisierung.')})
    assert all(item['text_identisch'] == (not item['abweichungen']) for item in paragraphs)
    assert [p['paragraph'] for p in paragraphs if not p['text_identisch']] == ERWARTETE_ABWEICHUNGEN, 'Abweichungen neu bewerten.'
    assert all(p['titel_identisch'] for p in paragraphs)

    # Muster: Wortmengen der Kopie gegen die amtliche Vorlage.
    muster_indices = [i for i in range(len(lines)) if MUSTER.match(lines[i])]
    assert len(muster_indices) == 6
    muster_results = []
    for position, index in enumerate(muster_indices):
        number = int(MUSTER.match(lines[index])[1])
        stop = muster_indices[position + 1] if position + 1 < len(muster_indices) else len(lines)
        body = []
        skip = False
        # Die Bezugszeile „(zu § n ErbStDV)“ steht in der XML als Titel, nicht im pre-Block; sie wird gesondert ausgewiesen.
        for i in range(index + 2, stop):
            text = lines[i]
            if DEF.fullmatch(text):
                skip = True
                continue
            if not text.strip():
                skip = False
                continue
            if not skip:
                body.append(text)
        copy_words = words(' '.join(body))
        official = xml_muster[number]
        if official['pre'] is not None:
            basis = 'XML-Gesamtausgabe, pre-Block (ASCII-Tabelle)'
            official_words = words(official['pre'])
        else:
            basis = f'BGBl-Auszug {official["datei"]} aus dem XML-Paket, Textextraktion mit pdftotext -layout'
            official_words = words(MUSTER5_TEXT.read_text(encoding='utf-8'))
        only_copy = copy_words - official_words
        only_official = official_words - copy_words
        assert (set(only_copy), set(only_official)) == ERWARTETE_MUSTER_DIFFERENZEN[number], (number, only_copy, only_official)
        muster_results.append({'muster': number, 'bezugszeile_kopie': lines[index + 1], 'bezug_xml': official['bezug'],
                               'fundstelle_xml': official['fundstelle'], 'vergleichsgrundlage': basis,
                               'woerter_kopie': sum(copy_words.values()), 'woerter_amtlich': sum(official_words.values()),
                               'wortformen_nur_kopie': dict(sorted(only_copy.items())),
                               'wortformen_nur_amtlich': dict(sorted(only_official.items())),
                               'bewertung': BEWERTUNG_MUSTER[number]})

    frame_result = {
        'kopie_zeile_7': lines[6], 'xml_standkommentar': frame.findtext('standangabe/standkommentar'),
        'stand_stimmt_ueberein': lines[6].endswith('vom 22.6.2026 (BGBl. 2026 I Nr. 192)') and
                                 frame.findtext('standangabe/standkommentar') == 'Zuletzt geändert durch Art. 11 G v. 22.6.2026 I Nr. 192',
        'kopie_zeile_1': lines[0], 'xml_builddate': root.get('builddate'),
        'xml_ausfertigungsdatum': frame.findtext('ausfertigung-datum'), 'kopie_zeile_4': lines[3],
        'xml_fundstelle': frame.findtext('fundstelle/periodikum') + ' ' + frame.findtext('fundstelle/zitstelle'),
        'kopie_zeile_5': lines[4], 'xml_langue': frame.findtext('langue'), 'kopie_zeile_2': lines[1],
        'gliederungsbezeichnungen_xml': [n.find('metadaten/gliederungseinheit/gliederungsbez').text for n in norms
                                         if n.find('metadaten/gliederungseinheit') is not None],
        'gliederungsbezeichnungen_kopie': [l for l in lines if GROUP.match(l)],
    }
    assert frame_result['gliederungsbezeichnungen_xml'] == frame_result['gliederungsbezeichnungen_kopie']
    assert frame_result['xml_langue'] == lines[1] and frame_result['xml_ausfertigungsdatum'] == '1998-09-08'

    identical = [p['paragraph'] for p in paragraphs if p['text_identisch'] and p['titel_identisch']]
    deviating = [p['paragraph'] for p in paragraphs if not p['text_identisch']]
    result = {
        'erstellt_mit': 'Pruefung/wortlautabgleich.py',
        'webkopie': {'datei': 'Quellen/ErbStDV_Webkopie.txt', 'sha256': sha(SOURCE)},
        'amtliche_xml': {'datei': 'Quellen/Onlineabgleich/BJNR265800998.xml', 'sha256': sha(XML),
                         'builddate': root.get('builddate'), 'doknr': root.get('doknr')},
        'muster_5_textgrundlage': {'datei': 'Quellen/Onlineabgleich/bgbl1_2025_j0372_0010_pdftotext.txt', 'sha256': sha(MUSTER5_TEXT)},
        'normalisierung': ['Anbieterfußnoten der Kopie ausgelassen', 'Fußnotenmarker [n] entfernt', 'Satznummern der Kopie entfernt',
                           'Leerzeichen nach angeklebten Aufzählungszeichen eingefügt',
                           'U+2004, U+2009, U+00A0 zu Leerzeichen; U+00AD entfernt; Leerraum zusammengezogen',
                           'Muster: Vergleich als Wortmengen (Token [0-9A-Za-zÄÖÜäöüß]+), Layoutzeichen bleiben unberücksichtigt'],
        'rahmen': frame_result,
        'paragraphen': paragraphs,
        'nur_in_der_xml': xml_only,
        'anwendungshinweise_xml': xml_footnotes,
        'muster': muster_results,
        'ergebnis': {
            'paragraphen_gesamt': len(paragraphs), 'titel_identisch': sum(p['titel_identisch'] for p in paragraphs),
            'text_identisch': identical, 'text_abweichend': deviating,
            'zusammenfassung': f'{len(identical)} von {len(paragraphs)} Paragraphen sind nach Normalisierung zeichenidentisch; '
                               f'Abweichungen in {", ".join(deviating)} sind einzeln aufgeführt und bewertet. '
                               'Eingangsformel und Schlußformel der amtlichen Fassung fehlen in der Kopie. '
                               'Muster 1 bis 6 wurden als Wortmengen gegen die amtliche Vorlage verglichen.'},
    }
    TARGET.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['ergebnis'], ensure_ascii=False, indent=2))
    for item in paragraphs:
        if item['abweichungen']:
            print(item['paragraph'], json.dumps(item['abweichungen'], ensure_ascii=False))
    for item in muster_results:
        print('Muster', item['muster'], 'nur Kopie:', item['wortformen_nur_kopie'], 'nur amtlich:', item['wortformen_nur_amtlich'])


if __name__ == '__main__':
    main()
