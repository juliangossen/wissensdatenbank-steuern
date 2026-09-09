from steuer_import import ROOT,HERE,DOCS
from pathlib import Path
import json, shutil, subprocess, sys
sys.stdout.reconfigure(encoding='utf8')
TEMPLATE=ROOT/'Rechtsgebiete/Steuerrecht/Gesetze/Koerperschaftsteuer/KStG/Stand_2026-09-09/Pruefung'
for short,slug,topic,original in DOCS:
 if len(sys.argv)>1 and short not in sys.argv[1:]:continue
 p=ROOT/f'Rechtsgebiete/Steuerrecht/Gesetze/{topic}/{short}/Stand_2026-09-09/Pruefung'
 if not (p/'konfiguration.json').exists():continue
 for file in ['konvertieren.py','markdown_struktur_pruefen.py','pdf_xml_pruefen.py']:
  if not (p/file).exists():shutil.copy2(TEMPLATE/file,p/file)
 converter=(ROOT/'Werkzeuge/gesetz_konvertieren.py').read_text('utf8')
 if short=='KassenSichV':
  converter=converter.replace("self.add('# '+esc(c['titel'])", "self.add('# '+self.mixed(first.find('langue')).strip()")
 if short=='SolZG':
  converter=converter.replace("self.add('## Navigation", "self.add('**Historische Fassung:** Dies ist das Solidaritätszuschlaggesetz vom 24. Juni 1991 mit Änderungsstand 25. Februar 1992. Es ist nicht das Solidaritätszuschlaggesetz 1995. Die zeitlichen Anwendungsvorschriften der gelieferten Quelle bleiben maßgeblich.')\n        self.add('## Navigation")
 if not (p/'konverter_snapshot.py').exists(): (p/'konverter_snapshot.py').write_text(converter,encoding='utf8')
 # Account for both official service line variants (the old PDF footer was on top).
 pp=(p/'pdf_xml_pruefen.py').read_text('utf8')
 pp=pp.replace("raw=re.sub(r'Ein Service des Bundesministerium[^\\n]*\\n\\s*sowie des Bundesamts für Justiz [^\\n]*','',raw)","raw=re.sub(r'Ein Service des Bundesministerium.*?www\\.gesetze-im-internet\\.de','',raw,flags=re.S)")
 (p/'pdf_xml_pruefen.py').write_text(pp,encoding='utf8')
 results={}
 for file in ['konvertieren.py','markdown_struktur_pruefen.py','pdf_xml_pruefen.py']:
  r=subprocess.run([sys.executable,'-B',str(p/file)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (p/(file+'.log')).write_bytes(r.stdout)
  results[file]=r.returncode
  if r.returncode:print(short,file,'FAIL',r.stdout.decode('utf8')[-2500:],flush=True)
 print(short,results,flush=True)
