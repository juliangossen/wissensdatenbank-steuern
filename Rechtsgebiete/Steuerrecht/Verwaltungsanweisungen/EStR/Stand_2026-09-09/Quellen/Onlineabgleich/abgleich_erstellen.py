from pathlib import Path
import hashlib,json,re

HERE=Path(__file__).resolve().parent
DATE='2026-09-09'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads((HERE/'Abrufe.json').read_text(encoding='utf-8'))
for e in data:
    assert sha(HERE/e['datei'])==e['sha256']
    e['titel']=e['datei'].replace('_',' ').rsplit('.',1)[0]
    e['datei']='Quellen/Onlineabgleich/'+e['datei']
    e['abrufdatum']=DATE
assets=json.loads((HERE/'Abbildungen.json').read_text(encoding='utf-8'))
supp=json.loads((HERE/'Ergaenzungen.json').read_text(encoding='utf-8'))
for e in assets+supp:assert sha(HERE.parent.parent/e['datei'])==e['sha256']
result={
    'abgleichdatum':DATE,
    'pfadbasis':'Versionsordner EStR/Stand_2026-09-09',
    'gegenstand':'Einkommensteuer-Richtlinien 2012 mit den Einkommensteuer-Hinweisen 2025 und den in der Webkopie enthaltenen Anlagen 1 bis 6',
    'metadaten':{
        'richtlinien':'Einkommensteuer-Richtlinien 2005 vom 16.12.2005 (BStBl I 2005 Sondernummer 1/2005), geändert durch EStÄR 2008 vom 18.12.2008 (BStBl I S. 1017) und EStÄR 2012 vom 25.03.2013 (BStBl I S. 276); in der Webkopie bezeichnet als EStR 2012',
        'richtlinien_fassung_amtlich_bestaetigt':True,
        'richtlinien_nachweis':'EStH 2025 Vorwort, Berücksichtigte Vorschriften, Nr. 3',
        'hinweise':'Einkommensteuer-Hinweise für den VZ 2025; amtliches EStH 2025 bestätigt diesen Anwendungszeitraum',
        'redaktionsschluss_laut_webkopie':'20.01.2026 (höchstrichterliche Rechtsprechung und BMF-Schreiben)',
        'redaktionsschluss_online_bestaetigt':False,
        'redaktionsschluss_einschraenkung':'Im gespeicherten amtlichen Online-Vorwort wird kein konkretes Redaktionsschlussdatum genannt. 20.01.2026 bleibt eine Angabe der gelieferten Webkopie.',
        'archivdatum_ist_keine_rechtsstandgarantie':True,
        'anlagen_kopie':'Anlagen 1 bis 6; 3 und 5 ausdrücklich nicht belegt. Für die Anlagen 2 und 6 ist kein eigenes Quellenstanddatum in der Kopie angegeben.'
    },
    'umfang':{
        'textgrundlage':'Benutzerdatei EStR 2012.txt; Quellenkopie wird unverändert erhalten.',
        'nicht_enthalten':'Das vollständige Amtliche EStH 2025 einschließlich EStG, EStDV und sämtlichen Anhängen ist nicht Gegenstand dieser gelieferten Datei.',
        'vollstaendiger_amtlicher_wortlautabgleich':False,
        'strukturpruefung':'Titel/Fassung, Beginn R 1 und H 1a, Schluss Anlage 6 sowie bezeichnete Anlagen/Muster geprüft. Das amtliche Inhaltsverzeichnis wurde als Vergleichsquelle gesichert; es zeigt nur belegte Richtlinien und enthält nicht sämtliche unbesetzten Positionen der Webkopie.',
        'h1a':'Die amtliche Seite zu § 1 enthält R 1 und keine H 1. Die amtliche Seite zu § 1a enthält H 1a und beginnt mit Allgemeines/Auslandskorrespondenten. Diese Gliederung entspricht insoweit der Kopie.',
        'schluss':'Die amtliche Liste in EStH 2025 Anhang 12 II 1 endet ebenfalls mit Uganda und withholding tax (Quellensteuer für Beratungsleistungen (15 %); an dieser Stelle ist kein Abbruch der Kopie erkennbar.'
    },
    'abweichungen':[
        {'stelle':'Anlage 2, historische erste Tabellenposition und Nummerierung','webkopie':'Nr. 1: Fertigstellung nach dem 9.10.1962 und vor dem 1.1.1965 und Bauantrag nach dem 9.10.1962. Nr. 2 beginnt mit Fertigstellung nach dem 31.12.1964 und vor dem 1.9.1977 und Bauantrag vor dem 9.5.1973.','amtlich_2025':'Die historische Nr. 1 der Kopie ist nicht enthalten. Die amtliche Nr. 1 entspricht der Position Nr. 2 der Webkopie; dies ist keine abweichende Datumsangabe zur gleichen Tabellenposition.','behandlung':'Kopie unverändert; gesonderte amtliche Vergleichsfassung 2025 mit abweichender Nummerierung beigefügt.'},
        {'stelle':'Anlage 2, Tabellenumfang','webkopie':'Übersicht nach § 7 Abs. 5 EStG, Nummern 1 bis 11; Nr. 11 betrifft Bauantrag oder obligatorischen Vertrag nach dem 31.12.2003 und vor dem 1.1.2006.','amtlich_2025':'Übersicht nach § 7 Abs. 5 und 5a EStG, ebenfalls Nummern 1 bis 11, aber mit anderer Zuordnung: Nr. 10 betrifft die Position Nr. 11 der Kopie; amtliche Nr. 11 betrifft Herstellungsbeginn oder obligatorischen Vertrag nach dem 30.09.2023 und vor dem 01.10.2029 und hat keine entsprechende Position in der Kopie.','behandlung':'Keine unmarkierte Aktualisierung der kopierten Anlage; gesonderte Ergänzung.'},
        {'stelle':'Anlage 6, Länder/Gebiete','webkopie':'Andorra und Malediven sind nicht als Länderpositionen enthalten. Die Kopie nennt kein eigenes Standdatum.','amtlich_2025':'Anhang 12 II 1 mit Stand 1.1.2025 enthält Andorra und Malediven, insgesamt 79 Länder-/Gebietspositionen.','behandlung':'Gesonderte amtliche Liste 2025 mit vollständig geprüftem sichtbaren Tabellentext beigefügt. Keine vollständige Gleichheit der beiden Listen behauptet.'},
        {'stelle':'H 1a, Stichwort DBA, TXT-Zeile 83','webkopie':'BMF vom 20.01.2025 (BStBl. I 2026 S. 291); Fußnote der Kopie verweist auf BStBl I 2025 S. 291.','amtlich_2025':'BMF vom 20.01.2025 (BStBl I S. 291), Stand 01.01.2025','behandlung':'Abweichende Fundstellendarstellung dokumentiert, keine stille Änderung.'}
    ],
    'formularergaenzung':{
        'begruendung':'Die Webkopie führt 18 Muster mit Bildunterschriften auf, enthält aber nicht die Formularabbildungen. Das amtliche EStH 2025 Anhang 37 I verweist auf den letztmaligen Abdruck der Anlagen 1 bis 18 im EStH 2019.',
        'stand':'BMF-Schreiben vom 07.11.2013 (BStBl I S. 1333), ergänzt am 26.03.2014 (BStBl I S. 791), wie in der Kopie bezeichnet; Bildwiedergabe aus amtlicher Ausgabe 2019',
        'muster':18,
        'abbildungsseiten':24,
        'quellformate':'Muster 1 bis 12: unveränderte amtliche JPEG-Dateien; Muster 13 bis 18: jeweils zweitseitiges amtliches PDF, zu PNG gerendert.',
        'besonderheit':'Die Kopie hat für Muster 15 nur eine Bildunterschrift; beide amtlichen PDF-Seiten werden dort zugeordnet.',
        'pruefung':'Alle Bilddateien geöffnet/auf Integrität geprüft; 24 Abbildungsseiten in zwei Kontaktbögen auf Vollständigkeit, Zuordnung und nicht abgeschnittene Felder visuell geprüft.'
    },
    'quellen':data,
    'abbildungen':assets,
    'ergaenzungen':supp,
    'einschraenkungen':[
        'Keine Bestätigung, dass jede redaktionelle Fußnote der Webkopie oder jede darin zitierte Fundstelle amtlich ist.',
        'Keine Behauptung einer Vollwortidentität der gesamten Webkopie mit dem Amtlichen Einkommensteuer-Handbuch 2025.',
        'Die Hinweise 2025, die Richtlinienfassung 2013, die Formularwiedergaben 2013/2014 aus EStH 2019 und die Anlagen der Webkopie sind als verschiedene Quellenstände zu unterscheiden.'
    ]
}
(HERE/'Abgleich.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'quellen':len(data),'abbildungen':len(assets),'ergaenzungen':len(supp)},ensure_ascii=False))
