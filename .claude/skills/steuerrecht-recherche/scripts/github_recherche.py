#!/usr/bin/env python3
"""Read-only, commit-pinned research in the public tax-law repository (stdlib).

No token is needed. Document hashes cover original downloaded bytes, before
UTF-8 decoding. Search is literal, case-insensitive token matching in Markdown
paragraphs; it is neither German stemming nor semantic search. All read offsets
refer to Unicode characters in the decoded document, not bytes or line numbers.
"""

import argparse
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener


REPOSITORY = "juliangossen/wissensdatenbank-steuern"
API_ROOT = "https://api.github.com/repos/" + REPOSITORY
RAW_ROOT = "https://raw.githubusercontent.com/" + REPOSITORY
WEB_ROOT = "https://github.com/" + REPOSITORY
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
MAX_REGISTER_BYTES = 2 * 1024 * 1024
MAX_READ_CHARS = 12000
MAX_READ_LINES = 150
MAX_DOCUMENTS = 5
SHA_RE = re.compile(r"[0-9a-fA-F]{40}\Z")
HASH_RE = re.compile(r"[0-9a-fA-F]{64}\Z")


class ResearchError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ResearchError("network", "GitHub-Weiterleitung abgelehnt; die festgelegte Quelle wurde nicht geladen.")


def validate_commit(commit):
    if not isinstance(commit, str) or not SHA_RE.fullmatch(commit):
        raise ResearchError("commit", "Eine vollständige Commit-SHA mit 40 Hexzeichen ist erforderlich. Zuerst 'resolve' aufrufen.")
    return commit.lower()


def validate_ref(ref):
    if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}", ref)
            or any(part in ("", ".", "..") or part.endswith(".") or part.endswith(".lock")
                   for part in ref.split("/")) or ".." in ref):
        raise ResearchError("ref", "Ungültiger Git-Ref. Einen einfachen Branch-/Tag-Namen oder eine Commit-SHA verwenden.")
    return ref


def validate_path(path):
    if (not isinstance(path, str) or not path or len(path) > 1000
            or any(ord(c) < 32 for c in path) or any(c in path for c in "\\:%?#")
            or path.startswith("/") or any(p in ("", ".", "..") for p in path.split("/"))):
        raise ResearchError("register", "Unsicherer Dateipfad im Quellenregister; Zugriff abgebrochen.")
    if PurePosixPath(path).suffix.lower() != ".md":
        raise ResearchError("register", "Das Quellenregister muss auf eine Markdown-Datei verweisen.")
    return path


def github_url(commit, path, first_line=None, last_line=None):
    url = WEB_ROOT + "/blob/" + validate_commit(commit) + "/" + quote(path, safe="/")
    if first_line is not None:
        url += "?plain=1#L" + str(first_line)
        if last_line is not None and last_line != first_line:
            url += "-L" + str(last_line)
    return url


