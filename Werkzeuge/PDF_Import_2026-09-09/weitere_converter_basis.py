"""GII-XML vollständig nach Markdown; Aufruf: py gesetz_konvertieren.py --config DATEI.

Nur archivierte Quellen, keine Netzwerkzugriffe. Erfordert markdown-it-py.
Jeder Inhaltsblock wird aus dem gerenderten Markdown zeichengenau rückverglichen.
"""
from pathlib import Path
import argparse, collections, hashlib, html, json, re, unicodedata
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from markdown_it import MarkdownIt


def compact(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFC', s))


def tidy(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def text_of(e):
    return ''.join(e.itertext()) if e is not None else ''


def display_en(s):
    return re.sub(r'^\(XXXX\)\s*', '', tidy(s))


def html_marker(s):
    return ''.join('&#'+str(ord(c))+';' for c in s)


def esc(s):
    s = re.sub(r'\s+', ' ', s or '')
    s = html.escape(s, quote=False)
    s = re.sub(r'([\\`*_\[\]|])', r'\\\1', s)
    s = re.sub(r'^(\s*\d+)([.)])(?=\s|$)', r'\1\\\2', s)
    s = re.sub(r'^(\s*)([-+=])(\s*)$', r'\1\\\2\3', s)
    return re.sub(r'-{3,}', lambda m: m.group().replace('-', '\\-'), s)


class TextReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]; self.skip=[]; self.header=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'data-redaktionell' in a:
            self.skip.append(tag)
        elif self.skip and tag not in {'br','img','hr','input'}:
            self.skip.append(tag)
        if tag=='thead': self.header=[]
    def handle_endtag(self,tag):
        if self.skip:
            if self.skip[-1]==tag: self.skip.pop()
            return
        if tag=='thead':
            s=''.join(self.header or [])
            if not re.fullmatch(r'(Spalte\d+)+',compact(s)):
                self.parts.append(s)
            self.header=None
    def handle_data(self,s):
        if not self.skip:
            (self.header if self.header is not None else self.parts).append(s)


class Converter:
    def __init__(self,config):
        self.config_path=Path(config).resolve()
        self.base=self.config_path.parent.parent
        self.c=json.loads(self.config_path.read_text(encoding='utf-8-sig'))
        self.xml=self.base/self.c['xml_datei']
        self.root=ET.parse(self.xml).getroot()
        self.parser=MarkdownIt('commonmark',{'html':True}).enable('table')
        self.checks=[];self.parts=[];self.assets={};self.current='';self.level=3
        self.notes={e.get('ID'):str(e.get('FnZ') or e.get('Ref') or (i+1))+(e.get('Postfix') or '') for i,e in enumerate(self.root.iter('Footnote'))}
        self.anchors={n.get('doknr'):self.make_anchor(n,i) for i,n in enumerate(self.root)}
        self.labels={tidy(n.findtext('metadaten/enbez','')):self.anchors[n.get('doknr')] for n in self.root if n.findtext('metadaten/enbez','')}
    def make_anchor(self,n,i):
        en=tidy(n.findtext('metadaten/enbez',''))
        if en.startswith('§'):
            label='p-'+en.replace('§','').strip()
        elif en.startswith('Art'):
            label='art-'+en
        elif en:
            label=en
        else:
            label='gliederung-'+n.findtext('metadaten/gliederungseinheit/gliederungskennzahl',str(i))
        label=re.sub(r'[^\w-]+','-',label.lower()).strip('-')
        return label+'-'+str(i)
    def visible(self,s):
        r=TextReader();r.feed(self.parser.render(s));return ''.join(r.parts)
    def mixed(self,e,cell=False):
        s=esc(e.text)
        for c in e:
            s+=self.render(c,cell)+esc(c.tail)
        return s
    def note_marker(self,e):
        ident=e.get('ID');num=self.notes[ident]
        return f'<sup data-redaktionell="fussnotenmarker-aus-attribut"><a href="#fn-{ident}">{html_marker(num)}</a></sup>'
    def image(self,e,raw=False):
        name=e.get('SRC') or e.get('src');p=(self.xml.parent/name).resolve()
        if not p.is_file(): raise ValueError(f'Bildasset fehlt: {p}')
        relative=p.relative_to(self.base).as_posix()
        self.assets[relative]=hashlib.sha256(p.read_bytes()).hexdigest()
        alt=e.get('alt') or 'Abbildung der Originalquelle'
        return f'<img src="{html.escape(relative)}" alt="{html.escape(alt)}">' if raw else '!['+esc(alt)+']('+relative+')'
    def dl(self,e,cell=False):
        items=[];children=list(e)
        assert len(children)%2==0, (self.current,'DL-Paare')
        for i in range(0,len(children),2):
            dt,dd=children[i:i+2];assert dt.tag=='DT' and dd.tag=='DD'
            label='**'+self.mixed(dt,cell).strip()+'**'
            if label=='****':label=''
            body=self.mixed(dd,cell).strip()
            if cell:items.append(label+(' ' if label else '')+body)
            else:
                s=(label+'\n\n'+body) if body.startswith(('- ','| ','<table>')) else label+(' ' if label else '')+body
                lines=s.splitlines() or ['']
                items.append('- '+lines[0]+''.join('\n  '+l if l else '\n' for l in lines[1:]))
        return ('<br>'+'<br>'.join(items)+'<br>') if cell else '\n\n'+'\n\n'.join(items)+'\n\n'
    def raw(self,e):
        """HTML für komplexe Tabellen; verbundene Zellen bleiben verbunden."""
        t=e.tag
        def m():return html.escape(e.text or '',quote=False)+''.join(self.raw(c)+html.escape(c.tail or '',quote=False) for c in e)
        if t=='table':return self.html_table(e)
        if t=='IMG':return self.image(e,True)
        if t=='BR':return '<br>'
        if t=='FnR':return self.note_marker(e)
        if t=='DL':
            ch=list(e);assert len(ch)%2==0
            return '<ul>'+''.join('<li><strong>'+self.raw(ch[i])+'</strong> '+self.raw(ch[i+1])+'</li>' for i in range(0,len(ch),2))+'</ul>'
        if t=='Footnote':
            ident=e.get('ID');return f'<p><a id="fn-{ident}"></a><span data-redaktionell="fussnotenlabel">{html_marker(self.notes[ident])}</span> '+m()+'</p>'
        names={'P':'p','LA':'div','B':'strong','I':'em','SUP':'sup','SUB':'sub','Title':'div','pre':'pre','small':'small'}
        if t in names:return '<'+names[t]+'>'+m()+'</'+names[t]+'>'
        if t in {'Content','DD','DT','F','NB','SP','ABWFORMAT','noindex','kommentar','Ident','TOC','Footnotes','titel'}:return m()
        raise ValueError(f'{self.current}: Unbekannter HTML-Inhaltstag {t}')
    def html_table(self,e):
        group=e.find('tgroup');cols=int(group.get('cols'));names={c.get('colname'):i for i,c in enumerate(group.findall('colspec'))}
        rows=[]
        for r in group.findall('thead/row')+group.findall('tbody/row')+group.findall('tfoot/row'):
            cells=[]
            for c in r.findall('entry'):
                attrs=''
                if c.get('morerows'):attrs+=f' rowspan="{int(c.get("morerows"))+1}"'
                if c.get('nameend'):attrs+=f' colspan="{names[c.get("nameend")]-names[c.get("namest")]+1}"'
                styles=[]
                if c.get('rowsep',r.get('rowsep',group.get('rowsep','0')))=='1':styles.append('border-bottom:1px solid currentColor')
                if c.get('colsep',group.get('colsep','0'))=='1':styles.append('border-right:1px solid currentColor')
                if c.get('align') in {'left','center','right','justify'}:styles.append('text-align:'+c.get('align'))
                if c.get('valign') in {'top','middle','bottom'}:styles.append('vertical-align:'+c.get('valign'))
                if styles:attrs+=' style="'+';'.join(styles)+'"'
                body=html.escape(c.text or '',quote=False)+''.join(self.raw(x)+html.escape(x.tail or '',quote=False) for x in c)
                cells.append('<td'+attrs+'>'+body+'</td>')
            rows.append('<tr>'+''.join(cells)+'</tr>')
        return '<table style="border-collapse:collapse">\n'+ '\n'.join(rows)+'\n</table>'
    def table(self,e):
        if any(x.get('morerows') or x.get('nameend') for x in e.iter('entry')) or len(list(e.iter('table')))>1:
            return '\n\n'+self.html_table(e)+'\n\n'
        group=e.find('tgroup');cols=int(group.get('cols'))
        names={c.get('colname'):i for i,c in enumerate(group.findall('colspec'))}
        rows=[]
        for r in group.findall('thead/row')+group.findall('tbody/row')+group.findall('tfoot/row'):
            cells=['']*cols;pos=0
            for c in r.findall('entry'):
                if c.get('colname'):pos=names[c.get('colname')]
                assert pos<cols
                value=self.mixed(c,True).strip()
                value=re.sub(r'^(?:<br>\s*)+|(?:<br>\s*)+$','',value)
                plain=tidy(text_of(c))
                if self.current=='Inhaltsübersicht' and plain in self.labels:
                    value='['+value+'](#'+self.labels[plain]+')'
                cells[pos]=value;pos+=1
            rows.append(cells)
        header=rows.pop(0) if group.find('thead') is not None and len(group.findall('thead/row'))==1 else [f'Spalte {i+1}' for i in range(cols)]
        return '\n\n'+'\n'.join(['| '+' | '.join(header)+' |','| '+' | '.join(['---']*cols)+' |',*['| '+' | '.join(r)+' |' for r in rows]])+'\n\n'
    def render(self,e,cell=False):
        t=e.tag
        if t=='BR':return '<br>' if cell else '  \n'
        if t=='DL':return self.dl(e,cell)
        if t=='table':return self.table(e)
        if t=='IMG':return self.image(e)
        if t=='FnR':return self.note_marker(e)
        if t=='Footnote':
            ident=e.get('ID');return '\n\n'+f'<a id="fn-{ident}"></a><span data-redaktionell="fussnotenlabel">{html_marker(self.notes[ident])}</span> '+self.mixed(e,cell).strip()+'\n\n'
        if t=='pre':
            def rawpre(n):return (n.text or '')+''.join(('\n' if c.tag=='BR' else rawpre(c))+(c.tail or '') for c in n)
            return '\n\n```text\n'+rawpre(e).strip('\n')+'\n```\n\n'
        if t in {'B','I'}:
            mark='**' if t=='B' else '*';s=self.mixed(e,cell).strip();return mark+s+mark if s else ''
        if t in {'SUB','SUP','small'}:return '<'+t.lower()+'>'+self.mixed(e,cell)+'</'+t.lower()+'>'
        if t in {'P','LA','Title'}:
            s=self.mixed(e,cell).strip()
            if not s:return ''
            if s in {'-','+','='}:s='\\'+s
            if t=='P':s=re.sub(r'^\((\d+[a-z]?)\)',r'**(\1)**',s)
            if t=='Title':s='**'+s.replace('  \n',' ')+'**'
            return s+('<br>' if cell else '\n\n')
        if t in {'Content','DD','DT','NB','F','SP','ABWFORMAT','noindex','kommentar','titel','TOC','Ident','Footnotes','gliederungstitel','gliederungsbez'}:return self.mixed(e,cell)
        raise ValueError(f'{self.current}: Nicht behandeltes XML-Element {t}')
    def checked(self,e,name):
        s=self.render(e).strip();a=compact(text_of(e));b=compact(self.visible(s))
        if a!=b:
            i=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
            raise AssertionError(f'{self.c["kuerzel"]} {name} bei {i}\nXML: {a[max(0,i-90):i+230]}\nMD: {b[max(0,i-90):i+230]}')
        self.checks.append({'teil':name,'zeichen_ohne_whitespace':len(a),'sha256_normalisierter_text':hashlib.sha256(a.encode()).hexdigest(),'identisch':True})
        return s
    def add(self,s):
        if s.strip():self.parts.append(s.strip())
    def run(self):
        c=self.c;short=c['kuerzel'];first=self.root[0].find('metadaten')
        metadata={k:c.get(k) for k in ['kuerzel','titel','rechtsgebiet','ausfertigungsdatum','quellenabgleich','stand','quelle_url','pdf_seiten','pdf_identisch_aktuell']}
        self.add('---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in metadata.items())+'\n---')
        kurz=tidy(text_of(first.find('kurzue')))
        self.add('# '+esc(c['titel'])+' ('+(esc(kurz)+' - ' if kurz and kurz!=c['titel'] else '')+esc(short)+')')
        self.add('## Dokumentation der Fassung\n\n**Quellenabgleich: '+c['quellenabgleich']+'.** Das Ordnerdatum bezeichnet den Quellenabgleich. Die vollständigen Stand- und Bearbeitungshinweise der Quelle stehen im Dokumentkopf.\n\nQuelle: [Gesetze im Internet]('+c.get('quelle_html',c['quelle_url'])+'). Archivierte [PDF](Quellen/'+c['lokale_pdf']+') und [XML]('+c['xml_datei']+'). '+('Die bereitgestellte PDF ist bytegleich mit der am Prüftag abgerufenen PDF.' if c['pdf_identisch_aktuell'] else 'Die bereitgestellte und die aktuell abgerufene PDF unterscheiden sich; Einzelheiten siehe Prüfbericht.')+'\n\nDer folgende Volltext enthält alle mitgelieferten Gliederungsteile, Vorschriften, Anlagen, Fußnoten und Abbildungen. Wiederkehrende PDF-Servicezeilen, Seitennummern und wiederholte Tabellenköpfe entfallen. Die Navigation, generische Tabellenüberschriften und mit „Fn.“ gekennzeichnete Fußnotenverweise sind redaktionelle Ergänzungen. Komplexe Tabellen bleiben als HTML-Tabellen im Markdown erhalten. [Prüfbericht](Pruefung/Pruefbericht.md).')
        self.parts[-1]=self.parts[-1].replace('Die Navigation, generische Tabellenüberschriften und mit „Fn.“ gekennzeichnete Fußnotenverweise sind redaktionelle Ergänzungen.', 'Navigation und generische Tabellenüberschriften sind redaktionelle Ergänzungen. Fußnotenmarker werden aus den Quellattributen übernommen und verlinkt; nur bei fehlender Kennzeichnung wird eine laufende Nummer vergeben. Der technische XML-Präfix „(XXXX)“ bei weggefallenen Vorschriften wird wie in der PDF ausgeblendet.')
        self.add('## Navigation\n\n- [Dokumentkopf](#dokumentkopf)\n'+ '\n'.join('- ['+esc(tidy(display_en(n.findtext('metadaten/enbez',''))+' '+text_of(n.find('metadaten/titel')))) +'](#'+self.anchors[n.get('doknr')]+')' for n in self.root if n.findtext('metadaten/enbez','')))
        self.add('<a id="dokumentkopf"></a>\n\n## Dokumentkopf')
        self.add(esc(short)+'\n\nAusfertigungsdatum: '+esc(c['ausfertigungsdatum']))
        self.add('**Vollzitat:**\n\n'+esc(c.get('vollzitat','')))
        self.add('**Stand und Bearbeitungshinweise:**\n\n'+'  \n'.join(esc(s) for s in c['stand']))
        self.level=3;sections=0
        for i,n in enumerate(self.root):
            m=n.find('metadaten');en=display_en(m.findtext('enbez',''));self.current=en
            g=m.find('gliederungseinheit')
            if g is not None:
                key=g.findtext('gliederungskennzahl','');depth=max(1,len(key)//3);sections+=1;self.level=min(6,depth+2)
                title=' '.join(self.checked(g.find(k),'Gliederung '+str(i)+' / '+k).replace('  \n',' ') for k in ['gliederungsbez','gliederungstitel'] if g.find(k) is not None)
                if en:
                    if title.strip() in {'-', '\\-'}:title=''
                    title += (' <span data-redaktionell="trennung-gliederung-vorschrift">/</span> ' if title else '')+esc(en)
                    if m.find('titel') is not None:
                        title += ' '+self.checked(m.find('titel'), en+' / Überschrift').replace('  \n',' ')
                level=2 if en.startswith(('Anlage','Anhang')) else (6 if en else min(5,depth+1))
                self.add('<a id="'+self.anchors[n.get('doknr')]+'"></a>\n\n'+'#'*level+' '+title)
            elif i>0:
                title=m.find('titel');t=self.checked(title,en+' / Überschrift').replace('  \n',' ') if title is not None else ''
                level=2 if en in {'Inhaltsübersicht','Inhaltsverzeichnis','Eingangsformel'} or en.startswith(('Anlage','Anhang')) else self.level
                self.add('<a id="'+self.anchors[n.get('doknr')]+'"></a>\n\n'+'#'*level+' '+esc(en)+(' '+t if t else ''))
            for kind in ['text','fussnoten']:
                container=n.find('textdaten/'+kind)
                if container is None:continue
                contents=list(container)
                assert all(x.tag in {'Content','Footnotes','TOC'} for x in contents), [x.tag for x in contents]
                for content in contents:
                    s=self.checked(content,(en or ('Dokumentkopf' if i==0 else 'Gliederung '+str(i)))+' / '+kind+' / '+content.tag)
                    if s:
                        if kind=='fussnoten':self.add('**Fußnote**')
                        self.add(s)
                if not contents and tidy(text_of(container)):
                    raise ValueError('Nicht abgeholter Containertext: '+str(i)+' '+kind)
        document='\n\n'.join(self.parts)+'\n'
        assert '\ufffd' not in document
        ids=re.findall(r'<a id="([^"]+)"',document)
        assert len(ids)==len(set(ids)), 'Doppelte Anker'
        links=re.findall(r'\]\(#([^)]*)\)',document)+re.findall(r'href="#([^"]+)"',document)
        assert set(links)<=set(ids),set(links)-set(ids)
        path=self.base/(short+'.md');path.write_text(document,encoding='utf-8',newline='\n')
        report={'kuerzel':short,'quellenabgleich':c['quellenabgleich'],'xml_normdatensaetze':len(self.root),'gliederungsteile':sections,'vorschriften':sum(tidy(n.findtext('metadaten/enbez','')).startswith(('§','Art.','Artikel')) for n in self.root),'anlagen_anhaenge':sum(tidy(n.findtext('metadaten/enbez','')).startswith(('Anlage','Anhang')) for n in self.root),'tabellen':len(list(self.root.iter('table'))),'tabellenzeilen':len(list(self.root.iter('row'))),'tabellenzellen':len(list(self.root.iter('entry'))),'aufzaehlungskennzeichnungen':len(list(self.root.iter('DT'))),'bilder':len(list(self.root.iter('IMG'))),'gepruefte_textbloecke':len(self.checks),'alle_textbloecke_identisch':all(x['identisch'] for x in self.checks),'interne_links':len(links),'alle_linkziele_vorhanden':True,'sha256_markdown':hashlib.sha256(path.read_bytes()).hexdigest(),'sha256_xml':hashlib.sha256(self.xml.read_bytes()).hexdigest(),'sha256_pdf':hashlib.sha256((self.base/'Quellen'/c['lokale_pdf']).read_bytes()).hexdigest(),'bildassets':self.assets,'methode':'Vollständiger XML-Text je Inhalt, Fußnote und Überschrift gegen aus Markdown gerenderten Text. Nur NFC/Whitespace, generische Spaltenköpfe und ausdrücklich redaktionelle Fußnotenmarker ausgenommen. Alle übrigen Zeichen und Zahlen unverändert.','bloecke':self.checks}
        report['vorschriften']=sum(display_en(n.findtext('metadaten/enbez','')).startswith(('§','Art.','Artikel')) for n in self.root)
        report['anlagen_anhaenge']=sum(display_en(n.findtext('metadaten/enbez','')).startswith(('Anlage','Anhang')) for n in self.root)
        report['fussnotenmarker_aus_quellattributen']=self.notes
        (self.base/'Pruefung/Vollstaendigkeitspruefung.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k not in {'bloecke','bildassets'}},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);args=p.parse_args();Converter(args.config).run()
