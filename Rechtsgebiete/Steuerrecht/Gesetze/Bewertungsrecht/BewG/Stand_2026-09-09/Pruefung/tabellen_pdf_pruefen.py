"""Exakter PDF-Zellenvergleich mit beschränkter Lesereihenfolge für verbundene Zellen."""
from pathlib import Path
import xml.etree.ElementTree as ET
import json,re,unicodedata,hashlib,copy
BASE=Path(__file__).resolve().parent.parent
CFG=json.loads((BASE/'Pruefung/konfiguration.json').read_text('utf8'))
ROOT=ET.parse(BASE/CFG['xml_datei']).getroot()
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFC',s)).replace('\u00ad','')
RAW=(BASE/'Pruefung/PDF_Text_roh.txt').read_text('utf8')
RAW=re.sub(r'Ein Service des Bundesministerium.*?www\.gesetze-im-internet\.de','',RAW,flags=re.S)
RAW=re.sub(r'- Seite \d+ von \d+ -','',RAW)
PDF_NORM=norm(RAW);LINE_ENDS={};_offset=0;_page=1
for _line in RAW.splitlines(keepends=True):
 _offset+=len(norm(_line))
 if norm(_line):LINE_ENDS[_offset]={'pdf_seite':_page,'pdf_zeile':_line.strip()}
 _page+=_line.count('\f')
GLOBAL_START=0
def marked(e,markers,breaks=False):
 if e is None:return ''
 if breaks and e.tag=='BR':return '\n'
 return (markers.get(e.get('ID'),'') if e.tag in {'FnR','Footnote'} else '')+(e.text or '')+''.join(marked(c,markers,breaks)+(c.tail or '') for c in e)
def cell_items(table,markers):
 g=table.find('tgroup');names={c.get('colname'):i for i,c in enumerate(g.findall('colspec'))}
 items=[];rownum=0
 for section in ['thead','tbody','tfoot']:
  for row in g.findall(section+'/row'):
   col=0
   for cell in row.findall('entry'):
    if cell.get('colname') or cell.get('namest'):col=names[cell.get('colname') or cell.get('namest')]
    s=norm(marked(cell,markers));span=int(cell.get('morerows','0'))
    if s:items.append({'i':len(items),'text':s,'r':rownum,'end':rownum+span,'c':col,'header':section=='thead','numeric':bool(re.search(r'\d',s) and re.fullmatch(r'[\d.,%/–−+\-]+',s)), 'fragments':[norm(x) for x in marked(cell,markers,True).split('\n') if norm(x)]})
    col=(names[cell.get('nameend')]+1) if cell.get('nameend') else col+1
   rownum+=1
 return items
def consume_table(table,pdf,start,markers):
 items=cell_items(table,markers);remaining=copy.deepcopy(items);pos=start;order=[];repeats=[];fragments=[]
 # PDF-Seiten 127/128: eine Sanitärzelle bricht innerhalb des Wortes Gäste-WC um.
 split='➀mehreregroßzügige,hochwertigeBäder,Gäste-WC;➁2undmehrBäderjeWohneinheit'
 for cell in remaining:
  if split in cell['fragments']:
   i=cell['fragments'].index(split)
   cell['fragments'][i:i+1]=['➀mehreregroßzügige,hochwertigeBäder,Gäste-','WC;➁2undmehrBäderjeWohneinheit']
 headers=[x for x in items if x['header']];header_text=None;header_start=start
 while remaining:
  if header_text and pdf.startswith(header_text,pos):
   repeats.append(pos-start);pos+=len(header_text);continue
  earliest=min(x['end'] for x in remaining)
  candidates=[x for x in remaining if x['r']<=earliest]
  # Numeric cells without rowspan must keep their column order in each data row.
  nums=[x for x in candidates if x['numeric'] and not x['header'] and x['r']==x['end']]
  if nums:
   first=min(nums,key=lambda x:(x['r'],x['c']))
   candidates=[x for x in candidates if x not in nums or x==first]
  possible=[x for x in candidates if pdf.startswith(x['text'],pos)]
  if not possible:
   split=[x for x in candidates if len(x['fragments'])>1 and pdf.startswith(x['fragments'][0],pos)]
   if split:
    chosen=max(split,key=lambda x:len(x['fragments'][0]));part=chosen['fragments'].pop(0)
    fragments.append({'zelle':chosen['i'],'text':part,'position':pos-start});pos+=len(part);chosen['text']=chosen['text'][len(part):]
    continue
   # Physically wrapped PDF cells can be interrupted by other cells or a page header.
   # Every extra split must end at an independently extracted PDF line boundary.
   physical=[]
   for x in candidates:
    length=0
    for a,b in zip(x['text'],pdf[pos:]):
     if a!=b:break
     length+=1
    if 8<=length<len(x['text']):
     boundaries=[b-GLOBAL_START-pos for b in LINE_ENDS if GLOBAL_START+pos+8<=b<=GLOBAL_START+pos+length]
     if boundaries:physical.append((max(boundaries),x))
   if physical:
    length,chosen=max(physical,key=lambda pair:pair[0]);part=chosen['text'][:length]
    fragments.append({'zelle':chosen['i'],'text':part,'position':pos-start,'physischer_pdf_zeilenumbruch':LINE_ENDS[GLOBAL_START+pos+length]})
    pos+=length;chosen['text']=chosen['text'][length:];chosen['fragments']=[chosen['text']]
    continue
   return None,{'error':'Zelle nicht zuordenbar','position':pos,'kontext':pdf[pos:pos+180],'kandidaten':candidates[:12],'verarbeitet':len(order)}
  chosen=max(possible,key=lambda x:len(x['text']))
  order.append(chosen['i']);remaining.remove(chosen);pos+=len(chosen['text'])
  if headers and header_text is None and all(x not in remaining for x in headers):
   assert all(items[i]['header'] for i in order)
   header_text=pdf[header_start:pos]
 result={'zellen':len(items),'nichtleere_zellen_einmalig_identisch':True,'reine_zahlen_und_wertebereiche_ohne_zeilenverbund_in_datenzeilen_identisch':True,'lesereihenfolge_xml_zellindizes':order,'wiederholte_tabellenkoepfe':len(repeats),'wiederholung_positionen':repeats,'pdf_kopf':header_text,'xml_kopf':''.join(x['text'] for x in headers),'an_nachgewiesenen_zeilenumbruechen_geteilte_zellen':fragments}
 return pos,result