def fetch_bytes(url, max_bytes):
    request = Request(url, headers={"User-Agent": "steuerrecht-recherche-skill/1.0",
                                   "Accept": "application/vnd.github.sha" if url.startswith(API_ROOT + "/commits/") else "text/plain",
                                   "Accept-Encoding": "identity"})
    deadline = time.monotonic() + 40
    try:
        with build_opener(NoRedirects()).open(request, timeout=15) as response:
            if response.status != 200 or response.geturl() != url:
                raise ResearchError("network", "GitHub lieferte keine unveränderte erfolgreiche Antwort.")
            length = response.headers.get("Content-Length")
            if length and (not length.isdigit() or int(length) > max_bytes):
                raise ResearchError("size", "Die GitHub-Datei überschreitet das erlaubte Download-Limit.")
            chunks, size = [], 0
            while True:
                if time.monotonic() > deadline:
                    raise ResearchError("network", "GitHub-Download dauerte zu lange; später erneut versuchen.")
                chunk = response.read(min(65536, max_bytes + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > max_bytes:
                    raise ResearchError("size", "Die GitHub-Datei überschreitet das erlaubte Download-Limit.")
            if length and size != int(length):
                raise ResearchError("network", "Unvollständiger GitHub-Download; keine Inhalte verwendet.")
            return b"".join(chunks)
    except HTTPError as exc:
        if exc.code in (403, 429):
            message = "GitHub-Zugriff blockiert oder Anfragelimit erreicht (HTTP %s). Netzwerkfreigabe für api.github.com und raw.githubusercontent.com prüfen oder später erneut versuchen." % exc.code
        elif exc.code == 404:
            message = "GitHub-Quelle nicht gefunden (HTTP 404). Repository, Ref und registrierten Pfad prüfen."
        else:
            message = "GitHub-Anfrage fehlgeschlagen (HTTP %s); später erneut versuchen." % exc.code
        raise ResearchError("network", message) from None
    except (URLError, TimeoutError, socket.timeout, OSError, HTTPException):
        raise ResearchError("network", "GitHub nicht erreichbar. Netzwerkfreigabe für api.github.com und raw.githubusercontent.com prüfen. Ohne Zugriff wurde keine Quelle gelesen.") from None


def parse_json(data, kind):
    try:
        return json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ResearchError(kind, "GitHub lieferte kein gültiges UTF-8-JSON.") from None


def resolve(ref="main", fetch=fetch_bytes):
    ref = validate_ref(ref)
    # The SHA media type avoids downloading the potentially huge commit diff.
    data = fetch(API_ROOT + "/commits/" + quote(ref, safe=""), 1024)
    try:
        commit = validate_commit(data.decode("ascii").strip())
    except UnicodeDecodeError:
        raise ResearchError("commit", "GitHub lieferte keine gültige Commit-SHA.") from None
    return {"repository": REPOSITORY, "requested_ref": ref, "commit": commit,
            "commit_url": WEB_ROOT + "/commit/" + commit,
            "next_step": "Diese Commit-SHA bei catalog, headings, search und read unverändert verwenden."}


class Repository:
    def __init__(self, commit, cache_dir=None, fetch=fetch_bytes):
        self.commit = validate_commit(commit)
        self.fetch = fetch
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "claude-steuerrecht-recherche-v1"
        raw = fetch(RAW_ROOT + "/" + self.commit + "/Bestand.json", MAX_REGISTER_BYTES)
        self.register_sha256 = hashlib.sha256(raw).hexdigest()
        self.register = parse_json(raw, "register")
        if not isinstance(self.register, dict) or not isinstance(self.register.get("eintraege"), list):
            raise ResearchError("register", "Bestand.json enthält keine gültige Dokumentliste.")
        self.entries = self.register["eintraege"]
        if not 1 <= len(self.entries) <= 1000 or self.register.get("dokumente") != len(self.entries):
            raise ResearchError("register", "Dokumentanzahl im Quellenregister ist inkonsistent.")
        self.by_name = {}
        for entry in self.entries:
            if not isinstance(entry, dict) or len(json.dumps(entry, ensure_ascii=False)) > 8000:
                raise ResearchError("register", "Ungültiger oder übergroßer Eintrag im Quellenregister.")
            name = entry.get("kuerzel")
            if not isinstance(name, str) or not name.strip() or len(name) > 200 or name.casefold() in self.by_name:
                raise ResearchError("register", "Dokumentkürzel im Quellenregister fehlen oder sind mehrdeutig.")
            validate_path(entry.get("markdown"))
            digest = entry.get("sha256_markdown")
            if not isinstance(digest, str) or not HASH_RE.fullmatch(digest):
                raise ResearchError("register", "Markdown-Prüfsumme im Quellenregister fehlt oder ist ungültig.")
            self.by_name[name.casefold()] = entry

    def envelope(self):
        return {"repository": REPOSITORY, "commit": self.commit,
                "register_sha256": self.register_sha256,
                "register_url": github_url(self.commit, "Bestand.json"),
                "quellenabgleich": self.register.get("quellenabgleich"),
                "document_count": len(self.entries)}

    def source(self, entry):
        result = dict(entry)
        result["github_url"] = github_url(self.commit, entry["markdown"])
        return result

    def select(self, names):
        if not 1 <= len(names) <= MAX_DOCUMENTS:
            raise ResearchError("selection", "Ein bis fünf Dokumente anhand ihres exakten Katalog-Kürzels auswählen.")
        selected = []
        for name in names:
            entry = self.by_name.get(name.casefold())
            if entry is None:
                raise ResearchError("selection", "Unbekanntes Dokumentkürzel. Die genaue Schreibweise mit 'catalog' ermitteln.")
            if entry not in selected:
                selected.append(entry)
        return selected

    def document(self, entry):
        digest = entry["sha256_markdown"].lower()
        key = hashlib.sha256((self.commit + ":" + entry["markdown"]).encode("utf-8")).hexdigest()
        cache_file = self.cache_dir / (key + ".bin")
        data = None
        try:
            if cache_file.is_file() and cache_file.stat().st_size <= MAX_DOCUMENT_BYTES:
                with cache_file.open("rb") as handle:
                    candidate = handle.read(MAX_DOCUMENT_BYTES + 1)
                if hashlib.sha256(candidate).hexdigest() == digest:
                    data = candidate
        except OSError:
            pass  # A cache is optional; an unreadable cache is never evidence.
        if data is None:
            data = self.fetch(RAW_ROOT + "/" + self.commit + "/" + quote(entry["markdown"], safe="/"), MAX_DOCUMENT_BYTES)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ResearchError("integrity", "SHA256 der vollständigen Markdown-Rohdatei stimmt nicht mit Bestand.json überein. Keine Inhalte verwendet.")
            temporary = None
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=self.cache_dir, delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(data)
                os.replace(temporary, cache_file)
            except OSError:
                pass  # Verified data can still be read if caching is unavailable.
            finally:
                if temporary is not None:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        pass
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ResearchError("encoding", "Die geprüfte Markdown-Datei ist kein gültiges UTF-8.") from None

    def catalog(self, offset=0, limit=10):
        check_page(offset, limit, 20)
        return dict(self.envelope(), **pagination(len(self.entries), offset, limit),
                    documents=[self.source(entry) for entry in self.entries[offset:offset + limit]])

    def read(self, name, offset=0, limit=MAX_READ_CHARS):
        check_page(offset, limit, MAX_READ_CHARS)
        entry = self.select([name])[0]
        text = self.document(entry)
        if offset > len(text):
            raise ResearchError("offset", "Lese-Offset liegt hinter dem Dokumentende.")
        end = min(len(text), offset + limit)
        # Cap line-number overhead too, without skipping a character at boundaries.
        probe = offset
        for _ in range(MAX_READ_LINES):
            newline = text.find("\n", probe, end)
            if newline < 0:
                break
            probe = newline + 1
        else:
            end = probe
        chunk = text[offset:end]
        first_line = text.count("\n", 0, offset) + 1
        last_line = first_line + chunk.count("\n") - int(chunk.endswith("\n")) if chunk else first_line
        numbered = "".join("L%s: %s" % (first_line + index, part)
                           for index, part in enumerate(re.findall(r"[^\n]*\n|[^\n]+$", chunk)))
        return dict(self.envelope(), source=self.source(entry), sha256_verified=True,
                    offset_unit="unicode_characters", offset=offset, returned_characters=len(chunk),
                    total_characters=len(text), next_offset=end if end < len(text) else None,
                    start_line=first_line, end_line=last_line,
                    starts_mid_line=offset > 0 and text[offset - 1] != "\n",
                    ends_mid_line=end < len(text) and end > 0 and text[end - 1] != "\n",
                    text=chunk, numbered_text=numbered,
                    source_url=github_url(self.commit, entry["markdown"], first_line, last_line),
                    scope="Dokumentfenster; keine automatische Zusicherung einer vollständigen Norm. Fußnoten, Verweise und Anlagen gegebenenfalls gesondert lesen.")

    def headings(self, name, query="", offset=0, limit=20):
        check_page(offset, limit, 30)
        validate_query(query, allow_empty=True)
        entry = self.select([name])[0]
        text = self.document(entry)
        matches = list(re.finditer(r"(?m)^(#{1,6})[ \t]+([^\r\n]+)", text))
        normalized = " ".join(query.casefold().split())
        items = []
        for index, match in enumerate(matches):
            if normalized not in " ".join(match.group(2).casefold().split()):
                continue
            line = text.count("\n", 0, match.start()) + 1
            following = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            items.append({"heading": match.group(2)[:1000], "heading_truncated": len(match.group(2)) > 1000,
                          "level": len(match.group(1)), "line": line, "read_offset": match.start(),
                          "next_heading_offset": following,
                          "source_url": github_url(self.commit, entry["markdown"], line)})
        return dict(self.envelope(), source=self.source(entry), sha256_verified=True,
                    **pagination(len(items), offset, limit), headings=items[offset:offset + limit],
                    scope="Markdown-Überschriften als Fundstellenkandidaten; die nächste Überschrift ist keine verifizierte Normgrenze.")

    def search(self, names, query, mode="all", offset=0, limit=10):
        check_page(offset, limit, 20)
        validate_query(query)
        terms = list(dict.fromkeys(re.findall(r"[\w§]+(?:[.-]\w+)*", query)))
        if not terms or len(terms) > 12:
            raise ResearchError("query", "Eine bis zwölf Suchkomponenten verwenden.")
        if mode not in ("all", "any"):
            raise ResearchError("query", "Suchmodus muss 'all' oder 'any' sein.")
        patterns = [re.compile(re.escape(term), re.IGNORECASE) for term in terms]
        entries = self.select(names)
        results, total = [], 0
        for entry in entries:
            text = self.document(entry)
            for block in re.finditer(r"\S[\s\S]*?(?=\n[ \t\r]*\n|\Z)", text):
                matches = [pattern.search(block.group()) for pattern in patterns]
                if not (all(matches) if mode == "all" else any(matches)):
                    continue
                if offset <= total < offset + limit:
                    relative = min(match.start() for match in matches if match is not None)
                    center = block.start() + relative
                    start = max(block.start(), center - 180)
                    end = min(block.end(), start + 700)
                    line = text.count("\n", 0, center) + 1
                    results.append({"kuerzel": entry["kuerzel"], "line": line,
                                    "read_offset": max(0, start), "paragraph_offset": block.start(),
                                    "snippet": text[start:end], "snippet_truncated": start > block.start() or end < block.end(),
                                    "source_url": github_url(self.commit, entry["markdown"], line)})
                total += 1
        return dict(self.envelope(), sources=[self.source(entry) for entry in entries],
                    sha256_verified=True, query=query, terms=terms, mode=mode,
                    semantics="Wörtliche Teilzeichenfolgen ohne Beachtung der Groß-/Kleinschreibung; all/any innerhalb eines Markdown-Absatzes. Keine Wortstämme oder semantische Suche.",
                    order="document_order_then_source_order", **pagination(total, offset, limit),
                    results=results, scope="Vollständige ausgewählte Markdown-Dateien durchsucht; Treffer sind Ausschnitte und müssen mit read im Kontext gelesen werden.")


def check_page(offset, limit, maximum):
    if offset < 0 or not 1 <= limit <= maximum:
        raise ResearchError("pagination", "Offset muss mindestens 0 und Limit zwischen 1 und %s liegen." % maximum)


def pagination(total, offset, limit):
    return {"total": total, "offset": offset, "limit": limit,
            "next_offset": offset + limit if offset + limit < total else None}


def validate_query(query, allow_empty=False):
    if len(query) > 250 or (not allow_empty and not query.strip()):
        raise ResearchError("query", "Eine nichtleere Suchanfrage mit höchstens 250 Zeichen verwenden.")


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    resolver = commands.add_parser("resolve", help="Branch/Tag einmalig in unveränderliche Commit-SHA auflösen")
    resolver.add_argument("--ref", default="main")
    for name in ("catalog", "search", "headings", "read"):
        command = commands.add_parser(name)
        command.add_argument("--commit", required=True, help="40-stellige Commit-SHA aus resolve")
        command.add_argument("--cache-dir", help="Optionaler Cache-Ordner; Standard: System-Temp außerhalb des Skills")
        command.add_argument("--offset", type=int, default=0, help="0-basiert: Trefferindex; bei read Unicode-Zeichenoffset")
        command.add_argument("--limit", type=int, default={"catalog": 10, "search": 10, "headings": 20, "read": MAX_READ_CHARS}[name])
        if name != "catalog":
            command.add_argument("--document", required=True, action="append" if name == "search" else "store",
                                 help="Exaktes Katalog-Kürzel; bei search bis zu fünfmal verwendbar")
        if name in ("search", "headings"):
            command.add_argument("--query", required=name == "search", default="")
        if name == "search":
            command.add_argument("--mode", choices=("all", "any"), default="all")
    return parser


def main(argv=None):
    args = make_parser().parse_args(argv)
    try:
        if args.command == "resolve":
            result = resolve(args.ref)
        else:
            repository = Repository(args.commit, args.cache_dir)
            if args.command == "catalog":
                result = repository.catalog(args.offset, args.limit)
            elif args.command == "read":
                result = repository.read(args.document, args.offset, args.limit)
            elif args.command == "headings":
                result = repository.headings(args.document, args.query, args.offset, args.limit)
            else:
                result = repository.search(args.document, args.query, args.mode, args.offset, args.limit)
        print(json.dumps(dict(ok=True, **result), ensure_ascii=False, indent=2))
        return 0
    except ResearchError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": str(exc)}}, ensure_ascii=False))
        return 1
    except OSError:
        print(json.dumps({"ok": False, "error": {"code": "io", "message": "Lokaler Ein-/Ausgabefehler; keine erfolgreiche Recherche bestätigt."}}))
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
