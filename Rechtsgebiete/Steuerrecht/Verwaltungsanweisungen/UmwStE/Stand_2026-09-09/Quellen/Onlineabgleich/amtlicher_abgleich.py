"""Amtlicher Abgleich der UmwStE-2025-Webkopie mit den BMF-Veröffentlichungen.

Liest die archivierte Webkopie sowie die im selben Ordner gesicherten amtlichen PDF-Dateien
(BMF-Schreiben vom 2.1.2025 und Änderungsschreiben vom 1.8.2025) und schreibt Abgleich.json,
Randnummernabgleich.json und Textabgleich_Abweichungen.txt. Es wird nichts heruntergeladen;
die Adressen und Abrufangaben stehen als Konstanten im Skript.

Vergleichsschritte:
1. Prüfsummen und Größen der gesicherten Dateien.
2. Vollständigkeit und Reihenfolge der Randnummern (Kopie gegen die Randmarken der PDF).
3. Wortlautvergleich je Randnummer nach dokumentierter Normalisierung (difflib-Ähnlichkeit).
4. Neufassungen der Rn. 15.35a und Org.03 gegen das Änderungsschreiben vom 1.8.2025.
5. Amtliche Fußnoten der PDF gegen die als „[Amtl. Anm.:]“ gekennzeichneten Fußnoten der Kopie.
6. Inhaltsverzeichnis der Kopie gegen das Inhaltsverzeichnis der PDF (Bezeichnung und Titel).
"""
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re

