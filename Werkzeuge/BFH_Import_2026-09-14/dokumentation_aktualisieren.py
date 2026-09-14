"""Aktualisiert nur Dokumentation nach dem erfolgreichen BFH-Cloudimport.

Erst nach beendetem cloud/sync.py ausführen. Register, Quellen und Datenbank
werden nicht verändert. Alle Änderungen werden vor dem Schreiben vorbereitet.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "Werkzeuge/BFH_Import_2026-09-14"
OLD_RELEASE = "r-2ba1572b7978ca909270331f"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    return f"{value:,}".replace(",", ".")


def paragraph(text, prefix, replacement):
    parts = text.split("\n\n")
    matches = [i for i, part in enumerate(parts) if part.startswith(prefix)]
    require(len(matches) == 1, f"Dokumentationsabsatz nicht eindeutig: {prefix}")
    parts[matches[0]] = replacement
    return "\n\n".join(parts)


def replace_once(text, old, new):
    if old == new or (old not in text and text.count(new) == 1):
        return text
    require(text.count(old) == 1, f"Dokumentationsstelle nicht eindeutig: {old}")
    return text.replace(old, new, 1)


def prepare(report, root=ROOT):
    rows, checks = report["compared_rows"], report["checks"]
    release = report["release_id"]
    stamp = datetime.fromisoformat(report["checked_at"]).astimezone(timezone.utc)
    day = stamp.strftime("%d.%m.%Y")
    completed = stamp.strftime("%d.%m.%Y um %H:%M Uhr (UTC)")
    documents, provisions, vectors, assets = (number(rows[key]) for key in
                                           ("documents", "provisions", "search_chunks", "assets"))
    byte_count = number(report["asset_bytes"])
    pages, probes = number(checks["text_pages"]), number(checks["exact_reference_probes"])
    result = {}

    path = "Chat_KI_starten.md"
    text = (root / path).read_text(encoding="utf-8")
    text = paragraph(text, "**Stand ",
        f"**Stand {day}:** Alle **{documents} registrierten Dokumente** sind vollständig in Supabase veröffentlicht. "
        f"Aktiv ist `{release}` mit **{provisions} Fundstellen**, **{vectors} Suchabschnitten samt Vektoren** "
        f"und **{assets} Dateieinträgen**. Texte, Metadaten, Vektoren und Dateien wurden zurückgelesen und verglichen; "
        "die aktive Fassung wurde nach dem COMMIT im Importlauf erneut abgefragt. "
        "[Prüfnachweis](Werkzeuge/BFH_Import_2026-09-14/Abschluss.md)")
    text = paragraph(text, "Deine bereits bestätigte Supabase-MCP-Verbindung",
        "Deine bereits bestätigte Supabase-MCP-Verbindung bleibt dieselbe. "
        "Hat der Chat sich noch einen älteren Datenstand gemerkt, sende einmal:")
    text = paragraph(text, "> Prüfe den aktiven Bestand mit",
        f"> Prüfe den aktiven Bestand mit `SELECT kb.release_info();` erneut. Erwartet werden {documents} Dokumente "
        f"in der Fassung `{release}`. Ermittle die verfügbaren Quellen neu und verwende diese Fassung für meine nächsten Fragen.")
    text = paragraph(text, "Die neue Fassung wurde",
        "Die neue Fassung wurde über die Lese-API innerhalb des Importlaufs geprüft. Eine zusätzliche Prüfung mit "
        "einer separaten Leseranmeldung und ein erneuter Aufruf aus deiner Chatoberfläche sind für diese Fassung nicht dokumentiert.")
    result[path] = text

    path = "Werkzeuge/Recherche/README.md"
    text = (root / path).read_text(encoding="utf-8")
    text = re.sub(r"(?m)^Stand: \d{2}\.\d{2}\.\d{4}\.", f"Stand: {day}.", text, count=1)
    text = paragraph(text, "**Alle ",
        f"**Alle {documents} registrierten Dokumente sind vollständig in Supabase gespeichert und aktiviert.** "
        f"Die Cloudfassung `{release}` enthält **{provisions} Fundstellen und Dokumentteile**, **{vectors} Suchvektoren** "
        f"sowie **{assets} Dateieinträge mit insgesamt {byte_count} Bytes**. Der Import wurde am **{completed}** "
        "erfolgreich abgeschlossen. Alle gespeicherten Texte, Metadaten, Vektoren und Dateiinhalte wurden zurückgelesen "
        f"und verglichen; sämtliche Fundstellen wurden zusätzlich über **{pages} Textfenster** der Lese-API geprüft.")
    text = paragraph(text, "Die persönliche Supabase-Anmeldung",
        "Die persönliche Supabase-Anmeldung und der Abruf der früheren Pilotfassung aus Claude wurden vom Nutzer bestätigt. "
        "Die aktuelle Fassung ist im Importlauf über die Datenbank-Lese-API geprüft; ein neuer Test mit separater "
        "Leseranmeldung oder innerhalb der Claude- beziehungsweise ChatGPT-Oberfläche ist damit nicht dokumentiert. "
        "Eine bestehende Verbindung muss wegen des neuen Datenstands nicht erneut eingerichtet werden. "
        "Den freigegebenen Bestand zeigt `SELECT kb.release_info();`.")
    text = replace_once(text, "58 Hauptdokumente mit 52 PDF- und 6 TXT-Ursprungsdateien",
                        "60 Hauptdokumente mit 52 PDF- und 8 TXT-Ursprungsdateien")
    text = replace_once(text, "als die 58 Hauptdokumente", "als die 60 Hauptdokumente")
    text = replace_once(text,
        "- [Vollimport und Abnahme](cloud/Vollimport_Pruefung.md), [aktueller Projektstatus](cloud/projekt.json), "
        "[abgeschlossene Cloud-Importprüfung](cloud/Importpruefung_apply.json) und "
        "[gesonderte Leserprüfung nach COMMIT](cloud/Vollimport_Lesepruefung.json)",
        "- [BFH-Ergänzung und aktueller Cloudabschluss](../BFH_Import_2026-09-14/Abschluss.md), "
        "[fester Importnachweis](../BFH_Import_2026-09-14/Cloud_Importpruefung.json) und [aktueller Projektstatus](cloud/projekt.json)\n"
        "- Historische Fassung mit 58 Dokumenten: [Vollimport und Abnahme](cloud/Vollimport_Pruefung.md) und "
        "[damalige separate Leserprüfung](cloud/Vollimport_Lesepruefung.json)")
    text = replace_once(text, "- [Lokaler Exportvertrag für den Vollbestand](cloud/Vollimport_Exportvertrag.json): ausdrücklich ein Test ohne Cloudübertragung",
        "- [Historischer lokaler Exportvertrag für 58 Dokumente](cloud/Vollimport_Exportvertrag.json): ausdrücklich ein Test ohne Cloudübertragung")
    result[path] = text

    path = "Werkzeuge/Recherche/cloud/READMECloudSetup.md"
    text = (root / path).read_text(encoding="utf-8")
    text = re.sub(r"(?m)^Stand: \d{2}\.\d{2}\.\d{4}\.", f"Stand: {day}.", text, count=1)
    text = paragraph(text, "**Der vollständige Bestand",
        f"**Der vollständige Bestand ist in Supabase gespeichert und aktiviert.** Die aktive Fassung `{release}` "
        f"umfasst **{documents} Dokumente, {provisions} Fundstellen und Dokumentteile, {vectors} Suchvektoren sowie "
        f"{assets} Dateieinträge**. Die Dateiinhalte umfassen zusammen **{byte_count} Bytes**. Der Import wurde am "
        f"**{completed}** erfolgreich festgeschrieben; der Importlauf fragte die aktive Fassung nach dem COMMIT erneut ab.")
    text = paragraph(text, "Alle Datenzeilen einschließlich Texte",
        "Alle Datenzeilen einschließlich Texte, Metadaten und Vektoren sowie alle Dateibytes wurden verglichen. "
        f"Die Lese-API lieferte sämtliche Fundstellen vollständig über **{pages} Textfenster**; Volltextsuche und "
        f"**{probes} exakte Referenz- und Aliasprüfungen** deckten alle {documents} Dokumente ab. Nachweise: "
        "[BFH-Importabschluss](../../BFH_Import_2026-09-14/Abschluss.md) und "
        "[fester Importbericht mit `committed=true`](../../BFH_Import_2026-09-14/Cloud_Importpruefung.json). "
        "Die frühere Pilotfassung `r-ad68e666980668e7ca4e6b81` bleibt als historische Fassung erhalten; "
        "ihr [Importbericht ist separat archiviert](Importpruefung_Pilot_2026-09-09.json).")
    historical_reader = (f"Die [gesonderte Leserprüfung nach COMMIT](Vollimport_Lesepruefung.json) gehört zur historischen "
        f"Fassung `{OLD_RELEASE}` mit 58 Dokumenten. Sie bestätigte damals den Umfang über die eigene Leseranmeldung, "
        "vollständige Abrufe von EStG § 7 und AO § 146 einschließlich SHA-256 sowie einen passenden Volltextsuchtreffer. "
        "Für die aktuelle Fassung wurde kein zusätzlicher Test mit separater Leseranmeldung und kein erneuter "
        "Abruf aus einer Claude- oder ChatGPT-Oberfläche durchgeführt; die aktuellen Leseprüfungen gehören zum Importlauf.")
    prefix = "Eine [gesonderte Leserprüfung" if "Eine [gesonderte Leserprüfung" in text else "Die [gesonderte Leserprüfung"
    text = paragraph(text, prefix, historical_reader)
    text = replace_once(text, "58 registrierten Hauptdokumente stammen aus 52 PDF- und 6 TXT-Originalen",
                        "60 registrierten Hauptdokumente stammen aus 52 PDF- und 8 TXT-Originalen")
    text = replace_once(text,
        "- [Vollimport und Abnahme](Vollimport_Pruefung.md), [Projektstatus](projekt.json) und "
        "[abgeschlossene Cloud-Importprüfung](Importpruefung_apply.json)",
        "- [Aktueller BFH-Importabschluss](../../BFH_Import_2026-09-14/Abschluss.md), "
        "[fester Cloud-Importnachweis](../../BFH_Import_2026-09-14/Cloud_Importpruefung.json) und [Projektstatus](projekt.json)\n"
        "- Historische Fassung mit 58 Dokumenten: [Vollimport und Abnahme](Vollimport_Pruefung.md), "
        "[damaliger Importbericht](../../BFH_Import_2026-09-14/Cloud_Vorbestand.json) und "
        "[separate Leserprüfung](Vollimport_Lesepruefung.json)")
    text = replace_once(text, "- [Vollimport-Exportvertrag](Vollimport_Exportvertrag.json): lokaler Vertragstest, keine Cloudübertragung",
        "- [Historischer Vollimport-Exportvertrag für 58 Dokumente](Vollimport_Exportvertrag.json): lokaler Vertragstest, keine Cloudübertragung")
    text = paragraph(text, "Die historischen Pilotmessungen",
        "Die historischen Pilotmessungen beziehen sich auf drei Dokumente; die Vollimport- und Leserprüfung vom "
        "10.09.2026 betrifft 58 Dokumente. Der aktuelle Cloudimport mit 60 Dokumenten ist im BFH-Importbericht separat "
        "nachgewiesen. Die bisherigen Quellen behalten ihre Erfassung vom 09.09.2026; die beiden BFH-Webkopien wurden "
        "am 14.09.2026 ergänzt. Weder Erfassung noch Cloudabschluss sind neue rechtliche Geltungsdaten.")
    result[path] = text

    path = "Werkzeuge/Claude_Skill/README.md"
    text = (root / path).read_text(encoding="utf-8")
    text = replace_once(text, "Suche in allen 58 großen Dokumenten", "Suche in allen 60 registrierten Dokumenten")
    prefix = "**Veröffentlichter Cloudbestand"
    current = (f"**Veröffentlichter Cloudbestand ({day}):** {documents} Dokumente in der Fassung `{release}`. "
        "Die beiden BFH-Webkopien sind in der Cloudsuche enthalten. "
        "[Importabschluss und Prüfnachweis](../BFH_Import_2026-09-14/Abschluss.md). "
        "Der GitHub-Zugang liest den jeweils veröffentlichten Repository-Commit; ein lokaler Quellenimport veröffentlicht diesen nicht automatisch.")
    if prefix in text:
        text = paragraph(text, prefix, current)
    else:
        text = replace_once(text, "## Supabase und GitHub\n\n", "## Supabase und GitHub\n\n" + current + "\n\n")
    result[path] = text

    path = "Werkzeuge/Recherche/cloud/Vollimport_Pruefung.md"
    text = (root / path).read_text(encoding="utf-8")
    marker = ("**Historischer Nachweis:** Dieser Bericht beschreibt die Fassung mit 58 Dokumenten vom 10.09.2026. "
              "Den aktuellen Bestand mit der BFH-Ergänzung dokumentiert der "
              "[Importabschluss vom 14.09.2026](../../BFH_Import_2026-09-14/Abschluss.md).")
    if marker not in text:
        text = replace_once(text, "# Vollständiger Import nach Supabase\n\n",
                            "# Vollständiger Import nach Supabase\n\n" + marker + "\n\n")
    text = replace_once(text, "(Importpruefung_apply.json)", "(../../BFH_Import_2026-09-14/Cloud_Vorbestand.json)")
    result[path] = text

    result["Werkzeuge/BFH_Import_2026-09-14/Abschluss.md"] = f"""# BFH-Import vom 14.09.2026 – Abschluss

