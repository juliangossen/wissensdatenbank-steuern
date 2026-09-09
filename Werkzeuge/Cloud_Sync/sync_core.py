"""Versionierte, geprüfte Bereitstellung für einen lokalen Cloud-Sync-Ordner.

Keine Netzwerkzugriffe und keine Aussage über den Uploadstatus von Drive Desktop.
Die Originaldaten werden nur gelesen; bestehende Fassungen bleiben unverändert.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Callable
from urllib.parse import quote


class SyncError(ValueError):
    """Eine Quelle oder ein Ziel ist nicht konsistent bzw. nicht geeignet."""


TOOL = "wissensdatenbank-cloud-sync-v1"
CLOUD_NAME = "Wissensdatenbank_Cloud"
MARKER = ".wissensdatenbank-cloud-sync.json"
SNAPSHOT_MARKER = ".bereitstellung.json"
MANIFEST = "MANIFEST.json"
CURRENT = "AKTUELL.json"
DONE = "in_markdown_umgewandelt"
_HEX = re.compile(r"[0-9a-f]{64}\Z")


def _json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SyncError(message)


def _relative(value: object) -> str:
    _require(isinstance(value, str) and bool(value), "Leerer oder ungültiger Projektpfad.")
    p = PurePosixPath(value)
    _require(not p.is_absolute() and ".." not in p.parts and "\\" not in value
             and ":" not in value and str(p) == value,
             f"Unsicherer Projektpfad: {value!r}")
    return value


def _inside(base: Path, relative: str) -> Path:
    relative = _relative(relative)
    candidate = base.joinpath(*PurePosixPath(relative).parts)
    resolved = candidate.resolve()
    _require(resolved.is_relative_to(base.resolve()) and resolved != base.resolve(),
             f"Pfad verlässt den vorgesehenen Ordner: {candidate}")
    # Auch interne Verknüpfungen werden nicht als eigenständige Archivdateien übernommen.
    cursor = candidate
    while cursor != base:
        _require(not cursor.is_symlink() and not getattr(cursor, "is_junction", lambda: False)(),
                 f"Verknüpfungen sind im Export nicht zulässig: {cursor}")
        cursor = cursor.parent
    return candidate


def _read_json(path: Path) -> dict:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
        _require(isinstance(result, dict), f"JSON-Objekt erwartet: {path}")
        return result
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SyncError(f"Datei nicht lesbar: {path}: {exc}") from exc


@dataclass(frozen=True)
class _File:
    path: str
    sha256: str
    size: int
    source: Path | None = None
    generated: bytes | None = None

    def read(self) -> bytes:
        data = self.generated if self.generated is not None else self.source.read_bytes()
        _require(len(data) == self.size and _digest(data) == self.sha256,
                 f"Quelldatei wurde während der Bereitstellung verändert: {self.path}")
        return data

    def record(self) -> dict:
        return {"path": self.path, "bytes": self.size, "sha256": self.sha256}


@dataclass
class _Plan:
    root: Path
    documents: int
    date: str
    files: dict[str, _File]
    fingerprint: str

    @property
    def version(self) -> str:
        return f"Stand_{self.date}_{self.fingerprint[:12]}"

    def summary(self) -> dict:
        return {"documents": self.documents, "files": len(self.files),
                "bytes": sum(f.size for f in self.files.values()),
                "version": self.version, "fingerprint": self.fingerprint}


def _plan(root: Path) -> _Plan:
    root = Path(root).expanduser().resolve()
    _require(root.is_dir(), f"Quellordner fehlt: {root}")
    inventory = _read_json(_inside(root, "Bestand.json"))
    archive = _read_json(_inside(root, "PDF_Archiv/Archivregister.json"))
    entries = inventory.get("eintraege")
    _require(isinstance(entries, list) and bool(entries), "Bestand.json enthält keinen bearbeiteten Bestand.")
    _require(inventory.get("dokumente") == len(entries), "Dokumentzahl in Bestand.json stimmt nicht.")
    checked = inventory.get("quellenabgleich", "")
    try:
        _require(date.fromisoformat(checked).isoformat() == checked, "Ungültiges Abgleichdatum.")
    except (TypeError, ValueError) as exc:
        raise SyncError("Ungültiges Datum quellenabgleich in Bestand.json.") from exc
    archive_entries = archive.get("eintraege")
    _require(isinstance(archive_entries, list), "Archivregister enthält keine Einträge.")
    web_register = _inside(root, "Web_Archiv/Archivregister.json")
    web_entries = _read_json(web_register).get("eintraege") if web_register.is_file() else []
    _require(isinstance(web_entries, list), "Web-Archivregister enthält keine Einträge.")
    files: dict[str, _File] = {}
    selected_archive = []
    selected_web_archive = []
    stand_entries: dict[Path, list[dict]] = {}
    seen_sources, seen_md = set(), set()

    def add_source(relative: str, expected: str | None = None) -> None:
        relative = _relative(relative)
        source = _inside(root, relative)
        _require(source.is_file(), f"Registrierte Datei fehlt: {relative}")
        data = source.read_bytes()
        actual = _digest(data)
        if expected is not None:
            _require(isinstance(expected, str) and _HEX.fullmatch(expected) is not None
                     and actual == expected, f"Prüfsumme stimmt nicht: {relative}")
        if relative in files:
            _require(files[relative].sha256 == actual,
                     f"Quelle wurde während der Bestandsprüfung geändert: {relative}")
        files[relative] = _File(relative, actual, len(data), source=source)

    def add_generated(relative: str, data: bytes) -> None:
        _require(relative not in files, f"Doppelter Exportpfad: {relative}")
        files[relative] = _File(relative, _digest(data), len(data), generated=data)

    for entry in entries:
        _require(isinstance(entry, dict) and entry.get("bearbeitungsstatus") == DONE,
                 "Nur vollständig registrierte, bearbeitete Dokumente können bereitgestellt werden.")
        is_pdf = "original_pdf" in entry
        _require(is_pdf != ("original_quelle" in entry),
                 "Jedes Dokument benötigt genau eine registrierte Originalquelle.")
        source_key = "original_pdf" if is_pdf else "original_quelle"
        digest_key = "sha256_original_pdf" if is_pdf else "sha256_original_quelle"
        archive_key = "pdf" if is_pdf else "original_quelle"
        archive_hash_key = "sha256_pdf" if is_pdf else "sha256_original_quelle"
        archive_name = "PDF_Archiv" if is_pdf else "Web_Archiv"
        source, md, report = (entry.get(key) for key in (source_key, "markdown", "pruefbericht"))
        source, md, report = _relative(source), _relative(md), _relative(report)
        _require(source not in seen_sources and md not in seen_md, f"Doppelte Dokumentzuordnung: {md}")
        seen_sources.add(source)
        seen_md.add(md)
        version = entry.get("pdf_archivversion" if is_pdf else "archivversion", "")
        _require(isinstance(version, str) and re.fullmatch(r"Stand_\d{4}-\d{2}-\d{2}", version) is not None,
                 f"Ungültige Archivversion: {version!r}")
        _require(source.startswith(f"{archive_name}/02_In_Markdown_umgewandelt/{version}/")
                 and (source.lower().endswith(".pdf") if is_pdf else source.lower().endswith(".txt")),
                 f"Originalquelle liegt außerhalb des passenden bearbeiteten Archivs: {source}")
        _require(md.startswith("Rechtsgebiete/") and md.lower().endswith(".md"),
                 f"Markdown liegt außerhalb der Rechtsgebiete: {md}")
        stand = _inside(root, md).parent
        _require(stand.name == version, f"Markdown und Originalquelle haben verschiedene Standordner: {md}")
        _require(_inside(root, report).is_relative_to(stand), f"Prüfbericht gehört nicht zum Standordner: {report}")
        matching = [e for e in (archive_entries if is_pdf else web_entries)
                    if isinstance(e, dict) and e.get(archive_key) == source]
        _require(len(matching) == 1, f"Originalquelle ist im {archive_name}-Register nicht eindeutig: {source}")
        registered = matching[0]
        pairs = {"markdown": md, "pruefbericht": report, "status": DONE,
                 "archivversion": version, archive_hash_key: entry.get(digest_key),
                 "sha256_markdown": entry.get("sha256_markdown")}
        for key, value in pairs.items():
            _require(registered.get(key) == value, f"Bestand und Archivregister widersprechen sich ({key}): {md}")
        metadata_keys = ("quellenabgleich", "pdf_seiten") if is_pdf else (
            "quellenabgleich", "erfasst_am", "quellenstand", "quellformat", "vollstaendigkeit")
        if not is_pdf:
            _require(isinstance(entry.get("quellenstand"), list) and bool(entry["quellenstand"])
                     and all(isinstance(value, str) and bool(value.strip()) for value in entry["quellenstand"]),
                     f"Standangabe der Webkopie fehlt: {md}")
            for key in ("erfasst_am", "quellformat", "vollstaendigkeit"):
                _require(isinstance(entry.get(key), str) and bool(entry[key].strip()),
                         f"Erforderliche Angabe zur Webkopie fehlt ({key}): {md}")
        for key in metadata_keys:
            _require(registered.get(key) == entry.get(key), f"Bestand und Archivregister widersprechen sich ({key}): {md}")
        for key in (digest_key, "sha256_markdown"):
            _require(isinstance(entry.get(key), str) and _HEX.fullmatch(entry[key]) is not None,
                     f"Erforderliche Prüfsumme fehlt ({key}): {md}")
        add_source(source, entry.get(digest_key))
        add_source(md, entry.get("sha256_markdown"))
        add_source(report)
        (selected_archive if is_pdf else selected_web_archive).append(registered)
        stand_entries.setdefault(stand, []).append(entry)

    for stand, documents in stand_entries.items():
        # Nur ausdrücklich registrierte Standordner, niemals das gesamte Projekt.
        for folder, dirs, names in os.walk(stand, followlinks=False):
            for name in dirs + names:
                child = Path(folder) / name
                relative = child.relative_to(root).as_posix()
                _inside(root, relative)
            for name in names:
                add_source((Path(folder) / name).relative_to(root).as_posix())
        pdf_hashes = {e["sha256_original_pdf"] for e in documents if "original_pdf" in e}
        web_hashes = {e["sha256_original_quelle"] for e in documents if "original_quelle" in e}
        md_hashes = {e["sha256_markdown"] for e in documents}
        xml_hashes = {f.sha256 for f in files.values()
                      if f.source is not None and f.source.is_relative_to(stand)
                      and f.source.suffix.lower() == ".xml"}
        proved_pdf, proved_web, proved_md = set(), set(), set()
        for report in sorted((stand / "Pruefung").glob("*.json")):
            try:
                record = json.loads(report.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise SyncError(f"Prüfnachweis nicht lesbar: {report}") from exc
            if not isinstance(record, dict):
                continue  # Quellblocklisten haben keine Dateiprüfsummen.
            if "sha256_original_quelle" in record:
                _require(record.get("pruefung_erfolgreich") is True,
                         f"Prüfung der Webquelle ist nicht erfolgreich abgeschlossen: {report}")
            for keys, expected, proved in (("sha256_pdf pdf_sha256 source_pdf_sha256", pdf_hashes, proved_pdf),
                                           ("sha256_original_quelle", web_hashes, proved_web),
                                           ("sha256_markdown markdown_sha256", md_hashes, proved_md),
                                           ("sha256_xml xml_sha256", xml_hashes, set())):
                for key in keys.split():
                    if key in record:
                        _require(record[key] in expected, f"Veralteter oder widersprüchlicher Prüfnachweis ({key}): {report}")
                        proved.add(record[key])
        _require(proved_pdf == pdf_hashes and proved_web == web_hashes and proved_md == md_hashes,
                 f"Prüfnachweise für Originalquelle/Markdown fehlen oder sind unvollständig: {stand}")

    converter = "Werkzeuge/gesetz_konvertieren.py"
    if _inside(root, converter).is_file():
        add_source(converter)

    approved = dict(inventory)
    approved["unbearbeitete_pdfs"] = []
    if "unbearbeitete_webquellen" in approved:
        approved["unbearbeitete_webquellen"] = []
    add_generated("Bestand.json", _json(approved))
    add_generated("PDF_Archiv/Archivregister.json", _json({
        "pfadbasis": "Projektwurzel", "beschreibung": "Nur die in dieser Fassung enthaltenen bearbeiteten Original-PDFs.",
        "eintraege": selected_archive}))
    if selected_web_archive:
        add_generated("Web_Archiv/Archivregister.json", _json({
            "pfadbasis": "Projektwurzel", "beschreibung": "Nur die in dieser Fassung enthaltenen bearbeiteten Webkopien.",
            "eintraege": selected_web_archive}))
        add_generated("Web_Archiv/README.md", (
            "# Bearbeitete Webkopien\n\nDie Original-Textkopien wurden unverändert archiviert und in Markdown strukturiert. "
            "Die [Dokumentübersicht](../README.md) verknüpft Textkopie, Volltext und Prüfnachweis. "
            "Der jeweilige Prüfnachweis nennt den Stand und die Grenzen der Ausgangskopie. "
            "[Archivregister](Archivregister.json): Pfade beziehen sich auf die Wurzel dieser Fassung.\n").encode("utf-8"))
    rows = ["| Dokument | Markdown-Volltext | Originalquelle | Prüfnachweis |",
            "| --- | --- | --- | --- |"]
    for entry in entries:
        title = str(entry.get("titel", entry.get("kuerzel", "Dokument"))).replace("|", "\\|").replace("\n", " ")
        original = entry.get("original_pdf", entry.get("original_quelle"))
        source_label = "PDF" if "original_pdf" in entry else "Textkopie"
        rows.append(f"| {title} | [Markdown]({quote(entry['markdown'], safe='/')}) | "
                    f"[{source_label}]({quote(original, safe='/')}) | [Prüfung]({quote(entry['pruefbericht'], safe='/')}) |")
    readme = (f"# Wissensdatenbank – bereitgestellte Fassung\n\n"
              f"Erfassung/Quellenprüfung: **{checked}**. Enthalten: **{len(entries)} bearbeitete Dokumente**.\n\n"
              "Diese Fassung enthält die registrierten Markdown-Volltexte, Original-PDFs beziehungsweise Textkopien und zugehörigen "
              "Standordner mit Quellen, vorhandenen Abbildungen und Prüfnachweisen. Maßgeblich sind die Standangaben "
              "und Einschränkungen im jeweiligen Dokument; das Erfassungsdatum bestätigt keine aktuelle amtliche Gesamtfassung. "
              "Eine heutige Prüfung auf neue Gesetzesänderungen erfolgt beim Kopieren nicht.\n\n"
              "Die Dateiprüfsummen stehen in [MANIFEST.json](MANIFEST.json). Diese Datei wird erst nach "
              "vollständig geprüfter lokaler Bereitstellung erzeugt. Ein Cloud-Upload ist damit nicht bestätigt; "
              "den Synchronisationsstatus zeigt Google Drive für Desktop.\n\n" + "\n".join(rows) + "\n")
    add_generated("README.md", readme.encode("utf-8"))
    add_generated("PDF_Archiv/README.md", (
        "# Bearbeitete Original-PDFs\n\nAlle hier enthaltenen PDFs wurden in Markdown umgewandelt. "
        "Die [Dokumentübersicht](../README.md) verknüpft PDF, Volltext und Prüfnachweis. "
        "[Archivregister](Archivregister.json): Pfade beziehen sich auf die Wurzel dieser Fassung.\n").encode("utf-8"))
    fingerprint = _digest(_json([files[p].record() for p in sorted(files)]))
    return _Plan(root, len(entries), checked, files, fingerprint)


def inspect_source(root: Path) -> dict:
    """Bestand, Register und Prüfnachweise lesen; ohne Schreibzugriff planen."""
    return _plan(root).summary()


def _match(path: Path, expected: bytes) -> None:
    _require(path.is_file() and path.read_bytes() == expected,
             f"Vorhandene Datei weicht ab; sie wird nicht überschrieben: {path}")


def _write_new(path: Path, data: bytes) -> bool:
    """Fertig geschriebene Datei exklusiv installieren; vorhandene Bytes prüfen."""
    if path.exists():
        _match(path, data)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".cloud-sync-", suffix=".tmp", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            if os.name == "nt":
                os.rename(temporary, path)  # Windows: bestehende Ziele werden nie ersetzt.
            else:
                os.link(temporary, path)  # POSIX: ebenfalls exklusiv und atomisch.
        except FileExistsError:
            _match(path, data)
            return False
        _match(path, data)
        return True
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()  # Nur die von diesem Aufruf erzeugte temporäre Datei.


def _validate_snapshot(snapshot: Path, plan: _Plan, allow_partial: bool) -> None:
    allowed = set(plan.files) | {SNAPSHOT_MARKER, MANIFEST}
    for folder, dirs, names in os.walk(snapshot, followlinks=False):
        for name in dirs + names:
            _inside(snapshot, (Path(folder) / name).relative_to(snapshot).as_posix())
        for name in names:
            relative = (Path(folder) / name).relative_to(snapshot).as_posix()
            _require(relative in allowed, f"Unbekannte Datei in bestehender Fassung: {relative}")
            if relative in plan.files:
                _match(snapshot / relative, plan.files[relative].read())
    if not allow_partial:
        for relative, item in plan.files.items():
            _match(_inside(snapshot, relative), item.read())


def publish(root: Path, target_parent: Path, log: Callable[[str], None] = lambda _: None) -> dict:
    """Geprüfte Fassung bereitstellen. Der tatsächliche Drive-Upload bleibt unbekannt."""
    root = Path(root).expanduser().resolve()
    parent = Path(target_parent).expanduser().resolve()
    cloud = (parent / CLOUD_NAME).resolve()
    _require(not parent.is_relative_to(root) and not root.is_relative_to(cloud),
             "Quelle und Ziel dürfen nicht ineinander liegen. Bitte einen separaten Zielordner wählen.")
    _require(cloud == parent / CLOUD_NAME, "Das Cloud-Ziel darf keine Verknüpfung sein.")
    plan = _plan(root)  # Vollständige Prüfung vor dem ersten Schreibzugriff.
    log(f"{plan.documents} Dokumente geprüft; {len(plan.files)} Dateien werden bereitgestellt.")
    marker_data = _json({"tool": TOOL})
    if cloud.exists():
        _match(_inside(cloud, MARKER), marker_data)
    else:
        parent.mkdir(parents=True, exist_ok=True)
        try:
            cloud.mkdir()
        except FileExistsError as exc:
            raise SyncError("Ziel wurde gleichzeitig angelegt; bitte erneut prüfen.") from exc
        _write_new(_inside(cloud, MARKER), marker_data)
    current_path = _inside(cloud, CURRENT)
    current_before = current_path.read_bytes() if current_path.exists() else None
    if current_before is not None:
        previous = _read_json(current_path)
        _require(previous.get("tool") == TOOL and previous.get("state") == "lokal_bereitgestellt"
                 and re.fullmatch(r"Fassungen/Stand_\d{4}-\d{2}-\d{2}_[0-9a-f]{12}", previous.get("snapshot", "")) is not None,
                 "AKTUELL.json ist keine gültige, vom Werkzeug verwaltete Referenz.")
        _require(_inside(cloud, previous["snapshot"] + "/" + MANIFEST).is_file(),
                 "Die vorherige aktuelle Fassung ist unvollständig; zuerst das Ziel prüfen.")
    snapshot = _inside(cloud, f"Fassungen/{plan.version}")
    snapshot_marker = _json({"tool": TOOL, "fingerprint": plan.fingerprint})
    if snapshot.exists():
        _match(_inside(snapshot, SNAPSHOT_MARKER), snapshot_marker)
    else:
        snapshot.mkdir(parents=True)
        _write_new(_inside(snapshot, SNAPSHOT_MARKER), snapshot_marker)
    manifest = _json({"tool": TOOL, "state": "lokal_bereitgestellt", "cloud_upload": "unbekannt",
                      **plan.summary(), "entries": [plan.files[p].record() for p in sorted(plan.files)]})
    manifest_path = _inside(snapshot, MANIFEST)
    complete = manifest_path.exists()
    if complete:
        _match(manifest_path, manifest)
    _validate_snapshot(snapshot, plan, allow_partial=not complete)
    copied = unchanged = 0
    for relative in sorted(plan.files):
        if relative == "README.md":
            continue
        item = plan.files[relative]
        changed = _write_new(_inside(snapshot, relative), item.read())
        copied += int(changed)
        unchanged += int(not changed)
        log(f"{'Kopiert' if changed else 'Unverändert'}: {relative}")
    # Lesbarer Einstieg und Fertigmanifest erst nach erneuter Prüfung aller Nutzdateien.
    for relative, item in plan.files.items():
        if relative != "README.md":
            _match(_inside(snapshot, relative), item.read())
    changed = _write_new(_inside(snapshot, "README.md"), plan.files["README.md"].read())
    copied += int(changed)
    unchanged += int(not changed)
    _validate_snapshot(snapshot, plan, allow_partial=False)
    _write_new(manifest_path, manifest)
    _write_new(_inside(cloud, "README.md"), (
        "# Wissensdatenbank in der Cloud\n\n"
        "[AKTUELL.json](AKTUELL.json) nennt die zuletzt vollständig lokal bereitgestellte Fassung. "
        "Unter [Fassungen](Fassungen/) bleiben frühere Fassungen erhalten. "
        "Öffne die README.md der dort genannten Fassung für die Links zu allen Dokumenten.\n\n"
        "Diese Dateien werden lokal bereitgestellt. Google Drive für Desktop übernimmt den Upload, "
        "sofern dieser Ordner dafür eingerichtet ist. Der Uploadstatus ist dem Werkzeug nicht bekannt. "
        "Bei einer nur teilweise hochgeladenen Fassung fehlen möglicherweise noch Dateien; "
        "das MANIFEST.json enthält die vollständige Dateiliste und Prüfsummen.\n").encode("utf-8"))
    current = _json({"tool": TOOL, "state": "lokal_bereitgestellt", "cloud_upload": "unbekannt",
                     "snapshot": f"Fassungen/{plan.version}", "fingerprint": plan.fingerprint,
                     "documents": plan.documents, "quellenabgleich": plan.date})
    now = current_path.read_bytes() if current_path.exists() else None
    _require(now == current_before or now == current, "AKTUELL.json wurde gleichzeitig verändert; bitte erneut starten.")
    if now != current:
        with tempfile.NamedTemporaryFile(prefix=".cloud-sync-", suffix=".tmp", dir=cloud, delete=False) as stream:
            temp = Path(stream.name)
            try:
                stream.write(current)
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException:
                stream.close()
                temp.unlink(missing_ok=True)
                raise
        try:
            os.replace(temp, current_path)  # Nur die zuvor geprüfte, eigene Aktualitätsreferenz.
        finally:
            temp.unlink(missing_ok=True)
    return {**plan.summary(), "snapshot": str(snapshot), "copied": copied,
            "unchanged": unchanged, "state": "lokal_bereitgestellt", "cloud_upload": "unbekannt"}
