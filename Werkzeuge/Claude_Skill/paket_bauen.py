"""Build the portable Claude skill ZIP from the maintained repository folder."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
NAME = "steuerrecht-recherche"
SKILL = ROOT / ".claude" / "skills" / NAME
OUTPUT = ROOT / "dist" / (NAME + ".zip")


def build() -> Path:
    main = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not main.startswith("---\n") or "\n---\n" not in main[4:]:
        raise ValueError("SKILL.md benötigt YAML-Frontmatter.")
    frontmatter = main.split("---", 2)[1]
    if not re.search(r"^name: " + re.escape(NAME) + r"$", frontmatter, re.M):
        raise ValueError("Skillname und Paketordner stimmen nicht überein.")
    description = re.search(r"^description: (.+)$", frontmatter, re.M)
    if not description or len(description.group(1)) > 200:
        raise ValueError("Beschreibung fehlt oder überschreitet 200 Zeichen.")
    files = sorted(p for p in SKILL.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    if not files or any(p.is_symlink() or p.suffix not in {".md", ".py"} for p in files):
        raise ValueError("Das Paket darf nur reguläre Markdown- und Python-Dateien enthalten.")
    for p in files:
        if not p.resolve().is_relative_to(SKILL.resolve()):
            raise ValueError("Dateipfad verlässt den Skillordner.")
    for required in ["SKILL.md", "references/github.md", "references/supabase.md", "scripts/github_recherche.py"]:
        if not (SKILL / required).is_file():
            raise ValueError("Erforderliche Paketdatei fehlt: " + required)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in files:
            info = zipfile.ZipInfo(NAME + "/" + p.relative_to(SKILL).as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, p.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP-Prüfung fehlgeschlagen.")
        for p in files:
            name = NAME + "/" + p.relative_to(SKILL).as_posix()
            if archive.read(name) != p.read_bytes():
                raise ValueError("Paketdatei weicht von der Arbeitsdatei ab: " + name)
    temporary.replace(OUTPUT)
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    OUTPUT.with_suffix(".zip.sha256").write_bytes((digest + "  " + OUTPUT.name + "\n").encode("ascii"))
    print(f"{OUTPUT.relative_to(ROOT)}: {len(files)} Dateien, {OUTPUT.stat().st_size} Bytes")
    print("SHA-256:", digest)
    return OUTPUT


if __name__ == "__main__":
    build()
