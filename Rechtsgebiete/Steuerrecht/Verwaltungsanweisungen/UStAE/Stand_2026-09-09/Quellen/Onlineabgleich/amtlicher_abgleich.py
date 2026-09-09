"""Amtliche UStAE-Quelle lesen und unveränderte Seitendarstellungen rendern."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

import fitz
import requests

HERE = Path(__file__).resolve().parent
STAND = HERE.parent.parent
ROOT = next(p for p in HERE.parents if (p / "Bestand.json").exists())
URL = "https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Steuerarten/Umsatzsteuer/Umsatzsteuer-Anwendungserlass/Umsatzsteuer-Anwendungserlass-aktuell.pdf?__blob=publicationFile&v=52"
SEITE = "https://www.bundesfinanzministerium.de/Web/DE/Themen/Steuern/Steuerarten/Umsatzsteuer/Umsatzsteuer_Anwendungserlass/umsatzsteuer_anwendungserlass.html"
PDF = HERE / "UStAE_BMF_Stand_2026-06-02.pdf"
doc = fitz.open(PDF)
assert len(doc) == 886
assert "Stand 2. Juni 2026" in doc[0].get_text()
toc = doc.get_toc()
sections = [entry for entry in toc if re.match(r"\d+[a-z]?\.", entry[1])]
assert len(sections) == 432
images = STAND / "Quellen" / "Abbildungen"
images.mkdir(parents=True, exist_ok=True)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def render(page_number, name):
    target = images / name
    page = doc[page_number - 1]
    pix = page.get_pixmap(dpi=180, alpha=False)
    pix.save(target)
    return {
        "pfad": target.relative_to(STAND).as_posix(),
        "pdf_seite": page_number,
        "gedruckte_seite": page_number - 24,
        "sha256": digest(target),
        "breite_pixel": pix.width,
        "hoehe_pixel": pix.height,
        "dpi": 180,
        "vollstaendige_seite_ohne_beschnitt": True,
    }

annex_pages = {1: [870], 2: [871], 3: [872], 4: [873], 5: [874],
               6: list(range(875, 881)), 7: [881, 882], 8: [883, 884, 885]}
annexes = []
for number, pages in annex_pages.items():
    annexes.append({
        "anlage": number,
        "titel": next(a[1] for a in toc if a[1].startswith(f"Anlage {number} ")),
        "seiten": [render(page, f"Anlage_{number:02d}_Seite_{i:02d}.png")
                   for i, page in enumerate(pages, 1)],
        "webkopie_einschraenkung": "Formularinhalt fehlt; nur Titel oder Alternativtext vorhanden"
            if number in (1, 2, 3, 4, 5, 7)
            else "Tabelle als linearisierter Text vorhanden; Spaltenlayout in der Webkopie verloren",
    })

schemes = []
for section, start, end, count in [("3.14", 139, 149, 13), ("3.15", 150, 153, 6), ("25b.1", 844, 847, 4)]:
    schemes.append({
        "abschnitt": section,
        "schema_marker_in_webkopie": count,
        "hinweis": "Vollständige amtliche Abschnittsseiten als Ergänzung der in der Webkopie nur als Alternativtext vorhandenen Schemata.",
        "seiten": [render(page, f"Abschnitt_{section.replace('.', '_')}_PDF_Seite_{page:03d}.png")
                   for page in range(start, end + 1)],
    })

source_input = ROOT / "UStAE.txt"
if not source_input.exists():
    source_input = next(p for p in (STAND / "Quellen").rglob("*.txt") if p.name != "UStAE_BMF_Text.txt")
user_text = source_input.read_text(encoding="utf-8-sig")
schema_markers = [{"quellzeile": n, "text": line}
                  for n, line in enumerate(user_text.splitlines(), 1) if line.startswith("Schema ")]
assert len(schema_markers) == 23

html = requests.get(SEITE, headers={"Accept-Encoding": "identity", "User-Agent": "Mozilla/5.0"}, timeout=60)
html.raise_for_status()
(HERE / "BMF_UStAE_Uebersichtsseite.html").write_bytes(html.content)
(HERE / "Amtliches_Inhaltsverzeichnis.json").write_text(json.dumps(toc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report = {
    "abgerufen_am": datetime.now(timezone.utc).isoformat(),
    "quellenstand": "2026-06-02",
    "quellenstand_bestaetigung": "Titelseite der aktuellen amtlichen PDF: Stand 2. Juni 2026. Passt zum Geltungsstand 02.06.2026 in der bereitgestellten Webkopie.",
    "uebersichtsseite_url": SEITE,
    "pdf_url": URL,
    "pdf_pfad": PDF.relative_to(STAND).as_posix(),
    "pdf_sha256": digest(PDF),
    "pdf_bytes": PDF.stat().st_size,
    "pdf_seiten": len(doc),
    "amtliche_nummerierte_abschnitte": len(sections),
    "amtliche_anlagen": len(annexes),
    "quelltext_sha256": digest(source_input),
    "vollstaendiger_textidentitaetsabgleich_mit_bmf": False,
    "abgleichumfang": "Standdatum, amtliches Inhaltsverzeichnis, fehlende Formular- und Schemaabbildungen sowie gestrichener Abschnitt 25d.1. Kein vollständiger Wort-für-Wort-Abgleich der Beck-Webkopie gegen den amtlichen PDF-Text.",
    "fehlender_gestrichener_abschnitt": {
        "abschnitt": "25d.1",
        "amtlicher_text": "25d.1. - gestrichen -",
        "pdf_seite": 849,
        "gedruckte_seite": 825,
    },
    "anlagen_details": annexes,
    "schemata_haupttext": schemes,
    "schema_marker_in_webkopie": schema_markers,
    "nicht_gerenderte_leere_schlussseite": 886,
    "redaktionelle_zusatzinhalte_webkopie": "Die Webkopie enthält Beck-Oberfläche, redaktionelle Änderungs-/Anwendungshinweise und eine zusätzliche Synopse. Diese Inhalte sind von amtlichem Erlasstext und amtlichen BMF-Abbildungen zu unterscheiden.",
    "visuelle_pruefung": "Ausstehend",
}
report.update({
    "stand": report["quellenstand"],
    "pdf_datei": report["pdf_pfad"],
    "seiten": report["pdf_seiten"],
    "abschnitte": report["amtliche_nummerierte_abschnitte"],
    "anlagen": report["amtliche_anlagen"],
    "fehlender_abschnitt_25d_1": {"text": "25d.1. - gestrichen -", "pdf_seite": 849},
    "abbildungen": [
        {"anlage": entry["anlage"], "datei": page["pfad"], "pdf_seite": page["pdf_seite"], "sha256": page["sha256"]}
        for entry in annexes for page in entry["seiten"]
    ] + [
        {"abschnitt": entry["abschnitt"], "datei": page["pfad"], "pdf_seite": page["pdf_seite"], "sha256": page["sha256"]}
        for entry in schemes for page in entry["seiten"]
    ],
})
visual_check = HERE / "Visuelle_Pruefung.json"
if visual_check.exists():
    visual = json.loads(visual_check.read_text(encoding="utf-8"))
    expected = {entry["datei"]: entry["sha256"] for entry in report["abbildungen"]}
    if visual["gepruefte_abbildungen"] == expected:
        report["visuelle_pruefung"] = visual
(HERE / "Abgleich.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"pdf_seiten": len(doc), "abschnitte": len(sections), "anlagen": len(annexes),
                  "anlage_png": sum(len(a['seiten']) for a in annexes),
                  "haupttext_png": sum(len(a['seiten']) for a in schemes)}, ensure_ascii=False))
