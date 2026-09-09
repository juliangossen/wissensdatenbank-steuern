"""Prüft das PDF-Archiv und erzeugt seine lesbaren Übersichten."""
from collections import defaultdict
from datetime import date
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "PDF_Archiv"
INBOX = ARCHIVE / "01_Unbearbeitet"
DONE = ARCHIVE / "02_In_Markdown_umgewandelt"


def local_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Pfad außerhalb der Wissensdatenbank: {value}")
    return path


def link(label, target, base):
    relative = Path(os.path.relpath(target, base)).as_posix()
    return f"[{label}](<{relative}>)"


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
        date.fromisoformat(version.removeprefix("Stand_"))
        if version != "Stand_" + entry["quellenabgleich"]:
            raise ValueError(f"Version und Quellenabgleich abweichend: {entry['pdf']}")
        if entry["status"] != "in_markdown_umgewandelt":
            raise ValueError(f"Unbekannter Abschlussstatus: {entry['pdf']}")
        pdf = local_path(entry["pdf"])
        if not pdf.is_relative_to(DONE / version):
            raise ValueError(f"PDF liegt nicht in ihrer Archivversion: {pdf}")
        if pdf.name != entry["urspruenglicher_dateiname"] or pdf in registered:
            raise ValueError(f"Dateiname verändert oder doppelt registriert: {pdf}")
        registered.add(pdf)
        for field, hash_field in (("pdf", "sha256_pdf"), ("markdown", "sha256_markdown")):
            path = local_path(entry[field])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry[hash_field]:
                raise ValueError(f"Datei fehlt oder Prüfsumme weicht ab: {path}")
        if not local_path(entry["pruefbericht"]).is_file():
            raise ValueError(f"Prüfbericht fehlt: {entry['pruefbericht']}")
        versions[version].append(entry)
    actual = {path.resolve() for path in DONE.rglob("*.pdf")}
    if actual != registered:
        raise ValueError(f"Archiv und Register weichen ab: {actual.symmetric_difference(registered)}")

    pending = sorted(INBOX.rglob("*.pdf")) + sorted(ROOT.glob("*.pdf"))
    version_rows = ["| Quellenabgleich | In Markdown umgewandelt | Übersicht |", "| --- | ---: | --- |"]
    for version, documents in sorted(versions.items(), reverse=True):
        folder = DONE / version
        rows = ["| Rechtsgebiet | Original-PDF | Bearbeitungsstatus | Markdown-Volltext | Prüfung |",
                "| --- | --- | --- | --- | --- |"]
        for entry in sorted(documents, key=lambda x: (x["bereich"], x["urspruenglicher_dateiname"])):
            pdf_link = link(entry["urspruenglicher_dateiname"], local_path(entry["pdf"]), folder)
            md_link = link(entry["kuerzel"], local_path(entry["markdown"]), folder)
            proof_link = link("Prüfnachweis", local_path(entry["pruefbericht"]), folder)
            rows.append(f"| {entry['bereich']} | {pdf_link} | In Markdown umgewandelt | {md_link} | {proof_link} |")
        stamp = date.fromisoformat(version.removeprefix("Stand_")).strftime("%d.%m.%Y")
        write_readme(folder, [
            f"# In Markdown umgewandelte PDFs – Stand {stamp}",
            f"**{len(documents)} PDFs vollständig in Markdown umgewandelt.** Die Originale sind nach Rechtsgebiet sortiert. Jede Zeile führt von der PDF zum zugehörigen Markdown-Volltext und Prüfnachweis.",
            "Das Standdatum bezeichnet den Quellenabgleich. Der rechtliche Änderungsstand steht im jeweiligen Markdown-Dokument. Die Dateinamen und PDF-Inhalte sind unverändert; die Zuordnung und Prüfsummen wurden gegen das Archivregister geprüft.",
            "\n".join(rows),
            link("Zur PDF-Archivübersicht", ARCHIVE / "README.md", folder),
        ])
        version_rows.append(f"| {stamp} | {len(documents)} | {link(version, folder / 'README.md', DONE)} |")

    write_readme(DONE, [
        "# In Markdown umgewandelte PDFs",
        "Hier liegen die abgeschlossenen Original-PDFs nach Quellenabgleich und Rechtsgebiet. Über die Übersicht jeder Version sind die Markdown-Volltexte und Prüfberichte erreichbar.",
        "\n".join(version_rows),
        "Spätere Quellenstände erhalten einen eigenen datierten Ordner. Bereits archivierte Fassungen bleiben erhalten.",
        link("Zur PDF-Archivübersicht", ARCHIVE / "README.md", DONE),
    ])
    inbox_parts = [
        "# Unbearbeitete PDFs",
        "Neue PDF-Dokumente hier ablegen. Dieser Ordner ist der Eingang für Dokumente, deren Markdown-Übernahme und Prüfung noch ausstehen.",
        f"**Noch unbearbeitet: {len(pending)} PDFs** (einschließlich gegebenenfalls neu im Hauptordner abgelegter PDFs).",
        "Nach vollständiger Umwandlung und Prüfung erhält jede PDF einen Platz unter `02_In_Markdown_umgewandelt/Stand_JJJJ-MM-TT/` im passenden Rechtsgebiet sowie einen Eintrag im Archivregister mit Links und Prüfsummen. Erst dann wird der Status auf „In Markdown umgewandelt“ gesetzt.",
        link("Zur PDF-Archivübersicht", ARCHIVE / "README.md", INBOX),
    ]
    if pending:
        inbox_parts.insert(3, "\n".join("- " + link(path.name, path, INBOX) for path in pending))
    write_readme(INBOX, inbox_parts)
    overview = [
        "# PDF-Archiv",
        f"**{len(entries)} PDFs in Markdown umgewandelt · {len(pending)} PDFs unbearbeitet.**",
        "| Ordner | Bedeutung |\n| --- | --- |\n"
        f"| {link('01_Unbearbeitet', INBOX / 'README.md', ARCHIVE)} | Eingang für neue PDFs; Umwandlung und Prüfung stehen noch aus. |\n"
        f"| {link('02_In_Markdown_umgewandelt', DONE / 'README.md', ARCHIVE)} | Abgeschlossene PDFs, nach Quellenabgleich und Rechtsgebiet abgelegt. |",
        "## Abgeschlossene Fassungen",
        "\n".join(f"- {link(version, DONE / version / 'README.md', ARCHIVE)}: {len(documents)} Original-PDFs mit Links zu Markdown-Volltexten und Prüfberichten."
                  for version, documents in sorted(versions.items(), reverse=True)),
        "## Versionierung und Bearbeitungsstatus",
        "`Stand_JJJJ-MM-TT` bezeichnet den Tag des Quellenabgleichs; der rechtliche Änderungsstand ist im jeweiligen Volltext dokumentiert. Bei einer späteren Aktualisierung wird eine neue Fassung angelegt. Die vorhandenen Fassungen bleiben erhalten.",
        "Die Original-PDFs behalten ihre Dateinamen und Inhalte. Die bereits vorhandenen Quellenkopien bei den Markdown-Dokumenten bleiben für deren Quellenverweise und reproduzierbare Prüfung erhalten. Eine PDF gilt erst nach vollständiger Umwandlung und Prüfung als abgeschlossen.",
        "Die Übersicht wird aus dem " + link("Archivregister.json", ARCHIVE / "Archivregister.json", ARCHIVE)
        + " erzeugt. Es enthält Bearbeitungsstatus, Version, Dateipfade und SHA-256-Prüfsummen. Alle Pfade im Register beziehen sich auf die Projektwurzel.",
        link("Zur Wissensdatenbank", ROOT / "README.md", ARCHIVE),
    ]
    write_readme(ARCHIVE, overview)
    print(json.dumps({"archivierte_pdfs": len(entries), "unbearbeitete_pdfs": len(pending),
                      "versionen": sorted(versions), "pruefsummen": "PDFs und Markdown unverändert"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
