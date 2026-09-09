"""Amtlicher Abgleich der ErbStR-2019-Webkopie mit den amtlichen PDF-Fassungen.

Verglichen werden die bereitgestellte beck-online-Kopie (Richtlinien R E/R B und
Hinweise H E/H B) mit der amtlichen Verwaltungsvorschrift ErbStR 2019 (PDF des BMF,
191 Seiten) und den gleich lautenden Ländererlassen ErbStH 2019 (PDF, 228 Seiten):
1. Gliederung: jede Überschrift der Kopie (Hauptteile, Teile A–F, „Zu § …“, R-Blöcke,
   Anlagen) wird in der Reihenfolge der Kopie im amtlichen Richtlinientext gesucht;
   jede H-Überschrift in den Kopfzeilen „Hinweise … H E/H B …“ des Hinweistextes.
2. Wortlaut: je Block wird der normalisierte Text der Kopie (ohne die Fußnoten der
   Webquelle) mit dem amtlichen Block verglichen. Normalisierung: Zerlegung in Wörter
   an Leerraum, je Wort bleiben nur Buchstaben, Ziffern, § und %; damit entfallen
   Satzzeichen, Pfeile („→“ der Kopie, „>“ des PDF), Binde-/Gedankenstriche, geschützte
   und schmale Leerzeichen sowie die Fußnotenmarken „[n]“ der Kopie. Silbentrennungen
   des PDF am Zeilenende bleiben als getrennte Wörter erhalten und mindern die Ähnlichkeit
   geringfügig. Maß: difflib-Ähnlichkeit der Wortfolgen (2·Treffer/Gesamtlänge) sowie der
   Anteil der Kopiezeilen mit mindestens sechs Wörtern, deren Wortfolge unverändert im
   amtlichen Block vorkommt.
Das Skript liest nur die abgelegten Dateien, erzeugt die Textextraktionen mit Poppler
pdftotext neu und schreibt Abgleich.json sowie Textvergleich_Bloecke.json.
"""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
SOURCE = BASE / 'Quellen/ErbStR_2019_Webkopie.txt'
RICHTLINIEN_PDF = HERE / 'ErbStR_2019_BMF.pdf'
HINWEISE_PDF = HERE / 'ErbStH_2019_BMF.pdf'
RICHTLINIEN_TXT = HERE / 'ErbStR_2019_BMF_pdftotext.txt'
HINWEISE_TXT = HERE / 'ErbStH_2019_BMF_pdftotext.txt'
FIRST, INTRO, ANNEX, LAST = 33, 47, 27750, 33483

ROMAN = re.compile(r'^(I|II|III)\. (Einführung|Erbschaftsteuer- und Schenkungsteuergesetz|Bewertungsgesetz)$')
PART = re.compile(r'^([A-F])\. (\S.*)$')
GROUP = re.compile(r'^Zu §§? (\d+[a-z]?(?: (?:bis|und) \d+[a-z]?)?) (ErbStG|BewG)((?:\[\d+\])*)$')
RH = re.compile(r'^([RH]) ([EB]) (\d+[a-z]?(?:\.\d+)?)((?:\[\d+\])*)(?: \((\d+)\))?((?:\[\d+\])*)(?: (\S.*))?$')
ANNEX_HEAD = re.compile(r'^Anlage (\d)$')
DEF = re.compile(r'^\[(\d+)\]\s*$')
MARKERS = re.compile(r'\[\d+\]')
TOKEN = re.compile(r'[^0-9A-Za-zÄÖÜäöüß§%]')
PAGE = re.compile(r'^\s*-\s*\d+\s*-\s*$')
# Randbeschriftung „H E 3.1 (1)“ des Hinweis-PDF: allein auf der Zeile oder rechtsbündig hinter Text.
LABEL = re.compile(r'^(?P<pre>.*?)(?:^|\s{2,})(?P<label>H ?[EB] ?\d+[a-z]?(?:\.\d+)?(?: ?\(\d+\))?)\s*$')
LABEL_PARTS = re.compile(r'^H ?([EB]) ?(\d+[a-z]?(?:\.\d+)?)(?: ?\((\d+)\))?$')
LIST_MARK = re.compile(r'(?m)^(\d{1,2}\.|[a-z]\)|–)(?=\S)')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokens(text):
    # Angeklebte Aufzählungszeichen der Kopie („1.zum“, „a)der“, „–nur“) werden wie im PDF abgetrennt.
    text = LIST_MARK.sub(r'\1 ', text)
    return [t for t in (TOKEN.sub('', w) for w in text.split()) if t]


