"""Ergänzungen für originale Formatmarkierungen und verlinkte PDF-Anlagen."""
import argparse,html,sys,subprocess,re,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from weitere_converter_basis import Converter,esc

class ExtendedConverter(Converter):
 def run(self):
  super().run()
  if self.c['kuerzel']=='EGBGB':
   path=self.base/'EGBGB.md';md=path.read_text(encoding='utf8');lines=[]
   for node in list(self.root)[1:]:
    m=node.find('metadaten');g=m.find('gliederungseinheit');en=m.findtext('enbez','');title=' '.join(''.join(g.find(k).itertext()) for k in ['gliederungsbez','gliederungstitel']) if g is not None else ''
    title=title.strip()
    if title=='-':title=''
    if en:title+=(' / ' if title else '')+en+' '+''.join(m.find('titel').itertext()) if m.find('titel') is not None else en
    lines.append('- ['+esc(re.sub(r'\s+',' ',title).strip())+'](#'+self.anchors[node.get('doknr')]+')')
   start=md.index('## Navigation');end=md.index('<a id="dokumentkopf">',start)
   md=md[:start]+'## Navigation\n\n- [Dokumentkopf](#dokumentkopf)\n'+'\n'.join(lines)+'\n\n'+md[end:]
   path.write_text(md,encoding='utf8',newline='\n')
   rp=self.base/'Pruefung/Vollstaendigkeitspruefung.json';report=json.loads(rp.read_text(encoding='utf8'));report['sha256_markdown']=hashlib.sha256(path.read_bytes()).hexdigest();report['interne_links']=len(re.findall(r'\]\(#([^)]*)\)',md)+re.findall(r'href="#([^"]+)"',md));report['technische_leere_gliederung_minus_ausgeblendet']=sum(n.findtext('metadaten/gliederungseinheit/gliederungsbez','').strip()=='-' for n in self.root)
   report['xml_gliederungsmetadaten_vorkommen']=report['gliederungsteile'];report['gliederungsteile']=len({n.findtext('metadaten/gliederungseinheit/gliederungskennzahl') for n in self.root if n.find('metadaten/gliederungseinheit') is not None});report['gliederungszaehlung']='Verschiedene XML-Gliederungsschlüssel; wiederholte Artikelmetadaten bei untergeordneten Paragraphen zählen einmal.'
   rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 def raw(self,e):
  if e.tag in {'FnArea','Split'}:return html.escape(e.text or '',quote=False)+''.join(self.raw(c)+html.escape(c.tail or '',quote=False) for c in e)
  if e.tag=='U':return '<u>'+html.escape(e.text or '',quote=False)+''.join(self.raw(c)+html.escape(c.tail or '',quote=False) for c in e)+'</u>'
  if e.tag=='FILE':return self.file(e)
  return super().raw(e)
 def render(self,e,cell=False):
  if e.tag in {'FnArea','Split'}:return self.mixed(e,cell)
  if e.tag=='titel':return re.sub(r'\s+',' ',html.escape(e.text or '',quote=False)+''.join(self.raw(c)+html.escape(c.tail or '',quote=False) for c in e))
  if e.tag=='U':return self.raw(e)
  if e.tag=='FILE':return self.file(e)
  if e.tag=='Title':
   content=html.escape(e.text or '',quote=False)+''.join(self.raw(c)+html.escape(c.tail or '',quote=False) for c in e)
   return ('<strong>'+content+'</strong><br>') if cell else '\n\n<div><strong>'+content+'</strong></div>\n\n'
  return super().render(e,cell)
 def file(self,e):
  path=(self.xml.parent/e.get('SRC')).resolve();assert path.is_file()
  rel=path.relative_to(self.base).as_posix();self.assets[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
  info=subprocess.check_output(['pdfinfo',str(path)]).decode('utf8',errors='replace')
  count=int(re.search(r'Pages:\s+(\d+)',info).group(1))
  out=self.base/'Quellen/Dateianlagen';out.mkdir(exist_ok=True)
  images=[]
  for page in range(1,count+1):
   stem=out/(path.stem+f'_Seite_{page}')
   img=stem.with_suffix('.png')
   if not img.exists():subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-r','120','-png','-singlefile',str(path),str(stem)],check=True,capture_output=True)
   ir=img.relative_to(self.base).as_posix();self.assets[ir]=hashlib.sha256(img.read_bytes()).hexdigest()
   images.append('<p><img src="'+ir+'" alt="Originalformular, Seite '+str(page)+'"></p>')
  raw=subprocess.check_output(['pdftotext','-raw','-enc','UTF-8',str(path),'-']).decode('utf8').replace('\r\n','\n').replace('\r','\n')
  raw=re.sub(r'(?m)^\s*\d+\s+Bundesgesetzblatt Jahrgang.*?$','',raw)
  raw=re.sub(r'(?m)^\s*Bundesgesetzblatt Jahrgang.*?\s+\d+\s*$','',raw)
  raw=re.sub(r'(?m)^\s*Das Bundesgesetzblatt im Internet:.*?$','',raw)
  raw=re.sub(r'(?m)^\s*Ein Service des Bundesanzeiger Verlag.*?$','',raw)
  (out/(path.stem+'_Text.txt')).write_text(raw,encoding='utf8',newline='\n')
  # Der Dateiinhalt ist kein XML-itertext. Separater vollständiger Vergleich in Datei_Anlagenpruefung.json.
  body='<div data-redaktionell="volltext-aus-xml-dateianhang"><p><strong>Volltext der in der XML referenzierten Dateianlage</strong></p><p><a href="'+rel+'">Original-PDF der Anlage</a></p><pre>'+html.escape(raw)+'</pre>'+''.join(images)+'</div>'
  proof={'datei':rel,'pdf_seiten':count,'textdatei':(out/(path.stem+'_Text.txt')).relative_to(self.base).as_posix(),'sha256_anlagen_pdf':hashlib.sha256(path.read_bytes()).hexdigest(),'sha256_uebernommener_text':hashlib.sha256(raw.encode()).hexdigest(),'methode':'Vollständiger pdftotext-Rohtext der XML-Dateianlage, nur Bundesgesetzblatt-Seitenkopf und Druckservice entfernt; HTML-escaped als vollständiger Textblock übernommen. Zusätzlich jede Originalseite als Abbildung.'}
  (self.base/'Pruefung/Datei_Anlagenpruefung.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  return '\n\n'+body+'\n\n'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();ExtendedConverter(a.config).run()
