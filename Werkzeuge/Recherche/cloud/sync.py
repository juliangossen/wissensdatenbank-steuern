"""Validate every registered source and publish a complete new cloud version."""
from datetime import date
import json
from pathlib import Path
import sys

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))
from cli import ROOT, build_store
from parser import parse_collection
from publish import publish


def sync():
    print("Cloud-Aktualisierung: alle in Bestand.json registrierten Dokumente und Quelldateien.", flush=True)
    collection = parse_collection(ROOT)
    store = build_store()
    version = store.import_collection(collection, ROOT, progress=lambda message: print(message, flush=True))
    rid = version["release_id"]
    del collection
    pointer = APP / ".daten" / "Cloud_Paketpfad.json"
    previous = json.loads(pointer.read_text(encoding="utf-8")) if pointer.is_file() else {}
    base = Path(previous["base"]) if previous.get("release_id") == rid else APP / ".daten" / "Cloud_Pakete" / ("Stand_" + date.today().isoformat()) / rid
    if not (base / "Export").exists():
        store.export(base / "Export", rid)
    manifest = json.loads((base / "Export" / "manifest.json").read_text(encoding="utf-8"))
    if manifest["release_id"] != rid:
        raise ValueError("Export passt nicht zur lokal aktiven Fassung.")
    # publish() validates and normalizes the authoritative export in memory.
    # A second, unused copy of every text, vector and original is unnecessary.
    result = publish(base / "Export", apply=True)
    temporary = pointer.with_suffix(".tmp")
    temporary.write_text(json.dumps({"release_id": rid, "base": str(base.resolve())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(pointer)
    print("Cloudfassung vollständig geprüft und verfügbar:", result["release_id"])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        sync()
    except Exception as exc:
        print("Cloud-Aktualisierung abgebrochen:", type(exc).__name__)
        print("Eine unvollständige Übertragung ersetzt die bisherige Cloudfassung nicht.")
        raise SystemExit(1) from None
