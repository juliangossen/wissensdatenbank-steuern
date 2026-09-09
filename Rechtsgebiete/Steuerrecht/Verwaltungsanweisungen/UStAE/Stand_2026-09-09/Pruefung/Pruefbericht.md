# Prüfbericht: UStAE-Webkopie nach Markdown

Quelle: vom Nutzer bereitgestellte Datei `UStAE.txt`, UTF-8, 27.139 Zeilen. Die Kopfzeilen nennen beck-online und den Stand 02.06.2026. Die unveränderte Quelle liegt unter [Quellen/UStAE_Webkopie.txt](../Quellen/UStAE_Webkopie.txt); zusätzlich wird sie im versionierten Web-Archiv geführt.

## Umfang und Übernahme

Alle 14.835 nichtleeren Sachtextzeilen von Zeile 293 bis 27.139 werden genau einmal übernommen. 9.837 Quellblöcke ordnen Originalzeilen den Zieldateien zu. Jeder Block wird als Markdown gerendert; der sichtbare Text muss nach Entfernung ausschließlich von Leerraum vollständig mit dem Original übereinstimmen. Buchstaben, Zahlen, Satzzeichen und vorhandene weiche Trennzeichen bleiben unverändert. Die Website-Navigation in Zeilen 1–292 bleibt in der Originaldatei erhalten und wird nicht in den Erlasstext aufgenommen.

Die strukturierte Hauptdatei enthält Einleitung, Inhaltsübersicht, 171 Abkürzungen, 428 im kopierten Erlasstext vorhandene Abschnittsblöcke und acht Anlagen. Die redaktionelle Synopse wird in einer gesonderten Markdown-Datei erhalten. Zusammen entsprechen die 427 Einzelabschnitte, die vier zusammengefasst aufgehobenen Abschnitte 23.1–23.4 und die ergänzte gestrichene Position 25d.1 den 432 amtlichen Abschnittspositionen.

Alle 829 Fußnotenverweise haben genau eine zugehörige Definition. Die Definition wird jeweils anhand der nächsten folgenden Definition derselben Nummer bestimmt; die Zuordnung ist bijektiv. Anker verwenden die ursprüngliche Zeilennummer und bleiben deshalb trotz wiederholter Fußnotennummern eindeutig. Die Quelle kennzeichnet nur zwei Anmerkungen ausdrücklich als amtlich; andere Anmerkungen werden nicht als amtlicher Erlasstext ausgegeben.

## Amtlicher Abgleich und ergänzte Inhalte

Die [amtliche BMF-PDF](../Quellen/Onlineabgleich/UStAE_BMF_Stand_2026-06-02.pdf) nennt denselben Stand 2. Juni 2026. Ihre Gliederung umfasst 432 Abschnittspositionen und acht Anlagen. Quellenadresse, Prüfsumme und Seitenzuordnung stehen im [Abgleich](../Quellen/Onlineabgleich/Abgleich.json).

- `4.4c.1` ist im kopierten Inhaltsverzeichnis doppelt enthalten. Beide Quellangaben bleiben erhalten und verlinken auf denselben Abschnitt.
- `25d.1` fehlt im kopierten Erlasstext. Die amtliche Seite 849 enthält nur „25d.1. - gestrichen -“. Dieser Hinweis wird ausdrücklich als amtliche Ergänzung aufgenommen.
- 23 Schaubilder in 3.14, 3.15 und 25b.1 fehlen als Bilder in der Textkopie. Vollständige amtliche Seitendarstellungen dieser Abschnitte ergänzen sie.
- Die Formulare der Anlagen 1–5 und 7 fehlen in der Textkopie; die Anlagen 6 und 8 enthalten abgeflachte Tabellen. Alle acht Anlagen werden durch 16 vollständige amtliche Seitenbilder gesichert. Zusammen mit den 19 Haupttextseiten sind 35 PNGs eingebunden und visuell geprüft.

Die Sprachentabelle der Anlage 8 ist mit 23 Sprachzeilen und sieben Spalten rekonstruiert. Die amtlichen Seiten wurden dafür visuell geprüft: Der einzige gälische Begriff steht in der Spalte zur Steuerschuldnerschaft; die beiden kroatischen Alternativen samt „oder“ gehören gemeinsam in dieselbe Spalte. Alle Texte bleiben im zeichengetreuen Rückvergleich enthalten.

Die Bildseiten werden als Ergänzungen gekennzeichnet und nicht als kopierter Text mitgezählt. Sie können überlappenden Begleittext enthalten. Die amtliche Anlage 7 liegt selbst als Scan begrenzter Auflösung vor.

## Wiederholbare Prüfung

Aus der Projektwurzel:

```powershell
py -B Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/UStAE/Stand_2026-09-09/Pruefung/konvertieren.py
py -B Rechtsgebiete/Steuerrecht/Verwaltungsanweisungen/UStAE/Stand_2026-09-09/Pruefung/pruefen.py
```

[Vollstaendigkeitspruefung.json](Vollstaendigkeitspruefung.json) enthält Quell- und Zielprüfsummen; [Quellbloecke.json](Quellbloecke.json) dokumentiert sämtliche Zeilenbereiche. Die unabhängige Leseprüfung kontrolliert die gespeicherten Dateien erneut, einschließlich lokaler Fußnotenanker, Links, eingebundener Abbildungen und Prüfsummen.

## Grenze des Nachweises

Nachgewiesen ist die vollständige Übernahme der bereitgestellten Sachtexte sowie der amtliche Stand- und Strukturabgleich mit gekennzeichneten Ergänzungen. Ein vollständiger Wortlautvergleich der Webkopie mit der amtlichen PDF wird nicht behauptet. Verlorene Hochstellungen, Spaltenzuordnungen, Schreibweisen und sonstige mögliche Kopierfehler werden nicht durch vermutete Korrekturen ersetzt.
