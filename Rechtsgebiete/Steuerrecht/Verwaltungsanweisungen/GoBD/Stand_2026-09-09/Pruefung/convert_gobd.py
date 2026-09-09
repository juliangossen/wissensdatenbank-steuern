"""Reproduzierbare, quellengenaue GoBD-PDF -> Markdown-Konvertierung.
Voraussetzungen: Python 3, PyMuPDF (fitz), Poppler pdftotext.
Aufruf nach Ablage: py Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/GoBD/Stand_2026-09-09/Pruefung/convert_gobd.py
"""
from pathlib import Path
import re,json,hashlib,subprocess,shutil,unicodedata,collections,html
import fitz
from markdown_it import MarkdownIt
from html.parser import HTMLParser
MD=MarkdownIt('commonmark',{'html':True}).enable('table')
class PlainHTML(HTMLParser):
 def __init__(self):super().__init__();self.values=[]
 def handle_data(self,data):self.values.append(data)
def rendered_text(value):
 parser=PlainHTML();parser.feed(MD.render(value));return ''.join(parser.values)

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'PDF_Archiv/Archivregister.json').is_file())
DEST=HERE.parent
ARCHIV=json.loads((ROOT/'PDF_Archiv/Archivregister.json').read_text(encoding='utf-8'))
TMP=ROOT/'tmp/gobd_dokumente'
SRC=DEST/'Quellen';QA=DEST/'Pruefung';ASSETS=SRC/'Abbildungen'
for p in (DEST,SRC,QA,ASSETS):p.mkdir(parents=True,exist_ok=True)
NAMES=['2019-11-28-GoBD','2024-03-11-aenderung-gobd','2025-07-14-GoBD-2-aenderung']
URLS=[
'https://ao.bundesfinanzministerium.de/ao/2023/Anhaenge/BMF-Schreiben-und-gleichlautende-Laendererlasse/Anhang-64/inhalt.html',
'https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/AO-Anwendungserlass/2024-03-11-aenderung-gobd.html',
'https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/2025-07-14-GoBD-2-aenderung.html']

def canon(s):
 s=unicodedata.normalize('NFC',s)
 return re.sub(r'\s+|[-\u00ad]','',s)

def join_lines(lines):
 out=''
 for line in lines:
  line=re.sub(r'\s+',' ',line.strip())
  if not line:continue
  if out and out.endswith('-') and re.match(r'^[a-zäöüß]',line) and not re.match(r'^(und|oder|bzw\.|sowie)\b',line):
   out=out[:-1]+line
  else:out+=(' ' if out else '')+line
 return out

def table_cells(pg, bounds):
 rows=[]
 for lo,hi in zip(bounds,bounds[1:]):
  cells=[]
  for x0,x1 in [(125,324),(325,540)]:
   txt=pg.get_text('text',clip=fitz.Rect(x0,lo,x1,hi),sort=True)
   cells.append(join_lines(txt.splitlines()))
  rows.append(cells)
 return rows

