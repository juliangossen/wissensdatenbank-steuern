"""Unabhängige, schreibgeschützte Prüfung der drei erzeugten EU-Markdown-Dateien."""
from pathlib import Path
import hashlib, json, re, unicodedata, warnings
from urllib.parse import unquote
import fitz
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from markdown_it import MarkdownIt
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compact(s):return re.sub(r'\s+','',unicodedata.normalize('NFC',s))
local=Path(__file__).resolve().parent/'konfiguration.json'
if local.is_file():
    cfg=json.loads(local.read_text(encoding='utf-8'))
    pr=json.loads((local.parent/'Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    results=[dict(kuerzel=cfg['kuerzel'],markdown=(local.parent.parent/cfg['markdown_datei']).relative_to(ROOT).as_posix(),sha256_markdown=pr['sha256_markdown'],sha256_original_pdf=pr['sha256_pdf'])]
else:results=json.loads((Path(__file__).resolve().parent.parent/'ergebnis_eu.json').read_text(encoding='utf-8'))
for result in results:
    md=ROOT/result['markdown'];base=md.parent
    cfg=json.loads((base/'Pruefung/konfiguration.json').read_text(encoding='utf-8'))
    proof=json.loads((base/'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
    assert proof['pruefung_erfolgreich'] and sha(md)==proof['sha256_markdown']==result['sha256_markdown']
    pdf=base/'Quellen'/cfg['lokale_pdf']
    assert sha(pdf)==proof['sha256_pdf']==proof['sha256_amtliche_pdf']==result['sha256_original_pdf']
    source=base/'Quellen/EUR-Lex_Amtsblatt.html'
    assert sha(source)==proof['sha256_html']
    soup=BeautifulSoup(source.read_bytes(),'lxml')
    for e in soup.find_all(['script','style']):e.decompose()
    for e in soup.find_all('a',href=re.compile('^javascript:')):e.decompose()
    text=md.read_text(encoding='utf-8')
    body=text.split('## Amtsblatttext\n\n',1)[1]
    body=body[body.index('<table'):]
    parser=MarkdownIt('commonmark',{'html':True}).enable('table')
    rendered=BeautifulSoup(parser.render(body),'lxml')
    assert compact(soup.body.get_text())==compact(rendered.get_text())
    full=BeautifulSoup(parser.render(text),'lxml')
    ids=[e['id'] for e in full.find_all(id=True)]
    assert len(ids)==len(set(ids))
    links=0
    for e in full.find_all(['a','img']):
        target=e.get('href',e.get('src',''))
        if not target:continue
        if target.startswith('#'):assert target[1:] in ids
        elif not re.match('https?://',target):assert (base/unquote(target.split('#')[0])).is_file(),target
        links+=1
    original=fitz.open(pdf)
    assert len(original)==proof['pdf_seiten']
    for i,(asset,expected_sha) in enumerate(proof['bildassets'].items()):
        path=base/asset;assert sha(path)==expected_sha
        assert path.read_bytes()==original[16+i].parent.extract_image(original[16+i].get_images()[0][0])['image']
    # Alle verbundenen Tabellenzellen der amtlichen HTML-Fassung unverändert erhalten.
    def spans(s):return [(e.name,e.get('rowspan'),e.get('colspan'),compact(e.get_text())) for e in s.find_all(['td','th']) if e.get('rowspan') or e.get('colspan')]
    assert spans(soup)==spans(rendered)
    pageproof=json.loads((base/'Pruefung/PDF_Textabgleich.json').read_text(encoding='utf-8'))
    assert len(pageproof['seiten'])==len(original)
    for p in pageproof['seiten']:assert p['alle_textzeilen_nachgewiesen'] and all(z['in_html_nachgewiesen'] for z in p['einzelzeilen'])
    print(result['kuerzel'],': OK;',proof['vorschriften'],'Artikel;',links,'Links/Bilder;',len(spans(soup)),'verbundene Tabellenzellen')
