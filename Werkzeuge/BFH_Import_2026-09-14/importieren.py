"""Reproduzierbare, zeilengetreue Übernahme der beiden gelieferten BFH-Kopien."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
import hashlib
import json
import os
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATE = "2026-09-14"
VERSION = "Stand_" + DATE
AREA = Path("Steuerrecht/Rechtsprechung/Umsatzsteuer/BFH")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def relative(path, base):
    return Path(os.path.relpath(path, base)).as_posix()


def convert(number, receipt):
    name = f"v_r_{number}_12.txt"
    abbreviation = f"BFH V R {number}/12"
    folder = f"V_R_{number}_12"
    base = ROOT / "Rechtsgebiete" / AREA / folder / VERSION
    archive = ROOT / "Web_Archiv/02_In_Markdown_umgewandelt" / VERSION / AREA / folder / name
    for directory in [base / "Quellen", base / "Pruefung", archive.parent]:
        directory.mkdir(parents=True, exist_ok=True)
    incoming = ROOT / name
    if incoming.exists():
        if archive.exists():
            assert incoming.read_bytes() == archive.read_bytes(), "Archivquelle weicht vom Eingang ab"
        else:
            shutil.copyfile(incoming, archive)
    assert archive.is_file(), f"Quelle fehlt: {name}"
    shutil.copyfile(archive, base / "Quellen" / name)
    official = HERE / "quellen" / receipt["file"]
    assert digest(official) == receipt["sha256"]
    shutil.copyfile(official, base / "Quellen" / official.name)
    write_json(base / "Quellen/Abrufmanifest.json", receipt)

    lines = archive.read_text(encoding="utf-8-sig").splitlines()
    title = lines[1]
    citation = "DStR 2014, 1109" if number == 6 else "MwStR 2014, 480"
    expected = list(range(1, 16)) + list(range(33, 47)) if number == 6 else list(range(1, 59))
    limitation = (
        "Die gelieferte Kopie enthält Rn. 1–15 und 33–46. Statt Rn. 16–32 steht dort wörtlich "
        "„6-32 (inhaltsgleich zu BFH v. 19. 12. 2013, V R 7/12, DStR 2014, 1104 – in diesem Heft –, Rz. 16-31)“. "
        "Dieser Auslassungsvermerk bleibt unverändert; fehlende Randnummern werden nicht aus dem Parallelurteil ergänzt."
        if number == 6 else
        "Die gelieferte Kopie enthält Rn. 1–58 sowie die gesonderte „Erste Einordnung“ von Ursula Slapio. "
        "Die Anmerkung und die redaktionellen Zwischenüberschriften sind keine gerichtlichen Entscheidungsgründe. "
        "Die Zwischenüberschrift vor Rn. 58 nennt „§ 173 Abs. 3 AO“, der folgende Absatz dagegen § 174 Abs. 3 AO; "
        "die abweichende Überschrift wird unverändert erhalten."
    )
    official_note = (
        f"Amtliche BFH-Seite am 14.09.2026: Aktenzeichen, Entscheidungsdatum und Randnummernfolge "
        f"1–{46 if number == 6 else 58} geprüft. Die Vorinstanz ist dort mit 25.10.2011, in der "
        "gelieferten Kopie mit 26.10.2011 angegeben. Kein vollständiger Wortlautvergleich; keine Prüfung späterer Rechtsprechung."
    )
    parts = [
        f"# {abbreviation} – Urteil vom 19.12.2013",
        title,
        f"**Fundstelle der gelieferten Kopie: {citation} · Erfassung und Quellenprüfung: 14.09.2026.**",
        "Quelle ist die vom Nutzer bereitgestellte Zeitschriften-/Webtextkopie; Ausgangs-URL und ursprüngliches Abrufdatum fehlen. "
        "Der historische Entscheidungsstand bleibt maßgeblich. Sämtliche nichtleeren Quellzeilen einschließlich "
        "Leitsätzen, Verlagsüberschriften, Seitenzahlen und wiederholten Seitenköpfen werden unverändert übertragen. "
        "Zusätzliche Randnummernüberschriften dienen der Navigation; angeklebte Nummern und Seitentrennungen der Kopie bleiben erhalten.",
        "**Übertragungsgrenzen:** " + limitation,
        "**Amtlicher Abgleich:** " + official_note,
        f"[Originalkopie](Quellen/{name}) · [Prüfbericht](Pruefung/Pruefbericht.md) · "
        f"[Amtliche BFH-Seite]({receipt['request_url']}) · [Archivierte BFH-Seite](Quellen/{official.name})",
        '<a id="dokumentkopf"></a>\n\n## Dokumentkopf und Leitsätze der Kopie',
    ]
    mapped, found = [], []
    in_judgment = False
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if line == "Sachverhalt:":
            in_judgment = True
            parts.append('<a id="sachverhalt"></a>\n\n## Sachverhalt der Kopie')
        elif line == "Gründe:":
            parts.append('<a id="gruende"></a>\n\n## Entscheidungsgründe der Kopie')
        elif line == "Erste Einordnung:":
            in_judgment = False
            parts.append('<a id="anmerkung"></a>\n\n## Verlagsanmerkung von Ursula Slapio (kein Urteilstext)')
        if in_judgment and len(found) < len(expected):
            rn = expected[len(found)]
            token = str(rn)
            tail = line[len(token):] if line.startswith(token) else ""
            if tail and (not tail[0].isdigit() or re.match(r"\d\.\s", tail)) and not tail.startswith("-"):
                found.append(rn)
                parts.append(f'<a id="rn-{rn}"></a>\n\n### Rn. {rn}')
        block = f"<p>{escape(line, quote=False)}</p>"
        parts.append(f"<!-- quelle:z{line_no}-{line_no} -->\n{block}\n<!-- /quelle:z{line_no}-{line_no} -->")
        mapped.append(line_no)
    assert found == expected, (abbreviation, found, expected)
    markdown = base / (folder + ".md")
    markdown.write_text("\n\n".join(parts) + "\n", encoding="utf-8")

    # Read the actual generated file back, then verify every source block's visible text.
    actual = markdown.read_text(encoding="utf-8")
    blocks = re.findall(r"<!-- quelle:z(\d+)-(\d+) -->\n(.*?)\n<!-- /quelle:z\1-\2 -->", actual, re.S)
    assert [int(start) for start, _, _ in blocks] == mapped
    for start, end, body in blocks:
        assert start == end
        visible = VisibleText()
        visible.feed(body)
        assert "".join(visible.parts) == lines[int(start) - 1], f"Textabweichung in Zeile {start}"
    assert mapped == [i for i, line in enumerate(lines, 1) if line.strip()]
    assert digest(archive) == digest(base / "Quellen" / name)
    completeness = f"Alle {len(mapped)} nichtleeren Quellzeilen vollständig und zeichengetreu übertragen; {len(found)} Randnummern mit Sprungmarken. " + limitation
    check = {
        "pruefung_erfolgreich": True,
        "sha256_original_quelle": digest(archive),
        "sha256_markdown": digest(markdown),
        "quellzeilen_gesamt": len(lines),
        "quellzeilen_nichtleer": len(mapped),
        "uebernommene_quellzeilen": mapped,
        "randnummern": found,
        "amtliche_randnummern_nicht_in_der_kopie": list(range(16, 33)) if number == 6 else [],
        "methode": "Jeder nichtleere Quelltext genau einmal in ursprünglicher Reihenfolge; sichtbarer HTML-Text jedes zurückgelesenen Quellblocks zeichenidentisch zur TXT-Zeile.",
        "einschraenkung": limitation + " " + official_note,
    }
    write_json(base / "Pruefung/Vollstaendigkeitspruefung.json", check)
    (base / "Pruefung/Pruefbericht.md").write_text("\n\n".join([
        f"# Prüfnachweis – {abbreviation}",
        "Prüfung am 14.09.2026. Die vollständige Übertragung der gelieferten Kopie wurde bestätigt.",
        completeness,
        "## Übertragungsprüfung",
        f"{len(lines)} Quellzeilen, davon {len(mapped)} nichtleer. Alle nichtleeren Zeilen wurden genau einmal in Originalreihenfolge übernommen. "
        "Nach Rücklesen des erzeugten Dokuments wurde der sichtbare HTML-Text jedes markierten Blocks zeichenweise mit seiner Quellzeile verglichen. "
        "Leerzeilen dienen lediglich der Formatierung. Originaldatei und Quellenkopie sind byteidentisch. Der Prüfnachweis enthält beide SHA-256-Prüfsummen.",
        "## Abgrenzung und amtlicher Quellenabgleich",
        official_note,
        f"[Amtliche Fundstelle]({receipt['request_url']}) · [Gesicherte HTML-Datei](../Quellen/{official.name}) · [Abrufmanifest](../Quellen/Abrufmanifest.json)",
        "Die Zeitschriftenredaktion, zitierte Parallelentscheidungen und gegebenenfalls die Fachanmerkung wurden nicht als zusätzliche gerichtliche Aussagen eingeordnet. "
        "Schreibweisen, Druck-/Kopierfehler und abweichende Anonymisierung wurden nicht berichtigt. Die amtliche HTML-Datei ist ein gesonderter Vergleichsbeleg. "
        "Die Übernahme bestätigt weder die vollständige Wiedergabe der amtlichen Entscheidung in der Verlagskopie noch deren heutige Anwendbarkeit.",
        "## Reproduktion",
        "Im Projektordner: `Werkzeuge/Recherche/.venv/Scripts/python.exe -B Werkzeuge/BFH_Import_2026-09-14/importieren.py`. "
        "Der Konverter verwendet beim Wiederholungslauf die archivierte TXT-Datei und die gesicherten amtlichen HTML-Dateien. "
        "Anschließend `Werkzeuge/web_archiv_index_erstellen.py` und `Werkzeuge/bestand_erstellen.py` ausführen.",
        "[Maschinenlesbare Prüfung](Vollstaendigkeitspruefung.json)",
    ]) + "\n", encoding="utf-8")
    (base / "README.md").write_text(f"# {abbreviation}\n\nUrteil vom 19.12.2013; {citation}. Erfasst und quellengeprüft am 14.09.2026.\n\n"
        f"[Strukturierte Textkopie]({folder}.md) · [Original](Quellen/{name}) · [Prüfnachweis](Pruefung/Pruefbericht.md)\n\n{limitation}\n", encoding="utf-8")
    (base.parent / "README.md").write_text(f"# {abbreviation}\n\n{title}\n\n[Erfassung vom 14.09.2026]({VERSION}/README.md)\n", encoding="utf-8")
    entry = {
        "dokument": f"{abbreviation} vom 19.12.2013 – {title}", "kuerzel": abbreviation,
        "bereich": "Steuerrecht / Rechtsprechung / Umsatzsteuer / BFH", "typ": "Rechtsprechung (Webkopie)",
        "urspruenglicher_dateiname": name, "status": "in_markdown_umgewandelt", "archivversion": VERSION,
        "erfasst_am": DATE, "quellenabgleich": DATE,
        "quellenstand": [f"BFH-Urteil vom 19.12.2013, V R {number}/12; Verlagskopie aus {citation}.", official_note],
        "quellformat": "Webkopie (TXT)", "original_quelle": archive.relative_to(ROOT).as_posix(),
        "markdown": markdown.relative_to(ROOT).as_posix(), "pruefbericht": (base / "Pruefung/Pruefbericht.md").relative_to(ROOT).as_posix(),
        "sha256_original_quelle": digest(archive), "sha256_markdown": digest(markdown),
        "quelle": "Vom Nutzer bereitgestellte Verlags-/Webtextkopie; genaue Ausgangs-URL nicht mitkopiert. Amtliche BFH-Entscheidung: " + receipt["request_url"],
        "vollstaendigkeit": completeness,
    }
    return entry


def main():
    receipts = json.loads((HERE / "quellen/abrufmanifest.json").read_text(encoding="utf-8-sig"))
    entries = [convert(n, next(r for r in receipts if r["aktenzeichen"] == f"V R {n}/12")) for n in (6, 7)]
    register_path = ROOT / "Web_Archiv/Archivregister.json"
    register = json.loads(register_path.read_text(encoding="utf-8-sig"))
    added = {e["original_quelle"] for e in entries}
    register["eintraege"] = [e for e in register["eintraege"] if e["original_quelle"] not in added] + entries
    write_json(register_path, register)
    print(json.dumps({"dokumente": [e["kuerzel"] for e in entries], "pruefung_erfolgreich": True}, ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