results=[]
for idx,name in enumerate(NAMES):
 pdf=SRC/(name+'.pdf')
 originals=[e for e in ARCHIV['eintraege'] if e['urspruenglicher_dateiname']==name+'.pdf' and e['archivversion']==DEST.name]
 assert len(originals)==1, name
 original=ROOT/originals[0]['pdf']
 assert hashlib.sha256(original.read_bytes()).hexdigest()==originals[0]['sha256_pdf']
 if not pdf.exists():shutil.copyfile(original,pdf)
 assert pdf.read_bytes()==original.read_bytes()
 d=fitz.open(pdf)
 outtxt=QA/(name+'-pdftotext-layout.txt')
 subprocess.run(['pdftotext','-layout','-enc','UTF-8',str(pdf),str(outtxt)],check=True)
 raw=outtxt.read_text(encoding='utf8')
 pages=raw.split('\f')
 if not pages[-1].strip():pages.pop()
 assert len(pages)==len(d)
 log=[];toc=[];chunks=[];sequence=0;rn=[];pointnums=[]
 def emit(kind,source,value=None,page=0):
  global sequence
  sequence+=1
  if value is None:value=join_lines(source.splitlines())
  sid=f'{sequence:04d}'
  log.append(dict(id=sid,kind=kind,page=page,source=source,value=value))
  chunks.append(f'<!-- source:{sid}:{kind} -->\n{value}\n<!-- /source:{sid} -->\n')
 def heading(source,level,ident,page):
  val=join_lines(source.splitlines())
  toc.append((level,val,ident))
  chunks.append(f'<a id="{ident}"></a>\n')
  emit('heading',source,'#'*level+' '+val,page)
 def prose(source,page):
  val=join_lines(source.splitlines())
  if not val:return
  if idx==0:
   m=re.match(r'^(\d{1,3})\s+(.+)',val)
   if m and page>=4 and int(m[1])==(rn[-1]+1 if rn else 1):
    rn.append(int(m[1]));chunks.append(f'<a id="rz-{m[1]}"></a>\n')
    return emit('randnummer',source,f'**{m[1]}** {m[2]}',page)
  # Escape numbered prose/list markers: their original numbers must not be reset by Markdown.
  if re.match(r'^\d+\. ',val):val=re.sub(r'^(\d+)\.',r'\1\\.',val)
  emit('paragraph',source,val,page)
 for page_no,txt in enumerate(pages,1):
  chunks.append(f'<a id="seite-{page_no}"></a>\n\n<!-- editorial:start -->\n## PDF-Seite {page_no}\n<!-- editorial:end -->\n')
  if d[page_no-1].get_images():
   im=d[page_no-1].get_images()[0][0];imdata=d.extract_image(im)
   image_name=name+'-briefkopf.'+imdata['ext']
   (ASSETS/image_name).write_bytes(imdata['image'])
   chunks.append(f'<!-- editorial:start -->\n![Originales Hoheitszeichen / Behördenlogo](Quellen/Abbildungen/{image_name})\n<!-- editorial:end -->\n')
  if page_no==1:
   splitword='Unter Bezugnahme' if idx==0 else 'Insbesondere'
   start=txt.index(splitword)
   # Briefkopf in ursprünglicher Spaltenanordnung; Haupttext separat.
   before=txt[:start].rstrip()
   emit('briefkopf',before,'```text\n'+before+'\n```',page_no)
   txt=txt[start:]
  if idx==0 and page_no in (2,3):
   # Die amtliche Übersicht enthält ihre Original-Seitenverweise und Füllpunkte.
   emit('original-inhalt',txt,'```text\n'+txt.strip()+'\n```',page_no)
   continue
  # Seitenlabel bleibt als sichtbarer Quelltext bestehen.
  m=re.match(r'\s*(Seite \d+(?: von \d+)?)',txt)
  if m:
   emit('seitenlabel',m[0],m[1],page_no);txt=txt[m.end():]
  table=None
  if idx==0 and page_no in (19,20):
   begin=txt.index('Bezeichnung')
   end=(len(txt) if page_no==19 else txt.index('Vgl. Rz. 85'))
   table=txt[begin:end]
   txt=txt[:begin]+'\n@@TABLE@@\n'+txt[end:]
  lines=txt.splitlines();buf=[];line_i=0
  boldlines=[];boldgroups={}
  for block in d[page_no-1].get_text('dict')['blocks']:
   for ln in block.get('lines',[]):
    spans=[s for s in ln['spans'] if s['text'].strip()]
    if spans and all('Bold' in s['font'] for s in spans):
     bt=''.join(s['text'] for s in spans);boldlines.append(canon(bt))
     key=round(ln['bbox'][1]);boldgroups.setdefault(key,[]).append((ln['bbox'][0],bt))
  for group in boldgroups.values():boldlines.append(canon(''.join(bt for x,bt in sorted(group))))
  def isbold(st):return canon(st) in boldlines
  def flush():
   if buf:prose('\n'.join(buf),page_no);buf.clear()
  while line_i<len(lines):
   line=lines[line_i];st=line.strip()
   if not st:
    flush();line_i+=1;continue
   if st=='@@TABLE@@':
    flush()
    rows=table_cells(d[page_no-1],[367,396,617,698,743] if page_no==19 else [52,77,139,187,274,454,499])
    assert rows[0]==['Bezeichnung','Begründung'],rows[0]
    table_md='| Bezeichnung | Begründung |\n| --- | --- |\n'+'\n'.join('| '+' | '.join(c.replace('|','&#124;') for c in row)+' |' for row in rows[1:])
    emit('table',table,table_md,page_no)
    d[page_no-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(ASSETS/f'{name}-seite-{page_no}.png')
    chunks.append(f'<!-- editorial:start -->\n[Originalabbildung der Tabelle auf PDF-Seite {page_no}](Quellen/Abbildungen/{name}-seite-{page_no}.png).\n<!-- editorial:end -->\n')
    line_i+=1;continue
   h=re.match(r'^(\d+(?:\.\d+){1,2}|\d+\.)\s+\S',st)
   ishead=False
   if idx==0 and h and page_no>=4:
    ishead=isbold(st)
   elif idx==1 and (page_no>=5 or (page_no==4 and st.startswith('„Ergänzende'))):
    ishead=(bool(h) and isbold(st)) or st.startswith('„Ergänzende')
   elif idx in (1,2) and h and '.' in h[1] and h[1].endswith('.') and (idx==2 or page_no<=4):
    ishead=True;pointnums.append(int(h[1][:-1]))
   if ishead:
    flush();headlines=[line];line_i+=1
    # PDF section headings can wrap onto several adjacent indented lines.
    # Numbered amending instructions keep their complete first physical paragraph.
    while line_i<len(lines) and lines[line_i].strip():
     nxt=lines[line_i];ns=nxt.strip()
     if idx==0 or (idx==1 and page_no>=5):
      if not isbold(ns):break
     else:
      if headlines[-1].strip().endswith((':','.')):break
      if re.match(r'^(\d{1,3}\s{2,}|[a-z]\)|•|\d+\.\s)',ns):break
     headlines.append(nxt);line_i+=1
    num=h[1].rstrip('.') if h else 'anlage'
    ident=f'abschnitt-{num.replace(".","-")}'
    if any(t[2]==ident for t in toc):ident=f'{ident}-seite-{page_no}'
    level=min(5,3+num.count('.'))
    heading('\n'.join(headlines),level,ident,page_no)
    continue
   # Start every Randnummer or list marker as its own paragraph.
   if re.match(r'^\s*\d{1,3}\s{2,}\S',line) or re.match(r'^(?:•|o |[a-z]\))',st):flush()
   buf.append(line);line_i+=1
  flush()
 # Navigation is editorial. All source text is bounded by machine-readable comments.
 title=['GoBD – BMF-Schreiben vom 28. November 2019','GoBD – Änderung vom 11. März 2024','GoBD – 2. Änderung vom 14. Juli 2025'][idx]
 pre=f'''---
titel: "{title}"
dokumenttyp: "Verwaltungsanweisung / BMF-Schreiben"
rechtsgebiet: "Steuerrecht / Buchführung und Aufbewahrung"
quellenabgleich: "2026-09-09"
schreiben_vom: "{name[:10]}"
fassung: "Originalschreiben; nicht konsolidiert"
quelle: "{URLS[idx]}"
umfang_pdf_seiten: {len(d)}
---

# {title}

Vollständige Wiedergabe der bereitgestellten [Original-PDF](Quellen/{name}.pdf), einschließlich Briefkopf, Inhaltsübersicht (soweit vorhanden), Randnummern, Tabellen, Anlage (2024) und Schlusszeilen. Das Datum des Ordners bezeichnet den **Quellenabgleich vom 09.09.2026**, nicht eine Neufassung dieses Schreibens. Diese drei Schreiben sind gemeinsam zu lesen; spätere Änderungen wurden hier nicht in ältere Schreiben eingearbeitet. [Fassungsübersicht](README.md) · [Prüfbericht](Pruefung/Pruefbericht.md).

Die PDF-Seitenanker und Navigationslinks sind redaktionell. Zeilenumbrüche wurden aufgelöst, erkennbare Worttrennungen zusammengezogen; Schreibweisen, Zitate und Nummerierung der Quelle bleiben erhalten. Das amtliche Inhaltsverzeichnis und die mehrspaltigen Briefköpfe sind originalgetreu als Textblöcke wiedergegeben. Tabellen stehen als Markdown und zusätzlich als Originalabbildungen zur Verfügung.

## Navigation

'''
 pre+=' · '.join(f'[Seite {i}](#seite-{i})' for i in range(1,len(d)+1))+'\n\n'
 pre+='\n'.join('  '*(level-3)+f'- [{val}](#{ident})' for level,val,ident in toc)+'\n\n---\n\n'
 output=pre+'\n'.join(chunks)
 out=DEST/(name+'.md');out.write_text(output,encoding='utf8')
 # Reverse-parse every source block from the saved Markdown; exclude navigation only.
 restored=[];blockchecks=[]
 for item in log:
  match=re.search(r'<!-- source:'+item['id']+':'+item['kind']+r' -->\n(.*?)\n<!-- /source:'+item['id']+r' -->',output,re.S)
  assert match,item
  value=match[1]
  assert value==item['value']
  if item['kind'] in ('briefkopf','original-inhalt'):value=value.split('\n',1)[1].rsplit('\n',1)[0]
  elif item['kind']=='heading':value=re.sub(r'^#+ ','',value)
  elif item['kind']=='randnummer':value=value.replace('**','')
  elif item['kind']=='paragraph':value=value.replace('\\.','.')
  elif item['kind']=='table':
   value=' '.join(x for x in value.splitlines() if not re.fullmatch(r'\|[ |:-]+\|',x))
   value=html.unescape(value.replace('|',''))
  srcnorm=canon(item['source']);outnorm=canon(value)
  ok=(collections.Counter(srcnorm)==collections.Counter(outnorm)) if item['kind']=='table' else srcnorm==outnorm
  rendered=canon(rendered_text(item['value']))
  rendered_ok=(collections.Counter(srcnorm)==collections.Counter(rendered)) if item['kind']=='table' else srcnorm==rendered
  blockchecks.append(dict(id=item['id'],kind=item['kind'],page=item['page'],passed=ok,rendered_html_passed=rendered_ok,source_chars=len(srcnorm),markdown_chars=len(outnorm)))
  if not rendered_ok:print('RENDER FAILED',name,item['id'],repr(rendered[:80]),repr(srcnorm[:80]))
  if not ok:
   print('FAILED',name,item['id'],item['kind'],collections.Counter(srcnorm)-collections.Counter(outnorm),collections.Counter(outnorm)-collections.Counter(srcnorm))
  restored.append(item['source'])
 # Full page extraction coverage: even headers, footers and original TOC fill dots.
 original_counter=collections.Counter(canon(raw));source_counter=collections.Counter(canon(''.join(restored)))
 coverage=original_counter==source_counter
 if not coverage:print('COVERAGE FAILED',name,original_counter-source_counter,source_counter-original_counter)
 # Independent extractor, alphabetic / numeric character multiset (layout order differs).
 independent=''.join(p.get_text() for p in d)
 alnum=lambda s:collections.Counter(c for c in unicodedata.normalize('NFC',s) if c.isalnum())
 independent_ok=alnum(raw)==alnum(independent)
 if not independent_ok:print('INDEPENDENT DIFF',name,alnum(raw)-alnum(independent),alnum(independent)-alnum(raw))
 result=dict(document=name,pages=len(d),source_pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),markdown_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),source_blocks=len(log),all_source_characters_covered=coverage,markdown_roundtrip_all_blocks=all(c['passed'] for c in blockchecks),rendered_html_roundtrip_all_blocks=all(c['rendered_html_passed'] for c in blockchecks),independent_extractor_alnum_match=independent_ok,independent_extractor_missing=dict(alnum(raw)-alnum(independent)),independent_extractor_extra=dict(alnum(independent)-alnum(raw)),randnummern=rn,amendment_numbers=pointnums,checks=blockchecks)
 if idx==0:result['randnummern_1_bis_184_lueckenlos']=rn==list(range(1,185))
 (QA/(name+'-Quellbloecke.json')).write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf8')
 (QA/(name+'-Pruefung.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 results.append({k:v for k,v in result.items() if k not in ('checks','randnummern')})
 print(name,'pages',len(d),'blocks',len(log),'coverage',coverage,'roundtrip',result['markdown_roundtrip_all_blocks'],'rn',len(rn),'independent',independent_ok)
(QA/'Ergebnisse.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
if HERE!=QA:shutil.copyfile(__file__,QA/'convert_gobd.py')
assert all(x['all_source_characters_covered'] and x['markdown_roundtrip_all_blocks'] and x['rendered_html_roundtrip_all_blocks'] for x in results)
assert results[0]['randnummern_1_bis_184_lueckenlos']
