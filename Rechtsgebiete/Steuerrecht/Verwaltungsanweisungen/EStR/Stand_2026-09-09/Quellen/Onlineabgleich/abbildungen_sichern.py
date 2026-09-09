from pathlib import Path
from PIL import Image,ImageDraw
import fitz,hashlib,json,re

HERE=Path(__file__).resolve().parent
DEST=HERE.parent/'Abbildungen'
DEST.mkdir(exist_ok=True)
ROOT=next(p for p in HERE.parents if (p/'Bestand.json').exists())
source=ROOT/'EStR 2012.txt'
if not source.exists():source=HERE.parent/'EStR_2012_Webkopie.txt'
lines=source.read_text(encoding='utf-8').splitlines()
results=[]
for number in range(1,19):
    caption=[(i+1,l) for i,l in enumerate(lines) if i>19400 and re.match(fr'Muster {number}: .+',l)]
    assert len(caption) in (1,2),(number,caption)
    src=HERE/f'Muster_{number:02}_EStH_2019.{"jpg" if number<=12 else "pdf"}'
    pagepaths=[]
    if number<=12:
        target=DEST/f'Muster_{number:02}_2013.jpg'
        target.write_bytes(src.read_bytes())
        pagepaths.append((None,target))
    else:
        doc=fitz.open(src)
        for ix,page in enumerate(doc):
            target=DEST/f'Muster_{number:02}_2013_Seite_{ix+1}.png'
            page.get_pixmap(dpi=150).save(target)
            pagepaths.append((ix+1,target))
    for page,target in pagepaths:
        with Image.open(target) as im:width,height=im.size;im.verify()
        label=caption[min((page or 1)-1,len(caption)-1)]
        results.append({'muster':number,'quellzeile':label[0],'datei':target.relative_to(HERE.parent.parent).as_posix(),'pdf_seite':page,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'stand':'BMF-Schreiben 07.11.2013, ergänzt 26.03.2014; Wiedergabe EStH 2019','titel':label[1],'quelle':src.relative_to(HERE.parent.parent).as_posix(),'pixel':[width,height]})
(HERE/'Abbildungen.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
thumbwidth,thumbheight=320,470
for batch in range(2):
    subset=results[batch*12:(batch+1)*12]
    sheet=Image.new('RGB',(thumbwidth*4,thumbheight*3),'#cccccc')
    draw=ImageDraw.Draw(sheet)
    for ix,e in enumerate(subset):
        img=Image.open(HERE.parent.parent/e['datei']).convert('RGB');img.thumbnail((310,440))
        x=(ix%4)*thumbwidth;y=(ix//4)*thumbheight
        sheet.paste(img,(x+(thumbwidth-img.width)//2,y+25))
        draw.text((x+6,y+6),f"Muster {e['muster']} / Seite {e['pdf_seite'] or 1}",fill='black')
    sheet.save(HERE/f'Sichtpruefung_Kontaktbogen_{batch+1}.jpg',quality=92)
print(json.dumps({'abbildungen':len(results),'muster':18,'pixel_min':[min(e['pixel'][0] for e in results),min(e['pixel'][1] for e in results)]}))
