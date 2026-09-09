# EGBGB: Sichtprüfung der Tabellenfortsetzungen

Geprüft am 09.09.2026 anhand von Poppler-Renderbildern der bereitgestellten PDF, Seiten 111–112 und 116–117. Gegenstand sind die zwei im PDF/XML-Abgleich dokumentierten Abweichungen der Lesereihenfolge.

**Anlage 4:** Die linke Formularzelle beginnt auf Seite 111 mit Kreditgeber, Anschrift, Telefon und E-Mail. Die zugehörige rechte Zelle enthält bereits auf dieser Seite die Felder für Name und ladungsfähige Anschrift. Die linke Zelle setzt sich auf Seite 112 mit „Fax*)“ und „Internet-Adresse*)“ fort. Die PDF-Textextraktion liest diese Fortsetzung deshalb nach dem Inhalt der rechten Zelle. Die XML-Zellreihenfolge hält die gesamte linke Zelle zusammen. Sichtbar sind keine fehlenden Wörter, sondern ein Seitenumbruch innerhalb derselben Tabellenzeile.

**Anlage 5:** Die Kontaktzelle im Abschnitt über Fernabsatz beginnt auf Seite 116 und reicht bis „Fax*)“. Auf Seite 117 folgen in derselben linken Zelle „Internet-Adresse*)“ und „*) Freiwillige Angaben des Kreditgebers.“. Name und Anschrift in der rechten Zelle stehen bereits auf Seite 116. Die Verschiebung im extrahierten Text ist daher ebenfalls durch den Seitenumbruch belegt. Die Markdown-Tabelle muss diese Beschriftungen weiterhin der linken Zelle zuordnen.

Ergebnis: Die im maschinellen Abgleich bezeichneten Textblöcke sind vollständig vorhanden und den dokumentierten Tabellenzellen zuzuordnen. Der vollständige Textvergleich außerhalb dieser beiden ausdrücklich abgegrenzten Umordnungen wird separat maschinell geführt.

[Seite 111](EGBGB_111.png) · [Seite 112](EGBGB_112.png) · [Seite 116](EGBGB_116.png) · [Seite 117](EGBGB_117.png).
