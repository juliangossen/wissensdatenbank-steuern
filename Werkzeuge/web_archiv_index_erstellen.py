"""Prüft registrierte Webquellen und erzeugt die lesbaren Archivübersichten."""
from collections import defaultdict
from datetime import date
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "Web_Archiv"
INBOX = ARCHIVE / "01_Unbearbeitet"
DONE = ARCHIVE / "02_In_Markdown_umgewandelt"


def local_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Pfad außerhalb der Wissensdatenbank: {value}")
    return path


def escape(value):
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def link(label, target, base):
    relative = Path(os.path.relpath(target, base)).as_posix()
    return f"[{escape(label)}](<{relative}>)"


def write_readme(folder, parts):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "README.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def main():
    register = json.loads((ARCHIVE / "Archivregister.json").read_text(encoding="utf-8"))
    entries = register["eintraege"]
    versions = defaultdict(list)
    registered = set()
    for entry in entries:
        version = entry["archivversion"]
        if not version.startswith("Stand_"):
            raise ValueError(f"Ungültige Archivversion: {version}")
        date.fromisoformat(version.removeprefix("Stand_"))
        if entry["status"] != "in_markdown_umgewandelt":
            raise ValueError(f"Unbekannter Abschlussstatus: {entry['original_quelle']}")
        original = local_path(entry["original_quelle"])
        if not original.is_relative_to(DONE / version):
            raise ValueError(f"Original liegt nicht in seiner Archivversion: {original}")
        if original.name != entry["urspruenglicher_dateiname"] or original in registered:
            raise ValueError(f"Dateiname verändert oder doppelt registriert: {original}")
        registered.add(original)
        for field, hash_field in (("original_quelle", "sha256_original_quelle"), ("markdown", "sha256_markdown")):
            path = local_path(entry[field])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry[hash_field]:
                raise ValueError(f"Datei fehlt oder Prüfsumme weicht ab: {path}")
        if not local_path(entry["pruefbericht"]).is_file():
            raise ValueError(f"Prüfbericht fehlt: {entry['pruefbericht']}")
        versions[version].append(entry)
    actual = {path.resolve() for path in DONE.rglob("*") if path.is_file() and path.name != "README.md"}
    missing = registered - actual
    if missing:
        raise ValueError(f"Registrierte Archivquellen fehlen: {missing}")
    unregistered = sorted(actual - registered)

    pending = sorted({path.resolve() for path in INBOX.rglob("*") if path.is_file() and path.name != "README.md"}
                     | {path.resolve() for path in ROOT.glob("*.txt")})
    version_rows = ["| Erfassung / Quellenprüfung | In Markdown umgewandelt | Übersicht |", "| --- | ---: | --- |"]
    for version, documents in sorted(versions.items(), reverse=True):
        folder = DONE / version
        rows = ["| Rechtsgebiet | Originalquelle | Bearbeitungsstatus | Markdown-Dokument | Prüfung |",
                "| --- | --- | --- | --- | --- |"]
        for entry in sorted(documents, key=lambda x: (x["bereich"], x["urspruenglicher_dateiname"])):
            original_link = link(entry["urspruenglicher_dateiname"], local_path(entry["original_quelle"]), folder)
            md_link = link(entry["kuerzel"], local_path(entry["markdown"]), folder)
            proof_link = link("Prüfnachweis", local_path(entry["pruefbericht"]), folder)
            rows.append(f"| {escape(entry['bereich'])} | {original_link} | In Markdown umgewandelt | {md_link} | {proof_link} |")
        stamp = date.fromisoformat(version.removeprefix("Stand_")).strftime("%d.%m.%Y")
        parts = [
            f"# In Markdown umgewandelte Webquellen – Stand {stamp}",
            f"**{len(documents)} registrierte Webquellen in Markdown umgewandelt.** Die unveränderten Originale sind nach Rechtsgebiet und Dokument abgelegt. Die Tabelle verknüpft jede Quelle mit der strukturierten Fassung und ihrem Prüfnachweis.",
            "Das Standdatum bezeichnet die Erfassung beziehungsweise Quellenprüfung. Es bestätigt keine aktuelle amtliche Gesamtfassung. Der übernommene Quellenstand und die Grenzen der Ausgangskopie stehen im jeweiligen Dokument und Prüfnachweis.",
            "\n".join(rows),
            "## Quellenstand und Übertragungsumfang",
        ]
        for entry in sorted(documents, key=lambda x: x["kuerzel"]):
            parts.append(f"**{escape(entry['kuerzel'])}:** " + " ".join(entry["quellenstand"]) + "\n\n" + entry["vollstaendigkeit"])
        version_unregistered = [path for path in unregistered if path.is_relative_to(folder)]
        if version_unregistered:
            parts.extend([
                "## Offene Registrierungsbefunde",
                "Folgende Dateien liegen ebenfalls in diesem Archivordner, sind aber nicht im Archivregister eingetragen. Ihr Bearbeitungsstatus ist nicht bestätigt; sie gehören nicht zur Liste der registrierten Markdown-Dokumente.",
                "\n".join("- " + link(path.relative_to(folder).as_posix(), path, folder) for path in version_unregistered),
            ])
        parts.append(link("Zur Web-Archivübersicht", ARCHIVE / "README.md", folder))
        write_readme(folder, parts)
        version_rows.append(f"| {stamp} | {len(documents)} | {link(version, folder / 'README.md', DONE)} |")

    write_readme(DONE, [
        "# In Markdown umgewandelte Webquellen",
        "Hier liegen die registrierten Originalkopien von Webseiten nach Erfassung beziehungsweise Quellenprüfung und Rechtsgebiet. Die Versionsübersichten führen zu den strukturierten Markdown-Dokumenten und Prüfberichten.",
        "\n".join(version_rows),
        f"**Offene Registrierungsbefunde: {len(unregistered)} Dateien.** Zusätzliche, nicht registrierte Dateien sind in der Web-Archivübersicht gesondert aufgeführt; die Ablage allein bestätigt keinen Bearbeitungsstatus.",
        "Spätere Quellenstände erhalten einen eigenen datierten Ordner. Bereits archivierte Fassungen bleiben erhalten. Die dokumentierte Standangabe der Quelle gilt unabhängig vom Datum des Archivordners.",
        link("Zur Web-Archivübersicht", ARCHIVE / "README.md", DONE),
    ])
    inbox_parts = [
        "# Unbearbeitete Webquellen",
        "Neue Textkopien von Webseiten hier ablegen. Dieser Ordner ist der Eingang für Quellen, deren strukturierte Markdown-Übernahme und Prüfung noch ausstehen.",
        f"**Noch unbearbeitet: {len(pending)} Webquellen** (einschließlich gegebenenfalls im Hauptordner abgelegter TXT-Dateien).",
        "Nach der Umwandlung und Prüfung wird die Originaldatei unter `02_In_Markdown_umgewandelt/Stand_JJJJ-MM-TT/` im passenden Rechtsgebiet archiviert und mit Pfaden, Prüfsummen und Übertragungsumfang registriert. Eine Datei gilt nicht allein durch ihre Ablage als bearbeitet.",
        link("Zur Web-Archivübersicht", ARCHIVE / "README.md", INBOX),
    ]
    if pending:
        inbox_parts.insert(3, "\n".join("- " + link(path.name, path, INBOX) for path in pending))
    write_readme(INBOX, inbox_parts)
    overview = [
        "# Web-Archiv",
        f"**{len(entries)} Webquellen in Markdown umgewandelt · {len(pending)} Webquellen unbearbeitet.**",
        "| Ordner | Bedeutung |\n| --- | --- |\n"
        f"| {link('01_Unbearbeitet', INBOX / 'README.md', ARCHIVE)} | Neue Web- und Textquellen; Übernahme und Prüfung stehen noch aus. |\n"
        f"| {link('02_In_Markdown_umgewandelt', DONE / 'README.md', ARCHIVE)} | Registrierte Originalkopien mit Markdown-Dokument und Prüfnachweis. |",
        "## Abgeschlossene Fassungen",
        "\n".join(f"- {link(version, DONE / version / 'README.md', ARCHIVE)}: {len(documents)} Originalquellen mit Links zu Markdown-Dokumenten und Prüfberichten."
                  for version, documents in sorted(versions.items(), reverse=True)) or "Noch keine registrierten Fassungen.",
        "## Versionierung und Bearbeitungsstatus",
        "`Stand_JJJJ-MM-TT` bezeichnet die Erfassung beziehungsweise Quellenprüfung. Die ursprüngliche Standangabe der kopierten Quelle bleibt maßgeblich. Vollständige Übertragung einer gelieferten Textkopie und Vollständigkeit beziehungsweise Aktualität der amtlichen Gesamtfassung werden im Prüfnachweis getrennt behandelt.",
        "Die Originaldateien behalten ihre Dateinamen und Inhalte. Quellenkopien bei den Markdown-Dokumenten bleiben für Quellenverweise und reproduzierbare Prüfung erhalten. Spätere Fassungen werden separat archiviert.",
        "Die Übersicht wird aus dem " + link("Archivregister.json", ARCHIVE / "Archivregister.json", ARCHIVE)
        + " erzeugt. Das Register enthält Status, Version, Quellenstand, Übertragungsumfang, Dateipfade und SHA-256-Prüfsummen. Alle Registerpfade beziehen sich auf die Projektwurzel. Das Indexwerkzeug verschiebt keine Dateien und setzt keinen Bearbeitungsstatus automatisch.",
    ]
    if unregistered:
        overview.extend([
            "## Offene Registrierungsbefunde",
            f"**{len(unregistered)} zusätzliche Dateien im Ordner `02_In_Markdown_umgewandelt/` ohne Registereintrag.** Ihr Bearbeitungsstatus ist nicht bestätigt. Sie werden weder als abgeschlossene Dokumente gezählt noch durch diesen Index registriert.",
            "\n".join("- " + link(path.relative_to(ARCHIVE).as_posix(), path, ARCHIVE) for path in unregistered),
        ])
    overview.append(link("Zur Wissensdatenbank", ROOT / "README.md", ARCHIVE))
    write_readme(ARCHIVE, overview)
    print(json.dumps({"archivierte_webquellen": len(entries), "unbearbeitete_webquellen": len(pending),
                      "offene_registrierungsbefunde": [path.relative_to(ROOT).as_posix() for path in unregistered],
                      "versionen": sorted(versions), "pruefsummen": "Originalquellen und Markdown unverändert"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
