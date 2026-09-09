"""Local CLI/MCP frontend for the private Supabase corpus, using reader access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))

from cloud.postgres_store import PostgresStore
from cloud.reader_access import load_reader
from cli import interactive, output
from embeddings import LocalEmbedder


def build_cloud_store(semantic=True):
    project = json.loads((APP / "cloud" / "projekt.json").read_text(encoding="utf-8"))
    return PostgresStore(load_reader(project["project_ref"]),
                         LocalEmbedder(APP / ".daten" / "modelle") if semantic else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("interactive")
    sub.add_parser("versions")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--document")
    search.add_argument("--mode", choices=["hybrid", "lexical"], default="hybrid")
    get = sub.add_parser("get")
    get.add_argument("document")
    get.add_argument("reference")
    serve = sub.add_parser("serve")
    serve.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    serve.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    store = build_cloud_store(args.command in {"interactive", "search", "serve"} and getattr(args, "mode", "hybrid") != "lexical")
    if args.command == "interactive":
        interactive(store, source="Recherche in Supabase")
    elif args.command == "versions":
        output(store.list_versions())
    elif args.command == "search":
        output(store.search(args.query, document=args.document, mode=args.mode))
    elif args.command == "get":
        output(store.get_provision(args.document, args.reference))
    elif args.command == "serve":
        from server import create_server
        server = create_server(store)
        if args.transport == "stdio":
            server.run(transport="stdio")
        else:
            print(f"Lokaler MCP mit Cloud-Daten: http://127.0.0.1:{args.port}/mcp", file=sys.stderr)
            server.run(transport="streamable-http", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except Exception as exc:
        # Database/credential initialization failures must not expose secrets.
        print("Cloud-Recherche fehlgeschlagen:", type(exc).__name__, file=sys.stderr)
        raise SystemExit(1) from None
