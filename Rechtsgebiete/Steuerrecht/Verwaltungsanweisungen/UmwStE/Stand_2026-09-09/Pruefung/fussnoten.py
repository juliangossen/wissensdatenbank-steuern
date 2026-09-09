"""Redaktionell erschlossene Zuordnung der 94 Fußnoten der UmwStE-2025-Webkopie.

Die Kopie enthält am Dateiende 94 Fußnotendefinitionen, im Text aber keinerlei Verweiszeichen:
Die Fußnotenmarker sind beim Kopieren entfernt worden; nur in Tabellenzellen blieben Leerzeichen-
reste (führende oder abschließende Leerzeichen, ein doppeltes Leerzeichen). Die Zuordnung unten ist
deshalb keine Information der Kopie, sondern aus vier Quellen erschlossen:

1. Die Fußnoten sind in Textreihenfolge nummeriert; die Reihenfolge der zitierten Verwaltungs-
   anweisungen (BMF-Schreiben, gleich lautende Ländererlasse) im Text entspricht der Reihenfolge der
   „BeckVerw“-Dokumentverknüpfungen. Jede BeckVerw-Nummer bezeichnet dabei durchgehend genau
   ein zitiertes Schreiben (56 Nennungen, 56 mit „BeckVerw“ beginnende Fußnoten einschließlich [1]
   zum Änderungsvermerk des Dokumentkopfs); das wird in pruefe_zuordnung() geprüft.
2. Die amtliche BMF-PDF vom 2.1.2025 (Quellen/Onlineabgleich) zeigt die Marker der amtlichen
   Fußnoten (Tabellen zu Rn. 01.10, 01.12, 01.17; COVID-Fristen; Residualgröße; VWG BsGa;
   DBA-Quellensteuerrecht; Verfassungsbeschwerde).
3. Leerzeichenreste in Tabellenzellen der Kopie (Zeilen 1429, 1513, 1549, 1561, 1609, 1699, 1749,
   1779, 1840, 2006, 2201, 2251, 2313, 2341, 2363, 2403, 3253, 3399, 3603).
4. Die Änderungsvermerke [54] und [90] nennen ihre Randnummer selbst; [1] gehört zum Änderungs-
   vermerk des Dokumentkopfs (dieselbe BeckVerw-Nummer 656140).

Felder je Eintrag: Nummer, Art, Randnummer (oder „Dokumentkopf“/„Einleitung“), Zeile der Kopie
(1-basiert) oder None, Prüftext (muss in der Zeile stehen, in Reihenfolge), Stelle, Grundlage.
Zeile None bei bekannter Randnummer: Bezugszelle in der Kopie nicht identifizierbar. Zeile und
Randnummer None: Bezugsstelle nicht bestimmbar (nur Intervall zwischen den Nachbarfußnoten).
"""
import re

RN = re.compile(r'^(?!31\.12)((?:\d{2}|E \d{2}|Org|K|S)\.\d{2}[a-z]?(?: bis 27\.11)?)')
BODY = 1353

# BeckVerw-Dokumentnummer -> zitiertes Schreiben (aus der Reihenfolge erschlossen, in sich konsistent).
BECKVERW = {
    '656140': 'BMF v. 1.8.2025 (Änderung des UmwStE 2025)', '026939': 'BMF-Schreiben vom 25.3.1998 (UmwStE 1998)',
    '090216': 'BMF-Schreiben vom 21.8.2001', '047231': 'BMF-Schreiben vom 16.12.2003',
    '254520': 'BMF-Schreiben vom 11.11.2011 (UmwStE 2011)', '563450': 'BMF-Schreiben vom 10.11.2021',
    '049718': 'BMF-Schreiben vom 19.3.2004 (LLC)', '289910': 'BMF-Schreiben vom 26.9.2014',
    '027468': 'BMF-Schreiben vom 24.12.1999', '336125': 'BMF-Schreiben vom 22.12.2016',
    '234104': 'BMF-Schreiben vom 18.1.2010', '250805': 'gleich lautende Ländererlasse vom 17.5.2011',
    '253360': 'BMF-Schreiben vom 22.9.2011', '632010': 'BMF-Schreiben vom 22.12.2023',
    '037552': 'BMF-Schreiben vom 28.5.2002', '449914': 'BMF-Schreiben vom 5.4.2019',
    '571335': 'BMF-Schreiben vom 7.6.2022', '109656': 'BMF-Schreiben vom 29.1.2008',
    '451400': 'BMF-Schreiben vom 21.5.2019', '349265': 'BMF-Schreiben vom 28.11.2017',
    '571340': 'BMF-Schreiben vom 15.6.2022', '334030': 'BMF-Schreiben vom 3.11.2016',
    '574870': 'BMF-Schreiben vom 29.9.2022', '124054': 'BMF-Schreiben vom 4.7.2008',
    '513780': 'BMF-Schreiben vom 18.3.2021', '251250': 'BMF-Schreiben vom 11.7.2011',
    '330547': 'BMF-Schreiben vom 26.7.2016', '032460': 'BMF-Schreiben vom 30.5.1997',
    '336120': 'BMF-Schreiben vom 19.12.2016', '618726': 'BMF-Schreiben vom 10.2.2023',
    '279515': 'BMF-Schreiben vom 27.11.2013',
}

