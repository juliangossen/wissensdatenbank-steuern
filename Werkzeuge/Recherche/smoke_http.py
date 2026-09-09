"""Exercise the real loopback MCP transport and shut down the owned test server."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from mcp import Client


def main():
    app = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cloud", action="store_true", help="Dedizierten Supabase-Leser und Cloud-CLI testen")
    args = parser.parse_args()
    entry = app / "cloud" / "client.py" if args.cloud else app / "cli.py"
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    with tempfile.TemporaryFile() as logs:
        process = subprocess.Popen(
            [sys.executable, "-B", str(entry), "serve", "--transport", "http", "--port", str(port)],
            stdout=logs, stderr=logs,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise AssertionError("MCP-Dienst hat sich vor dem Test beendet.")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise AssertionError("MCP-Dienst wurde nicht erreichbar.")

            async def exercise():
                async with Client(f"http://127.0.0.1:{port}/mcp") as client:
                    discovered = await client.list_tools()
                    assert len(discovered.tools) == 5
                    search = await client.call_tool("search", {"query": "UStG § 15 Vorsteuerabzug", "limit": 3})
                    assert not search.is_error
                    hit = search.structured_content["results"][0]
                    assert hit["document"] == "UStG" and hit["reference"] == "§ 15"
                    result = await client.call_tool("fetch", {"id": hit["id"]})
                    assert not result.is_error and "Vorsteuerabzug" in result.structured_content["text"]
                    return {"http_mcp": True, "backend": "supabase" if args.cloud else "sqlite",
                            "loopback_only": True, "tools": len(discovered.tools), "release_id": hit["release_id"], "search_and_fetch": True}
            result = asyncio.run(exercise())
            if args.cloud:
                (app / "cloud" / "HTTP_Cloudpruefung.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, ensure_ascii=False))
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
