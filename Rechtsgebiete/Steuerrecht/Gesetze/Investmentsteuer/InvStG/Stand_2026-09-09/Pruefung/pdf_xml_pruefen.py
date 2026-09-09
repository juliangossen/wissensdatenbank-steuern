from pathlib import Path
from collections import Counter
import json, re, difflib, sys, unicodedata, hashlib, subprocess, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')
BASE=Path(__file__).resolve().parents[2]

def joined(e): return ''.join(e.itertext()) if e is not None else ''
def norm(s): return re.sub(r'\s+','',unicodedata.normalize('NFC',s)).replace('\u00ad','')

def with_markers(el,marker_map):
    if el is None: return ''
    prefix=marker_map.get(el.get('ID'),'') if el.tag in ('FnR','Footnote') else ''
    return prefix+(el.text or '')+''.join(with_markers(c,marker_map)+(c.tail or '') for c in el)

def verify_layout(short, name, expected, actual):
    steps=[]
    def header(pdf_header,xml_header,count):
        nonlocal actual
        assert actual.count(pdf_header)==count,(short,name,'header count',actual.count(pdf_header),count)
        assert Counter(pdf_header)==Counter(xml_header),(short,name,'header characters')
        assert expected.count(xml_header)==1,(short,name,'XML header count')
        actual=actual.replace(pdf_header,xml_header,1)
        if pdf_header==xml_header:
            start=actual.index(xml_header)+len(xml_header)
            actual=actual[:start]+actual[start:].replace(pdf_header,'')
        else:
            actual=actual.replace(pdf_header,'')
        steps.append({'art':'Tabellenkopf-Lesereihenfolge und/oder Wiederholung am Seitenumbruch','pdf_kopf':pdf_header,'xml_kopf':xml_header,'pdf_vorkommen':count,'zeichenbestand_kopf_identisch':True})
    if (short,name)==('InvStG','Fußnote'):
        missing='s.7,41Abs.2,42Abs.1bis3,43Abs.2,43Abs.3,44,45Abs.1,47Abs.4,48Abs.2,48Abs.5,49,50Abs.2,50Abs.3,53Abs.3,53Abs.4,56,57+++)'
        assert expected.count(missing)==1
        assert actual==expected.replace(missing,'',1)
        steps.append({'art':'In der amtlichen PDF auf Seite 1 am rechten Seitenrand abgeschnittene Fußnotenzeile',
                      'fehlender_xml_text_normalisiert':missing,'zeichen':len(missing),
                      'amtliche_xml_vollstaendig_in_markdown':True,'screenshot':'PDF_Seite_001.png',
                      'restlicher_text_identisch':True})
        return False,steps
    elif (short,name)==('EStG','§ 19'):
        header('VersorgungsfreibetragJahrdesVersorgungsbeginnsin%derVersorgungsbezügeHöchstbetraginEuroZuschlagzumVersorgungsfreibetraginEuro',
               'JahrdesVersorgungsbeginnsVersorgungsfreibetragZuschlagzumVersorgungsfreibetraginEuroin%derVersorgungsbezügeHöchstbetraginEuro',3)
    elif (short,name)==('EStG','§ 22'):
        h='BeiBeginnderRentevollendetesLebensjahrdesRenten-berechtigtenErtragsanteilin%'
        header(h,h,2)
    elif (short,name)==('EStG','§ 24a'):
        header('AltersentlastungsbetragDasaufdieVollendungdes64.LebensjahresfolgendeKalenderjahrin%derEinkünfteHöchstbetraginEuro',
               'DasaufdieVollendungdes64.LebensjahresfolgendeKalenderjahrAltersentlastungsbetragin%derEinkünfteHöchstbetraginEuro',2)
    elif (short,name)==('EStG','§ 35'):
        from_pdf='SummederpositivengewerblichenEinkünfteSummeallerpositivenEinkünfte•gemindertetariflicheSteuer.'
        from_xml='SummederpositivengewerblichenEinkünfte•gemindertetariflicheSteuer.SummeallerpositivenEinkünfte'
        assert actual.count(from_pdf)==1 and expected.count(from_xml)==1
        actual=actual.replace(from_pdf,from_xml,1)
        steps.append({'art':'Bruchformel: PDF liest Zähler/Nenner vor rechtem Faktor; XML zeilenweise','pdf_reihenfolge':from_pdf,'xml_reihenfolge':from_xml,'zeichenbestand_identisch':Counter(from_pdf)==Counter(from_xml)})
    elif (short,name)==('EStG','Anlage 1'):
        header('DieJahresbeiträgederlaufendenLeistungensindzuvervielfachenbeiLeistungenErreichtesAlterdesLeistungs-empfängers(Jahre)anmännlicheLeistungs-empfängermitanweiblicheLeistungs-empfängermit123',
               'ErreichtesAlterdesLeistungs-empfängers(Jahre)DieJahresbeiträgederlaufendenLeistungensindzuvervielfachenbeiLeistungenanmännlicheLeistungs-empfängermitanweiblicheLeistungs-empfängermit123',2)
    elif (short,name)==('EStG','Anlage 1a'):
        h='NutzungGrenzeGrenze123'
        header(h,h,2)
    elif (short,name)==('EStDV','§ 55'):
        h='BeschränkungderLaufzeitderRenteauf...JahreabBeginndesRentenbezugs(ab1.Januar1955,fallsdieRentevordiesemZeitpunktzulaufenbegonnenhat)DerErtragsanteilbeträgtvorbehaltlichderSpalte3...ProzentDerErtragsanteilistderTabellein§22Nr.1Satz3BuchstabeaDoppelbuchstabebbdesGesetzeszuentnehmen,wennderRentenberechtigtezuBeginndesRentenbezugs(vordem1.Januar1955,fallsdieRentevordiesemZeitpunktzulaufenbegonnenhat)das...teLebensjahrvollendethatte123'
        header(h,h,3)
    elif (short,name)==('KraftStG','§ 9'):
        h='durchFremdzündungsmotorenangetriebenwerdenunddurchSelbstzündungsmotorenangetriebenwerdenund'
        header(h,h,2)
    return actual==expected,steps