def find(sequence, pattern, start=0):
    n = len(pattern)
    first = pattern[0]
    i = start
    while True:
        try:
            i = sequence.index(first, i)
        except ValueError:
            return -1
        if sequence[i:i + n] == pattern:
            return i
        i += 1


def ratio(a, b):
    if not a and not b:
        return 1.0
    return round(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), 4)


def lines_found(copy_lines, pdf_tokens):
    candidates = [tokens(MARKERS.sub('', line)) for line in copy_lines]
    candidates = [c for c in candidates if len(c) >= 6]
    if not candidates:
        return None, 0
    hits = sum(1 for c in candidates if find(pdf_tokens, c) >= 0)
    return round(hits / len(candidates), 4), len(candidates)


def main():
    lines = SOURCE.read_bytes().decode('utf-8').splitlines()
    assert len(lines) == 33485 and lines[INTRO] == 'I. Einführung'
    subprocess.run(['pdftotext', '-enc', 'UTF-8', str(RICHTLINIEN_PDF), str(RICHTLINIEN_TXT)], check=True)
    subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', str(HINWEISE_PDF), str(HINWEISE_TXT)], check=True)
    annex_images = subprocess.run(['pdftotext', '-f', '184', '-l', '190', '-enc', 'UTF-8', str(RICHTLINIEN_PDF), '-'],
                                  check=True, capture_output=True).stdout.decode('utf-8')

    # Kopie: Überschriften und Fußnotenzeilen.
    definition_lines = {i for i in range(FIRST, LAST + 1) if DEF.fullmatch(lines[i])}
    heads = {}
    for index in range(INTRO, LAST + 1):
        text = lines[index]
        if not text.strip() or index in definition_lines or index - 1 in definition_lines:
            continue
        if ROMAN.match(text):
            heads[index] = 'hauptteil'
        elif PART.match(text) and 17264 < index < ANNEX and lines[index + 1].strip():
            heads[index] = 'teil'
        elif GROUP.match(text):
            heads[index] = 'gruppe'
        elif RH.match(text) and index < ANNEX:
            heads[index] = 'richtlinie' if text.startswith('R ') else 'hinweis'
        elif index >= ANNEX and ANNEX_HEAD.match(text) and lines[index + 1].startswith('(zu R B '):
            heads[index] = 'anlage'
    assert Counter(heads.values()) == Counter({'hauptteil': 3, 'teil': 6, 'gruppe': 90, 'richtlinie': 281, 'hinweis': 248, 'anlage': 2})
    footnote_lines = set()
    for index in sorted(definition_lines):
        end = index + 1
        while end <= LAST and end not in definition_lines and end not in heads:
            end += 1
        footnote_lines.update(range(index, end))
    head_list = sorted(heads)
    records = json.loads((BASE / 'Pruefung/Quellbloecke.json').read_text(encoding='utf-8'))
    table_starts = sorted(r['zeile_von'] - 1 for r in records if r['art'] in ('kurze_quellzeilen', 'tabelle'))

    def table_blocks(position):
        start = head_list[position]
        stop = head_list[position + 1] if position + 1 < len(head_list) else LAST + 1
        return sum(1 for t in table_starts if start <= t < stop)

    def copy_block(position):
        start = head_list[position]
        stop = head_list[position + 1] if position + 1 < len(head_list) else LAST + 1
        return [lines[i] for i in range(start, stop) if lines[i].strip() and i not in footnote_lines]

    # Amtliche Richtlinien: Wortfolge ohne Seitenzahlen, Suche der Überschriften in Reihenfolge.
    pdf_r_lines = [l for l in RICHTLINIEN_TXT.read_text(encoding='utf-8').splitlines() if not PAGE.match(l)]
    pdf_r = tokens('\n'.join(pdf_r_lines))
    body_start = find(pdf_r, ['I', 'Einführung', '1', '1Die', 'ErbschaftsteuerRichtlinien'])
    assert body_start > 0, 'Beginn des amtlichen Richtlinientextes nicht gefunden.'
    positions = {}
    cursor = body_start
    missing_r = []
    deviating_titles = []
    for index in head_list:
        if heads[index] == 'hinweis' or (heads[index] == 'anlage' and lines[index] == 'Anlage 2'):
            continue  # Hinweise stehen im Länder-PDF; Anlage 2 liegt amtlich nur als Bild vor.
        pattern = tokens(MARKERS.sub('', lines[index]))
        if heads[index] == 'anlage':
            pattern += tokens(lines[index + 1])
        found = find(pdf_r, pattern, cursor)
        if found < 0 and heads[index] == 'richtlinie':
            short = tokens(' '.join(lines[index].split()[:3]))
            found = find(pdf_r, short, cursor)
            if found >= 0:
                deviating_titles.append({'zeile': index + 1, 'kopie': MARKERS.sub('', lines[index]),
                                         'amtlich': ' '.join(pdf_r[found:found + len(pattern)])})
                pattern = short
        if found < 0:
            missing_r.append({'zeile': index + 1, 'text': lines[index]})
            continue
        positions[index] = found
        cursor = found + len(pattern)
    ordered = sorted(positions, key=positions.get)
    assert ordered == sorted(positions), 'Reihenfolge der Überschriften weicht ab.'
    artikel_2 = find(pdf_r, ['Artikel', '2', 'Anwendung', 'der', 'ErbschaftsteuerRichtlinien', 'vom', '19', 'Dezember', '2011'])
    results = []
    for position, index in enumerate(head_list):
        if heads[index] != 'richtlinie' and not (heads[index] == 'anlage' and index == ANNEX):
            continue
        if index not in positions:
            continue
        later = [positions[i] for i in positions if positions[i] > positions[index]]
        stop = min(later) if later else (artikel_2 if artikel_2 > 0 else len(pdf_r))
        copy_lines = copy_block(position)
        if heads[index] == 'anlage':
            copy_lines = [lines[i] for i in range(index, head_list[position + 1]) if lines[i].strip()]
        copy_tokens = tokens(MARKERS.sub('', '\n'.join(copy_lines)))
        pdf_tokens = pdf_r[positions[index]:stop]
        share, count = lines_found(copy_lines, pdf_tokens)
        results.append({'ueberschrift': MARKERS.sub('', lines[index]), 'zeile': index + 1, 'quelle': 'ErbStR 2019 (BMF-PDF)',
                        'woerter_kopie': len(copy_tokens), 'woerter_amtlich': len(pdf_tokens),
                        'aehnlichkeit_wortfolge': ratio(copy_tokens, pdf_tokens),
                        'anteil_zeilen_woertlich_gefunden': share, 'geprueft_zeilen': count,
                        'abgeflachte_tabellenbloecke_kopie': table_blocks(position)})

    # Amtliche Hinweise: Blöcke nach den Randbeschriftungen „H E/H B …“ des Layouttextes; die linke
    # Kopfzeile „Hinweise“ und Seitenzahlen entfallen. Stehen mehrere kurze Blöcke auf einer Seite,
    # setzt pdftotext ihre Beschriftungen gestapelt neben fremden Text; die Blockgrenzen sind dann unscharf.
    pdf_h_lines = []
    headers = []
    for raw_line in HINWEISE_TXT.read_text(encoding='utf-8').splitlines():
        if PAGE.match(raw_line) or raw_line.strip() == 'Hinweise':
            continue
        match = LABEL.match(raw_line)
        if match:
            pre = re.sub(r'^\s*(?:Hinweise|-\s*\d+\s*-)\s*$', '', match['pre'])
            parts = LABEL_PARTS.match(match['label'])
            label = f'H {parts[1]} {parts[2]}' + (f' ({parts[3]})' if parts[3] else '')  # „HE6“ des Layouttextes -> „H E 6“
            headers.append((len(pdf_h_lines), label))
            if pre.strip():
                pdf_h_lines.append(pre)
            continue
        pdf_h_lines.append(raw_line)
    laender_block = next((i for i in range(len(pdf_h_lines) - 1) if 'Ministerium für Finanzen' in pdf_h_lines[i]
                          and 'Baden-Württemberg' in pdf_h_lines[i + 1]), len(pdf_h_lines))
    assert laender_block < len(pdf_h_lines), 'Länderministerienblock der ErbStH nicht gefunden.'
    h_positions = {}
    cursor = 0
    missing_h = []
    for index in head_list:
        if heads[index] != 'hinweis':
            continue
        wanted = MARKERS.sub('', lines[index]).strip()
        hit = next((k for k in range(cursor, len(headers)) if headers[k][1] == wanted), None)
        if hit is None:
            missing_h.append({'zeile': index + 1, 'text': lines[index]})
            continue
        h_positions[index] = hit
        cursor = hit + 1
    for position, index in enumerate(head_list):
        if heads[index] != 'hinweis' or index not in h_positions:
            continue
        k = h_positions[index]
        start = headers[k][0]
        stop = headers[k + 1][0] if k + 1 < len(headers) else laender_block
        pdf_tokens = tokens('\n'.join(pdf_h_lines[start:stop]))
        copy_lines = copy_block(position)
        copy_tokens = tokens(MARKERS.sub('', '\n'.join(copy_lines[1:])))
        share, count = lines_found(copy_lines[1:], pdf_tokens)
        results.append({'ueberschrift': MARKERS.sub('', lines[index]), 'zeile': index + 1, 'quelle': 'ErbStH 2019 (Länder-PDF)',
                        'woerter_kopie': len(copy_tokens), 'woerter_amtlich': len(pdf_tokens),
                        'aehnlichkeit_wortfolge': ratio(copy_tokens, pdf_tokens),
                        'anteil_zeilen_woertlich_gefunden': share, 'geprueft_zeilen': count,
                        'abgeflachte_tabellenbloecke_kopie': table_blocks(position)})
    results.sort(key=lambda r: r['zeile'])
    (HERE / 'Textvergleich_Bloecke.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def summary(kind):
        values = [r for r in results if r['quelle'].startswith(kind)]
        sims = [r['aehnlichkeit_wortfolge'] for r in values]
        shares = [r['anteil_zeilen_woertlich_gefunden'] for r in values if r['anteil_zeilen_woertlich_gefunden'] is not None]
        low = [r for r in values if r['aehnlichkeit_wortfolge'] < 0.95]
        return {'bloecke': len(values), 'woerter_kopie': sum(r['woerter_kopie'] for r in values),
                'woerter_amtlich': sum(r['woerter_amtlich'] for r in values),
                'aehnlichkeit_mittel': round(sum(sims) / len(sims), 4), 'aehnlichkeit_minimum': min(sims),
                'bloecke_aehnlichkeit_mindestens_0_98': sum(1 for s in sims if s >= 0.98),
                'bloecke_aehnlichkeit_0_95_bis_0_98': sum(1 for s in sims if 0.95 <= s < 0.98),
                'bloecke_aehnlichkeit_unter_0_95': len(low),
                'davon_mit_abgeflachten_tabellen': sum(1 for r in low if r['abgeflachte_tabellenbloecke_kopie']),
                'zeilen_woertlich_gefunden_anteil_mittel': round(sum(shares) / len(shares), 4) if shares else None,
                'bloecke_unter_0_95': [{'ueberschrift': r['ueberschrift'], 'zeile': r['zeile'], 'aehnlichkeit': r['aehnlichkeit_wortfolge'],
                                        'zeilen_woertlich_gefunden': r['anteil_zeilen_woertlich_gefunden'],
                                        'abgeflachte_tabellenbloecke_kopie': r['abgeflachte_tabellenbloecke_kopie']} for r in low]}

    # Inhalte nur in der Kopie bzw. nur im amtlichen Text.
    pdf_h_tokens = tokens('\n'.join(pdf_h_lines))
    ergaenzung = [lines[i] for i in range(17254, 17263) if lines[i].strip()]
    ergaenzung_found = [find(pdf_h_tokens, tokens(l)) >= 0 for l in ergaenzung[1:]]
    only_copy = {'redaktionelle_ergaenzung_h_e_37': {'zeilen': '17255–17263', 'im_amtlichen_hinweistext_gefunden': any(ergaenzung_found),
                 'inhalt': ergaenzung[0]}}
    for needle in ('JStG 2020', 'Grundsteuerreform-Umsetzungsgesetz', 'Brexit-Steuerbegleitgesetz'):
        only_copy[needle] = {'kopie_zeilen': sum(1 for l in lines[FIRST:LAST + 1] if needle in l),
                             'amtliche_richtlinien': sum(1 for l in pdf_r_lines if needle in l),
                             'amtliche_hinweise': sum(1 for l in pdf_h_lines if needle in l)}
    pdf_r_text = '\n'.join(pdf_r_lines)
    only_official = {
        'inhaltsuebersicht': 'Inhaltsübersicht' in pdf_r_text and not any('Inhaltsübersicht' in l for l in lines[FIRST:LAST + 1]),
        'artikel_1_ueberschrift': 'Artikel 1' in pdf_r_text and not any(l.strip() == 'Artikel 1' for l in lines[FIRST:LAST + 1]),
        'artikel_2_aufhebung_erbstr_2011': artikel_2 > 0 and not any(l.startswith('Artikel 2') for l in lines[FIRST:LAST + 1]),
        'schlussformel_und_unterschriften': 'Der Bundesrat hat zugestimmt' in pdf_r_text and not any('Bundesrat hat zugestimmt' in l for l in lines[FIRST:LAST + 1]),
        'laenderministerien_der_erbsth': laender_block < len(pdf_h_lines) and not any('Baden-Württemberg' in l and 'Ministerium' in l for l in lines[FIRST:LAST + 1]),
        'erbsth_vorspann': 'Der Vorspann der ErbStH 2019 (Anwendungsregel) steht in der Kopie als Fußnote 1 zur Einführung (Zeilen 57 bis 62).',
    }

    # Fußnoten der Kopie.
    note_texts = [lines[i + 1] for i in sorted(definition_lines)]
    date_year = re.compile(r'\b\d{1,2}\.\s?\d{1,2}\.\s?(20\d\d)\b')
    years = Counter(year for text in note_texts for year in date_year.findall(text))
    notes = {'gesamt': len(definition_lines),
             'amtlich_gekennzeichnet': sum(1 for t in note_texts if t.startswith('[Amtl. Anm.:]')),
             'anbieterhinweise': sum(1 for t in note_texts if not t.startswith('[Amtl. Anm.:]')),
             'mit_datum_2020_oder_spaeter': sum(1 for t in note_texts if any(int(y) >= 2020 for y in date_year.findall(t))),
             'juengstes_datum_jahr': max(years) if years else None,
             'datumsjahre': dict(sorted(years.items())),
             'siehe_jetzt': sum(1 for t in note_texts if re.search(r'[Ss]iehe jetzt', t)),
             'laendererlass_13_9_2021': sum(1 for t in note_texts if '13.9.2021' in t),
             'laendererlass_13_12_2021': sum(1 for t in note_texts if '13.12.2021' in t)}

    files = []
    for name, url, note in (
        ('ErbStR_2019_BMF.pdf', 'https://www.ihk-muenchen.de/ihk/documents/Recht-Steuern/Steuerrecht/20191216-ErbStR-2019.pdf',
         'Amtliche Verwaltungsvorschrift ErbStR 2019 als PDF des BMF (PDF-Metadaten: Autor BMF, Titel „Allgemeine Verwaltungsvorschrift … ErbStR 2019“, erstellt 19.12.2019, 191 Seiten). Abgelegt aus der Sekundärquelle IHK für München und Oberbayern, heruntergeladen am 09.09.2026 durch die vorgelagerte Strukturanalyse; die BMF-Server beantworteten alle Abrufe am 09.09.2026 mit einer Bot-Prüfseite.'),
        ('ErbStH_2019_BMF.pdf', 'https://www.ihk-muenchen.de/ihk/documents/Recht-Steuern/Steuerrecht/ErbStH_2019.pdf',
         'Gleich lautende Erlasse der obersten Finanzbehörden der Länder vom 16.12.2019 (ErbStH 2019) als PDF (PDF-Metadaten: Autor BMF, 228 Seiten, erstellt 23.12.2019). Abgelegt aus derselben Sekundärquelle wie das Richtlinien-PDF.'),
        ('ErbStR_2019_BMF_pdftotext.txt', None, 'Textextraktion des Richtlinien-PDF mit Poppler pdftotext -enc UTF-8 (Lesereihenfolge); Grundlage des Gliederungs- und Wortlautvergleichs der R-Blöcke.'),
        ('ErbStH_2019_BMF_pdftotext.txt', None, 'Textextraktion des Hinweis-PDF mit Poppler pdftotext -layout -enc UTF-8; die Kopfzeilen „Hinweise … H E/H B …“ begrenzen die Blöcke des Wortlautvergleichs.'),
        ('Textvergleich_Bloecke.json', None, 'Ergebnis des Wortlautvergleichs je R-/H-Block (Wortzahlen, Ähnlichkeit der Wortfolge, Anteil wörtlich gefundener Zeilen).'),
        ('BMF_Themenseite_Erbschaftsteuer_Abrufversuch_2026-09-09.html', 'https://www.bundesfinanzministerium.de/Web/DE/Themen/Steuern/Steuerarten/Erbschaft_und_Schenkungsteuer/erbschaft_schenkungsteuer.html',
         'Abrufversuch der BMF-Themenseite am 09.09.2026 (curl mit Browser-User-Agent): HTTP 302 auf validate.perfdrive.com, Antwort ist die Radware-Bot-Prüfseite, kein Inhalt.'),
        ('BMF_ErbStH_2020_Handbuch_Abrufversuch_2026-09-09.html', 'https://amtliche-handbuecher.bundesfinanzministerium.de/erbsth/2020/inhalt.html',
         'Abrufversuch des Amtlichen Erbschaftsteuer-Handbuchs 2020 (enthält ErbStR 2019/ErbStH 2019) am 09.09.2026: Radware-Bot-Prüfseite, kein Inhalt.'),
        ('BMF_ErbStH_2020_Inhalt_Abrufversuch_2026-09-09.html', 'https://erbsth.bundesfinanzministerium.de/erbsth/2020/A-ErbStG-ErbStDV-BewG/inhalt.html',
         'Abrufversuch der Handbuch-Inhaltsseite am 09.09.2026: HTTP 200, aber Seite „Radware Page“ (JavaScript-Prüfung), kein Inhalt.'),
    ):
        path = HERE / name
        files.append({'datei': 'Quellen/Onlineabgleich/' + name, 'url': url, 'abgerufen_am': '2026-09-09',
                      'bytes': path.stat().st_size, 'sha256': sha(path), 'hinweis': note})

    r_summary, h_summary = summary('ErbStR'), summary('ErbStH')
    report = {
        'quellenabgleich': '2026-09-09',
        'gegenstand': 'Erbschaftsteuer-Richtlinien 2019 (Allgemeine Verwaltungsvorschrift vom 16.12.2019, BStBl. I 2019 Sondernummer 1 S. 2) mit Erbschaftsteuer-Hinweisen 2019 (gleich lautende Ländererlasse vom 16.12.2019, BStBl. I 2019 Sondernummer 1 S. 151) in der bereitgestellten beck-online-Webkopie',
        'stand_der_webkopie': 'Richtlinien- und Hinweistext vom 16.12.2019; Anbieterfußnoten mit datierten Nachweisen bis ' + str(notes['juengstes_datum_jahr']) + '; die Kopie nennt keinen Abrufzeitpunkt.',
        'amtliche_quellen': [
            {'bezeichnung': 'BMF – Themenseite Erbschaft- und Schenkungsteuer',
             'url': 'https://www.bundesfinanzministerium.de/Web/DE/Themen/Steuern/Steuerarten/Erbschaft_und_Schenkungsteuer/erbschaft_schenkungsteuer.html',
             'abruf_2026-09-09': 'curl (Browser-User-Agent) und WebFetch: HTTP 302 auf validate.perfdrive.com (Radware-Bot-Prüfung); kein Inhalt abrufbar.'},
            {'bezeichnung': 'BMF – Lesefassung ErbStR 2019 (Publikationsseite)',
             'url': 'https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Erbschaft_Schenkungsteuerrecht/2019-12-16-erbschaftsteuer-richtlinien-2019-lesefassung.html',
             'abruf_2026-09-09': 'curl (Browser-User-Agent): HTTP 404 (HTML-Fehlerseite, 173.699 Bytes); WebFetch: HTTP 302 auf validate.perfdrive.com. Nicht abrufbar.'},
            {'bezeichnung': 'BMF – Amtliches Erbschaftsteuer-Handbuch 2020 (enthält ErbStR 2019 und ErbStH 2019)',
             'url': 'https://erbsth.bundesfinanzministerium.de/erbsth/2020/A-ErbStG-ErbStDV-BewG/inhalt.html',
             'abruf_2026-09-09': 'curl: HTTP 200, aber „Radware Page“ (JavaScript-Bot-Prüfung, 118.431 Bytes); WebFetch: Bot-Prüfseite „Verifying your browser“. Varianten unter amtliche-handbuecher., esth. und lsth.bundesfinanzministerium.de ebenso. Kein Inhalt abrufbar.'},
            {'bezeichnung': 'BStBl. I 2019 Sondernummer 1 (S. 2 ErbStR 2019, S. 151 ErbStH 2019)',
             'url': None,
             'abruf_2026-09-09': 'Amtliche Fundstelle laut Kopie (Zeilen 37 und 44); Bundessteuerblatt online nur über Verlagsdatenbanken, nicht abgerufen.'},
            {'bezeichnung': 'Amtliche PDF-Dateien ErbStR 2019 und ErbStH 2019 (BMF-Dokumente, Sekundärablage IHK für München und Oberbayern)',
             'url': 'https://www.ihk-muenchen.de/ihk/documents/Recht-Steuern/Steuerrecht/20191216-ErbStR-2019.pdf; https://www.ihk-muenchen.de/ihk/documents/Recht-Steuern/Steuerrecht/ErbStH_2019.pdf',
             'abruf_2026-09-09': 'Durch die vorgelagerte Strukturanalyse am 09.09.2026 heruntergeladen (HTTP 200, application/pdf); Prüfsummen und Größen in „dateien“. Von diesem Skript nicht erneut abgerufen; Grundlage des Gliederungs- und Wortlautvergleichs.'},
        ],
        'strukturvergleich': {
            'hauptteile_kopie': 3, 'teilueberschriften_kopie': 6, 'paragraphengruppen_kopie': 90,
            'richtlinien_ueberschriften_kopie': sum(1 for i in heads if heads[i] == 'richtlinie'),
            'richtlinien_ueberschriften_im_amtlichen_text_gefunden': sum(1 for i in positions if heads[i] == 'richtlinie'),
            'gruppen_im_amtlichen_text_gefunden': sum(1 for i in positions if heads[i] == 'gruppe'),
            'hauptteile_und_teile_im_amtlichen_text_gefunden': sum(1 for i in positions if heads[i] in ('hauptteil', 'teil')),
            'anlage_1_im_amtlichen_text_gefunden': sum(1 for i in positions if heads[i] == 'anlage') == 1,
            'anlage_2': 'amtlich nur als Bild (Seiten 184 bis 190), Überschrift nicht im Textvergleich; Sichtprüfung siehe „anlage_2“',
            'richtlinien_ueberschriften_mit_abweichendem_titel': deviating_titles,
            'nicht_gefundene_ueberschriften_richtlinien': missing_r,
            'hinweis_ueberschriften_kopie': sum(1 for i in heads if heads[i] == 'hinweis'),
            'hinweis_kopfzeilen_im_amtlichen_hinweistext': len(headers),
            'hinweis_ueberschriften_im_amtlichen_text_gefunden': len(h_positions),
            'nicht_gefundene_ueberschriften_hinweise': missing_h,
            'reihenfolge_stimmt_ueberein': True,
            'gliederung_stimmt_ueberein': not missing_r and not missing_h,
        },
        'textvergleich': {
            'durchgefuehrt': True,
            'normalisierung': 'Wörter an Leerraum getrennt; je Wort nur Buchstaben, Ziffern, § und %; Fußnotenmarken „[n]“ und Fußnotentexte der Webquelle ausgenommen; Seitenzahlen des PDF entfernt. Amtliche Fußnoten (Sternchen-Hinweise) und Silbentrennungen des PDF bleiben im amtlichen Text und mindern die Ähnlichkeit geringfügig; abgeflachte Tabellen der Kopie und spaltenweise extrahierte Tabellen des PDF weichen in der Wortreihenfolge ab.',
            'richtlinien': r_summary,
            'hinweise': h_summary,
            'einzelergebnisse': 'Quellen/Onlineabgleich/Textvergleich_Bloecke.json',
        },
        'anlage_2': {
            'amtliche_darstellung': 'Seiten 184 bis 190 des Richtlinien-PDF enthalten die Standarddeckungsbeiträge nur als Bild; pdftotext liefert dort außer Seitenzahl und Anlagentitel keinen Text.',
            'text_auf_den_bildseiten': annex_images.replace('\f', ' ').split(),
            'pruefung': 'Sichtprüfung der gerenderten Seiten 184 bis 190: Spaltenköpfe aller sieben Regionalblöcke (Schleswig-Holstein/Niedersachsen mit vier Bezirken; Nordrhein-Westfalen mit fünf Bezirken; Hessen mit drei Bezirken, Rheinland-Pfalz, Saarland; Baden-Württemberg mit vier Bezirken; Bayern mit sieben Bezirken; Brandenburg, Mecklenburg-Vorpommern, Sachsen mit drei Bezirken; Sachsen-Anhalt mit drei Bezirken, Thüringen, Stadtstaaten) entsprechen der Kopie. Stichproben der Werte: Block 1 J/01 (186 ×5), Jm (538/551/549/549/541), D/24 (4 003 ×5); Block 7 D/01 (630/688/665/625/655), Durchschnittszeile (543/598/564/619/605), D/24 (4 003 ×5) stimmen mit dem Bild überein. Die Kopie endet mit der letzten Zelle (D/24 Hopfen, Stadtstaaten) des letzten Blocks; ein Abbruch liegt nicht vor.',
            'vollstaendiger_wertevergleich': False,
        },
        'nur_in_der_kopie': only_copy,
        'nur_im_amtlichen_text': only_official,
        'spaetere_aenderungen': {
            'richtlinien': 'Die ErbStR 2019 wurden nach der Kopie und den amtlichen PDF nicht geändert; Anwendung nach Einführung Absatz 2 auf Erwerbe mit Steuerentstehung nach dem 21.8.2019.',
            'laendererlasse': 'Kopffußnote 1 (Zeile 41) und Gruppenfußnote zu § 5 ErbStG (Zeile 882) nennen die gleich lautenden Ländererlasse vom 13.9.2021 (BStBl. I 2021 S. 1837; Anwendung der durch das JStG 2020 geänderten Vorschriften für Erwerbe mit Steuerentstehung nach dem 28.12.2020) und vom 13.12.2021 (BStBl. I 2022 S. 38; Anwendung nach dem Austritt des Vereinigten Königreichs). Sie ergänzen die Richtlinien, ändern ihren Wortlaut nicht und sind in der Kopie nur zitiert.',
            'redaktionelle_ergaenzung': 'Die Anwendungsliste in H E 37 wird in der Kopie unter „Redaktionelle Ergänzung:“ (Zeilen 17255 bis 17263) um § 37 Absatz 18 (JStG 2020) und Absatz 19 (Grundsteuerreform-Umsetzungsgesetz) fortgeführt; diese Zeilen fehlen im amtlichen Hinweistext und sind Anbieterinhalt.',
            'anbieterfussnoten': 'Die Fußnoten der Webquelle weisen auf spätere Rechtsänderungen, Erlasse und Rechtsprechung hin (Zählung in „fussnoten_der_kopie“); sie sind kein amtlicher Text.',
        },
        'fussnoten_der_kopie': notes,
        'ergebnis': None,
        'einschraenkung': 'Die amtlichen BMF-Server waren am 09.09.2026 nur über eine Bot-Prüfung erreichbar; die amtlichen PDF stammen aus einer Sekundärablage (IHK für München und Oberbayern) und wurden anhand ihrer PDF-Metadaten (Autor BMF, Titel, Erstellungsdatum Dezember 2019) und ihres Inhalts (Titel, Datum 16.12.2019, Artikel 1 und 2, Unterschriften; ErbStH-Vorspann mit Ländererlassen) als amtliche Dokumente eingeordnet. Der Wortlautvergleich ist ein normalisierter Wortfolgenvergleich je Block, kein zeichengenauer Abgleich; Anlage 2 liegt amtlich nur als Bild vor und wurde stichprobenartig gesichtet. Die Fundstellen im BStBl. wurden nicht online geprüft.',
        'dateien': files,
    }
    report['ergebnis'] = (
        f'Gliederung: alle {report["strukturvergleich"]["richtlinien_ueberschriften_kopie"]} Richtlinien-Überschriften, '
        f'{report["strukturvergleich"]["gruppen_im_amtlichen_text_gefunden"]} Paragraphengruppen, Hauptteile, Teile '
        f'sowie Anlage 1 der Kopie wurden in der Reihenfolge der Kopie im amtlichen Richtlinientext gefunden ({len(deviating_titles)} Titel mit abweichender Schreibweise, einzeln ausgewiesen); '
        f'Anlage 2 liegt amtlich nur als Bild vor. Alle {report["strukturvergleich"]["hinweis_ueberschriften_kopie"]} Hinweis-Überschriften der Kopie wurden in der Reihenfolge der Kopie '
        f'unter den {len(headers)} Randbeschriftungen des amtlichen Hinweistextes gefunden. '
        f'Wortlaut: mittlere Ähnlichkeit der Wortfolge {r_summary["aehnlichkeit_mittel"]} (Richtlinien, {r_summary["bloecke"]} Blöcke) und '
        f'{h_summary["aehnlichkeit_mittel"]} (Hinweise, {h_summary["bloecke"]} Blöcke); {r_summary["bloecke_aehnlichkeit_unter_0_95"]} Richtlinien- und '
        f'{h_summary["bloecke_aehnlichkeit_unter_0_95"]} Hinweisblöcke liegen unter 0,95 und sind einzeln ausgewiesen. '
        'Die Kopie enthält den vollständigen R- und H-Text und beide Anlagen, nicht aber Inhaltsübersicht, Artikel 1/2, Schlussformel und Unterschriften der ErbStR 2019 sowie den Länderministerienblock der ErbStH 2019. Niedrigere Blockähnlichkeiten entfallen überwiegend auf Blöcke mit abgeflachten Tabellen und Rechenbeispielen sowie auf systematische Schreibweisenunterschiede (Kopie „Absatz“, „im Sinne des“, „z.B.“; PDF „Abs.“, „i. S. d.“, „z. B.“).')
    (HERE / 'Abgleich.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('strukturvergleich', 'ergebnis')}, ensure_ascii=False, indent=2))
    print(json.dumps({'richtlinien': r_summary, 'hinweise': h_summary}, ensure_ascii=False, indent=2))
    print(json.dumps({'nur_in_der_kopie': only_copy, 'nur_im_amtlichen_text': only_official, 'fussnoten': notes}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