Die BFH-Entscheidungen V R 6/12 und V R 7/12 vom 19.12.2013 sind im registrierten Bestand enthalten und mit der gesamten Sammlung in Supabase veröffentlicht. Der erfolgreiche Importabschluss ist für **{completed}** dokumentiert. Aktiviert wurde `{release}`.

| Cloudbestand und Prüfung | Anzahl |
| --- | ---: |
| Registrierte Dokumente | {documents} |
| Vollständig abrufbare Fundstellen und Dokumentteile | {provisions} |
| Suchabschnitte mit Vektoren | {vectors} |
| Dateieinträge | {assets} |
| Dateibytes | {byte_count} |
| Vollständig verglichene Textfenster | {pages} |
| Exakte Referenz- und Aliasprüfungen | {probes} |

Alle Texte, Metadaten, Suchvektoren und Dateiinhalte wurden nach der Übertragung mit dem Export verglichen. Volltextsuche und exakte Referenzprüfungen decken alle {documents} Dokumente ab. Die Fassung wurde nach erfolgreicher Prüfung festgeschrieben; der Importlauf hat die aktive Fassung nach dem COMMIT erneut abgefragt. Dateieinträge können dieselbe Datei mehreren Dokumenten zuordnen.

## Übernahme der bereitgestellten Dateien

