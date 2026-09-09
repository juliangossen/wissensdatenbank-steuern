"""Registriert die geprüfte EStR-/EStH-Webkopie im versionierten Web-Archiv."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT = next(path for path in BASE.parents if (path / 'Bestand.json').is_file())
ORIGINAL = ROOT / 'Web_Archiv/02_In_Markdown_umgewandelt/Stand_2026-09-09/Steuerrecht/Verwaltungsanweisungen/EStR/EStR 2012.txt'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def main():
    proof = json.loads((BASE / 'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    assert proof['pruefung_erfolgreich'] is True
    assert sha(ORIGINAL) == sha(BASE / 'Quellen/EStR_2012_Webkopie.txt') == proof['sha256_original_quelle']
    assert sha(BASE / 'EStR_2012.md') == proof['sha256_markdown']
    assert (BASE / 'Pruefung/Pruefbericht.md').is_file()
    path = ROOT / 'Web_Archiv/Archivregister.json'
    registry = json.loads(path.read_text(encoding='utf-8'))
    entry = {
        'dokument': 'Einkommensteuer-Richtlinien 2012 mit Einkommensteuer-Hinweisen 2025',
        'kuerzel': 'EStR 2012 / EStH 2025', 'bereich': 'Steuerrecht / Verwaltungsanweisungen / EStR',
        'urspruenglicher_dateiname': 'EStR 2012.txt', 'status': 'in_markdown_umgewandelt',
        'archivversion': 'Stand_2026-09-09', 'erfasst_am': '2026-09-09', 'quellenabgleich': '2026-09-09',
        'quellenstand': ['EStR 2012 in der Fassung der EStÄR 2012 vom 25.03.2013.',
                        'Mit EStH 2025; Redaktionsschluss 20.01.2026 laut kopiertem Vorwort.',
                        'Formularmuster: 2013/2014. Amtliche Vergleichsübersichten 2025 zu Anlagen 2 und 6 gesondert abgelegt.'],
        'quellformat': 'Webkopie (TXT)', 'original_quelle': relative(ORIGINAL),
        'markdown': relative(BASE / 'EStR_2012.md'), 'pruefbericht': relative(BASE / 'Pruefung/Pruefbericht.md'),
        'sha256_original_quelle': proof['sha256_original_quelle'], 'sha256_markdown': proof['sha256_markdown'],
        'quelle': 'Vom Nutzer bereitgestellte beck-online-Webkopie; genaue Ausgangs-URL nicht mitkopiert. Amtliche BMF-Belege im Quellenordner.',
        'vollstaendigkeit': 'Alle bereitgestellten Sachtextzeilen vollständig übernommen; R 2012 und H 2025 unterscheidbar. 18 Formularmuster mit 24 amtlichen Abbildungsseiten ergänzt. Abweichende amtliche Anlagen 2 und 6 aus EStH 2025 separat. Kein vollständiger Wortvergleich der gesamten Webkopie mit dem amtlichen Handbuch.',
        'richtlinienbloecke': 302, 'hinweisbloecke': 344, 'fussnoten': 507,
        'anlagenpositionen': 6, 'nicht_belegte_anlagen': [3, 5], 'formularabbildungen': 24,
    }
    matches = [i for i, item in enumerate(registry['eintraege']) if item.get('original_quelle') == entry['original_quelle']]
    assert len(matches) <= 1
    if matches:
        registry['eintraege'][matches[0]] = entry
    else:
        registry['eintraege'].append(entry)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('EStR 2012 mit EStH 2025 als geprüfte Webquelle registriert.')


if __name__ == '__main__':
    main()
