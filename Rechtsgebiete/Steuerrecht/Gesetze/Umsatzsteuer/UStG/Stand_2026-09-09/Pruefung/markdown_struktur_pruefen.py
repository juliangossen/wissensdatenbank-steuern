"""Unabhaengige Pruefung des gerenderten UStG-Markdowns gegen die XML.
Aufruf: py Pruefung/markdown_struktur_pruefen.py
Voraussetzungen: Python 3, markdown-it-py (pip install markdown-it-py).
Prueft vollstaendige Paragraphentexte, Listenebenen jedes Zeichens,
Wortgrenzen, Ueberschriften, Codebloecke und alle Anlagen-Tabellenzellen.
"""
import sys, re, json, collections, hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from markdown_it import MarkdownIt

sys.stdout.reconfigure(encoding='utf-8')
BASE = Path(__file__).resolve().parent.parent
raw = (BASE/'UStG.md').read_text(encoding='utf-8')
source = ET.parse(BASE/'Quellen/XML/BJNR119530979.xml').getroot()
md = MarkdownIt('commonmark', {'html':True}).enable('table')
body = re.sub(r'\A---\n.*?\n---\n', '', raw, flags=re.S)
tokens = md.parse(body)

class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.chars=[]; self.depths=[]; self.tables=[]; self.row=None; self.cell=None; self.visible=[]; self.words=[]
    def handle_starttag(self,tag,attrs):
        if tag=='table':self.tables.append([])
        if tag=='tr':self.row=[]
        if tag in ('td','th'):self.cell=[]
        if tag not in ('br','hr','img','meta','link','input'):self.stack.append(tag)
        if tag in ('br','p','li','td','th'):self.visible.append(' ');self.words.append(' ')
    def handle_endtag(self,tag):
        if tag in ('td','th'):
            self.row.append(''.join(self.cell));self.cell=None
        if tag=='tr':self.tables[-1].append(self.row);self.row=None
        if tag in self.stack:
            at=len(self.stack)-1-self.stack[::-1].index(tag)
            del self.stack[at:]
        if tag in ('br','p','li','td','th'):self.visible.append(' ');self.words.append(' ')
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
        self.visible.append(data)
        if any(t in self.stack for t in ['h1','h2','h3','h4','h5','h6']):return
        self.words.append(data)
        chars=[c for c in data if not c.isspace()]
        self.chars.extend(chars);self.depths.extend([self.stack.count('li')]*len(chars))

def xml_annotated(el,depth=0):
    chars=[];depths=[]
    own=depth+(el.tag in ('DD','DT'))
    def put(text,d):
        c=[x for x in (text or '') if not x.isspace()]; chars.extend(c);depths.extend([d]*len(c))
    put(el.text,own)
    for child in el:
        c,d=xml_annotated(child,own);chars.extend(c);depths.extend(d)
        put(child.tail,own)
    return chars,depths

def norm(s):return re.sub(r'\s+','',s)
def xml_words(el):
    result = [' ' if el.tag in ('P','DL','DT','DD','LA','BR','row','entry') else '', el.text or '']
    for child in el:result.extend([xml_words(child),child.tail or ''])
    if el.tag in ('P','DL','DT','DD','LA','BR','row','entry'):result.append(' ')
    return ''.join(result)