| Entscheidung | Nichtleere Quellzeilen vollständig übertragen | Vorhandene Randnummern erschlossen | Prüfnachweis |
| --- | ---: | ---: | --- |
| BFH V R 6/12 | 48 | 29 | [Prüfbericht](../../Rechtsgebiete/Steuerrecht/Rechtsprechung/Umsatzsteuer/BFH/V_R_6_12/Stand_2026-09-14/Pruefung/Pruefbericht.md) |
| BFH V R 7/12 | 116 | 58 | [Prüfbericht](../../Rechtsgebiete/Steuerrecht/Rechtsprechung/Umsatzsteuer/BFH/V_R_7_12/Stand_2026-09-14/Pruefung/Pruefbericht.md) |

Die Originaldateien sind unverändert archiviert; der sichtbare Inhalt jeder nichtleeren Quellzeile wurde nach Rücklesen geprüft. In V R 6/12 fehlen die Randnummern 16–32 bereits in der gelieferten Kopie; die Auslassung bleibt gekennzeichnet. Die Anmerkung von Ursula Slapio zu V R 7/12 bleibt vom Urteilstext getrennt. Unterschiede zum amtlichen Vergleichstext sind dokumentiert. Vollständige Übertragung bezieht sich auf die gelieferten Kopien und bestätigt keinen darüber hinausgehenden amtlichen Volltext. Die Entscheidungen behalten ihr Datum vom 19.12.2013, ältere Quellen ihre bestehenden Erfassungsdaten.

