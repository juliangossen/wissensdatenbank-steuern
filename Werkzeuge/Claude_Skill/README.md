# Claude-Skill für die Wissensdatenbank

Der Skill **steuerrecht-recherche** beschreibt, wie Claude die Sammlung systematisch durchsucht, entscheidende Fundstellen vollständig liest und Quellenstände sowie Grenzen der Belege berücksichtigt. Er nutzt die vorhandene Supabase-Verbindung oder liest direkt aus dem öffentlichen GitHub-Repository.

## In Claude installieren

1. [Skill-ZIP herunterladen](../../dist/steuerrecht-recherche.zip). Die ZIP-Datei enthält nur den Skill, seine Referenzen und den kleinen GitHub-Helfer; die Dokumente bleiben in GitHub beziehungsweise Supabase.
2. In Claude die **Codeausführung und Dateierstellung** einschalten. Je nach Konto können Organisationseinstellungen die Funktion einschränken.
3. **Customize / Anpassen → Skills → + → Create skill / Skill erstellen → Upload a skill / Skill hochladen** öffnen und die ZIP-Datei hochladen. Anschließend den Skill einschalten.
4. Für Supabase die bereits eingerichtete Verbindung im Chat aktivieren. Für den eigenständigen GitHub-Zugang benötigt die Codeausführung HTTPS-Zugriff auf `api.github.com` und `raw.githubusercontent.com`; ein Supabase-Konto oder GitHub-Token ist dafür nicht erforderlich.

Beispielfragen:

> Nutze steuerrecht-recherche. Prüfe den verfügbaren Bestand und schlage § 25a UStG nach. Lies die Fundstelle vollständig und nenne den dokumentierten Quellenstand.

> Nutze steuerrecht-recherche ausschließlich über GitHub. Ermittle den Commit und finde § 7 EStG. Belege die gelesene Fundstelle mit einem Link auf diese Fassung.

> Kann die gespeicherte Fassung der Mehrwertsteuersystemrichtlinie meine Frage zur heutigen Rechtslage belegen? Prüfe zuerst den Quellenstand.

Die Installation in deinem Claude-Konto ist ein eigener Schritt. Die lokale Paketprüfung und Tests mit echten Daten ersetzen keinen beobachteten Durchlauf in deiner Claude-Oberfläche. Die KI entscheidet anhand der Beschreibung über die Verwendung; mit dem Skillnamen in der Frage lässt sich die gewünschte Nutzung ausdrücklich machen.

## Supabase und GitHub

**Veröffentlichter Cloudbestand (14.09.2026):** 60 Dokumente in der Fassung `r-d3c4b6a7e0e2bb66a0693478`. Die beiden BFH-Webkopien sind in der Cloudsuche enthalten. [Importabschluss und Prüfnachweis](../BFH_Import_2026-09-14/Abschluss.md). Der GitHub-Zugang liest den jeweils veröffentlichten Repository-Commit; ein lokaler Quellenimport veröffentlicht diesen nicht automatisch.

| Zugang | Arbeitsweise | Voraussetzung |
| --- | --- | --- |
| Supabase | Deutsche Volltextsuche über den veröffentlichten Gesamtbestand, gezielte Normabfrage und vollständige Textfenster | Bestehender Supabase-MCP mit Lesezugriff |
| GitHub | Katalog aus `Bestand.json`, Wortsuche in ausgewählten vollständigen Markdown-Dateien, zeichenweise Seitenfortsetzung und Prüfsummenvergleich | Python 3 und Netzwerkzugriff auf die beiden GitHub-Domains oder andere geeignete Dateiwerkzeuge |

Der Skill hält für jede Recherche die konkrete Release-ID oder Commit-SHA fest. Unterschiedliche Fassungen werden nicht still vermischt. Die Quellen-Prüfsumme kann belegen, ob eine konkrete Markdown-Datei in GitHub und Supabase übereinstimmt. Aktives Release, Importdatum und Commitzeitpunkt sind keine Aussage über den rechtlichen Geltungszeitraum.

Die vorhandenen e5-Vektoren werden durch den Skill nicht um einen automatischen Dienst für Fragevektoren ergänzt. Die beiden genannten Zugänge verwenden ohne zusätzliches Modell keine semantische Suche. Ebenso führt der Skill keine tägliche Aktualisierung der Quellen durch.

Die normale GitHub-Integration von Claude übernimmt ausgewählte Dateien in den Kontext. Ein Repository-Link allein aktiviert keine Suche in allen 60 registrierten Dokumenten. Der mitgelieferte Helfer lädt die jeweils ausgewählten Dateien vollständig und prüft sie vor der Ausgabe gegen das Register. Bei gesperrtem Netzwerk kann der Supabase-MCP weiterhin verwendet werden, soweit er im Chat verfügbar ist.

## In Claude Code

Der Skill liegt direkt unter [`.claude/skills/steuerrecht-recherche/SKILL.md`](../../.claude/skills/steuerrecht-recherche/SKILL.md). Nach dem Klonen oder Aktualisieren dieses Repositorys kann Claude Code ihn als Projektskill verwenden; expliziter Aufruf: `/steuerrecht-recherche`. Es werden keine persönlichen Claude- oder Codex-Einstellungen überschrieben.

Der portable Skill verwendet nur `name` und `description` im YAML-Frontmatter. Er enthält keine speziell für Claude Code gedachten Ausführungsflags und keine Zugangsdaten. Der GitHub-Helfer verwendet ausschließlich die Python-Standardbibliothek. Eine Nutzung des Netzwerkhelfers in der Claude-API-Sandbox wird nicht zugesagt; dort gelten andere Netzwerkbeschränkungen.

## Pflegen und paketieren

Die gepflegte Fassung liegt im Skillordner unter `.claude/skills/`; Änderungen werden dort vorgenommen. Das ZIP wird aus diesen Dateien erstellt und auf Bytegleichheit geprüft:

```text
python Werkzeuge/Claude_Skill/paket_bauen.py
python -m unittest discover -s Werkzeuge/Claude_Skill -p "test_*.py"
```

Unter Windows kann statt `python` der Python-Launcher `py -3` verwendet werden; unter Linux gegebenenfalls `python3`.

Das Paket liegt anschließend unter `dist/steuerrecht-recherche.zip`; die SHA-256-Prüfsumme daneben. Python-Caches, Datenbankexporte und lokale Modelle gelangen nicht in das ZIP. Ein identischer Skillinhalt erzeugt ein identisches Archiv.

Bei Aktualisierungen das neue ZIP in Claude hochladen beziehungsweise den bestehenden Skill ersetzen. Das Hochladen eines Skillpakets verändert weder die Dokumente auf GitHub noch das aktive Supabase-Release.

[Prüfbericht](Pruefung.md)

## Verwendete Herstellerdokumentation

Geprüft am 10.09.2026:

- [Anthropic: Eigene Skills erstellen](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
- [Anthropic: Skills in Claude verwenden](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
- [Anthropic: Codeausführung und Netzwerkzugriff](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)
- [Anthropic: GitHub-Integration und manuelle Synchronisierung](https://support.claude.com/en/articles/10167454-use-the-github-integration)
- [Claude Code: Skills](https://code.claude.com/docs/en/skills)
- [Claude API: Skills und Laufzeitgrenzen](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