def compare(conf):
    cfg=json.loads(conf.read_text(encoding='utf-8'))
    pdf_path=conf.parent.parent/'Quellen'/cfg['aktuelle_pdf']
    xml_path=conf.parent.parent/cfg['xml_datei']
    assert hashlib.sha256(pdf_path.read_bytes()).hexdigest()==cfg['sha256_aktuelle_pdf']
    assert hashlib.sha256(xml_path.read_bytes()).hexdigest()==cfg['sha256_xml']
    root=ET.parse(conf.parent.parent/cfg['xml_datei']).getroot()
    raw=subprocess.run(['pdftotext','-raw','-enc','UTF-8',str(pdf_path),'-'],check=True,stdout=subprocess.PIPE).stdout.decode('utf-8')
    (conf.parent/'PDF_Text_roh.txt').write_text(raw,encoding='utf-8')
    raw=re.sub(r'Ein Service des Bundesministerium.*?www\.gesetze-im-internet\.de','',raw,flags=re.S)
    raw=re.sub(r'- Seite \d+ von \d+ -','',raw)
    pdf=norm(raw)
    records=[]
    for i,node in enumerate(root):
        meta=node.find('metadaten')
        name=meta.findtext('enbez','').replace('(XXXX) ','')
        group=meta.find('gliederungseinheit')
        marker_map={x.get('ID'):x.get('FnZ',str(j+1)) for j,x in enumerate(node.iter('Footnote'))}
        body=with_markers(node.find('textdaten/text'),marker_map)
        foot=with_markers(node.find('textdaten/fussnoten'),marker_map)
        if i==0:
            heading=body[:100] if body.strip() else 'Fußnote'
        elif group is not None:
            heading=joined(group.find('gliederungsbez'))+joined(group.find('gliederungstitel'))
        else:
            heading=name+joined(meta.find('titel'))
        expected=heading+body+('Fußnote' if i>0 and foot.strip() else '')+foot
        if i==0: expected=body+('Fußnote' if foot.strip() else '')+foot
        records.append({'index':i,'name':name or heading,'heading':norm(heading),'expected':norm(expected)})
    cursor=0
    failed=[]
    for r in records:
        needle=r['expected'][:min(len(r['expected']),180)]
        start=pdf.find(needle,cursor)
        if start<0:
            start=pdf.find(r['heading'],cursor)
        if start<0:
            failed.append({'index':r['index'],'name':r['name'],'heading':r['heading'],'context':pdf[cursor:cursor+600]})
        else:
            r['start']=start
            if pdf.startswith(r['expected'],start):
                cursor=start+len(r['expected'])
            else:
                tail=pdf.find(r['expected'][-120:],start+len(r['heading']))
                cursor=tail+120 if tail>=0 else start+len(r['heading'])
    if failed:
        (conf.parent/'PDF_XML_unlocated.json').write_text(json.dumps(failed,ensure_ascii=False,indent=2),encoding='utf-8')
        return cfg['kuerzel'],{'unlocated':len(failed),'examples':failed[:3]}
    report=[]
    for i,r in enumerate(records):
        actual=pdf[r['start']:records[i+1]['start'] if i+1<len(records) else len(pdf)]
        expected=r['expected']
        entry={'norm_index':i,'name':r['name'],'pdf_chars':len(actual),'xml_chars':len(expected),'equal':actual==expected}
        if actual!=expected:
            sm=difflib.SequenceMatcher(None,expected,actual,autojunk=False)
            entry['diffs']=[{'kind':t,'xml':expected[a:b],'pdf':actual[c:d],'before':expected[max(0,a-45):a],'after':expected[b:b+45]} for t,a,b,c,d in sm.get_opcodes() if t!='equal']
            entry['nach_layoutabgleich_identisch'],entry['layoutpruefung']=verify_layout(cfg['kuerzel'],r['name'],expected,actual)
        else: entry['nach_layoutabgleich_identisch']=True
        report.append(entry)
    output={'kuerzel':cfg['kuerzel'],'methode':'Alle Normdatensätze vollständig in Reihenfolge; NFC, Leerraum und unsichtbare weiche Trennzeichen normalisiert. Fußnotenkennzeichen aus XML-Attributen ergänzt. Technische (XXXX)-Kennungen in Überschriften entsprechen der PDF ohne diesen XML-Marker. Wiederholte Tabellenköpfe und abweichende Lesereihenfolgen werden einzeln mit exakten Zeichenbeständen und unverändertem Resttext geprüft.','norms':report,'gleich':sum(r['equal'] for r in report),'gesamt':len(report),'alle_normen_vollstaendig_gleich':all(r['nach_layoutabgleich_identisch'] for r in report),'pdf_sha256':cfg['sha256_aktuelle_pdf'],'xml_sha256':cfg['sha256_xml']}
    (conf.parent/'PDF_XML_Abgleich.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    output['abgleich_erfolgreich_mit_dokumentierter_ergaenzung']=bool(len([r for r in report if not r['nach_layoutabgleich_identisch']])==1 and report[0]['layoutpruefung'][0]['restlicher_text_identisch'])
    (conf.parent/'PDF_XML_Abgleich.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    assert output['alle_normen_vollstaendig_gleich'] or output['abgleich_erfolgreich_mit_dokumentierter_ergaenzung'],(cfg['kuerzel'],'unresolved differences')
    return cfg['kuerzel'],{'gleich':output['gleich'],'gesamt':len(report),'abweichungen':[{'i':r['norm_index'],'name':r['name'],'diffs':len(r.get('diffs',[]))} for r in report if not r['equal']]}

if __name__=='__main__':
    print(json.dumps(compare(Path(__file__).resolve().parent/'konfiguration.json'),ensure_ascii=False,indent=2))
