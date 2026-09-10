# Prüfung des Claude-Skills

Geprüft am **10.09.2026**. Gepflegter Skill: [steuerrecht-recherche](../../.claude/skills/steuerrecht-recherche/SKILL.md). Installationspaket: [ZIP](../../dist/steuerrecht-recherche.zip).

## Ergebnis

Der Skill und sein GitHub-Helfer sind technisch geprüft. Die beiden vorgesehenen Datenzugänge wurden mit echten Quellen verwendet. Ein unabhängiger Agent hat den Rechercheablauf ausschließlich über das öffentliche GitHub-Repository nachvollzogen. Eine Installation oder ein Test in der persönlichen Claude-Oberfläche des Nutzers wurde nicht durchgeführt; dafür liegt das importierbare ZIP bereit.

| Prüfung | Ergebnis |
| --- | --- |
| Skillformat | `SKILL.md` mit gültigem Namen und präziser Beschreibung; struktureller Skill-Validator erfolgreich |
| Helfer | 15 automatisierte Tests erfolgreich; ausschließlich Python-Standardbibliothek |
| Originalbytes | UTF-8, CRLF und BOM vor Dekodierung korrekt gehasht; abweichende Dateien werden verworfen |
| Seitenfortsetzung | Lange Zeilen, Unicode-Zeichen, Seiten mit vielen Zeilen und letzte Zeilen ohne Umbruch verlustfrei rekonstruiert |
| Suche | Vollständige ausgewählte Dokumente durchsucht; Treffer am Dokumentende sowie stabile Trefferseiten geprüft |
| Ausfälle | Ungültige Commit-SHAs, unsichere Pfade, beschädigter Cache, fehlerhafte Register, blockiertes Netzwerk sowie zu große und unvollständige Antworten geprüft |
| GitHub live | Öffentlichen Commit aufgelöst, Katalog mit 58 Dokumenten gelesen; UStG § 25a gefunden und aus hashgeprüftem Originaltext gelesen |
| Supabase live | Alle sieben SQL-Beispiele der Skillreferenz mit dem separaten Leserlogin erfolgreich ausgeführt |
| Lange Cloud-Fundstellen | UStG § 25a: 5.122 Zeichen; UStAE 25a.1: 36.823 Zeichen über vier Fenster; EStG § 7: 12.522 Zeichen über zwei Fenster, jeweils vollständige SHA-256-Rekonstruktion |
| Vergleich der Zugänge | Markdown-Quellenprüfsummen aller 58 Dokumente im vorhandenen GitHub-Bestand stimmen mit dem aktiven Supabase-Release überein |
| Paket | Vier Dateien, vollständiger Ordner im ZIP, Bytegleichheit mit dem Skillordner und reproduzierbare Erstellung geprüft |
| Eigenständige Ausführung | ZIP außerhalb des Repositorys entpackt; Helfer dort ohne Repositorymodule ausgeführt; öffentlicher Katalog und UStG-Abruf erfolgreich |

Die GitHub-Liveprüfungen verwendeten den unveränderlichen Quellencommit `d5bf35baa89881ffc44d152da8b06db1e52874fb`. Der Supabase-Test verwendete `r-2ba1572b7978ca909270331f`. Der Skill selbst schreibt keine dieser Kennungen fest; er ermittelt den gewünschten Datenstand bei einer neuen Recherche erneut.

## Unabhängiger Rechercheprobelauf

Aufgabe an einen separaten Agenten ohne Gesprächsvorgeschichte:

> Nutze die Wissensdatenbank ausschließlich über GitHub. Finde § 7 EStG, lies die Vorschrift vollständig und belege den Quellenstand und den verwendeten Commit. Prüfe außerdem, ob die in dieser Repositoryfassung gespeicherte Mehrwertsteuersystemrichtlinie den heutigen Rechtsstand belegt.

Beobachtet:

- Der Agent hielt denselben Git-Commit durchgehend fest und verwendete keinen Supabase-Zugang oder lokalen Gesetzesbestand.
- EStG § 7 wurde ab Zeichenoffset 247.849 mit 12.000 Zeichen und anschließend ab 259.849 mit weiteren 1.000 Zeichen gelesen. Die Fundstelle einschließlich Tabellen und Anwendungsfußnote war vollständig sichtbar; die nachfolgende Überschrift § 7a diente der Abgrenzung.
- Der dokumentierte EStG-Quellenstand wurde genannt, ohne einen eigenen tagesaktuellen Abgleich zu behaupten.
- Die MwStSystRL wurde anhand des Dokumentkopfs und des öffentlichen Prüfberichts als ursprüngliche, nicht konsolidierte Amtsblattfassung erkannt. Der Import vom 09.09.2026 wurde nicht als aktueller Rechtsstand behandelt.
- Beide Haupttexte wurden vom Helfer gegen die SHA-256-Werte im Register geprüft.

Zwei Bedienhinweise aus dem Probelauf sind in der GitHub-Referenz ergänzt: `py -3` als Windows-Alternative zum Store-Alias `python` und die Katalogseitengröße von höchstens 20 Einträgen.

Dieser Probelauf prüft einen konkreten Rechercheablauf. Er ist kein Vergleich verschiedener Claude-Modelle, keine umfassende Bewertung steuerlicher Antwortqualität und kein Nachweis einer fehlerfreien automatischen Skillauswahl.

## Wiederholen und Nachweise

```text
python -m unittest discover -s Werkzeuge/Claude_Skill -p "test_*.py"
python Werkzeuge/Claude_Skill/paket_bauen.py
```

Unter Windows gegebenenfalls `py -3` verwenden.

- [Automatisierte Helfertests](test_github_recherche.py)
- [SQL- und Cloud-Leseprüfungen](Supabase_Pruefung.json)
- [Paket und eigenständiger GitHub-Probelauf](Paket_Pruefung.json)
- [ZIP-Prüfsumme](../../dist/steuerrecht-recherche.zip.sha256)

Die Tests verändern weder Quelldokumente noch Supabase-Daten. Code- und Dateitests ersetzen nicht die Prüfung des Sachverhalts und der passenden Rechtsfassung bei späteren Fachfragen.
