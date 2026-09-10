# Lesen aus dem GitHub-Repository

Repository: <https://github.com/juliangossen/wissensdatenbank-steuern>

Die Sammlung enthält `Bestand.json` mit Abkürzungen, Pfaden, Quellenständen und SHA-256-Prüfsummen sowie die vollständigen Markdown- und Originaldateien. Dieser Zugang benötigt kein Supabase-Konto. Es gibt im Repository keinen automatisch gestarteten Volltextserver.

## Python-Helfer

Verwende `scripts/github_recherche.py` relativ zum Ordner dieses Skills. Der Helfer benötigt Python 3 und nur die Standardbibliothek. Ermittle den tatsächlichen Skillpfad in der Umgebung; die folgenden Befehle setzen den Skillordner als Arbeitsverzeichnis voraus. In einer anderen Umgebung kann der vollständige Pfad zum Skript verwendet werden.

Nutze den verfügbaren Python-3-Interpreter: beispielsweise `python` oder `python3` in der Claude-Codeausführung und `py -3` unter Windows, falls `python` nur den Microsoft-Store-Alias startet. Eine Paketinstallation ist nicht nötig.

Zuerst die gewünschte Git-Fassung auflösen:

```text
python scripts/github_recherche.py resolve --ref main
```

Halte die ausgegebene vollständige Commit-SHA fest. Ersetze `COMMIT_SHA` in allen weiteren Befehlen durch diese Kennung. Eine vom Nutzer vorgegebene Fassung hat Vorrang. Die Auflösung von `main` erfolgt für eine neue Recherche erneut; nachfolgende Aufrufe bleiben an die festgehaltene SHA gebunden.

```text
python scripts/github_recherche.py catalog --commit COMMIT_SHA --offset 0 --limit 10
```

Der Katalog stammt aus `Bestand.json` genau dieses Commits. Verwende die ausgegebenen Dokumentabkürzungen; sie sind bei kombinierten Sammlungen beispielsweise länger als `EStR`.

`catalog --limit` erlaubt 1 bis 20 Einträge. Verwende den ausgegebenen `next_offset` für die nächste Katalogseite.

Suche in passenden Dokumenten:

```text
python scripts/github_recherche.py search --commit COMMIT_SHA --document UStG --document UStAE --query "Differenzbesteuerung" --limit 8
python scripts/github_recherche.py headings --commit COMMIT_SHA --document UStG --query "§ 25a" --limit 10
```

Die Suche lädt zunächst die vollständigen ausgewählten Markdown-Dateien und prüft ihre Rohbytes gegen `sha256_markdown` im Register. Es ist Wortsuche ohne deutsche Stammworterkennung, Vollbestand-Ranking oder semantisches Modell. Formuliere kurze Suchbegriffe, Varianten und Synonyme; wähle gegebenenfalls weitere Dokumente. `--mode all` beziehungsweise `--mode any` steuert die Verknüpfung der Suchwörter. Pro Suchaufruf sind höchstens fünf Dokumente vorgesehen.

Lies die relevante Textumgebung anhand des gelieferten `read_offset`:

```text
python scripts/github_recherche.py read --commit COMMIT_SHA --document UStG --offset 0 --limit 12000
```

Der Beispieloffset `0` liest den Dokumentanfang; ersetze ihn für einen Treffer durch dessen `read_offset`. Folge anschließend `next_offset`, solange die benötigte Fundstelle noch nicht vollständig gelesen wurde. Zeichenoffsets sind nullbasiert, Zeilennummern beginnen bei 1. Die Datei-Prüfsumme wird vor der UTF-8-Dekodierung geprüft; Zeilenenden werden nicht vereinheitlicht.

Ein Fenster enthält höchstens 12.000 Zeichen und 150 Zeilen. Die Ausgabe enthält sowohl den unveränderten `text` als auch `numbered_text` mit Zeilennummern. Bei gekürzter Werkzeugantwort dieselbe Seite mit einem kleineren `--limit`, etwa 4000, wiederholen; für die Fortsetzung ausschließlich `next_offset` aus einer vollständig erhaltenen Antwort verwenden.

Ein Suchtreffer oder eine gefundene Überschrift garantiert keinen vollständigen Normtext. Prüfe anhand des nachgeladenen Textes den tatsächlichen Beginn und das Ende der Vorschrift; gleichrangige Folgeüberschriften können beim Abgrenzen helfen. Unterabsätze, Unterüberschriften, Tabellen und zugehörige Fußnoten gehören weiterhin dazu. Fußnotendefinitionen können an anderer Stelle im Dokument liegen und sind gezielt nachzuladen. Wenn eine Gliederung nicht eindeutig ist, lies zusätzliche Umgebung oder benenne die verbleibende Grenze.

Der Helfer liefert Quellenmetadaten, Prüfsumme und unveränderliche GitHub-Links. Nutze die zurückgegebenen Links und Zeilenangaben zum Belegen der gelesenen Passage. Ein erfolgreicher Hashvergleich beweist die Übereinstimmung mit der registrierten Datei, nicht ihre rechtliche Aktualität oder Richtigkeit.

## Anlagen und andere Dateien

Markdown-Links können auf Original-PDFs, Abbildungen, Prüfberichte und gesonderte Ergänzungen zeigen. Löse relative Links gegen den Ordner der Markdown-Datei auf und halte denselben Commit fest. Öffne erforderliche Dateien mit verfügbaren GitHub-, Web- oder Dateiwerkzeugen. Der Helfer liefert registrierte Haupttexte; er rendert keine PDFs oder Bilder und ersetzt keine fachlich relevante Anlage durch Textvermutungen.

## Wenn die Codeausführung keine Verbindung erlaubt

Der Helfer verwendet ausschließlich das öffentliche Repository über HTTPS; benötigt werden `api.github.com` und `raw.githubusercontent.com`. Netzwerkzugriff kann in Claude durch Konto- oder Organisationseinstellungen gesperrt sein. Bei einem Zugriffsfehler keine erfundenen Suchergebnisse ausgeben.

Verwende dann, soweit verfügbar:

- den bestehenden Supabase-MCP gemäß [supabase.md](supabase.md), wobei ein Fassungswechsel kenntlich gemacht wird;
- einen GitHub-/Webzugang mit Abruf einzelner Dateien an einem festen Commit;
- bereits vorhandene Dateien eines lokalen Repository-Checkouts. Prüfe dessen Commit und mögliche lokale Änderungen, bevor du ihn als unveränderten Commit-Stand bezeichnest.

Beim direkten Lesen mit einem anderen Werkzeug dieselben Quellen- und Vollständigkeitsprüfungen anwenden. Wird der Inhalt gekürzt oder verändert zurückgegeben, behaupte keine Prüfung der Originalbytes. Fehlende Prüfmöglichkeiten offen benennen.

Die gewöhnliche GitHub-Verbindung von Claude übernimmt ausgewählte Dateien in den Kontext. Das Hinzufügen des Repository-Links allein bedeutet weder eine automatische Suche in sämtlichen Dokumenten noch eine sofortige Aktualisierung vorhandener Projektdateien. Für große Texte sind gezielte Abrufe erforderlich.
