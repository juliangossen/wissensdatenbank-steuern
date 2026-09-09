"""Aktualisiert nach bestandener UmwStE-Prüfung den Eintrag im Web-Archiv."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT = next(path for path in BASE.parents if (path / 'Bestand.json').is_file())
ARCHIVE = ROOT / 'Web_Archiv'
ORIGINAL = ARCHIVE / '02_In_Markdown_umgewandelt/Stand_2026-09-09/Steuerrecht/Verwaltungsanweisungen/UmwStE/UmwStE.txt'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def main():
    result = json.loads((BASE / 'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    online = json.loads((BASE / 'Quellen/Onlineabgleich/Abgleich.json').read_text(encoding='utf-8'))
    assert result['pruefung_erfolgreich'] is True
    assert sha(ORIGINAL) == sha(BASE / 'Quellen/UmwStE_2025_Webkopie.txt') == result['sha256_original_quelle']
    assert sha(BASE / 'UmwStE_2025.md') == result['sha256_markdown']
    assert (BASE / 'Pruefung/Pruefbericht.md').is_file()
    klassen = online['wortlautvergleich']['klassen']
    identisch = klassen['uebereinstimmend (>= 0,995)']
    zuordnung = result['fussnoten_zuordnung']
    path = ARCHIVE / 'Archivregister.json'
    registry = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'pfadbasis': 'Projektwurzel', 'beschreibung': 'Versionierte, in Markdown übernommene Web- und Textquellen.', 'eintraege': []}
    entry = {
        'dokument': 'Umwandlungssteuererlass 2025 (BMF-Schreiben vom 2. Januar 2025)', 'kuerzel': 'UmwStE 2025',
        'bereich': 'Steuerrecht / Verwaltungsanweisungen / UmwStE',
        'urspruenglicher_dateiname': 'UmwStE.txt', 'status': 'in_markdown_umgewandelt',
        'archivversion': 'Stand_2026-09-09', 'erfasst_am': '2026-09-09',
        'quellenabgleich': '2026-09-09',
        'quellenstand': ['Webkopie: BMF-Schreiben vom 2.1.2025 (BStBl. I S. 92), geändert durch BMF v. 1.8.2025 (BStBl. I S. 1591); Fassung des Bundessteuerblatts mit 94 Anbieterfußnoten.',
                         f'Amtlicher Abgleich am 09.09.2026 mit der BMF-PDF vom 2.1.2025 (Ursprungsfassung, {online["amtliche_quellen"]["grundfassung"]["pdf_seiten"]} Seiten) und dem Änderungsschreiben vom 1.8.2025: alle {online["randnummern"]["kopie"]} Randnummern in gleicher Reihenfolge; Wortlaut nach Normalisierung bei {identisch} von {sum(klassen.values())} Randnummern übereinstimmend, die übrigen Abweichungen (abgeflachte Tabellen, geänderte Rn. 15.35a und Org.03, BStBl-Redaktion) in Abgleich.json einzeln ausgewiesen. BMF-Themenseite wegen Bot-Prüfung nicht abrufbar; spätere Änderungen nach dem 1.8.2025 nicht amtlich ausgeschlossen.'],
        'quellformat': 'Webkopie (TXT)', 'original_quelle': relative(ORIGINAL),
        'markdown': relative(BASE / 'UmwStE_2025.md'), 'pruefbericht': relative(BASE / 'Pruefung/Pruefbericht.md'),
        'sha256_original_quelle': result['sha256_original_quelle'], 'sha256_markdown': result['sha256_markdown'],
        'quelle': 'Vom Nutzer bereitgestellte beck-online-Webkopie (BeckVerw 647650); genaue Ausgangs-URL nicht mitkopiert. Amtliche BMF-PDF und Änderungsschreiben im Quellenordner.',
        'vollstaendigkeit': f'Alle {result["quellzeilen_sachinhalt_nichtleer"]} bereitgestellten Sachtextzeilen vollständig übernommen; {result["randnummern"]} Randnummern mit Sprungmarken, Inhaltsverzeichnis der Kopie verlinkt. {result["fussnoten"]} Fußnotendefinitionen ohne Verweiszeichen im Text: Zuordnung redaktionell erschlossen ({zuordnung.get("erschlossen", 0)} auf Zeile, {zuordnung.get("erschlossen_ohne_zelle", 0)} nur auf Randnummer, {zuordnung.get("offen", 0)} offen). Abgeflachte Tabellen bleiben Textzeilen. Keine Satznummern, keine Anlagen.',
        'typ': 'Verwaltungsanweisung (Webkopie)',
        'gliederungspositionen': result['gliederungspositionen'], 'randnummern': result['randnummern'],
        'anlagen': result['anlagen'], 'fussnoten': result['fussnoten'],
    }
    existing = [i for i, item in enumerate(registry['eintraege']) if item.get('original_quelle') == entry['original_quelle']]
    assert len(existing) <= 1
    if existing:
        registry['eintraege'][existing[0]] = entry
    else:
        registry['eintraege'].append(entry)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('UmwStE-Webquelle mit geprüften Quell- und Zielprüfsummen registriert.')


if __name__ == '__main__':
    main()
