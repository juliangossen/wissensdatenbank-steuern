"""Amtliche EUR-Lex-Amtsblattfassungen nach Markdown; lokale PDF bleibt maßgeblich.

Aufruf vom Workspace: py -B Werkzeuge/PDF_Import_2026-09-09/EU/konvertieren_eu.py
Erfordert beautifulsoup4, lxml, pymupdf, markdown-it-py.
"""
from pathlib import Path
import base64, collections, hashlib, html, json, re, shutil, unicodedata, warnings
from urllib.parse import urljoin
import fitz
from bs4 import BeautifulSoup, NavigableString, Comment, XMLParsedAsHTMLWarning
from markdown_it import MarkdownIt

warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
ROOT=Path(__file__).resolve().parents[3]
CACHE=Path(__file__).resolve().parent
DATE='2026-09-09'
DOCS=[
 dict(code='32011R0282', kuerzel='DVO (EU) 282/2011', stem='DVO_EU_282_2011', original='DVO (EU) 282_2011.pdf', folder='Rechtsgebiete/Steuerrecht/Verordnungen/Umsatzsteuer/DVO_EU_282_2011', rechtsgebiet='Steuerrecht / Verordnungen / Umsatzsteuer', titel='Durchführungsverordnung (EU) Nr. 282/2011 des Rates zur Festlegung von Durchführungsvorschriften zur Richtlinie 2006/112/EG über das gemeinsame Mehrwertsteuersystem', typ='EU-Verordnung', datum='2011-03-15', publication='23.03.2011, ABl. L 77, S. 1–22', prefix='II\n\n(Rechtsakte ohne Gesetzescharakter)\n\nVERORDNUNGEN', articles=65, recitals=46, annexes=4),
 dict(code='32016R0679', kuerzel='DSGVO', stem='DSGVO', original='DSGVO 2016_679.pdf', folder='Rechtsgebiete/Datenschutzrecht/DSGVO', rechtsgebiet='Datenschutzrecht', titel='Verordnung (EU) 2016/679 des Europäischen Parlaments und des Rates (Datenschutz-Grundverordnung)', typ='EU-Verordnung', datum='2016-04-27', publication='04.05.2016, ABl. L 119, S. 1–88', prefix='I\n\n(Gesetzgebungsakte)\n\nVERORDNUNGEN', articles=99, recitals=173, annexes=0),
 dict(code='32006L0112', kuerzel='MwStSystRL', stem='MwStSystRL', original='MwStSystRL 2006_112_EG.pdf', folder='Rechtsgebiete/Steuerrecht/Richtlinien/Umsatzsteuer/MwStSystRL', rechtsgebiet='Steuerrecht / Richtlinien / Umsatzsteuer', titel='Richtlinie 2006/112/EG des Rates über das gemeinsame Mehrwertsteuersystem', typ='EU-Richtlinie', datum='2006-11-28', publication='11.12.2006, ABl. L 347, S. 1–118', prefix='I\n\n(Veröffentlichungsbedürftige Rechtsakte)', articles=414, recitals=67, annexes=12),
]

