from pathlib import Path
from html.parser import HTMLParser
import re,html,json,hashlib

HERE=Path(__file__).resolve().parent
BASE='https://amtliche-handbuecher.bundesfinanzministerium.de/'
DEST=HERE.parent.parent/'Ergaenzungen';DEST.mkdir(exist_ok=True)
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
    def handle_starttag(self,tag,attrs):
        if tag in ('br','p','h1','h2','h3','tr','td','th'):self.parts.append(' ')
    def handle_endtag(self,tag):
        if tag in ('p','h1','h2','h3','tr','td','th'):self.parts.append(' ')
def txt(t):
    p=Text();p.feed(t);return re.sub(r'\s+',' ',''.join(p.parts)).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
for num,fn,urlpath in [(2,'EStH_2025_Anhang_01_I_2.html','esth/2025/B-Anhaenge/Anhang-01/I-2/inhalt.html'),(6,'EStH_2025_Anhang_12_II_1.html','esth/2025/B-Anhaenge/Anhang-12/II-1/inhalt.html')]:
    source=(HERE/fn).read_text(encoding='utf-8')
    main=re.search(r'<main\b.*?</main>',source,re.S).group()
    table=re.search(r'<table\b.*?</table>',main,re.S).group()
    heading=txt(re.search(r'<h1\b.*?</h1>',main,re.S).group())
    assert not re.search(r'<(?:img|aside)\b',main),f'Zusatzinhalte ungeprueft: {fn}'
    intro=f'# Amtliche Vergleichsfassung 2025 zu Anlage {num}\n\n'
    intro+='Diese Ergänzung gibt die entsprechende Übersicht des Amtlichen Einkommensteuer-Handbuchs 2025 wieder. Die Anlage in der gelieferten Webkopie bleibt als eigener Quellenstand erhalten.\n\n'
    intro+=f'Quelle: [BMF, EStH 2025]({BASE+urlpath}); [gespeichertes Original-HTML](../Quellen/Onlineabgleich/{fn}). Abgerufen am 09.09.2026.\n\n'
    if num==6:
        rows=re.findall(r'<tr\b.*?</tr>',table,re.S)
        content=[];proof=[]
        for row in rows:
            name=txt(re.search(r'<h2\b.*?</h2>',row,re.S).group())
            paragraphs=[txt(x) for x in re.findall(r'<p\b.*?</p>',row,re.S)]
            assert txt(row)==name+' '+ ' '.join(paragraphs)
            content.append('| '+html.escape(name).replace('|','&#124;')+' | '+'<br>'.join(html.escape(t).replace('|','&#124;') for t in paragraphs)+' |')
            proof.extend([name,*paragraphs])
        assert txt(table)==' '.join(proof)
        assert len(rows)==79 and content[-1].startswith('| Uganda |')
        intro+='**In der amtlichen Quelle angegebener Stand: 1.1.2025.** Die Webkopie enthält für ihre Anlage 6 kein eigenes Standdatum; beispielsweise Andorra und Malediven sind dort nicht enthalten.\n\n'
        body=f'## {heading}\n\nStand: 1.1.2025\n\n| Staat / Gebiet | Steuern |\n| --- | --- |\n'+'\n'.join(content)+'\n'
        stats={'laender_gebiete':len(rows),'sichtbarer_tabellentext_vollstaendig':True,'endet_mit':'Uganda; withholding tax (Quellensteuer für Beratungsleistungen (15 %)'}
    else:
        # Native HTML table in Markdown preserves all merged cells and exact text.
        clean=re.sub(r'\s+(?:class|table-status)="[^"]*"','',table)
        clean=re.sub(r'<abbr\b[^>]*>(.*?)</abbr>',r'\1',clean,flags=re.S)
        clean=re.sub(r'</?span\b[^>]*>','',clean)
        clean=re.sub(r'(?:<br\s*/?>\s*){2,}','<br>',clean)
        clean=re.sub(r'>\s+<','><',clean)
        assert txt(clean)==txt(table)
        assert re.findall(r'(?:rowspan|colspan)="\d+"',clean)==re.findall(r'(?:rowspan|colspan)="\d+"',table)
        intro+='**Ausgabe: EStH 2025, Rechtsstand für den VZ 2025.** Die Webkopie enthält unter Nr. 1 eine zusätzliche historische Position: Fertigstellung nach dem 9.10.1962 und vor dem 1.1.1965 und Bauantrag nach dem 9.10.1962. Die amtliche Übersicht beginnt mit der Position, die in der Webkopie Nr. 2 trägt. Sie umfasst außerdem unter Nr. 11 die Absetzungen nach § 7 Abs. 5a EStG; diese Position enthält die Webkopie nicht. Die jeweils elf nummerierten Positionen beider Fassungen haben daher eine unterschiedliche Zuordnung.\n\n'
        body=f'## {heading}\n\n{clean}\n'
        stats={'tabellenzeilen':len(re.findall(r'<tr\b',table)),'sichtbarer_tabellentext_vollstaendig':True,'zellspans_unveraendert':True,'fussnoten_in_sachinhalt':0}
    target=DEST/f'Anlage_{num}_BMF_2025.md';target.write_text(intro+body,encoding='utf-8')
    results.append({'titel':f'Amtliche Vergleichsfassung zu Anlage {num} (EStH 2025)','datei':target.relative_to(HERE.parent.parent).as_posix(),'sha256':sha(target),'quelle_datei':'Quellen/Onlineabgleich/'+fn,'quelle_sha256':sha(HERE/fn),'url':BASE+urlpath,'pruefung':stats})
(HERE/'Ergaenzungen.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
