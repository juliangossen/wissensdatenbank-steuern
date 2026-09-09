"""Reproducible technical pilot check, not an expert legal benchmark."""
import asyncio
import json
from pathlib import Path
import time

from cli import APP, ROOT, build_store
from parser import parse_collection
from store import digest

CASES = [
    ("Exakte Vorschrift", "UStG § 15 Vorsteuerabzug", None, {("UStG", "§ 15")}),
    ("Gemischt genutzter Pkw", "Ein gekaufter Pkw wird für berufliche Fahrten und privat genutzt. Vorsteuer bei einem Unternehmer.", None, {("UStAE", "15.23"), ("UStG", "§ 15")}),
    ("Kleine Umsätze", "Ich habe nur geringe Umsätze. Wann bin ich als Kleinunternehmer von der Umsatzsteuer befreit?", None, {("UStG", "§ 19"), ("UStAE", "19.1")}),
    ("Grundstücksbewertung", "Wie wird ein vermietetes Grundstück im Ertragswertverfahren bewertet?", "BewG", {("BewG", "§ 184"), ("BewG", "§ 185"), ("BewG", "§ 252")}),
    ("Mehrteilige UStAE-Nummer", "Vermietung und Verpachtung von Betriebsvorrichtungen", "UStAE", {("UStAE", "4.12.10")}),
    ("Rechnungsvoraussetzung", "Für den Vorsteuerabzug fehlt mir eine ordnungsgemäße Rechnung.", "UStAE", {("UStAE", "15.2a")}),
]


def evaluate():
    store = build_store()
    collection = parse_collection(ROOT, ["UStG", "UStAE", "BewG"])
    release = store.list_versions()["versions"][0]["release_id"]
    report = {"release_id": release, "notice": "Technischer, nicht fachlich unabhängig geprüfter Recherche-Probelauf. Erwartete Ankertreffer sind keine vollständige Liste rechtlich einschlägiger Vorschriften.", "cases": [], "checks": {}}
    for name, query, document, expected in CASES:
        modes = {}
        for mode in ("hybrid", "lexical", "semantic"):
            result = store.search(query, limit=8, document=document, release_id=release, mode=mode)
            found = {(r["document"], r["reference"]) for r in result["results"]}
            modes[mode] = {"anchor_found_top8": bool(expected & found), "elapsed_ms": result["elapsed_ms"], "results": [{"title": r["title"], "reference": r["reference"], "document": r["document"], "matched_by": r["matched_by"]} for r in result["results"]]}
        report["cases"].append({"name": name, "query": query, "document": document, "expected_anchors": sorted(expected), "modes": modes})
        print(name, {m: (r["anchor_found_top8"], r["elapsed_ms"]) for m, r in modes.items()}, flush=True)

    pages = 0
    for p in collection["provisions"]:
        result = store.get_provision(next(d["abbreviation"] for d in collection["documents"] if d["doc_id"] == p["doc_id"]), p["reference"], release)
        text = result["text"]
        pages += 1
        while result["has_more"]:
            result = store.fetch(result["id"], result["next_offset"])
            text += result["text"]
            pages += 1
        if text != p["markdown"]:
            raise AssertionError("Unvollständige Fundstelle: " + p["provision_id"])
    for asset in collection["assets"]:
        metadata, content = store.asset(release, asset["asset_id"])
        if digest(content) != asset["sha256"]:
            raise AssertionError("Unvollständige Anlage: " + asset["asset_id"])
    for ref in ("23.1", "23.2", "23.3", "23.4"):
        result = store.get_provision("UStAE", ref, release)
        assert "23.1" in result["reference"]
    report["checks"].update({"complete_provisions": len(collection["provisions"]), "pages_compared": pages, "verified_assets": len(collection["assets"]), "grouped_reference_aliases": 4})

    async def mcp_check():
        from mcp import Client
        from server import create_server
        async with Client(create_server(store)) as client:
            result = await client.call_tool("get_provision", {"document": "UStG", "reference": "§ 15", "release_id": release})
            assert not result.is_error and "Vorsteuerabzug" in result.structured_content["text"]
            result = await client.call_tool("get_provision", {"document": "BewG", "reference": "Anlage 24", "release_id": release})
            assert not result.is_error
            asset_id = result.structured_content["asset_ids"][0]
            image = await client.call_tool("fetch_asset", {"release_id": release, "asset_id": asset_id})
            assert not image.is_error and any(c.type == "image" for c in image.content)
            report["checks"]["mcp_fulltext_and_image"] = True
    asyncio.run(mcp_check())
    target = APP / ".daten" / "Pilotpruefung.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["checks"], ensure_ascii=False))
    return report


if __name__ == "__main__":
    evaluate()
