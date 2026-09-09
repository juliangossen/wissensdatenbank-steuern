"""Read-only integration check against the real private Supabase pilot."""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))
from cloud.client import build_cloud_store
from evaluate import CASES
from mcp import Client
from server import create_server


def verify():
    store = build_cloud_store()
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "backend": "supabase",
              "login": "kb_reader_login", "remote_hosted": False,
              "notice": "Technischer Test mit bekannten Ankerstellen; keine fachlich unabhängig geprüfte Rechtsberatung.", "cases": []}
    for name, query, document, expected in CASES:
        result = store.search(query, document=document, limit=8)
        found = {(r["document"], r["reference"]) for r in result["results"]}
        case = {"name": name, "anchor_found_top8": bool(found & expected), "elapsed_ms": result["elapsed_ms"],
                "results": [{"document": r["document"], "reference": r["reference"]} for r in result["results"]]}
        report["cases"].append(case)
        print(name, case["anchor_found_top8"], case["elapsed_ms"], flush=True)

    async def mcp_checks():
        async with Client(create_server(store)) as client:
            tools = (await client.list_tools()).tools
            assert {t.name for t in tools} == {"search", "fetch", "get_provision", "list_versions", "fetch_asset"}
            versions = await client.call_tool("list_versions", {})
            assert not versions.is_error
            release = next(v for v in versions.structured_content["versions"] if v["active"])
            rid = release["release_id"]
            exact = await client.call_tool("get_provision", {"document": "UStG", "reference": "§ 15", "release_id": rid})
            assert not exact.is_error
            current = exact.structured_content
            body = current["text"]
            while current["has_more"]:
                result = await client.call_tool("fetch", {"id": current["id"], "offset": current["next_offset"]})
                assert not result.is_error
                current = result.structured_content
                body += current["text"]
            assert hashlib.sha256(body.encode("utf-8")).hexdigest() == current["text_sha256"]
            assert "Vorsteuerabzug" in body
            for ref in ("23.1", "23.2", "23.3", "23.4", "4.12.10", "15.2a"):
                result = await client.call_tool("get_provision", {"document": "UStAE", "reference": ref, "release_id": rid})
                assert not result.is_error
            annex = await client.call_tool("get_provision", {"document": "BewG", "reference": "Anlage 24", "release_id": rid})
            assert not annex.is_error and annex.structured_content["asset_ids"]
            picture = await client.call_tool("fetch_asset", {"release_id": rid, "asset_id": annex.structured_content["asset_ids"][0]})
            assert not picture.is_error and any(c.type == "image" for c in picture.content)
            missing = await client.call_tool("get_provision", {"document": "UStG", "reference": "§ 999999", "release_id": rid})
            assert missing.is_error
            search = await client.call_tool("search", {"query": "UStG § 15 Vorsteuerabzug", "release_id": rid})
            assert not search.is_error and search.structured_content["results"][0]["reference"] == "§ 15"
            report.update(release_id=rid, mcp_tools=5, mcp_full_text_hash=True, mcp_image=True,
                          reference_aliases=True, missing_reference_error=True)
    asyncio.run(mcp_checks())
    report["known_anchors_found"] = sum(c["anchor_found_top8"] for c in report["cases"])
    (APP / "cloud" / "MCP_Cloudpruefung.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("MCP cloud backend checks passed; anchors:", report["known_anchors_found"], "/", len(CASES))
    return report


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    verify()
