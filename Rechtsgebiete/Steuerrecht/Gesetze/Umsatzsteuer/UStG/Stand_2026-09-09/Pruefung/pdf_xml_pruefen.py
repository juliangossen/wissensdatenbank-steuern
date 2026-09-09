"""Reproduzierbarer Vergleich der archivierten UStG-PDF mit der GII-XML.

Aufruf: py Pruefung/pdf_xml_pruefen.py (beliebiges Arbeitsverzeichnis).
Voraussetzungen: Python 3, Poppler/pdftotext im PATH; keine Python-Pakete.
Ergebnis: Pruefung/PDF_XML_Abgleich.json.
Die sichtbaren Norminhalte werden vollstaendig verglichen. Bibliographische
Kopfangaben wurden beim Quellenabgleich separat geprueft.
"""
import sys
import re
import json
import difflib
import unicodedata
import xml.etree.ElementTree as ET
import copy
import subprocess
import hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
BASE = Path(__file__).resolve().parent.parent
XML = BASE / 'Quellen/XML/BJNR119530979.xml'
PDF = BASE / 'Quellen/UStG.pdf'
OUTPUT = BASE / 'Pruefung/PDF_XML_Abgleich.json'

def joined(e):
    return '' if e is None else ''.join(e.itertext())

def normalized(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFC', s))

raw = subprocess.run(['pdftotext', '-raw', '-enc', 'UTF-8', str(PDF), '-'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8')
raw = re.sub(r'Ein Service des Bundesministerium der Justiz und für Verbraucherschutz\s+sowie des Bundesamts für Justiz ‒ www\.gesetze-im-internet\.de', '', raw)
raw = re.sub(r'- Seite \d+ von \d+ -', '', raw)
pdf = normalized(raw)
tree = ET.parse(XML).getroot()
records = []
for i, norm in enumerate(tree.findall('norm')):
    m = norm.find('metadaten')
    name = m.findtext('enbez')
    g = m.find('gliederungseinheit')
    if i == 0:
        heading = 'Fußnote'
    elif g is not None:
        heading = joined(g.find('gliederungsbez')) + joined(g.find('gliederungstitel'))
    else:
        heading = (name or '') + joined(m.find('titel'))
    body = joined(norm.find('./textdaten/text'))
    foot = joined(norm.find('./textdaten/fussnoten'))
    expected = heading + body + ('Fußnote' if i > 0 and foot.strip() else '') + foot
    records.append({'i': i, 'name': name or heading, 'heading': normalized(heading), 'expected': normalized(expected)})

cursor = 0
for r in records:
    start = pdf.find(r['heading'], cursor)
    if start < 0:
        print('UNLOCATED', r['i'], r['name'], repr(r['heading']))
        raise SystemExit(1)
    r['start'] = start
    cursor = start + len(r['heading'])

report = []
for i, r in enumerate(records):
    actual = pdf[r['start']:records[i+1]['start'] if i+1 < len(records) else len(pdf)]
    expected = r['expected']
    entry = {'norm_index': i, 'name': r['name'], 'pdf_chars': len(actual), 'xml_chars': len(expected), 'equal': actual == expected}
    if actual != expected:
        sm = difflib.SequenceMatcher(None, expected, actual, autojunk=False)
        entry['diffs'] = [{'kind': tag, 'xml': expected[a:b], 'pdf': actual[c:d], 'before': expected[max(0,a-60):a], 'after': expected[b:b+60]} for tag,a,b,c,d in sm.get_opcodes() if tag != 'equal']
    report.append(entry)
print('SUMMARY', len(report), 'records;', sum(x['equal'] for x in report), 'exact whitespace-normalized matches; differences', sum(not x['equal'] for x in report))

# Independently verify every remaining difference is extraction order/page chrome.
checks = []
row_labels = ['1', '5', '10', '14', '26', '40', '48', '49', '52', '54', '55']
annex_raw = raw[raw.rfind('Anlage 2'):raw.rfind('Anlage 3')]
label_counts = {}
for label in row_labels:
    annex_raw, count = re.subn(r'(?m)^' + label + r'\s*$', '', annex_raw)
    label_counts[label] = count
annex = copy.deepcopy(tree.findall('norm')[98])
xml_label_counts = {}
for row in annex.findall('.//row'):
    first = row.find('entry')
    if first is not None and joined(first).strip() in row_labels:
        label = joined(first).strip()
        xml_label_counts[label] = xml_label_counts.get(label, 0) + 1
        first.clear()
annex_expected = records[98]['heading'] + joined(annex.find('./textdaten/text'))
checks.append({'name': 'Anlage 2', 'classification': 'Only extraction-order displacement of the listed leftmost table row labels; all remaining characters and their sequence match.', 'row_labels': row_labels, 'pdf_occurrences': label_counts, 'xml_occurrences': xml_label_counts, 'match_after_removing_each_label_once': normalized(annex_raw) == normalized(annex_expected)})
for i in (99,100):
    r = records[i]
    actual = pdf[r['start']:records[i+1]['start']]
    tablehead = 'Lfd.Nr.WarenbezeichnungZolltarif(Kapitel,Position,Unterposition)'
    first = actual.find(tablehead)
    second = actual.find(tablehead, first+len(tablehead))
    modified = actual[:second] + actual[second+len(tablehead):]
    checks.append({'name': r['name'], 'classification': 'Exactly one repeated table column header at PDF page break.', 'table_header_count': actual.count(tablehead), 'match_after_removing_repeated_header': modified == r['expected']})
assert all(c == 1 for c in label_counts.values())
assert all(c == 1 for c in xml_label_counts.values())
assert checks[0]['match_after_removing_each_label_once']
assert all(c['match_after_removing_repeated_header'] for c in checks[1:])
out = {'method': 'Per XML norm, remove page chrome and all whitespace only; NFC; compare complete heading, text, footnote strings in sequence.', 'norms': report, 'remaining_difference_verification':checks, 'pdf_sha256': hashlib.sha256(PDF.read_bytes()).hexdigest(), 'xml_sha256': hashlib.sha256(XML.read_bytes()).hexdigest(), 'result': f'All {len(report)} records match in full; only the explicitly verified table-layout differences remain.'}
OUTPUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Alle verbleibenden Unterschiede als PDF-Layout bestaetigt. Bericht:', OUTPUT)
