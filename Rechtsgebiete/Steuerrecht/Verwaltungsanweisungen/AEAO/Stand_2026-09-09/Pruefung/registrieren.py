"""Aktualisiert nach bestandener AEAO-Prüfung den Eintrag im Web-Archiv."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT = next(path for path in BASE.parents if (path / 'Bestand.json').is_file())
ARCHIVE = ROOT / 'Web_Archiv'
ORIGINAL = ARCHIVE / '02_In_Markdown_umgewandelt/Stand_2026-09-09/Steuerrecht/Verwaltungsanweisungen/AEAO/AEAO.txt'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def main():
    result = json.loads((BASE / 'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    assert result['pruefung_erfolgreich'] is True
    assert sha(ORIGINAL) == sha(BASE / 'Quellen/AEAO_Webkopie.txt') == result['sha256_original_quelle']
    assert sha(BASE / 'AEAO.md') == result['sha256_markdown']
    assert (BASE / 'Pruefung/Pruefbericht.md').is_file()
    path = ARCHIVE / 'Archivregister.json'
    registry = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'pfadbasis': 'Projektwurzel', 'beschreibung': 'Versionierte, in Markdown übernommene Web- und Textquellen.', 'eintraege': []}
    entry = {
        'dokument': 'Anwendungserlass zur Abgabenordnung', 'kuerzel': 'AEAO',
        'bereich': 'Steuerrecht / Verwaltungsanweisungen / AEAO',
        'urspruenglicher_dateiname': 'AEAO.txt', 'status': 'in_markdown_umgewandelt',
        'archivversion': 'Stand_2026-09-09', 'erfasst_am': '2026-09-09',
        'quellenabgleich': '2026-09-09',
        'quellenstand': ['Webkopie: Text gilt seit 02.07.2026; zuletzt geändert durch BMF-Schreiben vom 2.7.2026 (BStBl. I 2026, 950).',
                        'BMF-Übersichtsseite am 09.09.2026: jüngstes Änderungsschreiben vom 2.7.2026; die zehn darin geänderten Abschnitte tragen in der Kopie entsprechende Änderungsnachweise. Keine amtliche Gesamtfassung mit diesem Stand verfügbar, kein Wortlautvergleich.'],
        'quellformat': 'Webkopie (TXT)', 'original_quelle': relative(ORIGINAL),
        'markdown': relative(BASE / 'AEAO.md'), 'pruefbericht': relative(BASE / 'Pruefung/Pruefbericht.md'),
        'sha256_original_quelle': result['sha256_original_quelle'], 'sha256_markdown': result['sha256_markdown'],
        'quelle': 'Vom Nutzer bereitgestellte beck-online-Webkopie; genaue Ausgangs-URL nicht mitkopiert. Amtliches Änderungsschreiben und BMF-Übersichtsseite im Quellenordner.',
        'vollstaendigkeit': 'Alle bereitgestellten Sachtextzeilen vollständig übernommen; 983 Fußnoten eindeutig verlinkt. Formularseiten der Anlage 1 nur als Platzhalterzeilen in der Kopie; abgeflachte Tabellen bleiben Textzeilen. Standabgleich mit dem BMF-Änderungsschreiben vom 2.7.2026, kein Wortlautvergleich mit einer amtlichen Gesamtfassung.',
        'gliederungspositionen': result['gliederungspositionen'], 'anlagen': result['anlagen'], 'fussnoten': result['fussnoten'],
    }
    existing = [i for i, item in enumerate(registry['eintraege']) if item.get('original_quelle') == entry['original_quelle']]
    assert len(existing) <= 1
    if existing:
        registry['eintraege'][existing[0]] = entry
    else:
        registry['eintraege'].append(entry)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('AEAO-Webquelle mit geprüften Quell- und Zielprüfsummen registriert.')


if __name__ == '__main__':
    main()
