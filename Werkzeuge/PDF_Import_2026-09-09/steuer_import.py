from pathlib import Path
import concurrent.futures, requests, re, json, hashlib, zipfile, io, shutil, subprocess, sys, time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf8')
DOCS=[
('AStG','astg','Internationales_Steuerrecht','AStG.pdf'),
('BewG','bewg','Bewertungsrecht','BewG.pdf'),
('ErbStG','erbstg_1974','Erbschaft_und_Schenkungsteuer','ErbStG.pdf'),
('FzgLiefgMeldV','fzgliefgmeldv','Umsatzsteuer','FzgLiefgMeldV.pdf'),
('GewStDV','gewstdv_1955','Gewerbesteuer','GewStDV.pdf'),
('GrEStG','grestg_1983','Grunderwerbsteuer','GrEStG.pdf'),
('GrStG','grstg_1973','Grundsteuer','GrStG.pdf'),
('InvStG','invstg_2018','Investmentsteuer','InvStG.pdf'),
('KassenSichV','kassensichv','Allgemeines_Steuerrecht','KassenSichV.pdf'),
('KStDV','kstdv_1977','Koerperschaftsteuer','KStDV_1994.pdf'),
('LStDV','lstdv','Einkommensteuer','LStDV.pdf'),
('PStTG','psttg','Internationales_Steuerrecht','PStTG.pdf'),
('SolZG','solzg','Solidaritaetszuschlag','SolZG.pdf'),
('UmwStG','umwstg_2006','Umwandlungssteuer','UmwStG_2006.pdf')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def joined(e):return ''.join(e.itertext()) if e is not None else ''
def get(url):
 for attempt in range(5):
  try:
   r=requests.get(url,timeout=90);r.raise_for_status();return r.content
  except requests.RequestException:
   if attempt==4:raise
   time.sleep(2*(attempt+1))
def import_doc(d):
 short,slug,topic,original=d
 base=ROOT/f'Rechtsgebiete/Steuerrecht/Gesetze/{topic}/{short}/Stand_2026-09-09'
 q=base/'Quellen';p=base/'Pruefung';x=q/'XML'
 for path in [q,p,x]:path.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/original,q/original)
 url='https://www.gesetze-im-internet.de/'+slug+'/'
 index=q/'GII_Index.html'
 if not index.exists():index.write_bytes(get(url))
 soup=BeautifulSoup(index.read_bytes(),'html.parser')
 links={}
 from urllib.parse import urljoin
 for a in soup.find_all('a',href=True):
  h=a['href']
  if h.endswith('.pdf'):links['pdf']=urljoin(url,h)
  if h.endswith('.zip'):links['xml']=urljoin(url,h)
  if re.search(r'BJNR\w+\.html$',h):links['html']=urljoin(url,h)
 if not {'pdf','xml','html'}<=set(links):raise ValueError((short,links,url))
 online=q/(short+'_Gesetze_im_Internet.pdf');z=q/(short+'_XML.zip')
 if not online.exists():online.write_bytes(get(links['pdf']))
 if not z.exists():z.write_bytes(get(links['xml']))
 with zipfile.ZipFile(z) as zz:
  for name in zz.namelist():
   target=(x/name).resolve();assert target.is_relative_to(x.resolve())
  zz.extractall(x)
 xp=next(x.glob('*.xml'));root=ET.parse(xp).getroot();m=root[0].find('metadaten')
 full=q/'GII_Gesamtausgabe.html'
 if not full.exists():full.write_bytes(get(links['html']))
 html=BeautifulSoup(full.read_bytes(),'html.parser')
 text=html.get_text(' ',strip=True)
 # The original first-page text supplies all complete Stand and Hinweis lines.
 raw=subprocess.run(['pdftotext','-f','1','-l','1','-raw',str(q/original),'-'],check=True,stdout=subprocess.PIPE).stdout.decode('utf8')
 raw=raw.replace('\r','')
 cite=re.search(r'Vollzitat:\s*(.*?)\s*Stand:',raw,re.S).group(1)
 cite=re.sub(r'\s+',' ',cite).strip()
 standtext=re.search(r'Stand:\s*(.*?)\s*(?:Fußnote|\* Notifiziert)',raw,re.S).group(1)
 stand=[re.sub(r'\s+',' ',s).strip() for s in re.split(r'\n\s*\n',standtext) if s.strip()]
 info=subprocess.run(['pdfinfo',str(q/original)],stdout=subprocess.PIPE,check=True).stdout.decode('cp1252')
 cfg={'kuerzel':short,'titel':re.sub(r'\s+',' ',joined(m.find('langue'))).strip(),'rechtsgebiet':'Steuerrecht / '+topic,
 'quelle_url':url,'quelle_html':links['html'],'quelle_pdf':links['pdf'],'quelle_xml':links['xml'],'lokale_pdf':original,'aktuelle_pdf':online.name,
 'xml_datei':xp.relative_to(base).as_posix(),'ausfertigungsdatum':m.findtext('ausfertigung-datum'),
 'stand':stand,'vollzitat':cite,'pdf_seiten':int(re.search(r'Pages:\s*(\d+)',info).group(1)),
 'pdf_identisch_aktuell':sha(q/original)==sha(online),'quellenabgleich':'2026-09-09','xml_builddate':root.get('builddate'),
 'sha256_lokale_pdf':sha(q/original),'sha256_aktuelle_pdf':sha(online),'sha256_xml':sha(xp)}
 if short=='SolZG':cfg['historische_fassung']=True
 cfg['normenbestand']={'normdatensaetze':len(root),'gliederungsteile':len(root.findall('./norm/metadaten/gliederungseinheit')),'vorschriften_einschliesslich_bereichsdatensaetzen':sum(n.findtext('metadaten/enbez','').replace('(XXXX) ','').startswith(('§','Art')) for n in root),'anlagen':sum(n.findtext('metadaten/enbez','').startswith(('Anlage','Anhang')) for n in root),'tabellen':len(list(root.iter('table'))),'tabellenzeilen':len(list(root.iter('row'))),'tabellenzellen':len(list(root.iter('entry'))),'aufzaehlungskennzeichen':len(list(root.iter('DT')))}
 (p/'konfiguration.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (p/'Normenbestand.json').write_text(json.dumps([{'index':i,'doknr':n.get('doknr'),'enbez':n.findtext('metadaten/enbez',''),'titel':joined(n.find('metadaten/titel'))} for i,n in enumerate(root)],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return short,{'pdf_identisch':cfg['pdf_identisch_aktuell'],'seiten':cfg['pdf_seiten'],'xml':xp.relative_to(ROOT).as_posix(),'stand':stand,'tables':cfg['normenbestand']['tabellen'],'images':len(list(root.iter('IMG')))}
if __name__=='__main__':
 results={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  fs={ex.submit(import_doc,d):d[0] for d in DOCS}
  for f in concurrent.futures.as_completed(fs):
   try:k,v=f.result();results[k]=v;print(k,json.dumps(v,ensure_ascii=False),flush=True)
   except Exception as e:results[fs[f]]={'error':repr(e)};print(fs[f],repr(e),flush=True)
 (HERE/'steuer_download_status.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
