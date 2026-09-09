"""Unabhängiger Rückvergleich des fertigen Gesamtdokuments normweise."""
import sys,json,re,hashlib,unicodedata,argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser
from markdown_it import MarkdownIt
sys.stdout.reconfigure(encoding='utf-8')
BASE=Path(__file__).resolve().parents[2]
ABBR=['BGB','HGB','StGB','GewO','GwG','HwO','UWG']
def compact(s):return re.sub(r'\s+','',unicodedata.normalize('NFC',s))
def txt(e):return ''.join(e.itertext()) if e is not None else ''
class Reader(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.skip=0;self.parts=[];self.head=None
    def handle_starttag(self,t,a):
        if self.skip and t not in ['br','img','hr','input']:self.skip+=1
        elif 'data-redaktionell' in dict(a):self.skip=1
        if t=='thead':self.head=[]
    def handle_endtag(self,t):
        if self.skip:self.skip-=1;return
        if t=='thead':
            value=''.join(self.head)
            if not re.fullmatch('(Spalte[0-9]+)+',compact(value)):self.parts.append(value)
            self.head=None
    def handle_data(self,s):
        if not self.skip:(self.head if self.head is not None else self.parts).append(s)
def visible(md):
    r=Reader();r.feed(MarkdownIt('commonmark',{'html':True}).enable('table').render(md));return ''.join(r.parts)
def perform(cp):
    c=json.loads(cp.read_text(encoding='utf-8'))
    # Alle hier konfigurierten Gesetze werden geprüft.
    folder=cp.parent.parent;mdpath=folder/(c['kuerzel']+'.md')
    if not mdpath.exists():print(c['kuerzel'],'noch kein Markdown');return
    root=ET.parse(folder/c['xml_datei']).getroot()
    md=mdpath.read_text(encoding='utf-8')
    matches=list(re.finditer(r'^<a id="([^"]+)"></a>\n\n#{2,6} ',md,re.M))
    assert len(matches)==len(root),(c['kuerzel'],len(matches),len(root))
    checks=[]
    for i,(match,node) in enumerate(zip(matches,root)):
        piece=md[match.start():matches[i+1].start() if i+1<len(matches) else len(md)]
        g=node.find('metadaten/gliederungseinheit')
        en=re.sub(r'^\(XXXX\)\s*','',node.findtext('metadaten/enbez',''))
        if i==0:head=''
        elif g is not None:head=txt(g.find('gliederungsbez'))+txt(g.find('gliederungstitel'))
        else:head=en+txt(node.find('metadaten/titel'))
        expected=head
        for kind in ['text','fussnoten']:
            container=node.find('textdaten/'+kind)
            if container is None:continue
            for content in container:
                if txt(content).strip():expected+=('Fußnote' if kind=='fussnoten' else '')+txt(content)
        actual=compact(visible(piece));expected=compact(expected)
        if i==0:
            # Document heading, date, citation and source status are metadata before XML body.
            position=actual.find(expected[:100]);assert position>=0
            actual=actual[position:]
        entry={'xml_index':i,'doknr':node.get('doknr'),'anzeige':en or txt(g) or 'Dokumentkopf','identisch':expected==actual,'zeichen':len(expected),'sha256':hashlib.sha256(expected.encode()).hexdigest()}
        if actual!=expected:
            at=next((j for j,(x,y) in enumerate(zip(expected,actual)) if x!=y),min(len(expected),len(actual)))
            entry.update({'abweichung_bei':at,'xml_ausschnitt':expected[max(0,at-90):at+300],'markdown_ausschnitt':actual[max(0,at-90):at+300]})
            print(c['kuerzel'],json.dumps(entry,ensure_ascii=False))
        checks.append(entry)
    expected_notes={e.get('ID'):(e.get('FnZ','')+e.get('Postfix','')) for e in root.findall('.//Footnote')}
    marker_checks=[]
    for ident,num in expected_notes.items():
        refs=re.findall(r'href="#fn-'+re.escape(ident)+r'"[^>]*>(.*?)</a>',md)
        marker_checks.append({'id':ident,'kennzeichnung':num,'quellverweise':sum(e.get('ID')==ident for e in root.findall('.//FnR')),'markdown_verweise':len(refs),'kennzeichnung_erhalten':all(compact(visible(s))==num for s in refs)})
    marker_ok=all(e['quellverweise']==e['markdown_verweise'] and e['kennzeichnung_erhalten'] for e in marker_checks)
    report={'kuerzel':c['kuerzel'],'pruefdatum':c['quellenabgleich'],'methode':'Fertige Markdown-Datei unabhängig normweise an Überschriftsankern zerlegt; alle sichtbaren Texte aus dem gerenderten Markdown gegen sämtliche XML-Normen in derselben Reihenfolge verglichen. Nur redaktionelle Metadaten und markierte Ergänzungen, PDF-technischer (XXXX)-Präfix, NFC/Whitespace ausgenommen. Aus XML-Attributen stammende Fußnotenmarker werden zusätzlich auf vollständige Zahl und Kennzeichnung geprüft.',
        'sha256_markdown':hashlib.sha256(mdpath.read_bytes()).hexdigest(),'normen_erwartet':len(root),'normen_vorhanden':len(matches),'alle_normtexte_identisch':all(e['identisch'] for e in checks),'alle_fussnotenverweise_erhalten':marker_ok,'fussnoten':marker_checks,'normen':checks}
    (cp.parent/'Markdown_Gesamtpruefung.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(c['kuerzel'],'fertige MD',len(matches),'normen','identisch',report['alle_normtexte_identisch'],'markers',marker_ok)
    assert report['alle_normtexte_identisch'] and marker_ok
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config');args=parser.parse_args()
    if args.config:perform(Path(args.config).resolve())
    elif (Path(__file__).parent/'konfiguration.json').exists():perform(Path(__file__).parent/'konfiguration.json')
    else:
        for cp in (BASE/'Rechtsgebiete').glob('**/konfiguration.json'):perform(cp)
