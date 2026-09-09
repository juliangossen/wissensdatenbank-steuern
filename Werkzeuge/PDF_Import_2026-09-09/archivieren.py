"""Prüft diesen PDF-Import und registriert zuvor sicher verschobene Originale.

Vorbereiten schreibt ausschließlich einen überprüfbaren Ablageplan. Die eigentliche
Verschiebung erfolgt durch archivieren.ps1 mit LiteralPath und erneutem Hashvergleich.
"""
from pathlib import Path
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REGISTER = ROOT / 'PDF_Archiv/Archivregister.json'
DATE = '2026-09-09'
VERSION = 'Stand_' + DATE


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def local(relative):
    path = (ROOT / relative).resolve()
    assert path.is_relative_to(ROOT), f'Pfad außerhalb des Projekts: {relative}'
    return path


def prepare():
    inputs = read(HERE / 'Eingang.json')['pdfs']
    assert len(inputs) == len({x['datei'] for x in inputs})
    assert len(inputs) == len({x['sha256_pdf'] for x in inputs}), 'Doppelte Eingangsquelle'
    by_hash = {x['sha256_pdf']: x for x in inputs}
    candidates = {}
    for config in (ROOT / 'Rechtsgebiete').glob('**/Pruefung/konfiguration.json'):
        c = read(config)
        base = config.parent.parent
        pdf = base / 'Quellen' / c['lokale_pdf']
        if not pdf.is_file() or sha(pdf) not in by_hash:
            continue
        digest = sha(pdf)
        assert digest not in candidates, f'Doppelte Konvertierung: {config}'
        original = by_hash[digest]
        source = local(original['datei'])
        assert source.is_file() and sha(source) == digest, f'Eingang verändert: {source}'
        assert base.name == VERSION and c['quellenabgleich'] == DATE
        md = base / c.get('markdown_datei', c['kuerzel'] + '.md')
        check = read(config.parent / 'Vollstaendigkeitspruefung.json')
        report = config.parent / 'Pruefbericht.md'
        assert md.is_file() and report.is_file(), f'Markdown oder Prüfbericht fehlt: {md}; {report}'
        assert sha(md) == check['sha256_markdown'], f'Markdown verändert: {md}'
        assert digest == check['sha256_pdf'], f'Prüfung andere PDF: {config}'
        assert c['pdf_seiten'] == original['seiten']
        if c.get('xml_datei'):
            assert check['alle_textbloecke_identisch'] is True
            structure = read(config.parent / 'Markdown_Strukturpruefung.json')
            assert structure['alle_normen_identisch'] is True
            assert structure['sha256_markdown'] == sha(md)
            pdf_check = read(config.parent / 'PDF_XML_Abgleich.json')
            assert pdf_check.get('sha256_pdf', pdf_check.get('pdf_sha256')) == digest
            assert pdf_check.get('sha256_xml', pdf_check.get('xml_sha256')) == check['sha256_xml']
            exact = pdf_check.get('alle_normen_vollstaendig_gleich') is True
            layout_confirmed = pdf_check.get('alle_normen_vollstaendig_bestaetigt') is True
            supplemented = pdf_check.get('abgleich_erfolgreich_mit_dokumentierter_ergaenzung') is True
            assert exact or layout_confirmed or supplemented, f'PDF-Abgleich noch offen: {config}'
            if layout_confirmed:
                assert len(pdf_check['normen']) == pdf_check['normdatensaetze']
                assert all(n['identisch'] or n.get('ausnahmepruefung', {}).get('vollstaendig_bestaetigt') is True
                           for n in pdf_check['normen'])
            if supplemented:
                assert c['kuerzel'] == 'InvStG'
                differences = [n for n in pdf_check['norms'] if not n['nach_layoutabgleich_identisch']]
                assert len(differences) == 1 and differences[0]['norm_index'] == 0
                notes = differences[0]['layoutpruefung']
                assert len(notes) == 1 and notes[0]['zeichen'] == 119
                assert notes[0]['amtliche_xml_vollstaendig_in_markdown'] is True
                assert notes[0]['restlicher_text_identisch'] is True
                assert (config.parent / notes[0]['screenshot']).is_file()
            assert sha(base / c['xml_datei']) == check['sha256_xml']
        else:
            assert check['pruefung_erfolgreich'] is True
        area = base.parent.relative_to(ROOT / 'Rechtsgebiete')
        target = local((Path('PDF_Archiv/02_In_Markdown_umgewandelt') / VERSION / area / source.name).as_posix())
        assert not target.exists(), f'Archivziel bereits vorhanden: {target}'
        entry = {
            'dokument': c['titel'], 'kuerzel': c['kuerzel'], 'bereich': c['rechtsgebiet'],
            'urspruenglicher_dateiname': source.name, 'status': 'in_markdown_umgewandelt',
            'archivversion': VERSION, 'quellenabgleich': DATE,
            'pdf': target.relative_to(ROOT).as_posix(),
            'markdown': md.relative_to(ROOT).as_posix(),
            'pruefbericht': report.relative_to(ROOT).as_posix(),
            'pdf_seiten': c['pdf_seiten'], 'sha256_pdf': digest,
            'sha256_markdown': sha(md), 'quellenstand': c['stand'],
            'quelle': c.get('quelle_html', c['quelle_url']),
        }
        candidates[digest] = {'quelle': source.relative_to(ROOT).as_posix(), 'eintrag': entry}
    missing = [x['datei'] for x in inputs if x['sha256_pdf'] not in candidates]
    assert not missing, f'Noch nicht fertig konvertiert: {missing}'
    register = read(REGISTER)
    old_hashes = {e['sha256_pdf'] for e in register['eintraege']}
    assert not old_hashes.intersection(by_hash), 'Eingangsquelle bereits registriert'
    plan = {'projektwurzel': str(ROOT), 'quellenabgleich': DATE,
            'sha256_register_vorher': sha(REGISTER),
            'dokumente': [candidates[x['sha256_pdf']] for x in inputs]}
    write(HERE / 'Archivregister_vorher.json', register)
    write(HERE / 'Ablageplan.json', plan)
    print(json.dumps({'gepruefte_neue_pdfs': len(inputs), 'seiten': sum(x['seiten'] for x in inputs),
                      'aktion': 'Ablageplan vorbereitet; keine Originaldatei verschoben'}, ensure_ascii=False))