def sha(data):return hashlib.sha256(data).hexdigest()
def writejson(path, value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def compact(s):return re.sub(r'\s+','',unicodedata.normalize('NFC',s))
def tidy(s):return re.sub(r'\s+',' ',s).strip()
def esc(s):
    s=html.escape(re.sub(r'\s+',' ',s),quote=False)
    s=re.sub(r'([\\`*_\[\]{}<>|])',r'\\\1',s)
    s=re.sub(r'(^\s*\d+)([.)])(?=\s|$)',r'\1\\\2',s)
    return re.sub(r'^(\s*)([-+#])(?=\s|$)',r'\1\\\2',s)
def pdfnorm(s):
    # PDF-Fußnoten beginnen auf jeder Seite bei 1, HTML zählt durch; * wird *1.
    s=re.sub(r'\(\s*\*?\s*\d*\s*\)','',s)
    return re.sub(r'[^\w]','',unicodedata.normalize('NFC',s)).lower()

class Converter:
    def __init__(self,c,base=None):
        self.c=c;self.base=Path(base) if base else ROOT/c['folder']/('Stand_'+DATE)
        for part in ['Quellen','Quellen/Abbildungen','Pruefung']:(self.base/part).mkdir(parents=True,exist_ok=True)
        self.url='https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:'+c['code']
        self.parser=MarkdownIt('commonmark',{'html':True}).enable('table')
        self.ids=set();self.toc=[];self.checks=[];self.images={};self.tables=0
        self.source_html=CACHE/(c['code']+'.html')
        if not self.source_html.exists():self.source_html=self.base/'Quellen'/'EUR-Lex_Amtsblatt.html'
        self.soup=BeautifulSoup(self.source_html.read_bytes(),'lxml')
        for e in self.soup.find_all(['script','style']):e.decompose()
        for e in self.soup.find_all('a',href=re.compile('^javascript:')):e.decompose()
        self.original=ROOT/c['original']
        if not self.original.exists():self.original=self.base/'Quellen'/c['original']
        official_pdf=CACHE/(c['code']+'.pdf')
        self.official_sha=sha(official_pdf.read_bytes()) if official_pdf.exists() else json.loads((self.base/'Quellen'/'Quellenabgleich.json').read_text(encoding='utf-8'))['sha256_amtliche_pdf']
        assert sha(self.original.read_bytes())==self.official_sha,'Amtliche PDF weicht ab'
        self.pdf=fitz.open(self.original)
    def visible(self,s):return BeautifulSoup(self.parser.render(s),'lxml').get_text()
    def anchor(self,e):
        ident=e.get('id')
        if not ident or ident in self.ids:return ''
        self.ids.add(ident)
        return '<a id="'+html.escape(ident,quote=True)+'"></a>'
    def check(self,e,out,kind):
        orig=e.get_text() if hasattr(e,'get_text') else str(e)
        a=compact(orig);b=compact(self.visible(out))
        assert a==b,(kind,orig[:100],self.visible(out)[:100],len(a),len(b))
        self.checks.append(dict(typ=kind,quelle=e.get('id') if hasattr(e,'get') else None,zeichen_ohne_whitespace=len(a),sha256_normalisierter_text=sha(a.encode()),identisch=True))
        return out
    def inline(self,e):
        if isinstance(e,Comment):return ''
        if isinstance(e,NavigableString):return esc(str(e))
        name=e.name
        if name=='img':return self.img(e)
        if name=='br':return '<br>'
        a=self.anchor(e);body=''.join(self.inline(x) for x in e.children)
        if name=='a' and e.get('href'):
            u=e['href'];u=u if u.startswith('#') else urljoin(self.url,u)
            return a+'['+body+'](<'+u+'>)'
        if name=='span':
            cls=e.get('class',[])
            if 'oj-super' in cls:return a+'<sup>'+body+'</sup>'
            if 'oj-sub' in cls:return a+'<sub>'+body+'</sub>'
            if 'oj-bold' in cls:return a+'<strong>'+body+'</strong>'
            if 'oj-italic' in cls:return a+'<em>'+body+'</em>'
        return a+body
    def img(self,e):
        src=e['src'];assert src.startswith('data:image/')
        # Vollauflösende Bilddaten direkt aus der maßgeblichen PDF verwenden.
        number=len(self.images)+1
        pdf_image=self.pdf.extract_image(self.pdf[15+number].get_images()[0][0])
        payload=pdf_image['image'];ext=pdf_image['ext']
        rel=f'Quellen/Abbildungen/Anhang_II_Formular_{len(self.images)+1:02d}.{ext}'
        (self.base/rel).write_bytes(payload)
        self.images[rel]=sha(payload)
        return '!['+esc(e.get('alt','Formular'))+']('+rel+')'
    def raw(self,e):
        if isinstance(e,Comment):return ''
        if isinstance(e,NavigableString):return html.escape(str(e),quote=False)
        name=e.name
        attrs={}
        for k in ['id','colspan','rowspan','align','valign','width']:
            if e.get(k):attrs[k]=e[k]
        if attrs.get('id'):
            if attrs['id'] in self.ids:attrs.pop('id')
            else:self.ids.add(attrs['id'])
        if name=='a' and e.get('href'):
            attrs['href']=e['href'] if e['href'].startswith('#') else urljoin(self.url,e['href'])
        if name=='span':
            classes=e.get('class',[])
            if 'oj-super' in classes:name='sup'
            elif 'oj-sub' in classes:name='sub'
            elif 'oj-bold' in classes:name='strong'
            elif 'oj-italic' in classes:name='em'
        astr=''.join(' '+k+'="'+html.escape(str(v),quote=True)+'"' for k,v in attrs.items())
        if name in ['br','col']:return '<'+name+astr+'>'
        if name=='table':astr+=' style="border-collapse:collapse"'
        if name in ['td','th']:astr+=' style="border:1px solid currentColor;padding:0.3em;vertical-align:top"'
        return '<'+name+astr+'>'+''.join(self.raw(x) for x in e.children)+'</'+name+'>'
    def heading(self,elems,level,ident):
        source=' '.join(e.get_text() for e in elems)
        text=' '.join(tidy(self.inline(e)) for e in elems)
        out='\n\n'+'#'*level+' '+text+'\n\n'
        assert compact(source)==compact(self.visible(out))
        self.checks.append(dict(typ='Überschrift',quelle=ident,zeichen_ohne_whitespace=len(compact(source)),sha256_normalisierter_text=sha(compact(source).encode()),identisch=True))
        self.toc.append((level,tidy(source),ident))
        return out
    def walk(self,e,level=2):
        if isinstance(e,Comment):return ''
        if isinstance(e,NavigableString):return esc(str(e)) if str(e).strip() else ''
        name=e.name;ident=e.get('id','');classes=e.get('class',[])
        if name=='hr':return '\n\n---\n\n'
        if name=='img':return '\n\n'+self.img(e)+'\n\n'
        if name=='table':
            if 'oj-table' in classes or any(len(r.find_all(['td','th'],recursive=False))!=2 for r in e.find_all('tr',recursive=False)):
                self.tables+=1;return '\n\n'+self.check(e,self.raw(e),'Datentabelle')+'\n\n'
            rows=e.find_all('tr',recursive=False) or [r for r in e.find_all('tr') if r.find_parent('table') is e]
            if any(len(r.find_all(['td','th'],recursive=False))!=2 for r in rows):
                self.tables+=1;return '\n\n'+self.check(e,self.raw(e),'Datentabelle')+'\n\n'
            pieces=[]
            for row in rows:
                left,right=row.find_all(['td','th'],recursive=False)
                label=tidy(self.inline(left));body=''.join(self.walk(x,level) for x in right.children).strip()
                pieces.append(('**'+label+'** ' if label else '')+body)
            return '\n\n'+self.check(e,'\n\n'.join(pieces),'Aufzählung')+'\n\n'
        if name=='div':
            a=self.anchor(e)
            head=e.find('p',class_=['oj-ti-art','oj-ti-section-1'],recursive=False)
            sub=e.find('div',class_='eli-title',recursive=False)
            if head:
                isarticle=bool(re.fullmatch(r'art_\d+',ident))
                lev=min(6,level+1) if isarticle else min(5,2+ident.count('.'))
                parts=[head]+([sub] if sub else [])
                out='\n\n'+a+self.heading(parts,lev,ident)
                for x in e.children:
                    if x is head or x is sub:continue
                    out+=self.walk(x,lev)
                return out
            if re.fullmatch(r'anx_[IVXLCDM]+',ident):
                heads=e.find_all('p',class_='oj-doc-ti',recursive=False)
                out='\n\n'+a+self.heading(heads,2,ident)
                for x in e.children:
                    if any(x is h for h in heads):continue
                    out+=self.walk(x,2)
                return out
            return '\n\n'+a+'\n\n'+''.join(self.walk(x,level) for x in e.children)
        if name=='p':
            content=self.inline(e)
            if 'oj-ti-grseq-1' in classes or 'oj-ti-annotation' in classes:
                out='\n\n'+'#'*min(level+1,6)+' '+tidy(content)+'\n\n'
            elif 'oj-doc-ti' in classes:
                out='\n\n'+content.strip()+'\n\n'
            else:out='\n\n'+content.strip()+'\n\n'
            return self.check(e,out,'Fußnote' if 'oj-note' in classes else 'Absatz')
        if name in ['body','figure','span','td','tbody','tr']:
            return self.anchor(e)+''.join(self.walk(x,level) for x in e.children)
        return self.check(e,self.inline(e),'Text')
    def run(self):
        c=self.c
        shutil.copyfile(self.original,self.base/'Quellen'/c['original']) if self.original!=(self.base/'Quellen'/c['original']) else None
        if self.source_html!=(self.base/'Quellen'/'EUR-Lex_Amtsblatt.html'):shutil.copyfile(self.source_html,self.base/'Quellen'/'EUR-Lex_Amtsblatt.html')
        body=re.sub(r'\n{3,}','\n\n',self.walk(self.soup.body))
        a=compact(self.soup.body.get_text());b=compact(self.visible(body))
        assert a==b,('Gesamter HTML-Körper',len(a),len(b))
        ids=re.findall(r'<a id="([^"]+)"',body)+re.findall(r'<(?!a\b)[^>]*\bid="([^"]+)"',body)
        assert len(ids)==len(set(ids)), 'Doppelte IDs'
        body_html=BeautifulSoup(self.parser.render(body),'lxml')
        all_ids={x['id'] for x in body_html.find_all(id=True)}
        internal=[x['href'][1:] for x in body_html.find_all('a',href=True) if x['href'].startswith('#')]
        assert set(internal)<=all_ids, sorted(set(internal)-all_ids)
        article_count=len(self.soup.find_all(id=re.compile(r'^art_\d+$')))
        recital_count=len(self.soup.find_all(id=re.compile(r'^rct_\d+$')))
        annex_count=len(self.soup.find_all(id=re.compile(r'^anx_[IVXLCDM]+$')))
        assert (article_count,recital_count,annex_count)==(c['articles'],c['recitals'],c['annexes'])
        normhtml=pdfnorm(self.soup.body.get_text()+c['prefix']);coverage=[];rawpages=[]
        for number,page in enumerate(self.pdf,1):
            lines=[]
            for i,line in enumerate(page.get_text().splitlines(),1):
                s=line.strip()
                if not s:continue
                running=bool(re.fullmatch(r'L\s+\d+/\d+',s))
                n=pdfnorm(s)
                ok=running or n in normhtml
                lines.append(dict(zeile=i,text=s,art='Amtsblatt-Seitenzahl' if running else 'Text',in_html_nachgewiesen=ok))
                assert ok,(c['code'],number,i,s)
            coverage.append(dict(pdf_seite=number,zeilen=len(lines),alle_textzeilen_nachgewiesen=True,einzelzeilen=lines))
            rawpages.append('=== PDF-Seite '+str(number)+' ===\n'+page.get_text())
        (self.base/'Quellen'/'PDF_Seitentext.txt').write_text('\n\n'.join(rawpages),encoding='utf-8')
        writejson(self.base/'Pruefung'/'PDF_Textabgleich.json',dict(normalisierung='NFC, Kleinschreibung, nur Wortzeichen; geklammerte Fußnotennummern (PDF seitenweise, HTML fortlaufend) und reine Amtsblatt-Seitenzahlen getrennt behandelt. Vollständige Einzelzeilen erhalten; zusätzliche HTML→Markdown-Prüfung ignoriert ausschließlich Whitespace.',seiten=coverage))
        toc='\n'.join('  '*min(3,l-2)+'- ['+esc(t)+'](#'+ident+')' for l,t,ident in self.toc)
        stand=[f'Ursprüngliche Amtsblattfassung vom {c["publication"]}; Rechtsakt vom {c["datum"]}.','Keine konsolidierte Fassung: spätere Änderungen und Berichtigungen sind nicht in diese Originalfassung eingearbeitet.',f'Import und Abgleich am {DATE}; das Ordnerdatum bezeichnet den Importstand, nicht einen aktuellen Rechtsstand.']
        metadata=f'# {c["kuerzel"]}\n\n{c["titel"]}\n\n## Fassung und Quellen\n\n'+''.join('- '+x+'\n' for x in stand)
        metadata+=f'\nDie lokale PDF ist bytegenau identisch mit der amtlichen EUR-Lex-PDF dieser Fassung. Der Text folgt der zugehörigen [amtlichen HTML-Fassung]({self.url}). Fußnoten sind entsprechend dieser HTML-Fassung fortlaufend nummeriert und beidseitig verlinkt; die PDF verwendet teilweise je Seite neue Nummern.\n\n'
        metadata+=f'- [Original-PDF](<Quellen/{c["original"]}>)\n- [Archivierte amtliche HTML-Fassung](Quellen/EUR-Lex_Amtsblatt.html)\n- [Vollständigkeitsprüfung](Pruefung/Pruefbericht.md)\n'
        if self.images:metadata+='\nDie beiden Formularseiten in Anhang II sind als Originalabbildungen und mit den amtlichen Bildtexten enthalten. Für räumliche Zuordnung und Ankreuzfelder gilt die Abbildung.\n'
        metadata+='\n## Inhaltsverzeichnis\n\n'+toc+'\n\n## Amtsblatttext\n\n'+c['prefix']+'\n\n'
        md=metadata+body.strip()+'\n';mdpath=self.base/(c['stem']+'.md');mdpath.write_text(md,encoding='utf-8')
        proof=dict(kuerzel=c['kuerzel'],quellenabgleich=DATE,pdf_seiten=len(self.pdf),pdf_byteidentisch_mit_amtlichem_original=True,pdf_identisch_aktuell=False,sha256_pdf=sha(self.original.read_bytes()),sha256_original_pdf=sha(self.original.read_bytes()),sha256_amtliche_pdf=self.official_sha,sha256_html=sha(self.source_html.read_bytes()),sha256_markdown=sha(mdpath.read_bytes()),vorschriften=article_count,erwaegungsgruende=recital_count,anlagen_anhaenge=annex_count,tabellen=self.tables,bilder=len(self.images),bildassets=self.images,fussnoten=len(self.soup.select('p.oj-note')),gepruefte_textbloecke=len(self.checks),alle_textbloecke_identisch=True,gesamter_html_text_identisch=True,alle_pdf_textzeilen_nachgewiesen=True,interne_links=len(internal),alle_linkziele_vorhanden=True,methode='Byteidentität des lokalen PDF mit amtlichem EUR-Lex-PDF; jede extrahierte PDF-Textzeile gegen den zugehörigen HTML-Volltext geprüft (separates Zeilenprotokoll); anschließend jede Inhaltskomponente und der gesamte HTML-Text zeichengenau gegen aus Markdown gerenderten Text, ausschließlich Whitespace normalisiert. HTML-Formularbilder lokal bewahrt, amtliche Bildtexte mitkonvertiert. Kein Abgleich mit einer späteren Konsolidierung.',bloecke=self.checks)
        proof['pruefung_erfolgreich']=True
        proof['abbildungen_aus_original_pdf']=bool(self.images)
        proof['sichtpruefung_pdf_seiten']=([17,18,20,21] if c['code']=='32011R0282' else [32] if c['code']=='32016R0679' else [71,80,81,118])
        writejson(self.base/'Pruefung'/'Vollstaendigkeitspruefung.json',proof)
        config=dict(kuerzel=c['kuerzel'],titel=c['titel'],rechtsgebiet=c['rechtsgebiet'],lokale_pdf=c['original'],pdf_seiten=len(self.pdf),quellenabgleich=DATE,stand=stand,quelle_url=self.url,quelle_html=self.url,typ=c['typ'],ausfertigungsdatum=c['datum'],pdf_identisch_aktuell=False,markdown_datei=c['stem']+'.md')
        writejson(self.base/'Pruefung'/'konfiguration.json',config)
        writejson(self.base/'Quellen'/'Quellenabgleich.json',dict(abrufdatum=DATE,celex=c['code'],html_url=self.url,pdf_url=self.url.replace('/HTML/','/PDF/'),pdf_byteidentisch=True,sha256_amtliche_pdf=proof['sha256_amtliche_pdf'],sha256_html=proof['sha256_html'],fassungsart='Ursprüngliche Amtsblattfassung',stand=stand))
        report=f'# Vollständigkeitsprüfung: {c["kuerzel"]}\n\nGeprüft am {DATE}.\n\n**Bestanden:** Die lokale PDF stimmt bytegenau mit der amtlichen EUR-Lex-PDF der ursprünglichen Amtsblattfassung überein.\n\n'
        report+=f'- {len(self.pdf)} PDF-Seiten; alle extrahierten nichtleeren Textzeilen einzeln nachgewiesen.\n- {article_count} Artikel, {recital_count} Erwägungsgründe, {annex_count} Anhänge.\n- {proof["fussnoten"]} Fußnotenblöcke, {self.tables} Datentabellen einschließlich Amtsblattkopf, {len(self.images)} Abbildungen.\n- {len(self.checks)} Inhaltskomponenten und der gesamte HTML-Körper nach Markdown-Rendering textidentisch (nur Whitespace normalisiert).\n- Sämtliche {len(internal)} internen Querverweise haben ein vorhandenes Ziel.\n\n'
        report+='Bei PDF → HTML sind ausschließlich Layoutzeichen, Trennstriche, Groß-/Kleinschreibung und die abweichende Fußnotenzählung für die Suchprüfung normalisiert. Die PDF-Einzelzeilen bleiben im [Prüfprotokoll](PDF_Textabgleich.json) vollständig lesbar. Der zusätzliche strenge HTML → Markdown-Abgleich bewahrt sämtliche Buchstaben, Ziffern, Satzzeichen und Tabellenzellen. Fußnoten und Anhänge sind nicht ausgelassen. Nur wiederkehrende Seitenköpfe und Seitenzahlen werden im strukturierten Lesetext nicht auf jeder Seite wiederholt. Sie stehen im [PDF-Seitentext](../Quellen/PDF_Seitentext.txt) und im Original.\n\n'
        report+='Die HTML-Oberfläche (Skripte und zwei Schaltflächen „Text von Bild“) ist kein Normtext; bei vorhandenen Bildtexten wird deren voller Inhalt übernommen. Verschmolzene Tabellenzellen bleiben als HTML-Tabellen innerhalb der Markdown-Datei erhalten.\n\n'
        report+='**Fassungsgrenze:** '+stand[0]+' '+stand[1]+' '+stand[2]+'\n\n[Maschinenlesbarer Nachweis](Vollstaendigkeitspruefung.json) · [Quellenmetadaten](../Quellen/Quellenabgleich.json)\n'
        (self.base/'Pruefung'/'Pruefbericht.md').write_text(report,encoding='utf-8')
        (self.base/'README.md').write_text(f'# {c["kuerzel"]} · Importstand {DATE}\n\n[Vollständiger Markdown-Text]({c["stem"]}.md)\n\n'+ '\n\n'.join(stand)+f'\n\n[Original-PDF](<Quellen/{c["original"]}>) · [Prüfbericht](Pruefung/Pruefbericht.md)\n',encoding='utf-8')
        (self.base.parent/'README.md').write_text(f'# {c["kuerzel"]}\n\n{c["titel"]}\n\n[Erfasste Fassung · Stand_{DATE}](Stand_{DATE}/{c["stem"]}.md)\n\n'+ '\n\n'.join(stand)+'\n',encoding='utf-8')
        return dict(kuerzel=c['kuerzel'],titel=c['titel'],bereich=c['rechtsgebiet'],original=c['original'],markdown=mdpath.relative_to(ROOT).as_posix(),pruefbericht=(self.base/'Pruefung'/'Pruefbericht.md').relative_to(ROOT).as_posix(),pdf_seiten=len(self.pdf),quellenstand=stand,quelle=self.url,sha256_original_pdf=proof['sha256_pdf'],sha256_markdown=proof['sha256_markdown'])

if __name__=='__main__':
    results=[]
    local_config=CACHE/'konfiguration.json'
    docs=DOCS
    if local_config.is_file():
        cfg=json.loads(local_config.read_text(encoding='utf-8'))
        docs=[c for c in DOCS if c['code'] in cfg['quelle_url']]
        assert len(docs)==1
    for config in docs:
        result=Converter(config,base=CACHE.parent if local_config.is_file() else None).run();results.append(result);print(config['kuerzel'],'OK',result['pdf_seiten'],'Seiten',flush=True)
    if not local_config.is_file():writejson(CACHE.parent/'ergebnis_eu.json',results)
