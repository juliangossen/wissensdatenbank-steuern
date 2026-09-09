"""Unabhängige Prüfung des vollständigen, zusammengesetzten Markdown-Dokuments."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json,re,sys,unicodedata,xml.etree.ElementTree as ET
from markdown_it import MarkdownIt
sys.stdout.reconfigure(encoding='utf-8')

def compact(s):return re.sub(r'\s+','',unicodedata.normalize('NFC',s))
def joined(e):return ''.join(e.itertext()) if e is not None else ''

class Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[];self.suppression=[];self.cells=[];self.active_cell=None;self.rows=0;self.tables=0
    def handle_starttag(self,tag,attrs):
        if self.suppression or 'data-redaktionell' in dict(attrs):
            if tag not in ('br','img','hr'):self.suppression.append(tag)
            return
        if tag=='table':self.tables+=1
        if tag=='tr':self.rows+=1
        if tag in ('td','th'):self.active_cell=[]
    def handle_endtag(self,tag):
        if self.suppression:
            if self.suppression[-1]==tag:self.suppression.pop()
            return
        if tag in ('td','th'):
            self.cells.append(''.join(self.active_cell or []));self.active_cell=None
    def handle_data(self,data):
        if not self.suppression:
            self.parts.append(data)
            if self.active_cell is not None:self.active_cell.append(data)

def read(md):
    html=MarkdownIt('commonmark',{'html':True}).enable('table').render(md)
    def remove_generated(m):
        plain=compact(re.sub('<[^>]*>','',m.group()))
        return '' if re.fullmatch(r'(Spalte\d+)+',plain) else m.group()
    html=re.sub(r'<thead>.*?</thead>',remove_generated,html,flags=re.S)
    reader=Reader();reader.feed(html);return reader

def verify(config):
    config=Path(config).resolve();base=config.parent.parent
    cfg=json.loads(config.read_text(encoding='utf-8'))
    root=ET.parse(base/cfg['xml_datei']).getroot()
    md_path=base/(cfg['kuerzel']+'.md');md=md_path.read_text(encoding='utf-8')
    anchors=[m for m in re.finditer(r'<a id="([^"\n]+)-(\d+)"></a>',md) if not m.group(1).startswith('fn-')]
    indexes=[int(m.group(2)) for m in anchors]
    assert indexes==list(range(1,len(root))),(cfg['kuerzel'],'Normanker fehlen oder falsche Reihenfolge',indexes)
    results=[]
    for k,match in enumerate(anchors):
        i=int(match.group(2));node=root[i];meta=node.find('metadaten');group=meta.find('gliederungseinheit')
        label=re.sub(r'^\(XXXX\)\s*','',meta.findtext('enbez',''))
        expected=(joined(group.find('gliederungsbez'))+joined(group.find('gliederungstitel'))+label+joined(meta.find('titel'))) if group is not None else label+joined(meta.find('titel'))
        for kind in ['text','fussnoten']:
            text=joined(node.find('textdaten/'+kind))
            if text.strip():expected+=('Fußnote' if kind=='fussnoten' else '')+text
        chunk=md[match.start():anchors[k+1].start() if k+1<len(anchors) else len(md)]
        parsed=read(chunk)
        actual=''.join(parsed.parts).replace('(XXXX) ','')
        ok=compact(expected)==compact(actual)
        if not ok:
            a,b=compact(expected),compact(actual)
            pos=next((j for j,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
            raise AssertionError((cfg['kuerzel'],label,i,pos,a[max(0,pos-80):pos+200],b[max(0,pos-80):pos+200]))
        source_cells=[compact(joined(x)) for x in node.iter('entry')]
        assert source_cells==[compact(x) for x in parsed.cells],(cfg['kuerzel'],label,'Tabellenzellen')
        assert parsed.rows==len(list(node.iter('row'))),(cfg['kuerzel'],label,'Tabellenzeilen')
        assert parsed.tables==len(list(node.iter('table'))),(cfg['kuerzel'],label,'Tabellenzahl')
        results.append({'index':i,'norm':label or joined(group),'vollstaendiger_text_identisch':ok,'tabellenzellen_identisch':True,'zeilen_identisch':True,'tabellen_identisch':True})
    all_ids=re.findall(r'<a id="([^"]+)"',md)
    assert len(set(all_ids))==len(all_ids)
    internal=re.findall(r'\]\(#([^)]+)\)',md)+re.findall(r'href="#([^"]+)"',md)
    assert set(internal)<=set(all_ids)
    report={'kuerzel':cfg['kuerzel'],'methode':'Unabhängiger Vergleich jedes vollständigen Markdown-Normabschnitts einschließlich Überschrift, Fließtext und Fußnoten; zusätzlich jede Tabellenzelle in Reihenfolge, Tabellen- und Zeilenzahl. Gerendertes Gesamtdokument wird nach Normankern aufgeteilt. Ausnahmen nur NFC/Leerraum, redaktionelle Fußnotenmarker und generische Spaltenüberschriften.','gepruefte_normen_ohne_metadatenkopf':len(results),'normreihenfolge_vollstaendig':True,'alle_normen_identisch':True,'alle_tabellenzellen_identisch':True,'alle_links_gueltig':True,'sha256_markdown':hashlib.sha256(md_path.read_bytes()).hexdigest(),'normen':results}
    (config.parent/'Markdown_Strukturpruefung.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {k:v for k,v in report.items() if k!='normen'}

if __name__=='__main__':
    config=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent/'konfiguration.json'
    print(json.dumps(verify(config),ensure_ascii=False,indent=2))