headings=[tokens[i+1].content for i,t in enumerate(tokens) if t.type=='heading_open']
report={'paragraph_headings':sum(h.startswith('§ ') for h in headings),'sections':sum(bool(re.match(r'(Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebenter) Abschnitt',h)) for h in headings),'annexes':sum(bool(re.match(r'Anlage [1-5](?: |$)',h)) for h in headings),'fences':[(t.info,t.map) for t in tokens if t.type=='fence'],'code_blocks':sum(t.type=='code_block' for t in tokens),'inline_code':sum(c.type=='code_inline' for t in tokens for c in (t.children or [])),'paragraphs':[],'tables':[]}
for n in source:
    name=n.findtext('./metadaten/enbez') or ''
    if not name.startswith('§ '):continue
    anchor='<a id="ustg-'+name[2:]+'"></a>'
    a=raw.index(anchor);b=raw.find('<a id=',a+len(anchor))
    section=raw[a:b if b>=0 else len(raw)]
    parsed=Collector();parsed.feed(md.render(section))
    xc=[];xd=[]
    for el in n.find('textdaten'):
        c,d=xml_annotated(el);xc.extend(c);xd.extend(d)
    entry={'name':name,'characters_match':xc==parsed.chars,'list_depth_of_every_character_matches':xd==parsed.depths}
    expected_words=re.findall(r'\w+',xml_words(n.find('textdaten')))
    actual_words=re.findall(r'\w+',''.join(parsed.words))
    entry['word_boundaries_match']=expected_words==actual_words
    if xc==parsed.chars and xd!=parsed.depths:
        bad=[i for i,(a,b) in enumerate(zip(xd,parsed.depths)) if a!=b]
        entry['depth_examples']=[{'text':''.join(xc[max(0,i-30):i+60]),'xml':xd[i],'md':parsed.depths[i]} for i in bad[:4]]
    report['paragraphs'].append(entry)

# Verify table cells independently, filling spans with empty continuation cells.
parsed=Collector();parsed.feed(md.render(body))
for idx,table in enumerate(source.findall('.//table')):
    if idx==0:
        report['tables'].append({'index':0,'note':'Editorial rearrangement in contents table is intentionally excluded from column-position audit.'});continue
    tg=table.find('tgroup');cols=int(tg.get('cols'));span=[0]*cols;expected=[]
    colnames={c.get('colname'):int(c.get('colnum',str(i+1)))-1 for i,c in enumerate(tg.findall('colspec'))}
    for row in tg.findall('.//row'):
        cells=['']*cols;occupied=[v>0 for v in span];nextspan=[max(0,v-1) for v in span];cursor=0
        for e in row.findall('entry'):
            if e.get('namest') or e.get('colname'):
                col=colnames[e.get('namest') or e.get('colname')]
            else:
                while cursor<cols and occupied[cursor]:cursor+=1
                col=cursor
            end=colnames[e.get('nameend')] if e.get('nameend') else col
            cells[col]=norm(''.join(e.itertext()))
            for c in range(col,end+1):occupied[c]=True;nextspan[c]=int(e.get('morerows','0'))
            cursor=end+1
        span=nextspan;expected.append(cells)
    actual=[[norm(c) for c in row] for row in parsed.tables[idx]]
    if len(actual)==len(expected)+1:actual=actual[1:]
    report['tables'].append({'index':idx,'rows':len(expected),'columns':cols,'all_cells_match':actual==expected,'rowspan_cells':len(table.findall('.//entry[@morerows]'))})
    if actual!=expected:
        report['tables'][-1]['examples']=[{'row':j,'expected':e,'actual':a} for j,(e,a) in enumerate(zip(expected,actual)) if e!=a][:3]

report['visible_syntax_fragments']=[s for s in re.findall(r'.{0,25}(?:\*\*|```|\]\(#|<br\s*/?>).{0,25}',''.join(parsed.visible))]
report['markdown_sha256']=hashlib.sha256((BASE/'UStG.md').read_bytes()).hexdigest()
(BASE/'Pruefung/Markdown_Strukturpruefung.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
summary={k:v for k,v in report.items() if k not in ('paragraphs','tables')}
summary['paragraphs_checked']=len(report['paragraphs']);summary['paragraph_failures']=[x for x in report['paragraphs'] if not x['characters_match'] or not x['list_depth_of_every_character_matches'] or not x['word_boundaries_match']];summary['tables']=report['tables']
print(json.dumps(summary,ensure_ascii=False,indent=2))
