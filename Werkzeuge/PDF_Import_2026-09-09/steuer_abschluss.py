"""Lokale Dokumentations- und Prüfnachweise für die 14 Steuer-PDFs erstellen."""
from steuer_import import ROOT,HERE,DOCS,sha
from pathlib import Path
import json,subprocess,sys,xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf8')
results=[]
for short,slug,topic,original in DOCS:
 base=ROOT/f'Rechtsgebiete/Steuerrecht/Gesetze/{topic}/{short}/Stand_2026-09-09';p=base/'Pruefung'
 cfg=json.loads((p/'konfiguration.json').read_text('utf8'));xml=ET.parse(base/cfg['xml_datei']).getroot();meta=xml[0].find('metadaten')
 abbreviation=meta.findtext('amtabk') or meta.findtext('jurabk')
 if abbreviation!=short:
  cfg['amtliche_abkuerzung']=abbreviation
  (p/'konfiguration.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n','utf8')
  converter=(p/'konverter_snapshot.py').read_text('utf8').replace("self.add(esc(short)+'\\n\\nAusfertigungsdatum:","self.add(esc(c.get('amtliche_abkuerzung',short))+'\\n\\nAusfertigungsdatum:")
  (p/'konverter_snapshot.py').write_text(converter,'utf8')
  for script in ['konvertieren.py','markdown_struktur_pruefen.py']:
   run=subprocess.run([sys.executable,'-B',str(p/script)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   (p/(script+'.log')).write_bytes(run.stdout);assert run.returncode==0,run.stdout.decode('utf8')
 check=json.loads((p/'Vollstaendigkeitspruefung.json').read_text('utf8'))
 structure=json.loads((p/'Markdown_Strukturpruefung.json').read_text('utf8'))
 pdf=json.loads((p/'PDF_XML_Abgleich.json').read_text('utf8'))
 assert sha(base/(short+'.md'))==check['sha256_markdown']==structure['sha256_markdown']
 assert sha(base/'Quellen'/original)==cfg['sha256_lokale_pdf']==check['sha256_pdf']==cfg['sha256_aktuelle_pdf']
 assert pdf['alle_normen_vollstaendig_gleich'] or (short=='InvStG' and pdf['abgleich_erfolgreich_mit_dokumentierter_ergaenzung'])
 special=''
 if short=='SolZG':special='**Historische Fassung:** Die gelieferte Quelle ist das Solidaritätszuschlaggesetz vom 24. Juni 1991, geändert am 25. Februar 1992. Sie ist nicht das Solidaritätszuschlaggesetz 1995. Das Erfassungsdatum ändert diesen Quellenstand nicht.'
 if short=='InvStG':special='**Dokumentierte Ergänzung:** Auf PDF-Seite 1 ist die lange Anwendungshinweis-Zeile am rechten Seitenrand abgeschnitten. Das Markdown enthält die vollständige Zeile aus der zugehörigen amtlichen XML-Datei. Die 119 im PDF fehlenden Zeichen sind im Prüfbericht einzeln dokumentiert; der übrige Text ist identisch.'
 stand='\n'.join('- '+x for x in cfg['stand'])
 links=f'- [Markdown-Volltext]({short}.md)\n- [Original-PDF](Quellen/{original})\n- [Archivierte XML]({cfg["xml_datei"]})\n- [Prüfbericht](Pruefung/Pruefbericht.md)'
 (base/'README.md').write_text(f'# {cfg["titel"]} ({abbreviation})\n\n**Erfassung und Quellenabgleich: 09.09.2026.**\n\n{special+chr(10)+chr(10) if special else ""}## Quellenstand\n\n{cfg["vollzitat"]}\n\n{stand}\n\nDas Datum des Standordners ist das Erfassungsdatum und kein einheitliches Inkrafttretensdatum. Die Anwendungsvorschriften und Bearbeitungshinweise der Quelle bleiben erhalten.\n\n## Dateien\n\n{links}\n\n## Übernahme und Prüfung\n\nAlle {cfg["pdf_seiten"]} PDF-Seiten und {check["xml_normdatensaetze"]} XML-Normdatensätze sind berücksichtigt. Sämtliche {check["gepruefte_textbloecke"]} Textblöcke stimmen mit dem gerenderten Markdown überein. {check["tabellen"]} Tabellen mit {check["tabellenzellen"]} Zellen und {check["bilder"]} Abbildungen sind übernommen. Weggefallene Vorschriften und zusammengefasste Normbereiche bleiben sichtbar.\n\nDie bereitgestellte PDF ist bytegleich mit dem am Prüftag abgerufenen Exemplar von [Gesetze im Internet]({cfg["quelle_url"]}). Details des PDF/XML-Abgleichs, Layoutbesonderheiten und SHA-256-Prüfsummen stehen im Prüfbericht.\n','utf8')
 (base.parent/'README.md').write_text(f'# {cfg["titel"]} ({abbreviation})\n\n[Markdown-Volltext: Erfassung 09.09.2026](Stand_2026-09-09/{short}.md) · [Dokumentation](Stand_2026-09-09/README.md) · [Prüfbericht](Stand_2026-09-09/Pruefung/Pruefbericht.md)\n\n{special+chr(10)+chr(10) if special else ""}## Quellenstand\n\n{stand}\n\nNeue Fassungen erhalten einen eigenen Standordner; archivierte Fassungen bleiben erhalten.\n','utf8')
 layout='Alle Normdatensätze stimmen nach der Grundnormalisierung unmittelbar überein.'
 extras=''
 if short=='ErbStG':layout='In § 19 wird im PDF der verbundene Gruppenkopf „Prozentsatz in der Steuerklasse“ vor dem mehrzeiligen linken Kopf gelesen. Die genau protokollierte Kopfumsortierung erhält sämtliche Zeichen; der übrige Text einschließlich aller Tabellenwerte ist unverändert.'
 if short=='BewG':
  layout=('250 von 272 Normdatensätzen stimmen unmittelbar überein. In der Inhaltsübersicht und 21 Anlagen bestehen ausschließlich nachgewiesene Layoutunterschiede. Der spezielle Tabellenprüfer konsumiert jede nichtleere XML-Zelle genau einmal mit identischem Text. Reine Zahlen, Prozentwerte und Wertebereiche ohne Zeilenverbund behalten in jeder Datenzeile ihre Spaltenfolge. Andere Zellen dürfen nur innerhalb der durch ihre XML-Zeilenspanne belegten Zeilen in abweichender Druckreihenfolge auftreten.\n\nWiederholte Tabellenköpfe werden nur als exakte Wiederholung des vollständig geprüften Originalkopfs entfernt. Geteilte Zellen werden nur an XML-Zeilenumbrüchen oder unabhängig extrahierten physischen PDF-Zeilenenden zusammengesetzt. Der Umbruch „Gäste-WC“ auf Seiten 127/128 ist gesondert belegt. Manuelle Fußnoten werden für den PDF-Vergleich an ihrer XML-FnArea-Druckposition berücksichtigt. Jede Umordnung, Kopf-Wiederholung und Zellteilung steht in `PDF_XML_Abgleich.json`; keine inhaltliche Abweichung wird pauschal ausgenommen.')
  extras='\n- [Bildprüfung](Bildpruefung.json): alle 20 JPEG-Bildvorkommen in PDF und XML-Paket in Originalreihenfolge bytegleich.\n- [Visuelle Prüfung](Visuelle_Pruefung/Sichtpruefung.md): Tabellen, verbundene Zellen und Hausquerschnitte auf PDF-Seiten 73, 74, 120, 121, 159 und 160.\n'
 if short=='InvStG':
  missing=pdf['norms'][0]['layoutpruefung'][0]['fehlender_xml_text_normalisiert']
  layout=f'Alle Vorschriften und Gliederungen sind unmittelbar identisch. Im Dokumentkopf fehlen im PDF die folgenden **119 Zeichen ohne Leerraum** am rechten Seitenrand:\n\n```text\n{missing}\n```\n\nDiese Zeichen werden aus der bytearchivierten amtlichen XML-Gesamtausgabe übernommen. Der [Screenshot von Seite 1](PDF_Seite_001.png) zeigt den abgeschnittenen Anwendungshinweis. Der übrige Text des Dokumentkopfs ist identisch. Das Prüffeld `alle_normen_vollstaendig_gleich` bleibt deshalb ausdrücklich `false`; `abgleich_erfolgreich_mit_dokumentierter_ergaenzung` bezeichnet den erfolgreich abgegrenzten Sonderfall.'
 report=f'''# Prüfbericht – {cfg['titel']} ({abbreviation})

**Ergebnis: vollständig in Markdown übernommen und geprüft{'; mit dokumentierter Ergänzung aus der amtlichen XML' if short=='InvStG' else ''}.** Quellenabgleich: 09.09.2026.

Die bereitgestellte Datei `{original}` ist bytegleich mit der am Prüftag abgerufenen [PDF-Gesamtausgabe]({cfg['quelle_pdf']}). Alle {cfg['pdf_seiten']} Seiten und {check['xml_normdatensaetze']} XML-Normdatensätze sind berücksichtigt. Die unveränderte XML-Gesamtausgabe stammt von derselben offiziellen Gesetzesseite.

{special}

## Stand und Quellen

{cfg['vollzitat']}

{stand}

Das Ordnerdatum bezeichnet die Erfassung und Quellenprüfung. Es bestätigt kein einheitliches Inkrafttretensdatum. Sämtliche dokumentarischen Hinweise und Anwendungsvorschriften stehen im Volltext.

## Vollständigkeitskontrolle

| Prüfung | Ergebnis |
| --- | --- |
| Normdatensätze | {check['xml_normdatensaetze']} |
| Gliederungsteile | {check['gliederungsteile']} |
| Vorschriftendatensätze | {check['vorschriften']} einschließlich weggefallener Normen und ggf. zusammengefasster Bereiche |
| Anlagen/Anhänge | {check['anlagen_anhaenge']} |
| Tabellen | {check['tabellen']} mit {check['tabellenzeilen']} Zeilen und {check['tabellenzellen']} Zellen |
| Aufzählungskennzeichen | {check['aufzaehlungskennzeichnungen']} |
| Originalabbildungen | {check['bilder']} |
| XML gegen gerendertes Markdown | {check['gepruefte_textbloecke']} Text-, Fußnoten-, Gliederungs- und Überschriftenblöcke identisch |
| Unabhängige Markdown-Strukturprüfung | {structure['gepruefte_normen_ohne_metadatenkopf']} vollständige Normabschnitte nach dem Dokumentkopf sowie jede Tabellenzelle in Originalreihenfolge identisch |
| Interne Links | Alle {check['interne_links']} Ziele vorhanden; keine doppelten Anker |

## PDF-Layout und Quellenbesonderheiten

{layout}

## Prüfmethoden und Reproduzierbarkeit

Der PDF/XML-Abgleich normalisiert Unicode-NFC, Leerraum und unsichtbare weiche Trennzeichen. Wiederkehrende PDF-Servicezeilen und Seitennummern werden entfernt. Fußnotenmarker stammen aus den XML-Attributen; der technische Marker `(XXXX)` wird wie im PDF nicht als Normbezeichnung ausgegeben. Alle übrigen Abweichungen sind einzeln nachgewiesen.

Der XML/Markdown-Abgleich vergleicht jedes gerenderte Inhaltssegment zeichengetreu nach NFC- und Leerraumnormalisierung. Nur ausdrücklich redaktionelle Fußnotenverknüpfungen und generische Spaltenüberschriften werden vom Vergleich ausgenommen. Ein zweiter Prüfer untersucht unabhängig davon jeden vollständigen Normabschnitt, die Normreihenfolge und jede einzelne Tabellenzelle. Komplexe Tabellen behalten verbundene Zellen als HTML im Markdown.

Erforderlich: Python 3, `markdown-it-py`, Poppler `pdftotext` im PATH; für die zusätzliche BewG-Bildprüfung `PyMuPDF`. Die archivierten Prüfer arbeiten ohne Netzwerkzugriff. Aufruf aus dem Standordner:

```powershell
py Pruefung/konvertieren.py
py Pruefung/markdown_struktur_pruefen.py
py Pruefung/pdf_xml_pruefen.py
```

- [Konfiguration](konfiguration.json): Quellenpfade, Fassungsangaben und Hashes.
- [Vollständigkeitsprüfung](Vollstaendigkeitspruefung.json): jeder XML/Markdown-Inhaltsblock.
- [Markdown-Strukturprüfung](Markdown_Strukturpruefung.json): vollständige Normabschnitte und Tabellen.
- [Normenbestand](Normenbestand.json): vollständiges Normverzeichnis und Originalkennungen.
- [PDF/XML-Abgleich](PDF_XML_Abgleich.json): alle PDF-Seiten und XML-Normdatensätze.
{extras}
## SHA-256-Prüfsummen

| Datei | SHA-256 |
| --- | --- |
| Original-PDF und am Prüftag abgerufene PDF | `{cfg['sha256_lokale_pdf']}` |
| XML | `{cfg['sha256_xml']}` |
| Markdown | `{check['sha256_markdown']}` |
'''
 (p/'Pruefbericht.md').write_text(report,'utf8')
 results.append({'kuerzel':short,'titel':cfg['titel'],'bereich':cfg['rechtsgebiet'],'original':original,'original_dateiname':original,'markdown':(base/(short+'.md')).relative_to(ROOT).as_posix(),'pruefbericht':(p/'Pruefbericht.md').relative_to(ROOT).as_posix(),'pdf_seiten':cfg['pdf_seiten'],'quellenstand':cfg['stand'],'quelle':cfg['quelle_html'],'sha256_original_pdf':cfg['sha256_lokale_pdf'],'sha256_markdown':check['sha256_markdown']})
(HERE/'ergebnis_steuer.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'dokumente':len(results),'seiten':sum(r['pdf_seiten'] for r in results),'alle_pruefungen_erfolgreich':True},ensure_ascii=False))