def register():
    plan = read(HERE / 'Ablageplan.json')
    assert Path(plan['projektwurzel']).resolve() == ROOT
    assert sha(REGISTER) == plan['sha256_register_vorher'], 'Register zwischenzeitlich verändert'
    content = read(REGISTER)
    for document in plan['dokumente']:
        entry = document['eintrag']
        assert not local(document['quelle']).exists(), 'Original liegt noch im Eingang'
        assert sha(local(entry['pdf'])) == entry['sha256_pdf']
        assert sha(local(entry['markdown'])) == entry['sha256_markdown']
        content['eintraege'].append(entry)
    assert len(content['eintraege']) == len({e['pdf'] for e in content['eintraege']})
    assert len(content['eintraege']) == len({e['markdown'] for e in content['eintraege']})
    temporary = REGISTER.with_suffix('.json.tmp')
    write(temporary, content)
    temporary.replace(REGISTER)
    write(HERE / 'Importabschluss.json', {
        'erfasst_am': DATE, 'neue_pdf_dokumente': len(plan['dokumente']),
        'neue_pdf_seiten': sum(d['eintrag']['pdf_seiten'] for d in plan['dokumente']),
        'originaldateien_unveraendert': True, 'sha256_archivregister': sha(REGISTER),
        'eintraege': [d['eintrag'] for d in plan['dokumente']],
    })
    print(f"Registriert: {len(plan['dokumente'])} neue PDFs; insgesamt {len(content['eintraege'])} PDFs.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('aktion', choices=['vorbereiten', 'registrieren'])
    args = parser.parse_args()
    prepare() if args.aktion == 'vorbereiten' else register()
