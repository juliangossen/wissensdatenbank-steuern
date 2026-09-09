"""Aktualisiert nach bestandener ErbStDV-Prüfung den Eintrag im Web-Archiv."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT = next(path for path in BASE.parents if (path / 'Bestand.json').is_file())
ARCHIVE = ROOT / 'Web_Archiv'
ORIGINAL = ARCHIVE / '02_In_Markdown_umgewandelt/Stand_2026-09-09/Steuerrecht/Gesetze/Erbschaft_und_Schenkungsteuer/ErbStDV/ErbStDV.txt'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def main():
    result = json.loads((BASE / 'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    assert result['pruefung_erfolgreich'] is True
    assert online['stand_stimmt_ueberein'] is True and online['wortlautabgleich_durchgefuehrt'] is True
    assert sha(ORIGINAL) == sha(BASE / 'Quellen/ErbStDV_Webkopie.txt') == result['sha256_original_quelle']
    assert sha(BASE / 'ErbStDV.md') == result['sha256_markdown']
    assert (BASE / 'Pruefung/Pruefbericht.md').is_file()
    path = ARCHIVE / 'Archivregister.json'
    registry = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'pfadbasis': 'Projektwurzel', 'beschreibung': 'Versionierte, in Markdown übernommene Web- und Textquellen.', 'eintraege': []}
    entry = {
        'dokument': 'Erbschaftsteuer-Durchführungsverordnung', 'kuerzel': 'ErbStDV',
        'bereich': 'Steuerrecht / Gesetze / Erbschaft- und Schenkungsteuer / ErbStDV',
        'urspruenglicher_dateiname': 'ErbStDV.txt', 'status': 'in_markdown_umgewandelt',
        'archivversion': 'Stand_2026-09-09', 'erfasst_am': '2026-09-09',
        'quellenabgleich': '2026-09-09',
        'quellenstand': ['Webkopie: Text gilt vom 30.12.2025 bis unbestimmt; zuletzt geändert durch Art. 11 G v. 22.6.2026 (BGBl. 2026 I Nr. 192).',
                         'Gesetze im Internet am 09.09.2026: XML-Gesamtausgabe vom 30.06.2026, Stand „Zuletzt geändert durch Art. 11 G v. 22.6.2026 I Nr. 192“; Stand identisch. Vollständiger Wortlautvergleich der §§ 1 bis 13: 8 Paragraphen zeichenidentisch, § 2 und § 3 nur typografisch abweichend, Wortabweichungen in § 10, § 11 und § 13 (Satz 2 nur in der Kopie); Muster 1 bis 6 als Wortmengen verglichen (Abweichungen in Muster 2, 3 und 5). Eingangs- und Schlußformel fehlen in der Kopie.'],
        'quellformat': 'Webkopie (TXT)', 'original_quelle': relative(ORIGINAL),
        'markdown': relative(BASE / 'ErbStDV.md'), 'pruefbericht': relative(BASE / 'Pruefung/Pruefbericht.md'),
        'sha256_original_quelle': result['sha256_original_quelle'], 'sha256_markdown': result['sha256_markdown'],
        'quelle': 'Vom Nutzer bereitgestellte beck-online-Webkopie; genaue Ausgangs-URL nicht mitkopiert. Amtliche Gesamtausgabe (XML, PDF, HTML) von Gesetze im Internet im Quellenordner.',
        'vollstaendigkeit': f'Alle {result["quellzeilen_sachinhalt_nichtleer"]} bereitgestellten Sachtextzeilen vollständig übernommen; {result["fussnoten"]} Anbieterfußnoten eindeutig verlinkt. Muster 1 bis 6 in der Kopie zellenweise abgeflacht und als Formularblöcke erhalten. Wortlautvergleich mit der amtlichen XML-Gesamtausgabe durchgeführt; Abweichungen dokumentiert, nicht berichtigt.',
        'typ': 'Verordnung (Webkopie)',
        'gliederungspositionen': result['gliederungspositionen'], 'anlagen': result['anlagen'], 'fussnoten': result['fussnoten'],
    }
    existing = [i for i, item in enumerate(registry['eintraege']) if item.get('original_quelle') == entry['original_quelle']]
    assert len(existing) <= 1
    if existing:
        registry['eintraege'][existing[0]] = entry
    else:
        registry['eintraege'].append(entry)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('ErbStDV-Webquelle mit geprüften Quell- und Zielprüfsummen registriert.')


if __name__ == '__main__':
    main()