import fitz  # PyMuPDF

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
SOURCE = BASE / 'Quellen/UmwStE_2025_Webkopie.txt'
ABRUF = '2026-09-09'
FILES = [
    {'datei': 'Quellen/Onlineabgleich/2025-01-02-umwStE.pdf',
     'url': 'https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Koerperschaftsteuer_Umwandlungssteuer/2025-01-02-umwStE.pdf?__blob=publicationFile',
     'hinweis': 'BMF-Schreiben vom 2.1.2025 (UmwStE 2025) in der Ursprungsfassung; Anschreiben S. 1, Inhaltsverzeichnis S. 2 bis oberer Teil von S. 9, Erlasstext ab S. 9 bis S. 89 mit Randnummern am Seitenrand (HTTP 200, application/pdf, curl mit Browser-User-Agent).'},
    {'datei': 'Quellen/Onlineabgleich/2025-01-02-umwStE_pdftotext.txt', 'url': None,
     'hinweis': 'Textextraktion der PDF mit Poppler pdftotext -layout -enc UTF-8 (nur zur Einsicht; der Abgleich nutzt PyMuPDF).'},
    {'datei': 'Quellen/Onlineabgleich/2025-08-01-aenderung-bmf-schreiben-umwste.pdf',
     'url': 'https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Koerperschaftsteuer_Umwandlungssteuer/2025-08-01-aenderung-bmf-schreiben-umwste.pdf?__blob=publicationFile&v=7',
     'hinweis': 'BMF-Schreiben vom 1.8.2025 (GZ IV C 2 - S 1978/00051/004/026): Neufassung der Rn. 15.35a und Org.03, 3 Seiten (HTTP 200, application/pdf).'},
    {'datei': 'Quellen/Onlineabgleich/2025-08-01-aenderung-bmf-schreiben-umwste_pdftotext.txt', 'url': None,
     'hinweis': 'Textextraktion des Änderungsschreibens mit Poppler pdftotext -layout -enc UTF-8; Grundlage des Vergleichs der Neufassungen.'},
]
ABBILDUNGEN = [
    {'datei': 'Quellen/Abbildungen/BMF_2025-01-02_Seite-11.png', 'pdf_seite': 11, 'randnummern': ['01.10', '01.12'],
     'hinweis': 'Verschmelzungstabelle (Rn. 01.10) mit Fußnoten 1 bis 9 und Beginn der Formwechseltabelle (Rn. 01.12).'},
    {'datei': 'Quellen/Abbildungen/BMF_2025-01-02_Seite-12.png', 'pdf_seite': 12, 'randnummern': ['01.12', '01.17'],
     'hinweis': 'Ende der Formwechseltabelle (Rn. 01.12), Spaltungstabelle (Rn. 01.17) mit Fußnoten 1 bis 3.'},
    {'datei': 'Quellen/Abbildungen/BMF_2025-01-02_Seite-13.png', 'pdf_seite': 13, 'randnummern': ['01.19'],
     'hinweis': 'Vermögensübertragungstabelle (Rn. 01.19).'},
]
BODY, LAST = 1353, 7495          # 0-basiert: Zeilen 1354 bis 7496 der Kopie
RN = re.compile(r'^(?!31\.12)(\d{2}|E \d{2}|Org|K|S)\.\d{2}[a-z]?(?: bis 27\.11)?')
RN_PDF = re.compile(r'^(\d{2}|Org|K|S)\.\d{2}[a-z]?$')
HEADING = re.compile(r'^(?:(?:Erstes|Zweites) Kapitel: |(?:Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebter|Achter|Neunter|Zehnter) Teil\. |Besonderer Teil zum UmwStG$|[A-H]\. |[IVX]+a?\. |\d{1,2}\. (?!Schritt$)|[a-e]\) |[a-e]{2}\) |\(\d\) )')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    """Dokumentierte Normalisierung für den Wortlautvergleich (beide Seiten gleich)."""
    s = text.replace(' ', '').replace('\xa0', ' ').replace('­', '')
    s = s.replace('×', 'x').replace('½', '1/2').replace('¼', '1/4').replace('⅕', '1/5').replace('⅘', '4/5')
    s = re.sub(r'[„“”"‚‘’]', '', s)
    s = re.sub(r'\bAbsatz\b', 'Abs.', s)
    s = re.sub(r'\bAbsätze\b', 'Abs.', s)
    s = re.sub(r'\bNummer\b', 'Nr.', s)
    s = re.sub(r'\bNummern\b', 'Nr.', s)
    s = re.sub(r'\bBuchstabe\b', 'Buchst.', s)
    s = re.sub(r'\bArtikel\b', 'Art.', s)
    months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
    s = re.sub(r'\b(\d{1,2})\. (' + '|'.join(months) + r') (\d{4})\b',
               lambda m: f'{int(m[1])}.{months.index(m[2]) + 1}.{m[3]}', s)
    s = re.sub(r'\bBStBl\.?\s+(\d{4})\s+(I{1,2})\s+S\.', r'BStBl. \2 \1 S.', s)      # Jahresangabe vereinheitlichen
    s = re.sub(r'\bBStBl\.?\s+(I{1,2})\s+(\d{4})\s+S\.', r'BStBl. \1 \2 S.', s)
    s = re.sub(r'\bBStBl\.?\s+(I{1,2})\s+S\.', r'BStBl. \1 S.', s)
    s = re.sub(r'(?<=\d)\.(?=\d{3}(?!\d))', '', s)                            # Tausenderpunkte der PDF
    s = re.sub(r'\bim Sinne des\b', 'i.S.d.', s)
    s = re.sub(r'\bim Sinne der\b', 'i.S.d.', s)
    s = re.sub(r'\bim Sinne von\b', 'i.S.v.', s)
    s = re.sub(r'\bin Höhe von\b', 'i.H.v.', s)
    s = re.sub(r'\bin Höhe des\b', 'i.H.d.', s)
    s = re.sub(r'\bin Höhe der\b', 'i.H.d.', s)
    s = re.sub(r'\bim Rahmen des\b', 'i.R.d.', s)
    s = re.sub(r'\bim Rahmen der\b', 'i.R.d.', s)
    s = re.sub(r'\bim Rahmen von\b', 'i.R.v.', s)
    s = re.sub(r'\bin Verbindung mit\b', 'i.V.m.', s)
    s = re.sub(r'\bin der Fassung\b', 'i.d.F.', s)
    s = re.sub(r'\bzum Beispiel\b', 'z.B.', s)
    s = re.sub(r'\bHalbs\.', 'Halbsatz', s)
    for _ in range(3):
        s = re.sub(r'(?<![A-Za-zÄÖÜäöü])([A-Za-z])\. (?=[A-Za-z]\.)', r'\1.', s)
    # Abkürzung und ausgeschriebene Wendung auf eine neutrale Form (ohne Artikel) bringen.
    s = re.sub(r'\bArtikels?\b', 'Art.', s)
    s = re.sub(r'\bim Rahmen (?:des|der|von|einer|eines|eine|einen)\b', 'IR', s, flags=re.I)
    s = re.sub(r'\bim Rahmen\b', 'IR', s, flags=re.I)
    s = re.sub(r'\bi\.R\.(?:d\.|v\.)?(?: (?:des|der|von|einer|eines|eine|einen)\b)?', 'IR', s, flags=re.I)
    s = re.sub(r'\bin Höhe (?:des|der|von|einer|eines)\b', 'IH', s, flags=re.I)
    s = re.sub(r'\bi\.H\.(?:d\.|v\.)?(?: (?:des|der|von|einer|eines)\b)?', 'IH', s, flags=re.I)
    s = re.sub(r'\bim Sinne (?:des|der|von|einer|eines)\b', 'IS', s, flags=re.I)
    s = re.sub(r'\bi\.S\.(?:d\.|v\.)?(?: (?:des|der|von|einer|eines)\b)?', 'IS', s, flags=re.I)
    s = re.sub(r'\bim Übrigen\b', 'i.ü.', s, flags=re.I)
    return re.sub(r'[\s\-–,]', '', s).lower()


