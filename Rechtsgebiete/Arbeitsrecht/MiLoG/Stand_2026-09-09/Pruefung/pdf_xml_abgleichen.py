"""Vollständiger PDF/XML-Abgleich mit dokumentierten XML-Layoutkonventionen."""
from pathlib import Path
import argparse,collections,difflib,hashlib,json,re,subprocess,sys,unicodedata,xml.etree.ElementTree as ET
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFC',s))
def text(e):return ''.join(e.itertext()) if e is not None else ''
def perform(cp):
 c=json.loads(cp.read_text(encoding='utf8'));base=cp.parent.parent;r=ET.parse(base/c['xml_datei']).getroot()
 notes={e.get('ID'):e for e in r.iter('Footnote')}
 numbers={key:e.get('FnZ','')+e.get('Postfix','') for key,e in notes.items()}
 relocated={e.get('ID') for a in r.iter('FnArea') for e in a.iter('FnR')}
 def visible(e,definition=False):
  if e is None:return ''
  if e.tag=='FILE':return e.get('title','')
  if e.tag=='FnArea':return ''.join(visible(notes[n.get('ID')],True) for n in e.iter('FnR'))
  if e.tag=='FnR':return numbers[e.get('ID')]
  if e.tag=='Footnote' and e.get('ID') in relocated and not definition:return ''
  prefix=numbers[e.get('ID')] if e.tag=='Footnote' else ''
  return prefix+(e.text or '')+''.join(visible(x)+(x.tail or '') for x in e)
 pdfpath=base/'Quellen'/c['lokale_pdf']
 raw=subprocess.check_output(['pdftotext','-raw','-enc','UTF-8',str(pdfpath),'-']).decode('utf8')
 raw=re.sub(r'Ein Service des Bundesministeriums? der Justiz(?: und für Verbraucherschutz)?\s+sowie des Bundesamts für\s+Justiz [‒–-] www\.gesetze-im-internet\.de','',raw)
 raw=re.sub(r'- Seite \d+ von \d+ -','',raw);pdf=norm(raw)
 records=[];cursor=0;lastgroup=None
 for i,n in enumerate(r):
  m=n.find('metadaten');g=m.find('gliederungseinheit');en=re.sub(r'^\(XXXX\)\s*','',m.findtext('enbez',''))
  head=''
  if i>0:
   if g is not None:
    key=g.findtext('gliederungskennzahl')
    if c['kuerzel']!='EGBGB' or key!=lastgroup:head=text(g.find('gliederungsbez'))+text(g.find('gliederungstitel'))
    if head.strip()=='-':head=''
    lastgroup=key
   head+=en+text(m.find('titel'))
  body=visible(n.find('textdaten/text'));foot=visible(n.find('textdaten/fussnoten'))
  if m.findtext('enbez','').startswith('(XXXX)') and m.find('titel') is None and not body.strip():head+='----'
  exp=norm(head+body+('Fußnote' if foot.strip() else '')+foot)
  key=exp[:min(120,len(exp))]
  start=pdf.find(key,cursor)
  if start<0 and head:start=pdf.find(norm(head),cursor)
  if start<0:
   raise AssertionError((c['kuerzel'],i,en,'nicht gefunden',key))
  records.append({'index':i,'name':en or head or 'Dokumentkopf','start':start,'expected':exp})
  cursor=start+(len(exp) if pdf.startswith(exp,start) else max(len(norm(head)),1))
 report=[]
 for i,record in enumerate(records):
  actual=pdf[record['start']:records[i+1]['start'] if i+1<len(records) else len(pdf)];exp=record['expected']
  e={'index':i,'name':record['name'],'identisch':exp==actual,'xml_zeichen':len(exp),'pdf_zeichen':len(actual),'sha256_xml_text':hashlib.sha256(exp.encode()).hexdigest(),'sha256_pdf_text':hashlib.sha256(actual.encode()).hexdigest()}
  if not e['identisch']:
   seq=difflib.SequenceMatcher(None,exp,actual,autojunk=False)
   e['abweichungen']=[{'art':tag,'xml':exp[a:b],'pdf':actual[x:y],'davor':exp[max(0,a-60):a],'danach':exp[b:b+60]} for tag,a,b,x,y in seq.get_opcodes() if tag!='equal']
   ds=e['abweichungen'];exception=None
   if c['kuerzel']=='SGB_4' and i==243:
    assert len(ds)==1 and ds[0]['xml']=='...' and ds[0]['pdf']=='…'
    assert actual.replace('…','...')==exp
    exception={'grund':'Ein Auslassungszeichen: XML enthält drei Punkte, PDF das einzelne typografische Zeichen U+2026. Originalseite 105 visuell geprüft. Keine Textauslassung.', 'visuelle_seiten':[105]}
   if c['kuerzel']=='EGBGB' and i in [503,504]:
    moved={503:'Fax*)Internet-Adresse*)',504:'Internet-Adresse*)*)FreiwilligeAngabendesKreditgebers.'}[i]
    assert len(ds)==2 and sorted((d['xml'],d['pdf']) for d in ds)==sorted([(moved,''),('',moved)])
    exception={'grund':'Ein zusammenhängender Teil der linken Formularzelle wird beim PDF-Textabruf nach der rechten Zelle ausgegeben. Genau derselbe Textblock einmal gelöscht/einmal eingefügt; alle übrigen Zeichen in gleicher Reihenfolge. Zellzuordnung anhand Originalseiten vor und nach dem Seitenumbruch geprüft. Markdown bewahrt XML-Zellen.', 'verschobener_text':moved,'visuelle_seiten':[111,112] if i==503 else [116,117]}
   if c['kuerzel']=='StBVV' and i==32:
    labels=['1.','2.','3.','5.','6.','7.','8.','10.','11.','11a.','12.','13.','14.','15.','16.','17.','18.','19.','20.','21.','22.','25.']
    deleted=collections.Counter(d['xml'] for d in ds if d['art']=='delete');inserted=collections.Counter(d['pdf'] for d in ds if d['art']=='insert')
    assert len(ds)==2*len(labels) and deleted==inserted==collections.Counter(labels)
    source_labels=[norm(text(row.find('entry'))) for row in r[i].iter('row') if row.find('entry') is not None]
    assert all(source_labels.count(label)==1 for label in labels)
    exception={'grund':'22 linke Tabellenkennzeichnungen werden von pdftotext nach statt vor dem ersten Textblock der jeweiligen Zeile ausgegeben. Jede Kennzeichnung in XML einmal, im PDF einmal und durch genau ein Verschiebungspaar nachgewiesen. Alle übrigen Textzeichen und Zahlen stimmen in gleicher Reihenfolge überein.', 'kennzeichnungen':labels,'visuelle_seiten':[7,8,9,10,11]}
   if c['kuerzel']=='StBVV' and i in [54,55,56,57]:
    allowed={54:['Gegenstandswertbis…EuroVolleGebühr(10/10)Euro']*2,55:['Gegenstandswertbis…EuroVolleGebühr(10/10)Euro']*2,56:['Gegenstandswertbis…EuroVolleGebühr(10/10)Euro'],57:['Betriebsflächebis…HektarVolleGebühr(10/10)Euro']*2+['JahresumsatzimSinnevon§39Absatz5bis…EuroVolleGebühr(10/10)Euro']*2}[i]
    assert len(ds)==len(allowed) and all(d['art']=='insert' and not d['xml'] for d in ds)
    assert collections.Counter(d['pdf'] for d in ds)==collections.Counter(allowed)
    exception={'grund':'Nur wiederholte Original-Tabellenköpfe nach Seiten- oder Spaltenumbrüchen. Sämtliche Zahlen und übrigen Zeichen in gleicher Reihenfolge identisch. Die zusätzlichen Köpfe sind wortgleich mit den im XML enthaltenen Tabellenköpfen.', 'wiederholte_koepfe':allowed,'visuelle_seiten':{54:[16,17,18],55:[18,19,20],56:[20,21],57:[21,22,23,24,25]}[i]}
   if exception:
    exception['vollstaendig_bestaetigt']=True;e['ausnahmepruefung']=exception
  report.append(e)
  if not e['identisch']:print(c['kuerzel'],i,record['name'],json.dumps(e,ensure_ascii=False)[:2200],flush=True)
 result={'kuerzel':c['kuerzel'],'datum':c['quellenabgleich'],'methode':'Vollständige Normtexte in Reihenfolge. NFC/Whitespace und PDF-Seitenservice entfernt. XML-FnArea setzt die bezeichneten Fußnoten an die Druckposition; zentrale Footnotes-Definitionen werden dort einmal ausgegeben. Wiederholte XML-Gliederungsmetadaten werden wie in der PDF nur bei Gruppenwechsel ausgegeben; alleinstehendes technisches Gliederungskennzeichen Minus entfällt im PDF. XML-FILE repräsentiert den Druckverweis; referenzierte Originaldateien werden zusätzlich separat vollständig integriert. Verbleibende Abweichungen nur bei konkret benannter und einzeln geprüfter Layoutausnahme zugelassen.', 'normdatensaetze':len(report),'exakt_identisch':sum(e['identisch'] for e in report),'alle_normen_vollstaendig_bestaetigt':all(e['identisch'] or e.get('ausnahmepruefung',{}).get('vollstaendig_bestaetigt') for e in report),'sha256_pdf':hashlib.sha256(pdfpath.read_bytes()).hexdigest(),'sha256_xml':hashlib.sha256((base/c['xml_datei']).read_bytes()).hexdigest(),'normen':report}
 (cp.parent/'PDF_XML_Abgleich.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(c['kuerzel'],result['exakt_identisch'],'/',len(report),flush=True)
 assert result['alle_normen_vollstaendig_bestaetigt']
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser();p.add_argument('--config',default=str(Path(__file__).parent/'konfiguration.json'));a=p.parse_args();perform(Path(a.config).resolve())
