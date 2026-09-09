"""Abruf und reproduzierbare Aufbereitung der weiteren GII-PDF-Eingänge."""
from pathlib import Path
import concurrent.futures, hashlib, json, re, shutil, subprocess, sys, urllib.request, urllib.parse, zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

BASE=Path(__file__).resolve().parents[2]
RUN=Path(__file__).resolve().parent
DOCS=[
 ('AAG','AAG.pdf','aufag','Sozialrecht'),
 ('AktG','AktG.pdf','aktg','Gesellschaftsrecht'),
 ('DVStB','DVStB.pdf','stbdv','Steuerrecht/Berufsrecht'),
 ('EGBGB','EGBGB.pdf','bgbeg','Zivilrecht'),
 ('GmbHG','GmbHG.pdf','gmbhg','Gesellschaftsrecht'),
 ('MiLoG','MiLoG.pdf','milog','Arbeitsrecht'),
 ('PAngV','PAngV.pdf','pangv_2022','Wettbewerbsrecht'),
 ('PublG','PublG.pdf','publg','Handelsrecht'),
 ('SGB_4','SGB_4.pdf','sgb_4','Sozialrecht'),
 ('StBerG','StBerG.pdf','stberg','Steuerrecht/Berufsrecht'),
 ('StBVV','StBVV.pdf','stbgebv','Steuerrecht/Berufsrecht'),
 ('SvEV','SvEV.pdf','svev','Sozialrecht'),
 ('UmwG','UmwG.pdf','umwg_1995','Gesellschaftsrecht'),
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fetch(url,p):
 if not p.exists():
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=90) as r:data=r.read()
  p.write_bytes(data)
 return p.read_bytes()
def download(item):
 short,original,slug,area=item
 folder=BASE/'Rechtsgebiete'/area/short/'Stand_2026-09-09'
 source=folder/'Quellen';proof=folder/'Pruefung';xmlfolder=source/'XML'
 source.mkdir(parents=True,exist_ok=True);proof.mkdir(exist_ok=True);xmlfolder.mkdir(exist_ok=True)
 provided=source/(short+'_bereitgestellt.pdf')
 if not provided.exists():shutil.copy2(BASE/original,provided)
 url=f'https://www.gesetze-im-internet.de/{slug}/'
 index=fetch(url,source/'index.html')
 soup=BeautifulSoup(index,'html.parser')
 pdfhref=next(a['href'] for a in soup.select('a[href]') if a['href'].lower().endswith('.pdf'))
 xmlhref=next(a['href'] for a in soup.select('a[href]') if a['href'].lower().endswith('xml.zip'))
 htmlhref=next(a['href'] for a in soup.select('a[href]') if re.match(r'BJNR.*\.html$',a['href']))
 pdfurl=urllib.parse.urljoin(url,pdfhref);xmlurl=urllib.parse.urljoin(url,xmlhref);htmlurl=urllib.parse.urljoin(url,htmlhref)
 fetch(pdfurl,source/(short+'_aktuell.pdf'));fetch(xmlurl,source/'xml.zip');full=fetch(htmlurl,source/'Gesamtausgabe.html')
 with zipfile.ZipFile(source/'xml.zip') as z:
  for name in z.namelist():
   target=(xmlfolder/name).resolve()
   assert target.is_relative_to(xmlfolder.resolve())
  z.extractall(xmlfolder)
 xp=next(xmlfolder.glob('*.xml'));root=ET.parse(xp).getroot();meta=root[0].find('metadaten')
 pages=int(re.search(r'Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(provided)]).decode('utf-8',errors='replace')).group(1))
 def pdftxt(p):return subprocess.check_output(['pdftotext','-raw','-enc','UTF-8',str(p),'-']).decode('utf-8')
 raw=pdftxt(provided);currentraw=pdftxt(source/(short+'_aktuell.pdf'))
 (source/(short+'_PDF_Rohtext.txt')).write_text(raw,encoding='utf-8')
 htmlsoup=BeautifulSoup(full,'html.parser');fulltext=htmlsoup.get_text(' ',strip=True)
 cite=re.search(r'Vollzitat:\s*(".*?")',fulltext)
 config={'kuerzel':short,'titel':meta.findtext('langue'),'rechtsgebiet':area.replace('/',' / '),'quelle_url':url,'quelle_html':htmlurl,'lokale_pdf':provided.name,'aktuelle_pdf':short+'_aktuell.pdf','xml_datei':xp.relative_to(folder).as_posix(),'ausfertigungsdatum':meta.findtext('ausfertigung-datum'),'stand':[s.findtext('standkommentar') for s in meta.findall('standangabe')],'vollzitat':cite.group(1) if cite else '', 'pdf_seiten':pages,'pdf_identisch_aktuell':sha(provided)==sha(source/(short+'_aktuell.pdf')),'pdf_text_identisch_aktuell':raw==currentraw,'quellenabgleich':'2026-09-09','pdf_url':pdfurl,'xml_url':xmlurl,'html_url':htmlurl,'original_dateiname':original}
 (proof/'konfiguration.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(short,'pages',pages,'PDF identical',config['pdf_identisch_aktuell'],'text',config['pdf_text_identisch_aktuell'],'norms',len(root),'images',len(list(root.iter('IMG'))),'tables',len(list(root.iter('table'))),flush=True)
 assert config['pdf_text_identisch_aktuell'],short+' unterschiedliche Fassung!'
 return config

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(download,item):item[0] for item in DOCS}
  for f in concurrent.futures.as_completed(futures):
   try:f.result()
   except Exception as e:print('ERROR',futures[f],repr(e),flush=True)
