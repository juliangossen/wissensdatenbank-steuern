"""Aktualisiert nach bestandener ErbStR-2019-Prüfung den Eintrag im Web-Archiv."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT = next(path for path in BASE.parents if (path / 'Bestand.json').is_file())
ARCHIVE = ROOT / 'Web_Archiv'
ORIGINAL = ARCHIVE / '02_In_Markdown_umgewandelt/Stand_2026-09-09/Steuerrecht/Verwaltungsanweisungen/ErbStR/ErbStR 2019.txt'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def main():
    result = json.loads((BASE / 'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    assert result['pruefung_erfolgreich'] is True
    assert online['strukturvergleich']['gliederung_stimmt_ueberein'] is True
    assert sha(ORIGINAL) == sha(BASE / 'Quellen/ErbStR_2019_Webkopie.txt') == result['sha256_original_quelle']
    assert sha(BASE / 'ErbStR_2019.md') == result['sha256_markdown']
    assert (BASE / 'Pruefung/Pruefbericht.md').is_file()
    path = ARCHIVE / 'Archivregister.json'
    registry = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'pfadbasis': 'Projektwurzel', 'beschreibung': 'Versionierte, in Markdown übernommene Web- und Textquellen.', 'eintraege': []}
    notes = online['fussnoten_der_kopie']
    entry = {
        'dokument': 'Erbschaftsteuer-Richtlinien 2019 mit Erbschaftsteuer-Hinweisen 2019',
        'kuerzel': 'ErbStR 2019 / ErbStH 2019',
        'bereich': 'Steuerrecht / Verwaltungsanweisungen / ErbStR',
        'urspruenglicher_dateiname': 'ErbStR 2019.txt', 'status': 'in_markdown_umgewandelt',
        'archivversion': 'Stand_2026-09-09', 'erfasst_am': '2026-09-09',
        'quellenabgleich': '2026-09-09',
        'quellenstand': ['Richtlinien: Allgemeine Verwaltungsvorschrift vom 16.12.2019 (ErbStR 2019, BStBl. I 2019 Sondernummer 1 S. 2); Hinweise: gleich lautende Ländererlasse vom 16.12.2019 (ErbStH 2019, BStBl. I 2019 Sondernummer 1 S. 151).',
                        f'Webkopie ohne Abrufdatum; {notes["anbieterhinweise"]} Anbieterfußnoten mit datierten Nachweisen bis {notes["juengstes_datum_jahr"]} und eine redaktionelle Fortführung der Anwendungsliste in H E 37 (JStG 2020, Grundsteuerreform-Umsetzungsgesetz); die gleich lautenden Ländererlasse vom 13.9.2021 (BStBl. I 2021 S. 1837) und 13.12.2021 (BStBl. I 2022 S. 38) sind nur in Fußnoten zitiert.',
                        'Amtlicher Abgleich am 09.09.2026 mit den amtlichen PDF-Fassungen ErbStR 2019 und ErbStH 2019 (BMF-Dokumente aus einer Sekundärablage; BMF-Server nur über Bot-Prüfung erreichbar): Gliederung vollständig in Reihenfolge bestätigt, normalisierter Wortlautvergleich je Block; Anlage 2 amtlich nur als Bild.'],
        'quellformat': 'Webkopie (TXT)', 'original_quelle': relative(ORIGINAL),
        'markdown': relative(BASE / 'ErbStR_2019.md'), 'pruefbericht': relative(BASE / 'Pruefung/Pruefbericht.md'),
        'sha256_original_quelle': result['sha256_original_quelle'], 'sha256_markdown': result['sha256_markdown'],
        'quelle': 'Vom Nutzer bereitgestellte beck-online-Webkopie; genaue Ausgangs-URL nicht mitkopiert. Amtliche PDF-Fassungen und Abrufnachweise im Quellenordner.',
        'vollstaendigkeit': (f'Alle bereitgestellten Sachtextzeilen vollständig übernommen; {result["fussnoten"]} Fußnoten eindeutig verlinkt '
                             f'({result["fussnoten_amtlich"]} amtlich gekennzeichnet). Die Kopie enthält keine Inhaltsübersicht, keinen Artikel 1/2, '
                             'keine Schlussformel/Unterschriften der ErbStR 2019 und keinen Länderministerienblock der ErbStH 2019; sie endet mit der '
                             'letzten Zelle der amtlichen Anlage 2. Abgeflachte Tabellen bleiben Textzeilen; Anlagen 1 und 2 nach amtlich geprüftem '
                             'Spaltenaufbau als Tabellen. Wortlautvergleich normalisiert je Block, kein zeichengenauer Abgleich.'),
        'gliederungspositionen': result['gliederungspositionen'], 'paragraphengruppen': result['paragraphengruppen'],
        'anlagen': result['anlagen'], 'fussnoten': result['fussnoten'],
        'typ': 'Verwaltungsanweisung (Webkopie)',
    }
    existing = [i for i, item in enumerate(registry['eintraege']) if item.get('original_quelle') == entry['original_quelle']]
    assert len(existing) <= 1
    if existing:
        registry['eintraege'][existing[0]] = entry
    else:
        registry['eintraege'].append(entry)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('ErbStR 2019 mit ErbStH 2019 als geprüfte Webquelle registriert.')


if __name__ == '__main__':
    main()
