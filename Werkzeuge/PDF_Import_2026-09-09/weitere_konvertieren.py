from pathlib import Path
import concurrent.futures,json,subprocess,sys
from weitere_importieren import BASE,RUN,DOCS

def run(item):
 short,original,slug,area=item
 proof=BASE/'Rechtsgebiete'/area/short/'Stand_2026-09-09/Pruefung'
 for name,template in [('pdf_xml_abgleichen.py','Gewerberecht/GewO'),('markdown_gesamtpruefen.py','Zivilrecht/BGB'),('markdown_struktur_pruefen.py','Zivilrecht/BGB')]:
  s=(BASE/'Rechtsgebiete'/template/'Stand_2026-09-09/Pruefung'/name).read_text(encoding='utf-8')
  s=s.replace("if c['kuerzel'] not in ABBR:return","# Alle hier konfigurierten Gesetze werden geprüft.")
  if name=='pdf_xml_abgleichen.py':
   s=s.replace('Ein Service des Bundesministerium der Justiz und für Verbraucherschutz\\s+sowie des Bundesamts für Justiz ‒ www\\.gesetze-im-internet\\.de','Ein Service des Bundesministeriums? der Justiz(?: und für Verbraucherschutz)?\\s+sowie des Bundesamts für\\s+Justiz [‒–-] www\\.gesetze-im-internet\\.de')
  if name=='markdown_gesamtpruefen.py':
   s=s.replace("head=txt(g.find('gliederungsbez'))+txt(g.find('gliederungstitel'))", "head=('' if txt(g.find('gliederungsbez')).strip()=='-' else txt(g.find('gliederungsbez')))+txt(g.find('gliederungstitel'))+en+txt(node.find('metadaten/titel'))")
  if name=='markdown_struktur_pruefen.py':
   s=s.replace("(joined(group.find('gliederungsbez'))+joined(group.find('gliederungstitel'))) if group", "(('' if joined(group.find('gliederungsbez')).strip()=='-' else joined(group.find('gliederungsbez')))+joined(group.find('gliederungstitel'))+label+joined(meta.find('titel'))) if group")
  (proof/name).write_text(s,encoding='utf-8')
 commands=[['-B',str(RUN/'weitere_converter.py'),'--config',str(proof/'konfiguration.json')],['-B',str(proof/'markdown_gesamtpruefen.py')],['-B',str(proof/'markdown_struktur_pruefen.py')],['-B',str(proof/'pdf_xml_abgleichen.py')]]
 for args in commands:
  result=subprocess.run([sys.executable,*args],capture_output=True,encoding='utf-8')
  name=Path(args[1]).stem
  (proof/(name+'.log')).write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
  if result.returncode:print(short,'FAIL',name,result.stderr[-1600:],result.stdout[-300:],flush=True);return
 pdf=json.loads((proof/'PDF_XML_Abgleich.json').read_text(encoding='utf8'))
 print(short,'DONE','PDF',pdf['exakt_identisch'],'/',pdf['normdatensaetze'],flush=True)
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8')
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:list(p.map(run,DOCS))
