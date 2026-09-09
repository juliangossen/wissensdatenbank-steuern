"""Dokumentation und abschließende Quell-/Hashprüfung; keine Registermutation."""
from pathlib import Path
import concurrent.futures,hashlib,json,re,shutil,subprocess,sys,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from weitere_importieren import BASE,RUN,DOCS,sha

def finish(item):
 short,original,slug,area=item
 folder=BASE/'Rechtsgebiete'/area/short/'Stand_2026-09-09';proof=folder/'Pruefung';cp=proof/'konfiguration.json';c=json.loads(cp.read_text(encoding='utf8'));rp=proof/'Vollstaendigkeitspruefung.json'
 shutil.copy2(RUN/'weitere_pdfpruefung.py',proof/'pdf_xml_abgleichen.py')
 if short in ['EGBGB','GmbHG','MiLoG','SGB_4']:
  shutil.copy2(RUN/'weitere_converter.py',proof/'konvertieren.py');shutil.copy2(RUN/'weitere_converter_basis.py',proof/'weitere_converter_basis.py')
  c['konverter_datei']='Pruefung/konvertieren.py'
  cp.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  if short in ['EGBGB','GmbHG']:
   result=subprocess.run([sys.executable,'-B',str(proof/'konvertieren.py'),'--config',str(cp)],capture_output=True,encoding='utf8');assert result.returncode==0,result.stderr
 for name in ['markdown_gesamtpruefen.py','markdown_struktur_pruefen.py','pdf_xml_abgleichen.py']:
  result=subprocess.run([sys.executable,'-B',str(proof/name)],capture_output=True,encoding='utf8');assert result.returncode==0,(short,name,result.stdout[-800:],result.stderr)
 v=json.loads(rp.read_text(encoding='utf8'));pdf=json.loads((proof/'PDF_XML_Abgleich.json').read_text(encoding='utf8'));md=folder/(short+'.md');mhash=sha(md)
 assert v['sha256_markdown']==mhash and v['alle_textbloecke_identisch'] and pdf['alle_normen_vollstaendig_bestaetigt']
 for name,field in [('Markdown_Gesamtpruefung.json','alle_normtexte_identisch'),('Markdown_Strukturpruefung.json','alle_normen_identisch')]:
  report=json.loads((proof/name).read_text(encoding='utf8'));assert report[field] and report['sha256_markdown']==mhash
 assert sha(folder/'Quellen'/c['lokale_pdf'])==sha(folder/'Quellen'/c['aktuelle_pdf'])
 for rel,digest in v['bildassets'].items():assert sha(folder/rel)==digest
 special=[]
 if short=='GmbHG':
  report=json.loads((proof/'Datei_Anlagenpruefung.json').read_text(encoding='utf8'));raw=(folder/report['textdatei']).read_text(encoding='utf8')
  rendered=BeautifulSoup(MarkdownIt('commonmark',{'html':True}).enable('table').render(md.read_text(encoding='utf8')),'html.parser');node=rendered.select_one('div[data-redaktionell="volltext-aus-xml-dateianhang"] pre')
  assert node is not None and node.get_text()==raw
  report['fertiges_markdown_anhangtext_identisch']=True;report['sha256_markdown']=mhash;report['visuell_gepruefte_formularseiten']=[1,2]
  (proof/'Datei_Anlagenpruefung.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  special.append('Anlage 1 enthält im GII-Gesamtdokument einen Dateiverweis. Die mitgelieferte amtliche PDF-Dateianlage wurde zusätzlich vollständig als durchsuchbarer Text und mit beiden Originalformularseiten eingebettet. [Separater Nachweis](Datei_Anlagenpruefung.json). Die HTML-Markierung `data-redaktionell="volltext-aus-xml-dateianhang"` trennt nur den separaten Dateiinhalt vom XML-Textvergleich; der Inhalt wird nicht ausgeblendet.')
 if short=='EGBGB':special.append(f"Die XML wiederholt Gliederungsmetadaten bei untergeordneten Paragraphen. {v['xml_gliederungsmetadaten_vorkommen']} Metadatenvorkommen ergeben {v['gliederungsteile']} verschiedene Gliederungsschlüssel. Artikel, darin enthaltene Paragraphen und Anlagen besitzen eindeutige, vollständige Überschriften und eine gemeinsame Navigation. {v['technische_leere_gliederung_minus_ausgeblendet']} reine technische Minus-Platzhalter vor Anlagen werden ausgeblendet; die Anlagen bleiben vollständig erhalten.")
 for e in pdf['normen']:
  if e.get('ausnahmepruefung'):special.append('**'+e['name']+':** '+e['ausnahmepruefung']['grund'])
 if v['bilder']:special.append(f"Alle {v['bilder']} aus XML referenzierten Formelbilder wurden unverändert archiviert und lokal eingebettet; die Originalabbildungen wurden visuell geprüft.")
 cstand='\n'.join('- '+s for s in c['stand'])
 (folder.parent/'README.md').write_text(f"# {c['titel']} ({short})\n\n[Strukturierter Volltext](Stand_2026-09-09/{short}.md) · [Fassung und Quellen](Stand_2026-09-09/README.md) · [Prüfbericht](Stand_2026-09-09/Pruefung/Pruefbericht.md)\n\nQuellenabgleich: **09.09.2026**. Rechtsgebiet: **{c['rechtsgebiet']}**. Das Ordnerdatum bezeichnet den Abgleich; maßgeblich für die Fassung sind die folgenden Originalhinweise:\n\n{cstand}\n",encoding='utf8')
 (folder/'README.md').write_text(f"# {short} – Fassung zum Quellenabgleich am 09.09.2026\n\n[Vollständiges Markdown]({short}.md) · [Quellen](Quellen/README.md) · [Prüfbericht](Pruefung/Pruefbericht.md)\n\n**{c['titel']}**\n\nDie bereitgestellte PDF mit {c['pdf_seiten']} Seiten ist bytegleich mit der am Prüftag abgerufenen amtlichen GII-PDF. Alle {v['xml_normdatensaetze']} XML-Normdatensätze einschließlich Überschriften, Fußnoten und Anlagen wurden vollständig in Originalreihenfolge übernommen. Es handelt sich um den dokumentierten Quellenstand; das Abgleichdatum ersetzt keine Übergangs- oder Inkrafttretensregelung.\n\n## Quellenstand\n\n{c['vollzitat']}\n\n{cstand}\n\n## Inhalt und Prüfung\n\n- {v['tabellen']} Tabellen mit {v['tabellenzellen']} Originalzellen.\n- Alle {v['gepruefte_textbloecke']} konvertierten Textblöcke zeichengenau rückverglichen.\n- Gesamtdokument und sämtliche Tabellenzellen unabhängig aus gerendertem Markdown gegen XML geprüft.\n- PDF/XML-Abgleich vollständig bestätigt; konkret benannte Druck- und Layoutbesonderheiten im Prüfbericht.\n",encoding='utf8')
 sources=[]
 for p in sorted((folder/'Quellen').rglob('*')):
  if p.is_file() and p.name!='README.md':sources.append({'datei':p.relative_to(folder).as_posix(),'sha256':sha(p)})
 sourceproof={'kuerzel':short,'abgleichdatum':'2026-09-09','quelle_url':c['quelle_url'],'pdf_url':c['pdf_url'],'xml_url':c['xml_url'],'html_url':c['html_url'],'original_dateiname':original,'pdf_identisch_aktuell':True,'pdf_text_identisch_aktuell':True,'pdf_seiten':c['pdf_seiten'],'dateien':sources}
 (proof/'Quellenabgleich.json').write_text(json.dumps(sourceproof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (folder/'Quellen/README.md').write_text(f"# Archivierte Quellen: {short}\n\nQuellenabgleich: **09.09.2026**. [Amtliche GII-Gesamtausgabe]({c['html_url']}).\n\n- [Bereitgestellte Original-PDF]({c['lokale_pdf']}) – unveränderte Kopie von `{original}`.\n- [Am Prüftag abgerufene PDF]({c['aktuelle_pdf']}) – SHA-256-identisch.\n- [Amtliches XML-Quellenpaket](xml.zip).\n- [Entpackte XML]({c['xml_datei'].removeprefix('Quellen/')}).\n- [Archivierte HTML-Gesamtausgabe](Gesamtausgabe.html).\n- [Dateifingerabdrücke und Abrufadressen](../Pruefung/Quellenabgleich.json).\n\nBilddateien und referenzierte PDF-Dateianlagen des Quellenpakets sind unverändert mitarchiviert. PDF-Rohtext und gegebenenfalls gerenderte Formularseiten sind daraus abgeleitete Prüf- und Darstellungsdateien.\n",encoding='utf8')
 root=ET.parse(folder/c['xml_datei']).getroot();normlist=[]
 for i,n in enumerate(root):
  m=n.find('metadaten');g=m.find('gliederungseinheit');normlist.append({'index':i,'doknr':n.get('doknr'),'enbez':m.findtext('enbez'),'gliederung':None if g is None else {x.tag:''.join(x.itertext()) for x in g},'titel':''.join(m.find('titel').itertext()) if m.find('titel') is not None else None,'sha256_xml_text':hashlib.sha256(''.join(n.find('textdaten').itertext()).encode()).hexdigest()})
 (proof/'Normbestand.json').write_text(json.dumps(normlist,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 con=('py Pruefung/konvertieren.py --config Pruefung/konfiguration.json' if 'konverter_datei' in c else f"py Werkzeuge/gesetz_konvertieren.py --config {cp.relative_to(BASE).as_posix()}")
 report=f"# Prüfbericht: {short}\n\n**Ergebnis:** Alle {len(root)} XML-Normdatensätze vollständig in Originalreihenfolge übernommen. Fertige Markdown-Normtexte und alle Tabellenzellen stimmen zeichengenau mit der archivierten XML überein. Alle PDF-Normtexte vollständig bestätigt; die unten genannten Unterschiede betreffen ausschließlich nachgewiesene Druck- und Layoutkonventionen.\n\n## Quellen und Fassungsstand\n\nQuellenabgleich **09.09.2026** mit [Gesetze im Internet]({c['html_url']}). Die bereitgestellte PDF (`{original}`, {c['pdf_seiten']} Seiten) ist bytegleich mit der am Prüftag abgerufenen PDF. Quellen unverändert unter [Quellen](../Quellen/README.md) archiviert.\n\n{c['vollzitat']}\n\n{cstand}\n\n## Vollständigkeitsnachweis\n\n| Gegenstand | Ergebnis |\n| --- | --- |\n| XML-Normdatensätze | {len(root)} vollständig |\n| PDF/XML | {pdf['exakt_identisch']} unmittelbar identisch; {len(root)-pdf['exakt_identisch']} gezielt bestätigte Druck-/Layoutfälle |\n| Konvertierte Textblöcke | {v['gepruefte_textbloecke']} zeichengenau identisch |\n| Tabellen | {v['tabellen']} |\n| Tabellenzeilen und -zellen | {v['tabellenzeilen']} Zeilen; {v['tabellenzellen']} Zellen vollständig und in Reihenfolge |\n| XML-Formelbilder | {v['bilder']} vollständig eingebettet |\n| Interne Links | {v['interne_links']} mit vorhandenen eindeutigen Zielen |\n\n[PDF/XML-Abgleich](PDF_XML_Abgleich.json), [Konvertierungsprüfung](Vollstaendigkeitspruefung.json), [unabhängige Gesamtprüfung](Markdown_Gesamtpruefung.json), [Tabellen- und Strukturprüfung](Markdown_Strukturpruefung.json), [Normbestand](Normbestand.json).\n\nVerglichen werden vollständige Normen, keine Stichproben. Nur Whitespace und Unicode-NFC werden vereinheitlicht. PDF-Seitenzähler und wiederkehrende Servicezeilen entfallen. XML-Fußnotenattribute bleiben erhalten und verlinkt; `FnArea` legt für den PDF-Abgleich die Druckposition der zentral definierten Fußnoten fest. Einfache Tabellen erhalten gegebenenfalls redaktionelle Spaltenüberschriften, verbundene Zellen bleiben in HTML-Tabellen erhalten.\n\n## Besonderheiten\n\n"+('\n\n'.join(special) if special else 'Keine weiteren Ausnahmen vom vollständigen Zeichenvergleich.')+f"\n\n## Reproduzierbarkeit\n\nKonvertierung {'aus diesem Stand-Ordner' if 'konverter_datei' in c else 'aus dem Hauptverzeichnis'}:\n\n```powershell\n{con}\n```\n\nUnabhängige Prüfprogramme aus diesem Stand-Ordner:\n\n```powershell\npy Pruefung/pdf_xml_abgleichen.py\npy Pruefung/markdown_gesamtpruefen.py\npy Pruefung/markdown_struktur_pruefen.py\n```\n\nPython 3, `markdown-it-py` und Poppler werden benötigt. Die archivierten Quellen genügen; kein neuer Abruf erfolgt.\n\n## Dateifingerabdrücke\n\n| Datei | SHA-256 |\n| --- | --- |\n| Markdown | `{mhash}` |\n| Original-PDF | `{sha(folder/'Quellen'/c['lokale_pdf'])}` |\n| XML | `{sha(folder/c['xml_datei'])}` |\n\n[Alle Quellfingerabdrücke](Quellenabgleich.json).\n"
 (proof/'Pruefbericht.md').write_text(report,encoding='utf8')
 for p in proof.glob('*.log'):
  assert p.resolve().is_relative_to(proof.resolve());p.unlink()
 probe=proof/'pdf_xml_layoutprobe.py'
 if probe.exists():probe.unlink()
 result={'kuerzel':short,'titel':c['titel'],'bereich':c['rechtsgebiet'],'original':original,'original_dateiname':original,'markdown':md.relative_to(BASE).as_posix(),'pruefbericht':(proof/'Pruefbericht.md').relative_to(BASE).as_posix(),'pdf_seiten':c['pdf_seiten'],'quellenstand':c['stand'],'quelle':c['quelle_url'],'sha256_original_pdf':sha(folder/'Quellen'/c['lokale_pdf']),'sha256_markdown':mhash}
 print(short,'fertig',len(root),'Normen',flush=True);return result
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf8')
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(finish,DOCS))
 (RUN/'ergebnis_weitere.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Abgeschlossen:',len(results),'Dokumente,',sum(r['pdf_seiten'] for r in results),'PDF-Seiten')
