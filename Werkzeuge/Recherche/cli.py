"""Import, inspect, search and export the local research prototype."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parents[1]
DATA = APP / ".daten"


def build_store(data=DATA, semantic=True):
    from store import Store
    if semantic:
        from embeddings import LocalEmbedder
        embedder = LocalEmbedder(Path(data) / "modelle")
    else:
        embedder = None
    return Store(Path(data) / "recherche.sqlite3", embedder)


def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def interactive(store, source="lokale Recherche"):
    print("Steuerrechtliche Wissensdatenbank – " + source)
    print("Eine Sachverhaltsfrage zu den importierten Rechtsquellen eingeben.")
    print("Die Suche zeigt Quellen; sie erstellt noch keine steuerliche Antwort.")
    print("Leere Eingabe beendet. :fassungen zeigt die vorhandenen Quellenstände.\n")
    while True:
        query = input("Frage > ").strip()
        if not query:
            return
        try:
            if query == ":fassungen":
                for version in store.list_versions()["versions"]:
                    print(version["release_id"], "[aktiv]" if version["active"] else "")
                    for doc in version["documents"]:
                        print(" ", doc["abbreviation"], "; ".join(doc["source_status"]))
                continue
            result = store.search(query)
            for i, hit in enumerate(result["results"], 1):
                print(f'\n{i}. {hit["title"]}')
                print("   " + hit["excerpt"][:450].replace("\n", " "))
                print("   Quellenstand: " + "; ".join(hit["source_status"]))
            print(f'\nSuchzeit: {result["elapsed_ms"]} ms. {result["version_notice"]}')
            choice = input("Treffer-Nummer zum vollständigen Lesen, Enter für neue Frage > ").strip()
            if choice:
                index = int(choice) - 1
                if not 0 <= index < len(result["results"]):
                    raise ValueError("Diese Treffer-Nummer gibt es nicht.")
                hit = result["results"][index]
                offset = 0
                while True:
                    page = store.fetch(hit["id"], offset=offset)
                    print("\n" + page["text"])
                    if not page["has_more"]:
                        break
                    input("Enter für Fortsetzung > ")
                    offset = page["next_offset"]
                print("\nQuelle:", hit["source_path"])
                print("Fassung:", hit["release_id"], "\n")
        except (ValueError, RuntimeError) as exc:
            print("Hinweis:", exc, "\n")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="Alle registrierten Dokumente prüfen und neue Fassung aktivieren")
    imp.add_argument("--root", type=Path, default=ROOT)
    imp.add_argument("--documents", nargs="+", default=None,
                     help="Optional auf Registerkürzel begrenzen; Standard: vollständiger Bestand")
    sub.add_parser("versions")
    sub.add_parser("interactive")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--document")
    search.add_argument("--release")
    search.add_argument("--mode", choices=["hybrid", "lexical", "semantic"], default="hybrid")
    search.add_argument("--limit", type=int, default=8)
    get = sub.add_parser("get")
    get.add_argument("document")
    get.add_argument("reference")
    get.add_argument("--release")
    get.add_argument("--offset", type=int, default=0)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("id")
    fetch.add_argument("--offset", type=int, default=0)
    export = sub.add_parser("export", help="Vollständiges lokales Übertragungspaket; kein Upload")
    export.add_argument("target", type=Path)
    export.add_argument("--release")
    serve = sub.add_parser("serve")
    serve.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    semantic = args.command in ("import", "search", "serve", "interactive") and getattr(args, "mode", "hybrid") != "lexical"
    store = build_store(args.data, semantic)
    try:
        if args.command == "import":
            from parser import parse_collection
            collection = parse_collection(args.root, args.documents)
            output(store.import_collection(collection, args.root, progress=lambda text: print(text, file=sys.stderr, flush=True)))
        elif args.command == "versions":
            output(store.list_versions())
        elif args.command == "search":
            output(store.search(args.query, args.limit, args.document, args.release, args.mode))
        elif args.command == "get":
            output(store.get_provision(args.document, args.reference, args.release, args.offset))
        elif args.command == "fetch":
            output(store.fetch(args.id, args.offset))
        elif args.command == "export":
            output(store.export(args.target, args.release))
        elif args.command == "interactive":
            interactive(store)
        elif args.command == "serve":
            from server import create_server
            server = create_server(store)
            if args.transport == "http":
                print(f"Lokaler MCP-Dienst: http://127.0.0.1:{args.port}/mcp", file=sys.stderr)
                server.run(transport="streamable-http", host="127.0.0.1", port=args.port)
            else:
                server.run(transport="stdio")
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"Recherche nicht abgeschlossen: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