## Nachweise und Zugriff

- [Fester Cloud-Importbericht mit erfolgreichem COMMIT](Cloud_Importpruefung.json)
- [Historischer Cloudvorbestand mit 58 Dokumenten](Cloud_Vorbestand.json)
- [Konvertierung und wiederholbare Prüfschritte](README.md)

Die aktuellen Leseprüfungen gehören zum Importlauf. Ein zusätzlicher Test mit separater Leseranmeldung und ein erneuter Abruf aus der Claude- oder ChatGPT-Oberfläche sind für diese Fassung nicht dokumentiert. Die frühere [separate Leserprüfung](../Recherche/cloud/Vollimport_Lesepruefung.json) betrifft `{OLD_RELEASE}`. Bestehende Chatverbindungen können den neuen Bestand mit `SELECT kb.release_info();` laden. Eine Veröffentlichung der lokalen Git-Änderungen ist kein Bestandteil dieses Cloudnachweises.
"""
    return result


def main():
    report_path = ROOT / "Werkzeuge/Recherche/cloud/Importpruefung_apply.json"
    raw = report_path.read_bytes()
    report = json.loads(raw)
    rows, checks = report.get("compared_rows", {}), report.get("checks", {})
    require(report.get("committed") is True and report.get("mode") == "apply",
            "Der Cloudimport wurde noch nicht erfolgreich festgeschrieben.")
    require(rows.get("documents") == 60, "Es liegt noch kein Cloudbericht für 60 Dokumente vor.")
    require(report.get("release_id") != OLD_RELEASE and re.fullmatch(r"r-[a-z0-9]+", report.get("release_id", "")),
            "Neue Releasekennung fehlt.")
    require(checks.get("full_provisions") == rows.get("provisions") and checks.get("verified_assets") == rows.get("assets"),
            "Vollständige Fundstellen-/Dateiprüfung fehlt.")
    require(checks.get("lexical_documents") == 60 and checks.get("exact_documents") == 60,
            "Dokumentübergreifende Such-/Referenzprüfungen fehlen.")
    inventory = json.loads((ROOT / "Bestand.json").read_text(encoding="utf-8"))
    require(inventory.get("dokumente") == 60 and inventory.get("pdf_dokumente") == 52 and inventory.get("webkopien") == 8,
            "Bestand entspricht nicht dem erwarteten BFH-Import.")
    project = json.loads((ROOT / "Werkzeuge/Recherche/cloud/projekt.json").read_text(encoding="utf-8"))
    require(project.get("active_release") == report["release_id"], "Projektstatus bestätigt die neue Fassung noch nicht.")
    previous = json.loads((TASK / "Cloud_Vorbestand.json").read_text(encoding="utf-8"))
    require(previous.get("release_id") == OLD_RELEASE and previous.get("compared_rows", {}).get("documents") == 58,
            "Der historische 58-Dokumente-Bericht ist nicht gesichert.")
    for case, line_count, margin_count in (("V_R_6_12", 48, 29), ("V_R_7_12", 116, 58)):
        stand = ROOT / "Rechtsgebiete/Steuerrecht/Rechtsprechung/Umsatzsteuer/BFH" / case / "Stand_2026-09-14"
        proof = json.loads((stand / "Pruefung/Vollstaendigkeitspruefung.json").read_text(encoding="utf-8"))
        require(proof.get("pruefung_erfolgreich") is True and proof.get("quellzeilen_nichtleer") == line_count
                and len(proof.get("uebernommene_quellzeilen", [])) == line_count and len(proof.get("randnummern", [])) == margin_count,
                f"Erwartete Übertragungsprüfung fehlt: {case}")
    updates = prepare(report)
    fixed_report = TASK / "Cloud_Importpruefung.json"
    require(not fixed_report.exists() or fixed_report.read_bytes() == raw,
            "Ein abweichender fester Importbericht existiert bereits und wird nicht überschrieben.")
    require(report_path.read_bytes() == raw, "Cloudbericht wurde während der Vorbereitung verändert.")
    fixed_report.write_bytes(raw)
    for relative, text in updates.items():
        (ROOT / relative).write_bytes(text.encode("utf-8"))
    print(json.dumps({"release_id": report["release_id"], "documents": rows["documents"],
                      "report_sha256": hashlib.sha256(raw).hexdigest(), "dokumentation": list(updates)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