def load_pdf_segments(pdf_path):
    """Randmarken und Haupttext der amtlichen PDF, nach Randnummern segmentiert."""
    doc = fitz.open(pdf_path)
    markers = []        # (seite, y, label)
    lines = []          # (seite, y, text, klein)
    sizes = Counter()
    footnotes = []
    for pno in range(8, doc.page_count):
        page = doc[pno]
        data = page.get_text('dict')
        for block in data['blocks']:
            for line in block.get('lines', []):
                spans = [s for s in line['spans'] if s['text'].strip()]
                if not spans:
                    continue
                x0 = min(s['bbox'][0] for s in spans)
                y0 = min(s['bbox'][1] for s in spans)
                text = ''.join(s['text'] for s in spans).strip()
                size = max(s['size'] for s in spans)
                sizes[round(size)] += 1
                if (x0 < 70 or x0 > 510) and re.fullmatch(r'(E )?(\d{2}|Org|K|S)\.\d{2}[a-z]?( bis 27\.11)?', text):
                    markers.append((pno + 1, y0, text))
                    continue
                if (x0 < 70 or x0 > 510) and re.fullmatch(r'\d{2}\.\d{2}[a-z]?\s+bis', text):
                    markers.append((pno + 1, y0, text.split()[0] + ' bis 27.11'))
                    continue
                if y0 > 790 and re.fullmatch(r'\d{1,2}', text):
                    continue        # Seitenzahl
                small = size < 7.4
                big = [s for s in spans if s["size"] >= 7.4]
                if small:
                    footnotes.append((pno + 1, y0, x0, text))
                    continue
                # Hochgestellte Fußnotenziffern (kleine Spans) aus dem Haupttext entfernen.
                text = ''.join(s['text'] for s in big).strip()
                if text:
                    lines.append((pno + 1, y0, text))
    return markers, lines, footnotes, sizes