def verify(name,expected,actual):
 global GLOBAL_START
 GLOBAL_START=PDF_NORM.find(actual)
 assert GLOBAL_START>=0
 if name=='Inhaltsübersicht':
  x='Anlage38(zu§253Absatz2und§259Absatz4)WirtschaftlicheGesamtnutzungsdauer'
  p='Anlage38WirtschaftlicheGesamtnutzungsdauer(zu§253Absatz2und§259Absatz4)'
  if expected.count(x)==1 and actual.count(p)==1 and actual.replace(p,x,1)==expected:return True,[{'art':'Inhaltsübersicht: Titel vor mehrzeiligem Bezug gelesen','xml':x,'pdf':p,'rest_identisch':True}]
 node=copy.deepcopy(next(n for n in ROOT if n.findtext('metadaten/enbez','')==name))
 markers={x.get('ID'):x.get('FnZ',str(j+1)) for j,x in enumerate(node.iter('Footnote'))}
 relocations=[]
 for area in node.iter('FnArea'):
  refs=list(area)
  for ref in refs:
   ident=ref.get('ID');original=next(x for x in node.iter('Footnote') if x.get('ID')==ident)
   foot=copy.deepcopy(original)
   owner=next(x for x in node.iter('Footnotes') if original in list(x));owner.remove(original)
   area.remove(ref);area.append(foot)
   relocations.append({'id':ident,'text':norm(marked(foot,markers))})
 if relocations:
  expected=norm(name+marked(node.find('metadaten/titel'),markers)+marked(node.find('textdaten/text'),markers)+('Fußnote' if norm(marked(node.find('textdaten/fussnoten'),markers)) else '')+marked(node.find('textdaten/fussnoten'),markers))
 tables=list(node.iter('table'))
 ex=0;pos=0;reports=([{'art':'Manuelle XML-Fußnoten werden an ihrer FnArea-Druckposition gelesen; der zusätzliche FnArea-Verweis ist kein zweiter gedruckter Marker','fussnoten':relocations}] if relocations else [])
 for i,t in enumerate(tables):
  token=norm(marked(t,markers))
  if not token:continue
  at=expected.find(token,ex)
  if at<0:return False,[{'error':'XML-Tabelle nicht gefunden','tabelle':i}]
  before=expected[ex:at]
  if not actual.startswith(before,pos):return False,reports+[{'error':'Text vor Tabelle abweichend','tabelle':i,'erwartet':before[:300],'pdf':actual[pos:pos+300],'position':pos}]
  pos+=len(before)
  newpos,report=consume_table(t,actual,pos,markers)
  report['tabelle']=i;reports.append(report)
  if newpos is None:return False,reports
  pos=newpos;ex=at+len(token)
 rest=expected[ex:]
 if actual[pos:]!=rest:return False,reports+[{'error':'Resttext abweichend','xml':rest[:1000],'pdf':actual[pos:pos+1000],'position':pos}]
 return True,reports
