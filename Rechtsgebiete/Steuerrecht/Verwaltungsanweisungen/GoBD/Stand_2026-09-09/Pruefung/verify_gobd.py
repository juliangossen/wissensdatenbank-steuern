"""Read-only Prüfung der archivierten GoBD-Dateien. Keine Netzzugriffe."""
from pathlib import Path
import re,json,hashlib,collections,unicodedata
from html.parser import HTMLParser
from markdown_it import MarkdownIt
P=Path(__file__).resolve().parent;D=P.parent
md=MarkdownIt('commonmark',{'html':True}).enable('table')
class Plain(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,s):self.parts.append(s)
def canon(s):return re.sub(r'\s+|[-\u00ad]','',unicodedata.normalize('NFC',s))
for result in json.loads((P/'Ergebnisse.json').read_text(encoding='utf8')):
 name=result['document'];text=(D/(name+'.md')).read_text(encoding='utf8')
 assert hashlib.sha256((D/(name+'.md')).read_bytes()).hexdigest()==result['markdown_sha256'],name
 assert hashlib.sha256((D/'Quellen'/(name+'.pdf')).read_bytes()).hexdigest()==result['source_pdf_sha256'],name
 blocks=json.loads((P/(name+'-Quellbloecke.json')).read_text(encoding='utf8'))
 for b in blocks:
  found=re.search(r'<!-- source:'+b['id']+':'+b['kind']+r' -->\n(.*?)\n<!-- /source:'+b['id']+r' -->',text,re.S)
  assert found and found[1]==b['value'],(name,b['id'])
  parser=Plain();parser.feed(md.render(found[1]));actual=canon(''.join(parser.parts));expected=canon(b['source'])
  assert (collections.Counter(actual)==collections.Counter(expected) if b['kind']=='table' else actual==expected),(name,b['id'])
 anchors=re.findall(r'<a id="([^"]+)"',text)
 assert len(anchors)==len(set(anchors)),name
 for anchor in re.findall(r'\]\(#([^)]*)\)',text):assert anchor in anchors,(name,anchor)
 assert len(re.findall(r'<a id="seite-',text))==result['pages']
 if name.startswith('2019'):assert [int(v) for v in re.findall(r'<a id="rz-(\d+)"',text)]==list(range(1,185))
 print(name+': SHA-256, Quellbloecke, sichtbarer Text, Seiten, Randnummern und Anker OK')
for file in D.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf8')):
  if not re.match(r'^(https?://|#)',target):assert (file.parent/target.split('#')[0]).exists(),(str(file),target)
print('Alle lokalen Markdown-Links vorhanden.')