def main():
    data = SOURCE.read_bytes()
    lines = data.decode('utf-8').splitlines()
    assert len(lines) == 7778
    files = []
    for item in FILES:
        path = BASE / item['datei']
        files.append({**item, 'abgerufen_am': ABRUF, 'bytes': path.stat().st_size, 'sha256': sha(path)})
    pdf_path = BASE / FILES[0]['datei']
    doc = fitz.open(pdf_path)
    pdf_pages = doc.page_count

    # 2. Randnummern der Kopie.
    copy_rn = []
    for index in range(BODY, LAST + 1):
        match = RN.match(lines[index])
        if match:
            copy_rn.append((match[0], index))
    copy_labels = [label for label, _ in copy_rn]
    assert len(copy_labels) == len(set(copy_labels)) == 572, len(copy_labels)

    markers, pdf_lines, pdf_footnotes, sizes = load_pdf_segments(pdf_path)
    markers.sort(key=lambda m: (m[0], m[1]))
    pdf_sequence = []
    for page, y, label in markers:
        if pdf_sequence and pdf_sequence[-1][0] == label:
            continue        # Wiederholung einer Randnummer beim Seitenwechsel
        pdf_sequence.append((label, page))
    pdf_labels = [label for label, _ in pdf_sequence]
    pdf_expanded = []
    for label in pdf_labels:
        pdf_expanded.append(label)
    # In der PDF stehen „27.09 bis“ und „27.11“ als getrennte Randmarken auf einer Höhe.
    if '27.09 bis 27.11' in pdf_expanded and '27.11' in pdf_expanded:
        pdf_expanded.remove('27.11')
    missing_in_pdf = [label for label in copy_labels if label not in pdf_expanded]
    missing_in_copy = [label for label in pdf_expanded if label not in copy_labels]
    same_order = [l for l in copy_labels if l in pdf_expanded] == [l for l in pdf_expanded if l in copy_labels]
    rn_page = {label: page for label, page in pdf_sequence}

    # 3. Wortlautvergleich je Randnummer.
    heading_norms = {norm(lines[i]) for i in range(BODY, LAST + 1) if HEADING.match(lines[i]) and lines[i].strip()}
    marker_positions = [(page, y, label) for page, y, label in markers]
    segments_pdf = {}
    current = None
    for page, y, text in sorted(pdf_lines, key=lambda l: (l[0], l[1])):
        while marker_positions and (marker_positions[0][0], marker_positions[0][1] - 2.5) <= (page, y):
            current = marker_positions.pop(0)[2]
        if current is None:
            continue
        key = current
        segments_pdf.setdefault(key, []).append((page, y, text))

    def join_pdf(items):
        # Fragmente gleicher Zeilenhöhe (z. B. „I.“ + „Sachlicher Anwendungsbereich“) zusammenführen.
        merged = []
        for page, y, text in items:
            if merged and merged[-1][0] == page and abs(merged[-1][1] - y) < 1.5:
                merged[-1] = (page, y, merged[-1][2] + ' ' + text)
            else:
                merged.append((page, y, text))
        parts = [text for _, _, text in merged]
        out = ''
        position = 0
        while position < len(parts):
            # Gliederungsüberschriften (auch über zwei bis drei PDF-Zeilen umbrochen) auslassen.
            skip = 0
            for width in (1, 2, 3):
                if position + width <= len(parts) and norm(' '.join(parts[position:position + width])) in heading_norms:
                    skip = width
            if skip:
                position += skip
                continue
            part = parts[position]
            if out.endswith('-') and part[:1].islower():
                out = out[:-1] + part
            else:
                out += ' ' + part
            position += 1
        return out

    segments_copy = {}
    for position, (label, index) in enumerate(copy_rn):
        end = copy_rn[position + 1][1] if position + 1 < len(copy_rn) else LAST + 1
        parts = []
        for i in range(index, end):
            text = lines[i]
            if not text.strip() or (i != index and HEADING.match(text)):
                continue
            if i == index:
                text = text[len(label):]
            parts.append(text)
        segments_copy[label] = ' '.join(parts)

    results = []
    buckets = Counter()
    diffs = []
    for label, index in copy_rn:
        pdf_key = label if label in segments_pdf else ('27.09 bis 27.11' if label.startswith('27.09') else label)
        a = norm(segments_copy[label])
        b = norm(join_pdf(segments_pdf.get(pdf_key, [])))
        ratio = SequenceMatcher(None, a, b, autojunk=False).ratio() if (a or b) else 1.0
        if ratio >= 0.995:
            klasse = 'uebereinstimmend'
        elif ratio >= 0.98:
            klasse = 'geringe_abweichung'
        elif ratio >= 0.95:
            klasse = 'abweichung'
        else:
            klasse = 'deutliche_abweichung'
        buckets[klasse] += 1
        results.append({'rn': label, 'zeile_kopie': index + 1, 'pdf_seite': rn_page.get(pdf_key),
                        'zeichen_kopie': len(a), 'zeichen_pdf': len(b), 'aehnlichkeit': round(ratio, 4), 'klasse': klasse})
        if ratio < 0.995:
            matcher = SequenceMatcher(None, a, b, autojunk=False)
            detail = []
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != 'equal':
                    detail.append(f'  {tag}: Kopie „{a[max(0, i1 - 25):i2 + 25]}“ | PDF „{b[max(0, j1 - 25):j2 + 25]}“')
            diffs.append(f'Rn. {label} (Kopie Zeile {index + 1}, PDF Seite {rn_page.get(pdf_key)}, Ähnlichkeit {ratio:.4f}, '
                         f'{len(a)}/{len(b)} Zeichen)\n' + '\n'.join(detail[:40]) + '\n')

    # 4. Änderungsschreiben vom 1.8.2025.
    change_text = (BASE / FILES[3]['datei']).read_text(encoding='utf-8')
    part_a = change_text.split('1. Rn. 15.35a wird wie folgt gefasst:')[1].split('2. Rn. Org.03 wird wie folgt gefasst:')[0]
    part_b = change_text.split('2. Rn. Org.03 wird wie folgt gefasst:')[1].split('Im Auftrag')[0]
    part_a = re.sub(r'Seite \d von 3', '', part_a)

    def dehyphen(text):
        out = ''
        for part in text.splitlines():
            part = part.strip()
            if not part:
                continue
            if out.endswith('-') and part[:1].islower():
                out = out[:-1] + part
            else:
                out += ' ' + part
        return out

    ratio_15_35a = SequenceMatcher(None, norm(segments_copy['15.35a']), norm(dehyphen(part_a)), autojunk=False).ratio()
    ratio_org_03 = SequenceMatcher(None, norm(segments_copy['Org.03']), norm(dehyphen(part_b)), autojunk=False).ratio()
    ratio_15_35a_old = next(r['aehnlichkeit'] for r in results if r['rn'] == '15.35a')
    ratio_org_03_old = next(r['aehnlichkeit'] for r in results if r['rn'] == 'Org.03')

    # 5. Amtliche Fußnoten.
    copy_footnotes = []
    for index in range(7497, len(lines)):
        match = re.fullmatch(r'\[(\d+)\] ', lines[index])
        if match:
            text = lines[index + 1]
            if text.startswith('[Amtl. Anm.:] '):
                copy_footnotes.append((int(match[1]), text[len('[Amtl. Anm.:] '):].removesuffix('zurück zum Text')))
    # Fußnotenzeilen der PDF: kleiner Schriftgrad, linker Rand (x < 100 pt), unteres Seitendrittel (y > 600 pt);
    # Tabellenzellen der Umwandlungsmatrizen (ebenfalls kleiner Schriftgrad) liegen rechts davon oder höher.
    pdf_fn_texts = []
    grouped = {}
    for page, y, x, text in sorted(pdf_footnotes, key=lambda f: (f[0], f[1])):
        if x < 100 and y > 600:
            grouped.setdefault(page, []).append(text)
    for page, parts in grouped.items():
        current = None
        for part in parts:
            if re.match(r'^\d{1,2}\)?\s*\S', part):
                if current:
                    pdf_fn_texts.append(current)
                current = [page, re.sub(r'^\d{1,2}\)?\s*', '', part)]
            elif current:
                if current[1].endswith('-') and part[:1].islower():
                    current[1] = current[1][:-1] + part
                else:
                    current[1] += ' ' + part
        if current:
            pdf_fn_texts.append(current)
    # Tabelleninterne Anmerkungen der PDF (Zeichen ❶ statt Ziffer, Haupttextgröße), z. B. „DBA-Quellensteuerrecht“.
    for page, text in [(p, t) for p, _, t in pdf_lines] + [(p, t) for p, _, _, t in pdf_footnotes]:
        if 'DBA-Quellensteuer' in text and len(text) < 30:
            pdf_fn_texts.append([page, 'DBA-Quellensteuerrecht'])
        elif 'Residualgröße' in text and len(text) < 20:
            pdf_fn_texts.append([page, 'Residualgröße'])
    pdf_fn_norm = [(page, norm(text)) for page, text in pdf_fn_texts]

    def same(a, b):
        return bool(a and b) and (a in b or b in a or SequenceMatcher(None, a, b, autojunk=False).ratio() > 0.9)

    matched = []
    unmatched_copy = []
    for number, text in copy_footnotes:
        target = norm(text)
        hits = [page for page, value in pdf_fn_norm if same(value, target)]
        if hits:
            matched.append({'fussnote': number, 'pdf_seiten': sorted(set(hits))})
        else:
            unmatched_copy.append({'fussnote': number, 'text': text})
    unmatched_pdf = [{'pdf_seite': page, 'text': text} for (page, text), (_, value) in zip(pdf_fn_texts, pdf_fn_norm)
                     if not any(same(value, norm(t)) for _, t in copy_footnotes)]

    # 6. Inhaltsverzeichnis.
    toc_copy = []
    entry = []
    for index in range(12, 1352):
        if lines[index].strip():
            entry.append(lines[index])
        elif entry:
            toc_copy.append(entry)
            entry = []
    if entry:
        toc_copy.append(entry)
    toc_copy_titles = [norm(' '.join(e[:2])) for e in toc_copy]
    # Inhaltsverzeichnis der PDF: Seiten 2 bis 9, Schriftgrad 7,56 pt (Erlasstext 8 pt, Randmarken 7 pt).
    pdf_toc_lines = []
    for pno in range(1, 9):
        for block in doc[pno].get_text('dict')['blocks']:
            for line in block.get('lines', []):
                spans = [s for s in line['spans'] if s['text'].strip()]
                if spans and all(7.3 < s['size'] < 7.8 for s in spans):
                    raw = ''.join(s['text'] for s in spans).strip()
                    if raw and raw != 'Rn.' and not re.fullmatch(r'\d{1,2}', raw):
                        pdf_toc_lines.append(raw)
    RANGE = r'(?:E ?)?(?:\d{2}|Org|K|S)\.\d{2}[a-z]?(?:\s*–\s*(?:E ?)?(?:\d{2}|Org|K|S)\.\d{2}[a-z]?)?'
    pdf_toc_titles = []
    buffer = ''
    for raw in pdf_toc_lines:
        if re.fullmatch(RANGE, raw):
            continue
        cleaned = re.sub(r'\s*\.{3,}.*$', '', raw)
        cleaned = re.sub(r'\s+' + RANGE + r'$', '', cleaned).strip().rstrip('.').strip()
        if re.match(r'^(?:(?:Erstes|Zweites) Kapitel:|(?:Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebter|Achter|Neunter|Zehnter) Teil\.|Besonderer Teil|[A-H]\.\s|[IVX]+a?\.\s|\d{1,2}\.\s|[a-e]\)\s|[a-e]{2}\)\s|\(\d\)\s)', cleaned):
            if buffer:
                pdf_toc_titles.append(buffer)
            buffer = cleaned
        elif buffer:
            buffer += ' ' + cleaned
    if buffer:
        pdf_toc_titles.append(buffer)
    pdf_toc_norm = [norm(t) for t in pdf_toc_titles]
    only_copy = [' '.join(toc_copy[i][:2]) for i, t in enumerate(toc_copy_titles) if t not in pdf_toc_norm]
    only_pdf = [pdf_toc_titles[i] for i, t in enumerate(pdf_toc_norm) if t not in toc_copy_titles]
    copy_with_rn = sum(1 for e in toc_copy if len(e) == 3)
    pdf_rn_entries = sum(1 for raw in pdf_toc_lines if re.fullmatch(r'(?:E ?)?(?:\d{2}|Org|K|S)\.\d{2}[a-z]?(?:\s*–\s*(?:E ?)?(?:\d{2}|Org|K|S)\.\d{2}[a-z]?)?', raw))

    unter_0995 = [r for r in results if r['klasse'] != 'uebereinstimmend']
    report = {
        'quellenabgleich': ABRUF,
        'stand_der_webkopie': 'BMF-Schreiben vom 2.1.2025 (BStBl. I S. 92), geändert durch BMF v. 1.8.2025 (BStBl. I S. 1591); Zeile 7 der Kopie.',
        'amtliche_quellen': {
            'grundfassung': {'datei': FILES[0]['datei'], 'pdf_seiten': pdf_pages, 'pdf_titel': doc.metadata.get('title'), 'pdf_erstellt': doc.metadata.get('creationDate')},
            'aenderungsschreiben': {'datei': FILES[2]['datei'], 'pdf_seiten': fitz.open(BASE / FILES[2]['datei']).page_count},
            'themenseite': {'url': 'https://www.bundesfinanzministerium.de/Web/DE/Themen/Steuern/Steuerarten/Umwandlungssteuer/umwandlungssteuer.html',
                            'abruf': 'nicht möglich: Aufruf wird auf eine Bot-Prüfseite (validate.perfdrive.com) umgeleitet; deshalb keine amtliche Bestätigung, dass nach dem 1.8.2025 kein weiteres Änderungsschreiben ergangen ist.'},
        },
        'randnummern': {
            'kopie': len(copy_labels), 'pdf_randmarken': len(pdf_expanded),
            'fehlen_in_pdf': missing_in_pdf, 'fehlen_in_kopie': missing_in_copy, 'gleiche_reihenfolge': same_order,
            'hinweis': 'Randmarken der PDF aus den Seitenrändern (x < 70 pt oder x > 510 pt) mit PyMuPDF gelesen; „27.09 bis 27.11“ steht in Kopie und PDF als Sammelangabe.',
        },
        'wortlautvergleich': {
            'verfahren': 'Je Randnummer wird der Text der Kopie (Rn-Zeile bis zur nächsten Rn-Zeile ohne Gliederungsüberschriften) mit dem Haupttext der PDF zwischen den Randmarken verglichen (Schriftgrad ≥ 7,4 pt; Fußnoten, Seitenzahlen, hochgestellte Ziffern und Gliederungsüberschriften ausgeschlossen). Ähnlichkeit = difflib.SequenceMatcher.ratio auf den normalisierten Zeichenketten.',
            'normalisierung': ['Leerraum, Bindestriche, Gedankenstriche, Kommas und schmale Leerzeichen entfernt; Kleinschreibung',
                               'Absatz→Abs., Nummer→Nr., Buchstabe→Buchst., Artikel→Art.; ausgeschriebene Monatsnamen → numerisches Datum; BStBl→BStBl.; Jahresangabe in BStBl-Zitaten vereinheitlicht',
                               'Leerzeichen in Buchstabenabkürzungen (i. S. d.) entfernt; „im Sinne des/der“ und i.S.d./i.S.v., „in Höhe von/des“ und i.H.v./i.H.d., „im Rahmen des/der/einer“ und i.R.d./i.R. jeweils auf eine neutrale Form ohne Artikel gebracht (auch am Satzanfang); im Übrigen→i.ü., in Verbindung mit→i.V.m., in der Fassung→i.d.F., zum Beispiel→z.B.',
                               'Tausenderpunkte der PDF entfernt; Anführungszeichen entfernt; × → x; ½ ¼ ⅕ ⅘ → 1/2 1/4 1/5 4/5',
                               'Silbentrennung am Zeilenende der PDF zusammengeführt (Bindestrich + Kleinbuchstabe)'],
            'klassen': {'uebereinstimmend (>= 0,995)': buckets['uebereinstimmend'], 'geringe_abweichung (0,98–0,995)': buckets['geringe_abweichung'],
                        'abweichung (0,95–0,98)': buckets['abweichung'], 'deutliche_abweichung (< 0,95)': buckets['deutliche_abweichung']},
            'randnummern_unter_0995': [{'rn': r['rn'], 'aehnlichkeit': r['aehnlichkeit'], 'pdf_seite': r['pdf_seite']} for r in unter_0995],
            'einzelwerte': 'Quellen/Onlineabgleich/Randnummernabgleich.json',
            'abweichungsprotokoll': 'Quellen/Onlineabgleich/Textabgleich_Abweichungen.txt',
        },
        'aenderungsschreiben_2025_08_01': {
            'rn_15_35a_aehnlichkeit_neufassung': round(ratio_15_35a, 4), 'rn_15_35a_aehnlichkeit_grundfassung_pdf': ratio_15_35a_old,
            'rn_org_03_aehnlichkeit_neufassung': round(ratio_org_03, 4), 'rn_org_03_aehnlichkeit_grundfassung_pdf': ratio_org_03_old,
        },
        'amtliche_fussnoten': {
            'kopie_amtl_anm': len(copy_footnotes), 'pdf_fussnoten_erkannt': len(pdf_fn_texts),
            'kopie_fussnoten_mit_pdf_entsprechung': len(matched), 'kopie_fussnoten_ohne_pdf_entsprechung': unmatched_copy,
            'pdf_fussnoten_ohne_kopie_entsprechung': unmatched_pdf,
            'hinweis': 'PDF-Fußnoten = Zeilen mit Schriftgrad < 7,4 pt am linken Rand im unteren Seitendrittel sowie die tabelleninternen Anmerkungen „Residualgröße“ und „DBA-Quellensteuerrecht“ (Zeichen ❶); Zuordnung über Textgleichheit (Teilstring oder Ähnlichkeit > 0,9 nach Normalisierung). Die Fußnoten [2] bis [5] der Kopie (BStBl-Fundstellen) sind Zusätze der BStBl-Fassung.',
        },
        'inhaltsverzeichnis': {
            'eintraege_kopie': len(toc_copy), 'eintraege_pdf': len(pdf_toc_titles),
            'eintraege_mit_rn_angabe_kopie': copy_with_rn, 'rn_angaben_pdf': pdf_rn_entries,
            'nur_in_kopie': only_copy, 'nur_in_pdf': only_pdf,
        },
        'pdf_schriftgrade': dict(sorted(sizes.items())),
        'abbildungen': [{**item, 'bytes': (BASE / item['datei']).stat().st_size, 'sha256': sha(BASE / item['datei']),
                         'erzeugt_mit': 'pdftoppm -r 150 -png aus der gesicherten PDF'} for item in ABBILDUNGEN],
        'dateien': files,
    }
    (HERE / 'Randnummernabgleich.json').write_text(json.dumps(results, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (HERE / 'Textabgleich_Abweichungen.txt').write_text(
        'Wortlautvergleich Webkopie gegen BMF-PDF vom 2.1.2025 je Randnummer (nur Ähnlichkeit < 0,995).\n'
        'Normalisierung siehe Abgleich.json. Ausschnitte nach Normalisierung (Leerraum entfernt, Kleinschreibung).\n\n' + '\n'.join(diffs), encoding='utf-8')
    return report


if __name__ == '__main__':
    result = main()
    (HERE / 'Abgleich.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('dateien',)}, ensure_ascii=False, indent=2))