AMTLICH = 'amtliche Anmerkung'
BECK = 'Dokumentverknüpfung des Anbieters (BeckVerw)'
RED = 'redaktionelle Anmerkung des Anbieters'
AEND = 'Änderungsvermerk des Anbieters'
PDF_TAB = 'Marker in der amtlichen PDF (Tabelle) und Leerzeichenrest in der Kopie'

ZUORDNUNG = [
    (1, AEND, 'Dokumentkopf', 7, 'BMF v. 1.8.2025', 'Änderungsvermerk „Geänd. durch BMF v. 1.8.2025 (BStBl. I S. 1591)“',
     'BeckVerw 656140 bezeichnet in [54] und [90] das Änderungsschreiben vom 1.8.2025.'),
    (2, AMTLICH, 'Einleitung', 9, 'vom 7.12.2006', 'SEStEG vom 7.12.2006', 'Fundstelle BStBl. 2007 I S. 4 des SEStEG; Zusatz der BStBl-Fassung, in der BMF-PDF nicht enthalten.'),
    (3, AMTLICH, 'Einleitung', 9, 'Jahressteuergesetz 2024', 'Jahressteuergesetz 2024 vom 2.12.2024', 'Fundstelle BStBl. I S. 1484 des JStG 2024; Zusatz der BStBl-Fassung.'),
    (4, AMTLICH, '00.01', 1356, 'Bekanntmachung vom 15.10.2002', 'UmwStG 1995 i.d.F. der Bekanntmachung vom 15.10.2002', 'Fundstellen BStBl. I S. 1157 und BStBl. 2003 I S. 380; Zusatz der BStBl-Fassung.'),
    (5, AMTLICH, '00.01', 1356, 'vom 7.12.2006', 'SEStEG vom 7.12.2006', 'Fundstelle BStBl. 2007 I S. 4; Zusatz der BStBl-Fassung.'),
    (6, BECK, '00.01', 1356, 'BMF-Schreiben vom 25.3.1998', None, '026939'),
    (7, BECK, '00.01', 1356, 'BMF-Schreiben vom 21.8.2001', None, '090216'),
    (8, BECK, '00.01', 1356, 'BMF-Schreiben vom 16.12.2003', None, '047231'),
    (9, BECK, '00.04a', 1366, 'BMF-Schreiben vom 11.11.2011', None, '254520'),
    (10, BECK, '01.02a', 1375, 'BMF-Schreiben vom 10.11.2021', None, '563450'),
    (11, AMTLICH, '01.10', 1429, 'eingetragene GbR ', 'Verschmelzungstabelle, Spaltenkopf „PershG/ PartG/ eingetragene GbR“ (Endleerzeichen)', 'PDF S. 11, Fußnote 1 am Spaltenkopf; ' + PDF_TAB),
    (12, AMTLICH, '01.10', 1513, ' §§ 2–38', 'Verschmelzungstabelle, Zelle „§§ 2–38“ (führendes Leerzeichen); nach PDF S. 11 Zeile „GmbH inkl. UG“, Spalte „nat. Person“', PDF_TAB),
    (13, AMTLICH, '01.10', 1549, ' §§ 2–38', 'Verschmelzungstabelle, Zelle „§§ 2–38“ (führendes Leerzeichen); nach PDF S. 11 Zeile „AG“, Spalte „AG“', PDF_TAB),
    (14, AMTLICH, '01.10', 1561, ' §§ 2–38', 'Verschmelzungstabelle, Zelle „§§ 2–38“ (führendes Leerzeichen); nach PDF S. 11 Zeile „AG“, Spalte „nat. Person“', PDF_TAB),
    (15, AMTLICH, '01.10', 1609, ' §§ 2–38', 'Verschmelzungstabelle, Zelle „§§ 2–38“ (führendes Leerzeichen); nach PDF S. 11 Zeile „KGaA“, Spalte „nat. Person“', PDF_TAB),
    (16, AMTLICH, '01.10', 1699, ' §§ 2–38', 'Verschmelzungstabelle, Zelle „§§ 2–38“ (führendes Leerzeichen); nach PDF S. 11 Zeile „eV/wirtsch. Verein“, Spalte „gen. Prüfungsverband“', PDF_TAB),
    (17, AMTLICH, '01.10', 1749, ' §§ 2–38', 'Verschmelzungstabelle, Zelle „§§ 2–38“ (führendes Leerzeichen); nach PDF S. 11 Zeile „gen. Prüfungsverband“, Spalte „gen. Prüfungsverband“ (siebte Zelle der Zeile in der Kopie)', PDF_TAB),
    (18, AMTLICH, '01.10', 1779, ' §§ 2–38', 'Verschmelzungstabelle, Zelle „§§ 2–38“ (führendes Leerzeichen); nach PDF S. 11 Zeile „VVaG“, Spalte „AG“', PDF_TAB),
    (19, AMTLICH, '01.12', 1840, '(eingetragene)  GbR', 'Formwechseltabelle, Spaltenkopf „PershG/PartG, (eingetragene) GbR“ (doppeltes Leerzeichen)', 'PDF S. 11, Fußnote 7 am Spaltenkopf; ' + PDF_TAB),
    (20, AMTLICH, '01.12', None, None, 'Formwechseltabelle, Strichzelle Zeile „GmbH inkl. UG“, Spalte „GmbH“ (PDF S. 11, Fußnote 8)', 'Marker in der amtlichen PDF; in der Kopie kein Leerzeichenrest, Zelle nicht identifizierbar.'),
    (21, AMTLICH, '01.12', None, None, 'Formwechseltabelle, Strichzelle Zeile „AG“, Spalte „AG“ (PDF S. 11, Fußnote 9)', 'Marker in der amtlichen PDF; in der Kopie kein Leerzeichenrest, Zelle nicht identifizierbar.'),
    (22, AMTLICH, '01.12', 2006, ' §§ 190–213', 'Formwechseltabelle, Zelle „§§ 190–213“ (führendes Leerzeichen); nach PDF S. 12 Zeile „VVaG“, Spalte „AG“', PDF_TAB),
    (23, AMTLICH, '01.17', 2201, ' §§ 123–137', 'Spaltungstabelle, Zelle „§§ 123–137“ (führendes Leerzeichen); nach PDF S. 12 Zeile „eV/wirtsch. Verein“, Spalte „eV“', PDF_TAB),
    (24, AMTLICH, '01.17', 2251, ' §§ 123–137', 'Spaltungstabelle, Zelle „§§ 123–137“ (führendes Leerzeichen); nach PDF S. 12 Zeile „gen. Prüfungsverband“, Spalte „gen. Prüfungsverband“', PDF_TAB),
    (25, AMTLICH, '01.17', 2313, ' §§ 123–137', 'Spaltungstabelle, Zelle „§§ 123–137“ (führendes Leerzeichen); nach PDF S. 12 Zeile „Einzelkaufmann“, Spalte „Eingetragene GbR/PershG/PartG“', PDF_TAB),
    (26, AMTLICH, '01.17', 2341, ' §§ 123–137', 'Spaltungstabelle, Zelle „§§ 123–137“ (führendes Leerzeichen); nach PDF S. 12 Zeile „Einzelkaufmann“, Spalte „eG“', PDF_TAB),
    (27, AMTLICH, '01.17', 2363, ' §§ 123–137', 'Spaltungstabelle, Zelle „§§ 123–137“ (führendes Leerzeichen); nach PDF S. 12 Zeile „Stiftungen“, Spalte „Eingetragene GbR/PershG/PartG“', PDF_TAB),
    (28, AMTLICH, '01.17', 2403, ' §§ 123–137', 'Spaltungstabelle, Zelle „§§ 123–137“ (führendes Leerzeichen); nach PDF S. 12 Zeile „Gebietskörpersch.“, Spalte „Eingetragene GbR/PershG/PartG“', PDF_TAB),
    (29, BECK, '01.27', 2630, 'vom 19.3.2004', None, '049718'),
    (30, BECK, '01.27', 2630, 'BMF-Schreiben vom 26.9.2014', None, '289910'),
    (31, BECK, '01.27', 2630, 'BMF-Schreibens vom 24.12.1999', None, '027468'),
    (32, BECK, '01.53', 2839, 'BMF-Schreiben vom 22.12.2016', None, '336125'),
    (33, AMTLICH, '02.03', 2880, 'zwölf Monate', 'Fristangabe „(für die Jahre 2020 und 2021: zwölf Monate)“', 'PDF S. 19, Fußnote 1 (COVID-19-Gesetz) an dieser Fristangabe.'),
    (34, AMTLICH, '02.06', 2917, 'zwölf Monate', 'Fristangabe „(für die Jahre 2020 und 2021: zwölf Monate)“', 'PDF S. 20, Fußnote 1 (COVID-19-Gesetz) an dieser Fristangabe.'),
    (35, BECK, '03.05', 3217, 'BMF-Schreiben vom 18.1.2010', None, '234104'),
    (36, BECK, '03.07', 3225, 'gleich lautenden Erlasse', None, '250805'),
    (37, BECK, '03.07', 3225, 'BMF-Schreiben vom 22.9.2011', None, '253360'),
    (38, AMTLICH, '03.09', 3253, '[2 000 000 €] ', 'Bilanzzelle „[2 000 000 €]“ (Endleerzeichen)', 'PDF S. 26, Anmerkung „Residualgröße“ an dieser Zelle; Leerzeichenrest in der Kopie.'),
    (39, BECK, '03.18', 3340, 'BMF-Schreibens vom 22.12.2023', None, '632010'),
    (40, AMTLICH, '03.20', 3358, '(VWG BsGa)', 'Kürzel „(VWG BsGa)“', 'PDF S. 28, Fußnote 1 am Kürzel VWG BsGa.'),
    (41, AMTLICH, '03.23', 3399, '[600 000 €] ', 'Bilanzzelle „[600 000 €]“ (Endleerzeichen)', 'PDF S. 28, Anmerkung „Residualgröße“ an dieser Zelle; Leerzeichenrest in der Kopie.'),
    (42, AMTLICH, '03.24', 3603, '[500 000 €] ', 'Bilanzzelle „[500 000 €]“ (Endleerzeichen)', 'PDF S. 29, Anmerkung „Residualgröße“ an dieser Zelle; Leerzeichenrest in der Kopie.'),
    (43, AMTLICH, '04.27', 4037, '30 000 €', 'Beispiel 1, Tabellenzelle „30 000 €“ (anzurechnende Kapitalertragsteuer, Spalte C) vor „Gesonderte und einheitliche Feststellung:“', 'PDF S. 34, Zeichen ❶ an dieser Zelle; kein Leerzeichenrest in der Kopie.'),
    (44, AMTLICH, '04.29', 4433, '30 000 €', 'Beispiel, Tabellenzelle „30 000 €“ (anzurechnende Kapitalertragsteuer, Spalte C) vor „Gesonderte und einheitliche Feststellung:“', 'PDF S. 36, Zeichen ❶ an dieser Zelle; kein Leerzeichenrest in der Kopie.'),
    (45, BECK, '04.34', 4696, 'BMF-Schreiben vom 18.1.2010', None, '234104'),
    (46, BECK, '06.01', 4776, 'BMF-Schreibens vom 28.5.2002', None, '037552'),
    (47, BECK, '06.03', 4784, 'BMF-Schreiben vom 5.4.2019', None, '449914'),
    (48, BECK, '06.03', 4784, 'BMF-Schreiben vom 7.6.2022', None, '571335'),
    (49, BECK, '06.06', 4791, 'BMF-Schreiben vom 29.1.2008', None, '109656'),
    (50, AMTLICH, '09.02', 4858, 'zwölf Monate', 'Fristangabe „(für die Jahre 2020 und 2021: zwölf Monate)“', 'PDF S. 42, Fußnote 1 (COVID-19-Gesetz) an dieser Fristangabe.'),
    (51, BECK, '11.01', 4866, 'BMF-Schreibens vom 21.5.2019', None, '451400'),
    (52, AMTLICH, '12.05', 4982, 'I R 58/12', 'Zitat „BFH-Urteil vom 30.7.2014 I R 58/12“', 'PDF S. 45, Fußnote 1 an diesem Zitat.'),
    (53, AMTLICH, '12.06', 4986, 'I R 58/12', 'Zitat „BFH-Urteil vom 30.7.2014 I R 58/12“', 'PDF S. 45, Fußnote 2 an diesem Zitat.'),
    (54, AEND, '15.35a', 5290, '15.35a ', 'Randnummer 15.35a', 'Der Änderungsvermerk nennt die Randnummer selbst.'),
    (55, BECK, '15.41', 5336, 'BMF-Schreiben vom 28.11.2017', None, '349265'),
    (56, BECK, '15.41', 5336, 'BMF-Schreibens vom 28.11.2017', None, '349265'),
    (57, BECK, '16.04', 5409, 'BMF-Schreibens vom 15.6.2022', None, '571340'),
    (58, BECK, '18.12', 5457, 'BMF-Schreiben vom 3.11.2016', None, '334030'),
    (59, RED, None, None, None, 'Berichtigte Fundstelle („Fälschlich im BStBl.: S. 22“); Bezugsstelle in der Kopie nicht bestimmbar', 'Nur das Intervall ist bekannt: zwischen [58] (Rn. 18.12, Zeile 5457) und [60] (Rn. 20.14, Zeile 5642). Die im BStBl fälschliche Angabe „S. 22“ kommt in der Kopie nicht vor.'),
    (60, AMTLICH, '20.14', 5642, 'zwölf Monate', 'Fristangabe „(für die Jahre 2020 und 2021: zwölf Monate)“', 'PDF S. 57, Fußnote 1 (COVID-19-Gesetz) an dieser Fristangabe.'),
    (61, BECK, '20.28', 5895, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (62, BECK, '20.28', 5895, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (63, BECK, '20.29', 5900, 'BMF-Schreiben vom 29.1.2008', None, '109656'),
    (64, BECK, '20.29', 5904, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (65, BECK, '20.29', 5904, 'BMF-Schreibens vom 25.3.1998', None, '026939'),
    (66, BECK, '20.31', 5908, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (67, BECK, '20.31', 5908, 'BMF-Schreibens vom 25.3.1998', None, '026939'),
    (68, BECK, '20.32', 5911, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (69, BECK, '20.32', 5931, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (70, BECK, '20.32', 5931, 'BMF-Schreibens vom 25.3.1998', None, '026939'),
    (71, BECK, '20.32', 5933, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (72, BECK, '20.33', 5937, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (73, BECK, '20.33', 5937, 'BMF-Schreibens vom 29.1.2008', None, '109656'),
    (74, BECK, '21.08', 5992, 'gleichlautenden Erlasse', None, '250805'),
    (75, BECK, '21.08', 5992, 'BMF-Schreiben vom 22.9.2011', None, '253360'),
    (76, BECK, '22.23', 6241, 'BMF-Schreibens vom 16.12.2003', None, '047231'),
    (77, BECK, '22.24', 6313, 'BMF-Schreiben vom 29.9.2022', None, '574870'),
    (78, BECK, '23.03', 6579, 'BMF-Schreiben vom 28.11.2017', None, '349265'),
    (79, BECK, '23.03', 6579, 'vom 4.7.2008', None, '124054'),
    (80, BECK, '23.03', 6579, 'BMF-Schreibens vom 18.3.2021', None, '513780'),
    (81, RED, '24.07', 6710, 'BFH vom 15.7.1976', 'Zitat „BFH vom 15.7.1976 I R 17/74“ (im BStBl fälschlich 15.6.1976)', 'Einzige Datumsangabe „15.7.1976“ zwischen [80] und [82]; die Anmerkung berichtigt das im BStBl gedruckte Datum.'),
    (82, BECK, '24.07', 6710, 'BMF-Schreiben vom 11.7.2011', None, '251250'),
    (83, BECK, '24.07', 6710, 'BMF-Schreiben vom 26.7.2016', None, '330547'),
    (84, BECK, '24.07', 6710, 'BMF-Schreiben vom 30.5.1997', None, '032460'),
    (85, BECK, '24.14', 6869, 'BMF-Schreibens vom 19.12.2016', None, '336120'),
    (86, BECK, '25.01', 6960, 'BMF-Schreiben vom 10.11.2021', None, '563450'),
    (87, BECK, '27.02', 6969, 'BMF-Schreibens vom 11.11.2011', None, '254520'),
    (88, BECK, 'S.01', 7006, 'BMF-Schreibens vom 25.3.1998', None, '026939'),
    (89, BECK, 'S.01', 7006, 'vom 25.3.1998, a.a.O.', None, '026939'),
    (90, AEND, 'Org.03', 7018, 'Org.03 ', 'Randnummer Org.03', 'Der Änderungsvermerk nennt die Randnummer selbst.'),
    (91, BECK, 'Org.27', 7089, 'BMF-Schreiben vom 10.2.2023', None, '618726'),
    (92, BECK, 'Org.31', 7105, 'BMF-Schreiben vom 27.11.2013', None, '279515'),
    (93, BECK, 'Org.35', 7115, 'BMF-Schreibens vom 11.11.2011', None, '254520'),
    (94, BECK, 'Org.35', 7115, 'BMF-Schreiben vom 29.9.2022', None, '574870'),
]


def eintraege(lines):
    """Prüft die Zuordnung gegen die Kopie und liefert sie als Liste von Wörterbüchern."""
    assert [entry[0] for entry in ZUORDNUNG] == list(range(1, 95))
    rn_of = {}
    current = None
    for index, line in enumerate(lines):
        match = RN.match(line) if index >= BODY else None
        if match:
            current = match[1]
        rn_of[index + 1] = current
    definitions = {}
    for index in range(len(lines)):
        match = re.fullmatch(r'\[(\d+)\] ', lines[index])
        if match:
            definitions[int(match[1])] = index + 1
    assert sorted(definitions) == list(range(1, 95))
    result = []
    cursor_line, cursor = None, 0
    used = {}
    for number, art, rn, zeile, pruefung, stelle, grundlage in ZUORDNUNG:
        text = lines[definitions[number]]
        entry = {'fussnote': number, 'definition_zeile': definitions[number], 'text': text.removesuffix('zurück zum Text'),
                 'art': art, 'randnummer': rn, 'zeile': zeile}
        if art == BECK:
            beckverw = re.fullmatch(r'BeckVerw (\d{6})\.zurück zum Text', text)[1]
            assert beckverw == grundlage, (number, beckverw, grundlage)
            date = re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', pruefung)
            used.setdefault(beckverw, set()).add(date[0] if date else 'gleich lautende Ländererlasse')
            entry['beckverw'] = beckverw
            entry['stelle'] = f'Zitat „{pruefung}“'
            entry['grundlage'] = f'Reihenfolge der Zitate; BeckVerw {beckverw} = {BECKVERW[beckverw]}.'
        else:
            entry['stelle'] = stelle
            entry['grundlage'] = grundlage
        if zeile is not None:
            assert pruefung is not None
            line = lines[zeile - 1]
            if cursor_line != zeile:
                cursor_line, cursor = zeile, 0
            position = line.find(pruefung, cursor)
            assert position >= 0, (number, zeile, pruefung)
            cursor = position + len(pruefung)
            if zeile > BODY:
                assert rn_of[zeile] == rn, (number, zeile, rn_of[zeile], rn)
            entry['status'] = 'erschlossen'
        elif rn is not None:
            entry['status'] = 'erschlossen_ohne_zelle'
        else:
            entry['status'] = 'offen'
        result.append(entry)
    # Reihenfolge: Bezugszeilen steigen mit der Fußnotennummer.
    known = [entry['zeile'] for entry in result if entry['zeile'] is not None]
    assert known == sorted(known)
    # Konsistenz: jede BeckVerw-Nummer bezeichnet genau ein Schreiben (Datum) und umgekehrt.
    for beckverw, dates in used.items():
        assert len(dates) == 1, (beckverw, dates)
    dates = {}
    for beckverw, values in used.items():
        date = next(iter(values))
        assert date not in dates, (date, beckverw, dates[date] if date in dates else None)
        dates[date] = beckverw
    assert set(used) == set(BECKVERW) - {'656140'}, set(used) ^ set(BECKVERW)   # 656140: Änderungsvermerk [1]
    return result
