"""Alle XML-Bildvorkommen gegen die eingebetteten PDF-Bildvorkommen prüfen."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
import fitz
BASE=Path(__file__).resolve().parent.parent
C=json.loads((BASE/'Pruefung/konfiguration.json').read_text('utf8'))
XML=BASE/C['xml_datei'];R=ET.parse(XML).getroot()
def sha(data):return hashlib.sha256(data).hexdigest()
images=[{'xml_datei':(XML.parent/i.get('SRC')).relative_to(BASE).as_posix(),'sha256':sha((XML.parent/i.get('SRC')).read_bytes())} for i in R.iter('IMG')]
pdf=fitz.open(BASE/'Quellen'/C['lokale_pdf']);embedded=[]
for p in pdf:
 for image in p.get_image_info(xrefs=True):
  data=pdf.extract_image(image['xref'])
  assert pdf.xref_get_key(image['xref'],'Filter')==('name','/DCTDecode')
  embedded.append({'pdf_seite':p.number+1,'pdf_objekt':image['xref'],'sha256':sha(pdf.xref_stream_raw(image['xref'])),'breite':data['width'],'hoehe':data['height']})
assert len(embedded)==len(images)==20
for a,b in zip(images,embedded):assert a['sha256']==b['sha256'],(a,b)
report={'pdf_sha256':sha((BASE/'Quellen'/C['lokale_pdf']).read_bytes()),'xml_sha256':sha(XML.read_bytes()),'abbildungen':20,'alle_bildvorkommen_in_originalreihenfolge_bytegleich':True,'vergleich':[dict(a,**b) for a,b in zip(images,embedded)]}
(BASE/'Pruefung/Bildpruefung.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print('20 von 20 Abbildungen in Originalreihenfolge bytegleich zwischen PDF und XML-Paket.')
