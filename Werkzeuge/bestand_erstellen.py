"""Erstellt den zentralen Index aus den archivierten Konfigurationen und Quellen."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parent.parent
DATE='2026-09-09'
# Einheitliche Bereichsanzeige; historische Quellmetadaten und Pfade bleiben erhalten.
BEREICHSNAMEN={'Steuerrecht / Allgemeines_Steuerrecht':'Steuerrecht / Allgemeines Steuerrecht'}
def md_link(label,target):
 label=str(label).replace('\\','\\\\').replace('|','\\|').replace('[','\\[').replace(']','\\]')
 return f'[{label}](<{target}>)'
ARCHIV=json.loads((ROOT/'PDF_Archiv/Archivregister.json').read_text(encoding='utf-8'))
ARCHIVSTAND=[e for e in ARCHIV['eintraege'] if e['archivversion']=='Stand_'+DATE]
def original_fuer(quelle):
 digest=hashlib.sha256(quelle.read_bytes()).hexdigest()
 matches=[e for e in ARCHIVSTAND if e['sha256_pdf']==digest]
 assert len(matches)==1, 'Original-PDF nicht eindeutig im Archivregister: '+str(quelle)
 path=ROOT/matches[0]['pdf']
 assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest
 return path
items=[]
for top in ['Rechtsgebiete']:
 for config in sorted((ROOT/top).glob('**/Pruefung/konfiguration.json')):
  c=json.loads(config.read_text(encoding='utf-8-sig'));base=config.parent.parent
  md=base/c.get('markdown_datei',c['kuerzel']+'.md')
  source=base/'Quellen'/c['lokale_pdf']
  assert source.exists() and md.exists()
  check=json.loads((config.parent/'Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
  assert check['sha256_markdown']==hashlib.sha256(md.read_bytes()).hexdigest()
  original=original_fuer(source)
  items.append({'kuerzel':c['kuerzel'],'titel':c['titel'],'bereich':c['rechtsgebiet'],'typ':c.get('typ','Gesetz/Verordnung'),'original_pdf':original.relative_to(ROOT).as_posix(),'pdf_seiten':c['pdf_seiten'],'markdown':md.relative_to(ROOT).as_posix(),'quellenabgleich':c['quellenabgleich'],'quellenstand':c['stand'],'quelle':c.get('quelle_html',c['quelle_url']),'sha256_original_pdf':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256_markdown':check['sha256_markdown'],'pruefbericht':(config.parent/'Pruefbericht.md').relative_to(ROOT).as_posix()})
ustg=ROOT/'Rechtsgebiete/Steuerrecht/Gesetze/Umsatzsteuer/UStG/Stand_2026-09-09'
ustg_original=original_fuer(ustg/'Quellen/UStG.pdf')
items.append({'kuerzel':'UStG','titel':'Umsatzsteuergesetz','bereich':'Steuerrecht / Umsatzsteuer','typ':'Gesetz/Verordnung','original_pdf':ustg_original.relative_to(ROOT).as_posix(),'pdf_seiten':98,'markdown':(ustg/'UStG.md').relative_to(ROOT).as_posix(),'quellenabgleich':DATE,'quellenstand':['Zuletzt geändert durch Art. 5 G v. 29.6.2026 I Nr. 197'],'quelle':'https://www.gesetze-im-internet.de/ustg_1980/BJNR119530979.html','sha256_original_pdf':hashlib.sha256(ustg_original.read_bytes()).hexdigest(),'sha256_markdown':hashlib.sha256((ustg/'UStG.md').read_bytes()).hexdigest(),'pruefbericht':(ustg/'Pruefung/Pruefbericht.md').relative_to(ROOT).as_posix()})
gobd=ROOT/'Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/GoBD/Stand_2026-09-09'
for name,title,pages in [('2019-11-28-GoBD','GoBD-Grundschreiben vom 28.11.2019',44),('2024-03-11-aenderung-gobd','GoBD-Änderung vom 11.03.2024',9),('2025-07-14-GoBD-2-aenderung','Zweite GoBD-Änderung vom 14.07.2025',4)]:
 md=gobd/(name+'.md');source=original_fuer(gobd/'Quellen'/(name+'.pdf'));assert md.is_file() and source.is_file()
 items.append({'kuerzel':title,'titel':title,'bereich':'Steuerrecht / Verwaltungsanweisungen / GoBD','typ':'BMF-Schreiben','original_pdf':source.relative_to(ROOT).as_posix(),'pdf_seiten':pages,'markdown':md.relative_to(ROOT).as_posix(),'quellenabgleich':DATE,'quellenstand':[name[:10]],'quelle':'Siehe Quellenmanifest und Prüfbericht im GoBD-Standordner','sha256_original_pdf':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256_markdown':hashlib.sha256(md.read_bytes()).hexdigest(),'pruefbericht':(gobd/'README.md').relative_to(ROOT).as_posix()})
assert {x['original_pdf'] for x in items}=={e['pdf'] for e in ARCHIVSTAND},'Archiv und Markdown-Bestand stimmen nicht überein'
assert len(items)==len({x['original_pdf'] for x in items})
for item in items:
 item['bearbeitungsstatus']='in_markdown_umgewandelt'
 item['pdf_archivversion']='Stand_'+DATE
 item['original_dateiname']=Path(item['original_pdf']).name
web_register=ROOT/'Web_Archiv/Archivregister.json'
if web_register.is_file():
 web_archive=json.loads(web_register.read_text(encoding='utf-8'))
 web_entries=[e for e in web_archive['eintraege'] if e['archivversion']=='Stand_'+DATE]
 assert len(web_entries)==len({e['original_quelle'] for e in web_entries}), 'Doppelte Webquelle im Archivregister'
 for entry in web_entries:
  assert entry['status']=='in_markdown_umgewandelt'
  source=ROOT/entry['original_quelle'];md=ROOT/entry['markdown'];report=ROOT/entry['pruefbericht']
  assert source.is_file() and md.is_file() and report.is_file()
  assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['sha256_original_quelle']
  assert hashlib.sha256(md.read_bytes()).hexdigest()==entry['sha256_markdown']
  check=json.loads((md.parent/'Pruefung/Vollstaendigkeitspruefung.json').read_text(encoding='utf-8'))
  assert check['pruefung_erfolgreich'] is True
  assert check['sha256_original_quelle']==entry['sha256_original_quelle']
  assert check['sha256_markdown']==entry['sha256_markdown']
  items.append({'kuerzel':entry['kuerzel'],'titel':entry['dokument'],'bereich':entry['bereich'],
   'typ':entry.get('typ','Verwaltungsanweisung (Webkopie)'),'original_quelle':entry['original_quelle'],
   'original_dateiname':entry['urspruenglicher_dateiname'],'quellformat':entry['quellformat'],
   'markdown':entry['markdown'],'pruefbericht':entry['pruefbericht'],
   'quellenabgleich':entry['quellenabgleich'],'erfasst_am':entry['erfasst_am'],
   'quellenstand':entry['quellenstand'],'quelle':entry.get('quelle','Siehe Quellenmanifest und Prüfbericht im Standordner'),
   'sha256_original_quelle':entry['sha256_original_quelle'],'sha256_markdown':entry['sha256_markdown'],
   'bearbeitungsstatus':entry['status'],'archivversion':entry['archivversion'],
   'vollstaendigkeit':entry['vollstaendigkeit']})
for item in items:
 item['bereich']=BEREICHSNAMEN.get(item['bereich'],item['bereich'])
items.sort(key=lambda x:(x['typ'],x['bereich'],x['kuerzel']))
assert len(items)==len({x['markdown'] for x in items}), 'Doppelte Markdown-Zuordnung im Gesamtbestand'
pending=list((ROOT/'PDF_Archiv/01_Unbearbeitet').rglob('*.pdf'))+list(ROOT.glob('*.pdf'))
pending_web=[p for p in (ROOT/'Web_Archiv/01_Unbearbeitet').rglob('*') if p.is_file() and p.name!='README.md']+list(ROOT.glob('*.txt'))
pdf_count=sum('original_pdf' in x for x in items)
web_count=len(items)-pdf_count
web_label='Webkopie' if web_count==1 else 'Webkopien'
manifest={'quellenabgleich':DATE,'dokumente':len(items),'pdf_dokumente':pdf_count,'webkopien':web_count,'pdf_seiten_gesamt':sum(x.get('pdf_seiten',0) for x in items),'originaldateien_unveraendert':True,'unbearbeitete_pdfs':[p.relative_to(ROOT).as_posix() for p in pending],'unbearbeitete_webquellen':[p.relative_to(ROOT).as_posix() for p in pending_web],'eintraege':items}
(ROOT/'Bestand.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
parts=['# Rechts- und Steuerwissensdatenbank',f'**{len(items)} Dokumente: {pdf_count} PDF-Dokumente ({manifest["pdf_seiten_gesamt"]:,} Seiten) und {web_count} {web_label}. Erfassung/Quellenprüfung: 09.09.2026.**'.replace(',','.'),'Die registrierten Quellen sind in Markdown umgewandelt und gegen die bereitgestellten Dateien geprüft. Die Original-PDFs liegen unverändert im [versionierten PDF-Archiv](PDF_Archiv/README.md). Dort sind Bearbeitungsstatus, PDF und zugehöriger Markdown-Volltext direkt verknüpft. Neue PDFs kommen in [01_Unbearbeitet](PDF_Archiv/01_Unbearbeitet/README.md). Zu jedem Dokument gehören Quellen und nachvollziehbare Prüfberichte. Änderungsstand, Umfang und Einschränkungen des Quellenabgleichs stehen im jeweiligen Dokument. Das Datum des Stand-Ordners bezeichnet die Erfassung beziehungsweise Quellenprüfung und bestätigt für sich allein keine aktuelle amtliche Gesamtfassung.',f'**Bearbeitungsstatus:** {len(items)} in Markdown umgewandelt; unbearbeitete PDFs: {len(pending)}; unbearbeitete Webquellen: {len(pending_web)}.']
if web_count:
 parts.append('Unveränderte Textkopien von Webseiten liegen im [Web-Archiv](Web_Archiv/README.md). Die dortigen Prüfberichte unterscheiden die vollständige Übertragung der gelieferten Kopie von der Vollständigkeit und Aktualität der amtlichen Gesamtfassung.')
for group in ['Steuerrecht','Weitere Rechtsgebiete']:
 entries=[x for x in items if x['typ'] in {'Gesetz/Verordnung','EU-Verordnung','EU-Richtlinie'} and ((x['markdown'].startswith('Rechtsgebiete/Steuerrecht/'))==(group=='Steuerrecht'))]
 parts.append('## '+group)
 rows=['| Dokument | Rechtsgebiet | PDF-Seiten | Standangabe der Quelle (Details im Dokument) |','| --- | --- | ---: | --- |']
 for x in entries:
  stand=next((s for s in x['quellenstand'] if 'geändert' in s.lower()),x['quellenstand'][0] if x['quellenstand'] else 'Siehe Dokument')
  rows.append(f'| {md_link(x["kuerzel"],x["markdown"])} | {x["bereich"].replace("Steuerrecht / ","")} | {x["pdf_seiten"]} | {stand} |')
 parts.append('\n'.join(rows))
parts.append('## GoBD: Verwaltungsanweisungen')
parts.append('Die drei BMF-Schreiben bleiben als vollständige Einzeldokumente erhalten. Das Grundschreiben und seine beiden Änderungen werden nicht zu einer eigenständig konsolidierten Fassung vermischt. Die jüngste im Quellenabgleich gefundene Änderung datiert vom 14.07.2025. Der eingeschränkte Onlineabgleich des Grundschreibens von 2019 ist in der [GoBD-Dokumentation](Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/GoBD/Stand_2026-09-09/README.md) erläutert.')
parts.append('\n'.join(['| Dokument | PDF-Seiten |','| --- | ---: |',*[f'| {md_link(x["titel"],x["markdown"])} | {x["pdf_seiten"]} |' for x in items if x['typ']=='BMF-Schreiben']]))
web_items=[x for x in items if x['typ'].endswith('(Webkopie)')]
if web_items:
 parts.append('## Verwaltungsanweisungen und Verordnungen aus Webkopien' if any(not x['typ'].startswith('Verwaltungsanweisung') for x in web_items) else '## Verwaltungsanweisungen aus Webkopien')
 parts.append('Die Textkopien werden mit ihrer ursprünglichen Standangabe archiviert. Erfassungsdatum und ein später datierter Standordner ändern diese Standangabe nicht. Fehlende Inhalte oder Abbildungen der Ausgangskopie und der Abgleich mit amtlichen Quellen sind im jeweiligen Prüfnachweis dokumentiert.')
 rows=['| Dokument | Originalquelle | Standangabe der Kopie | Prüfnachweis |','| --- | --- | --- | --- |']
 for x in web_items:
  stand='; '.join(x['quellenstand']).replace('|','\\|')
  rows.append(f'| {md_link(x["kuerzel"],x["markdown"])} | {md_link(x["quellformat"],x["original_quelle"])} | {stand} | {md_link("Prüfbericht",x["pruefbericht"])} |')
 parts.append('\n'.join(rows))
 for x in web_items:
  parts.append(f'**{x["kuerzel"]} – Übertragungsumfang:** {x["vollstaendigkeit"]}')
parts.append('## Ablage und Prüfung')
parts.append('Alle Rechtsgebiete liegen einheitlich unter `Rechtsgebiete/`, einschließlich `Rechtsgebiete/Steuerrecht/`. Gesetze und Verordnungen sind dort nach Thema und Abkürzung gegliedert. Jeder Ordner `Stand_2026-09-09` enthält den Markdown-Volltext der jeweiligen Quelle sowie `Quellen/` und `Pruefung/`. Bei den PDF/XML-Konvertierungen sind Anlagen, weggefallene Vorschriften, Fußnoten, Tabellen und Originalabbildungen einbezogen. Einfache Tabellen verwenden Markdown; komplexe Tabellen behalten verbundene Zellen und relevante Trennlinien als HTML innerhalb des Markdown-Dokuments. Die Übertragungsgrenzen einer Webkopie werden beim betroffenen Dokument ausgewiesen.')
parts.append('Bei Quellen von Gesetze im Internet erfolgt der Abgleich zwischen PDF und XML sowie zwischen XML und gerendertem Markdown. Für EU-Dokumente und BMF-Schreiben sind die jeweilige PDF-Übernahme und der amtliche Quellenabgleich im Prüfbericht dokumentiert. Erkannte Besonderheiten der Textextraktion, ältere Fassungen und Ergänzungen sind beim betroffenen Dokument ausgewiesen. Die gelieferte Fassung wird bei der Konvertierung nicht stillschweigend durch einen anderen Rechtsstand ersetzt.')
parts.append('Maschinenlesbarer Gesamtbestand mit Dateipfaden und Prüfsummen: [Bestand.json](Bestand.json). Wiederholbare Werkzeuge: [Werkzeuge/README.md](Werkzeuge/README.md).')
parts.append('Cloud-Übergabe: [Tool starten](Cloud_Sync_starten.cmd) · [Google Drive und Claude einrichten](Werkzeuge/Cloud_Sync/README.md). Das Tool stellt geprüfte Fassungen im gewählten Zielordner bereit; den Upload übernimmt Google Drive für Desktop.')
(ROOT/'README.md').write_text('\n\n'.join(parts)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k!='eintraege'},ensure_ascii=False))
