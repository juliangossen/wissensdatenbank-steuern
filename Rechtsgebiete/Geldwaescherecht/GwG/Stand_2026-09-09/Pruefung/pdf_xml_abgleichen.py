"""Vollständiger, normweiser Vergleich PDF-Text und archiviertes GII-XML."""
import sys,json,re,hashlib,difflib,unicodedata,argparse,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')
BASE=Path(__file__).resolve().parents[2]
ABBR=['BGB','HGB','StGB','GewO','GwG','HwO','UWG']
def normalize(s):return re.sub(r'\s+','',unicodedata.normalize('NFC',s))
def original(e):return ''.join(e.itertext()) if e is not None else ''
def visible(e,markers):
    if e is None:return ''
    if e.tag=='FnR':return markers[e.get('ID')]
    prefix=markers[e.get('ID')] if e.tag=='Footnote' else ''
    return prefix+(e.text or '')+''.join(visible(c,markers)+(c.tail or '') for c in e)
def perform(configpath):
    c=json.loads(configpath.read_text(encoding='utf-8'))
    if c['kuerzel'] not in ABBR:return
    folder=configpath.parent.parent
    root=ET.parse(folder/c['xml_datei']).getroot()
    markers={e.get('ID'):e.get('FnZ','')+e.get('Postfix','') for e in root.findall('.//Footnote')}
    pdffile=folder/'Quellen'/c['aktuelle_pdf']
    raw=subprocess.run(['pdftotext','-raw','-enc','UTF-8',str(pdffile),'-'],capture_output=True,check=True).stdout.decode('utf-8')
    raw=re.sub(r'Ein Service des Bundesministerium der Justiz und für Verbraucherschutz\s+sowie des Bundesamts für Justiz ‒ www\.gesetze-im-internet\.de','',raw)
    raw=re.sub(r'- Seite \d+ von \d+ -','',raw)
    pdf=normalize(raw)
    records=[]
    cursor=0
    for i,node in enumerate(root.findall('norm')):
        m=node.find('metadaten')
        name=m.findtext('enbez','')
        g=m.find('gliederungseinheit')
        body=visible(node.find('textdaten/text'),markers)
        foot=visible(node.find('textdaten/fussnoten'),markers)
        if i==0:head=''
        elif g is not None:head=visible(g.find('gliederungsbez'),markers)+visible(g.find('gliederungstitel'),markers)
        else:
            head=re.sub(r'^\(XXXX\)\s*','',name)+visible(m.find('titel'),markers)
            if name.startswith('(XXXX)') and m.find('titel') is None and not body.strip():head+='----'
        exp=normalize(head+body+('Fußnote' if foot.strip() else '')+foot)
        key=exp[:min(120,len(exp))]
        start=pdf.find(key,cursor)
        if start<0:
            print(c['kuerzel'],'UNLOCATED',i,name,repr(key[:180]),flush=True)
            raise ValueError(f'{c["kuerzel"]} {i}: Heading unlocated')
        cursor=start+(len(exp) if pdf.startswith(exp,start) else len(key))
        records.append({'index':i,'name':name or head or 'Gesetzeskopf','start':start,'expected':exp})
    report=[]
    for i,rec in enumerate(records):
        actual=pdf[rec['start']:records[i+1]['start'] if i+1<len(records) else len(pdf)]
        exp=rec['expected']
        entry={'norm_index':i,'name':rec['name'],'pdf_zeichen':len(actual),'xml_zeichen':len(exp),'identisch':actual==exp}
        if actual!=exp:
            seq=difflib.SequenceMatcher(None,exp,actual,autojunk=False)
            entry['abweichungen']=[{'art':tag,'xml':exp[a:b],'pdf':actual[x:y],'davor':exp[max(0,a-50):a],'danach':exp[b:b+50]} for tag,a,b,x,y in seq.get_opcodes() if tag!='equal']
            if c['kuerzel']=='StGB' and rec['name']=='§ 127':
                corrections=[('erm\u0308oglichen','ermöglichen'),('f\u0308ordern','fördern'),('Beẗaubungsmittelgesetzes','Betäubungsmittelgesetzes'),('Grundstoff\u0308uberwachungsgesetzes','Grundstoffüberwachungsgesetzes')]
                corrected=actual
                counts={}
                for wrong,right in corrections:
                    counts[wrong]=corrected.count(wrong)
                    corrected=corrected.replace(wrong,right)
                entry['ausnahmepruefung']={'grund':'Vier im PDF-Text vor statt nach dem Vokal ausgegebene kombinierende Umlautzeichen; Original-PDF Seite 84 visuell geprüft. XML enthält korrekt zugeordnete Zeichen. Nur diese vier konkret benannten Zeichenfolgen werden für den Vergleich korrigiert.',
                    'ersetzungen':dict(corrections),'vorkommen':counts,'nach_gezielter_korrektur_identisch':corrected==exp,
                    'visueller_beleg':'StGB_Seite_84.png'}
                assert all(n==1 for n in counts.values()) and corrected==exp
        report.append(entry)
    failures=[r for r in report if not r['identisch']]
    result={'kuerzel':c['kuerzel'],'datum':c['quellenabgleich'],'methode':'Normweise Vergleich aller Überschriften, Texte und Fußnoten einschließlich aus XML-Attributen rekonstruierter Fußnotenmarker; NFC und Entfernung nur von Whitespace, PDF-Servicezeilen und Seitenzählern. Abweichungen einzeln dokumentiert.',
        'normdatensaetze':len(report),'exakt_identisch':len(report)-len(failures),'abweichend':len(failures),
        'alle_normen_vollstaendig_bestaetigt':all(r['identisch'] or r.get('ausnahmepruefung',{}).get('nach_gezielter_korrektur_identisch',False) for r in report),
        'technische_xml_praefixe':{'regel':'Nur das GII-interne Kennzeichen (XXXX) vor enbez wird beim PDF-Vergleich entfernt. Die Vorschrift und ihr Wegfallhinweis bleiben erhalten.','anzahl':sum((n.findtext('metadaten/enbez','')).startswith('(XXXX)') for n in root)},
        'pdf_leertext_platzhalter':[r['name'] for r,n in zip(records,root) if (n.findtext('metadaten/enbez','')).startswith('(XXXX)') and n.find('metadaten/titel') is None and not original(n.find('textdaten/text')).strip()],
        'normen':report}
    output=configpath.parent/'PDF_XML_Abgleich.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(c['kuerzel'],len(report),'normen',len(failures),'abweichend',flush=True)
    for entry in failures[:15]:print(json.dumps(entry,ensure_ascii=False)[:600],flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--abbr');parser.add_argument('--config');args=parser.parse_args()
    if args.config:perform(Path(args.config).resolve());raise SystemExit(0)
    if (Path(__file__).parent/'konfiguration.json').exists():perform(Path(__file__).parent/'konfiguration.json');raise SystemExit(0)
    if args.abbr:ABBR=[args.abbr]
    for configpath in (BASE/'Rechtsgebiete').glob('**/konfiguration.json'):perform(configpath)
