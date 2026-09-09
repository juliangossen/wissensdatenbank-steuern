from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
import hashlib,json,re,requests
from concurrent.futures import ThreadPoolExecutor

HERE=Path(__file__).resolve().parent
BASE='https://amtliche-handbuecher.bundesfinanzministerium.de/'
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.images=[]; self.current=None; self.text=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='a': self.current=[d.get('href',''),'']
        if tag=='img':self.images.append(d)
    def handle_data(self,data):
        self.text.append(data)
        if self.current is not None:self.current[1]+=data
    def handle_endtag(self,tag):
        if tag=='a' and self.current is not None:self.links.append(self.current);self.current=None

def save(name,url):
    r=requests.get(url,timeout=45,headers={'User-Agent':'Mozilla/5.0'});r.raise_for_status()
    if 'text/html' in r.headers.get('Content-Type','') and '<title>Radware Page</title>' in r.text:raise ValueError('Kein Sachinhalt: '+url)
    p=HERE/name;p.write_bytes(r.content)
    return {'url':url,'endgueltige_url':r.url,'datei':name,'sha256':hashlib.sha256(r.content).hexdigest(),'bytes':len(r.content),'content_type':r.headers.get('Content-Type','')}

if __name__=='__main__':
    entries=[]
    pages=[('EStH_2025_Vorwort.html',BASE+'esth/2025/Vorwort/inhalt.html'),('EStH_2025_Inhaltsverzeichnis.html',BASE+'esth/2025/Meta/Inhaltsverzeichnis/inhalt.html'),('EStH_2025_Anhang_37_I.html',BASE+'esth/2025/B-Anhaenge/Anhang-37/I/inhalt.html'),('EStH_2019_Anhang_37_I.html',BASE+'esth/2019/C-Anhaenge/Anhang-37/I/inhalt.html'),('EStH_2025_Anhang_12_II_1.html',BASE+'esth/2025/B-Anhaenge/Anhang-12/II-1/inhalt.html'),('EStH_2025_Paragraf_1.html',BASE+'esth/2025/A-Einkommensteuergesetz/I-Steuerpflicht-1-1a/Paragraf-1/inhalt.html'),('EStH_2025_Paragraf_1a.html',BASE+'esth/2025/A-Einkommensteuergesetz/I-Steuerpflicht-1-1a/Paragraf-1a/inhalt.html'),('EStH_2025_Paragraf_4.html',BASE+'esth/2025/A-Einkommensteuergesetz/II-Einkommen-2-24b/3-Gewinn-4-7i/Paragraf-4/inhalt.html'),('EStH_2025_Anhang_01_I_2.html',BASE+'esth/2025/B-Anhaenge/Anhang-01/I-2/inhalt.html')]
    for name,url in pages:
        info=save(name,url);entries.append(info)
        p=Parser();p.feed((HERE/name).read_text(encoding='utf-8'))
        print(name,len((HERE/name).read_bytes()))
        if 'Inhaltsverzeichnis' in name:
            print(json.dumps([(t,urljoin(BASE,l)) for l,t in p.links if 'Berichtigung des Gewinns' in t],ensure_ascii=False))
    entries.append(save('EStH_2025_R_4_6_Anlage.html',BASE+'esth/2025/A-Einkommensteuergesetz/II-Einkommen-2-24b/3-Gewinn-4-7i/Paragraf-4/r-4-6-anlage.html'))
    p=Parser();p.feed((HERE/'EStH_2019_Anhang_37_I.html').read_text(encoding='utf-8'))
    assets=[]
    for l,t in p.links:
        m=re.search(r'/anlage(\d+)\.(jpg|pdf)',l)
        if m:assets.append(('Muster_'+m.group(1).zfill(2)+'_EStH_2019.'+m.group(2),urljoin(BASE,l)))
    with ThreadPoolExecutor(4) as pool:
        for info in pool.map(lambda a:save(*a),assets):entries.append(info);print(info['datei'],info['bytes'])
    (HERE/'Abrufe.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
