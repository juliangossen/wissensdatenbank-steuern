"""Read-only, lossless provision import from the checked knowledge-base register.

The full original Markdown is retained. Search text is a separate derived field.
Import dates never become legal validity dates. No source or register is changed.
"""
from __future__ import annotations

import hashlib
from bisect import bisect_right
from html import unescape
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path, PurePosixPath
import re
import unicodedata
from urllib.parse import unquote, urlsplit

PARSER_VERSION = "registered-provisions-v5"


class ParseError(ValueError):
    """The selected source cannot be imported without ambiguity or loss."""


_ANCHOR = re.compile(r'<a\s+id=["\']([^"\']+)["\'][^>]*>\s*</a>', re.I)
_HEADING = re.compile(r"(?m)^(#{1,6})[ \t]+([^\r\n]+)")
_FOOT_LINK = re.compile(r'<a\s+href=["\']#fn-[^"\']+["\'][^>]*>.*?</a>', re.I | re.S)
_MD_LINK = re.compile(r"!?\[([^\]\n]*)\]\((<[^>]+>|[^)\n]+)\)")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_REFERENCE = re.compile(
    r"^(AEAO\s+(?:zu|vor)\s+§§?\s*\d+[a-z]?(?:\s*(?:,|bis|und)\s*\d+[a-z]?)*|"
    r"(?:Artikel|Art\.?)\s*\d+[a-z]?(?:\s*/\s*§§?\s*\d+[a-z]?(?:\s+(?:bis|und)\s+\d+[a-z]?)?)?|"
    r"§§?\s*\d+[a-z]?(?:\s+(?:bis|und)\s+\d+[a-z]?)?|"
    r"(?:Anlage|Anhang)\s+(?:\d+[a-z]?|[IVXLCDM]+)|"
    r"[RH]\s+(?:[EB]\s+)?\d+[a-z]?(?:\.\d+[a-z]?)*(?:\s*\([\d ,–-]+\))?|"
    r"\d+[a-z]?(?:\.\d+[a-z]?)+(?:\s*[–-]\s*\d+[a-z]?(?:\.\d+[a-z]?)+)?)"
    r"(?=\W|$)", re.I
)
_NOTE_NAME = re.compile(r"(?:fn-|ntr(?:\d|\*))")
_ARCHIVE_SUFFIXES = {".md", ".txt", ".json", ".html", ".htm", ".pdf", ".xml", ".zip",
                     ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
_CROSS_REFERENCE = re.compile(
    r"§§?\s*\d+[a-z]?(?:\s*(?:,|bis|und)\s*\d+[a-z]?)*"
    r"(?:\s+(?:Abs\.|Absatz|Absätze)\s*\d+[a-z]?)?"
    r"(?:\s+Satz\s*\d+)?(?:\s+(?:Nr\.|Nummer)\s*\d+[a-z]?)?"
    r"(?:\s+(?:UStG|UStDV|BewG|AO|EStG|BGB))?|"
    r"(?:Abschnitt|A)\s+\d+[a-z]?(?:\.\d+[a-z]?)+|Anlage\s+\d+[a-z]?"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ParseError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path_inside(base: Path, relative: str) -> Path:
    """Reject absolute paths, traversal, Windows streams and filesystem links."""
    _require(isinstance(relative, str) and bool(relative), "Leerer Quellpfad.")
    path = PurePosixPath(relative)
    _require(not path.is_absolute() and ".." not in path.parts
             and "\\" not in relative and ":" not in relative,
             f"Unsicherer Quellpfad: {relative!r}")
    base = base.resolve()
    candidate = base.joinpath(*path.parts)
    _require(candidate.resolve().is_relative_to(base) and candidate.resolve() != base,
             f"Quellpfad verlässt den erlaubten Ordner: {relative}")
    cursor = candidate
    while cursor != base:
        _require(not cursor.is_symlink() and not getattr(cursor, "is_junction", lambda: False)(),
                 f"Verknüpfung als Quelle nicht zulässig: {relative}")
        cursor = cursor.parent
    _require(candidate.is_file(), f"Quelldatei fehlt: {relative}")
    return candidate


def _read_checked(root: Path, relative: str, expected: str, observed: dict[Path, str]) -> bytes:
    _require(isinstance(expected, str) and bool(_HASH.fullmatch(expected)),
             f"Registrierte SHA-256-Prüfsumme fehlt oder ist ungültig: {relative}")
    path = _path_inside(root, relative)
    data = path.read_bytes()
    _require(_sha256(data) == expected, f"Prüfsumme stimmt nicht: {relative}")
    observed[path] = expected
    return data


class _HTMLText(HTMLParser):
    _BLOCKS = {"p", "div", "table", "tr", "li", "ul", "ol", "br", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in self._BLOCKS:
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append(" | ")
        if tag == "a" and values.get("href"):
            self.links.append((values["href"], False))
        if tag == "img" and values.get("src"):
            self.links.append((values["src"], True))
            self.parts.append(values.get("alt") or "Abbildung")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._BLOCKS:
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def readable_text(markdown: str) -> str:
    """A searchable rendition; callers must quote the original Markdown instead."""
    text = _MD_LINK.sub(lambda m: m.group(1), markdown)
    parser = _HTMLText()
    parser.feed(text)
    text = "".join(parser.parts)
    text = re.sub(r"(?m)^\s*(?:#{1,6}\s+|```[^\n]*|\|[ :|\-]+\|\s*$)", "", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"\\([\W])", r"\1", text)
    text = unicodedata.normalize("NFC", unescape(text))
    return "\n".join(re.sub(r"[\t \u00a0]+", " ", line).strip()
                     for line in text.splitlines() if line.strip())


def _links(markdown: str) -> list[tuple[str, bool]]:
    parser = _HTMLText()
    parser.feed(markdown)
    links = parser.links
    for match in _MD_LINK.finditer(markdown):
        target = match.group(2).strip()
        if target.startswith("<"):
            target = target[1:target.index(">")]
        else:
            target = re.sub(r'\s+["\'].*["\']$', "", target)
        links.append((unescape(target), match.group(0).startswith("!")))
    return links


def _headings(markdown: str) -> list[dict]:
    anchors = list(_ANCHOR.finditer(markdown))
    anchor_ends = [match.end() for match in anchors]
    # Each heading gets its immediately preceding explicit source anchor only.
    result = []
    for match in _HEADING.finditer(markdown):
        index = bisect_right(anchor_ends, match.start()) - 1
        anchor = None
        aliases = []
        position = match.start()
        while index >= 0:
            candidate = anchors[index]
            gap = re.sub(r"<!--.*?-->", "", markdown[candidate.end():position], flags=re.S)
            if gap.strip():
                break
            anchor = candidate
            aliases.insert(0, candidate.group(1))
            position = candidate.start()
            index -= 1
        title = readable_text(_FOOT_LINK.sub("", match.group(2))).strip()
        reference = _REFERENCE.match(title)
        result.append({"start": anchor.start() if anchor else match.start(),
                       "heading_start": match.start(), "level": len(match.group(1)),
                       "title": title, "anchor": anchor.group(1) if anchor else None,
                       "anchor_aliases": aliases,
                       "reference": reference.group(1).strip() if reference else None})
    return result


def _footnotes(markdown: str, anchors: list[re.Match]) -> dict[str, str]:
    """Include continuation paragraphs up to the next anchor/major heading."""
    result = {}
    for index, anchor in enumerate(anchors):
        name = anchor.group(1)
        if not _NOTE_NAME.match(name):
            continue
        start = anchor.start()
        if markdown[max(0, start - 3):start] == "<p>":
            start -= 3
        end = anchors[index + 1].start() if index + 1 < len(anchors) else len(markdown)
        # The following heading belongs to the next source block, not the note.
        next_heading = _HEADING.search(markdown, anchor.end(), end)
        if next_heading:
            end = next_heading.start()
        # Do not attach the next block's opening provenance comment.
        block = markdown[start:end]
        block = re.sub(r"\s*<!-- quelle:z\d+-\d+ -->\s*$", "", block)
        result[name] = block.rstrip()
    return result


def _append_missing_footnotes(body: str, definitions: dict[str, str]) -> str:
    while True:
        present = {match.group(1) for match in _ANCHOR.finditer(body)}
        required = [unquote(urlsplit(target).fragment) for target, _ in _links(body)
                    if target.startswith("#") and _NOTE_NAME.match(unquote(urlsplit(target).fragment))]
        missing = list(dict.fromkeys(name for name in required if name not in present))
        if not missing:
            return body
        for name in missing:
            _require(name in definitions, f"Unaufgelöste Fußnote: #{name}")
            body += "\n\n" + definitions[name] + "\n"


def _reference_aliases(reference: str, anchors: list[str]) -> list[str]:
    """Individual references explicitly covered by source anchors/range titles.

    A numeric statute range also covers the plain integer section numbers within
    its endpoints. Letter variants are included only where the source names them;
    this does not invent a list of historically existing lettered provisions.
    """
    aliases = []
    for anchor in anchors:
        match = re.fullmatch(r"abschnitt-(\d+[a-z]?(?:-\d+[a-z]?)+)", anchor)
        if match:
            aliases.append(match.group(1).replace("-", "."))
        margin = re.fullmatch(r"rn-([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)", anchor)
        if margin:
            aliases.append("Rn. " + margin.group(1).replace("-", "."))
    grouped = re.fullmatch(r"§§\s*(\d+)([a-z]?)\s+(bis|und)\s+(\d+)([a-z]?)", reference)
    if grouped:
        start, first_letter, operator, stop, last_letter = grouped.groups()
        start_number, stop_number = int(start), int(stop)
        aliases.extend([f"§ {start}{first_letter}", f"§ {stop}{last_letter}"])
        if operator == "bis" and start_number <= stop_number and stop_number - start_number <= 1000:
            # A starting letter excludes the earlier unlettered start section.
            first_integer = start_number + bool(first_letter)
            aliases.extend(f"§ {number}" for number in range(first_integer, stop_number + 1))
    return list(dict.fromkeys(alias for alias in aliases if alias != reference))


def _provision_headings(markdown: str, abbreviation: str) -> list[dict]:
    """Recognize the register's statutes, administrative rules and margin notes.

    Quoted headings without source anchors stay inside their enclosing provision.
    This is essential for annexes that quote an article heading and for the AEAO,
    where local numbered explanations restart under every discussed AO section.
    """
    headings = _headings(markdown)
    aeao = abbreviation == "AEAO"
    gobd = "GoBD" in abbreviation
    in_annex = False
    for heading in headings:
        anchor = heading["anchor"] or ""
        if not anchor:
            heading["reference"] = None
        # Court decisions use explicit Markdown headings for integer margin
        # numbers. Require a matching source anchor so quoted margin headings
        # and incidental numeric anchors do not become independent provisions.
        margin = re.fullmatch(r"Rn\.\s+(\d+)", heading["title"])
        if margin and anchor == "rn-" + margin.group(1):
            heading["reference"] = "Rn. " + margin.group(1)
        if anchor.startswith("historisch-") and heading["reference"]:
            historical = re.match(r"(.+?\b(?:EStR|EStH)\s+\d{4})\b", heading["title"])
            _require(bool(historical), f"Historische Fassung ohne eindeutige Bezeichnung: {heading['title']}")
            heading["reference"] = historical.group(1)
        if aeao and not (anchor.startswith(("aeao-zu-", "aeao-vor-")) and "-nr-" not in anchor
                         or anchor.startswith("anlage-")):
            heading["reference"] = None
        if gobd:
            if anchor == "abschnitt-anlage":
                in_annex = True
                heading["reference"] = "Anlage"
            number = re.match(r"(\d+(?:\.\d+)*)\.?\s", heading["title"])
            if anchor.startswith("abschnitt-") and number:
                heading["reference"] = ("Anlage Abschnitt " if in_annex else "Abschnitt ") + number.group(1)
            # Page boundaries do not end provisions; preserve the continuation.
            heading["page_marker"] = bool(re.fullmatch(r"seite-\d+", anchor))
    # The UmwStE uses explicitly anchored HTML paragraphs, not Markdown
    # headings, for its authoritative margin numbers.
    source_headings = tuple(headings)
    source_heading_starts = [heading["start"] for heading in source_headings]
    source_anchors = list(_ANCHOR.finditer(markdown))
    consumed = set()
    for index, anchor in enumerate(source_anchors):
        if anchor.group(1) in consumed:
            continue
        match = re.fullmatch(r"rn-([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)", anchor.group(1))
        if not match:
            continue
        number = match.group(1).replace("-", ".")
        aliases = [anchor.group(1)]
        position = anchor.end()
        for following in source_anchors[index + 1:]:
            gap = re.sub(r"<!--.*?-->", "", markdown[position:following.start()], flags=re.S)
            if gap.strip() or not re.fullmatch(r"rn-([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)", following.group(1)):
                break
            aliases.append(following.group(1))
            consumed.add(following.group(1))
            position = following.end()
        if len(aliases) > 1:
            tail = re.sub(r"<!--.*?-->", "", markdown[position:], count=1, flags=re.S)
            printed = re.match(r'\s*<p class="randnummer"><strong>([^<]+)</strong>', tail)
            _require(bool(printed), f"Gruppierte Randnummer ohne gedruckte Referenz: {anchor.group(1)}")
            number = printed.group(1).strip()
        # Only actual source headings provide context. The generated margin
        # headings appended below must never become another margin's parent.
        context_index = bisect_right(source_heading_starts, anchor.start()) - 1
        context = source_headings[context_index]["title"] if context_index >= 0 else abbreviation
        headings.append({"start": anchor.start(), "heading_start": anchor.start(), "level": 7,
                         "title": f"Rn. {number} – {context}", "anchor": anchor.group(1),
                         "anchor_aliases": aliases, "reference": f"Rn. {number}"})
    return sorted(headings, key=lambda h: h["start"])


def _uncovered_ranges(length: int, provisions: list[dict]) -> list[tuple[int, int]]:
    """All source characters outside named provisions remain searchable too."""
    ranges = []
    cursor = 0
    for provision in sorted(provisions, key=lambda p: p["source_start"]):
        start, end = provision["source_start"], provision["source_end"]
        if start > cursor:
            ranges.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < length:
        ranges.append((cursor, length))
    return ranges


def _parse_document(root: Path, entry: dict, observed: dict[Path, str]) -> tuple[dict, list[dict], list[dict]]:
    abbreviation = entry["kuerzel"]
    _require(entry.get("bearbeitungsstatus") == "in_markdown_umgewandelt",
             f"Dokument ist nicht zur Recherche registriert: {abbreviation}")
    source_path = entry["markdown"]
    data = _read_checked(root, source_path, entry.get("sha256_markdown"), observed)
    markdown = data.decode("utf-8-sig")
    source = _path_inside(root, source_path)
    stand = source.parent
    _require(bool(re.fullmatch(r"Stand_\d{4}-\d{2}-\d{2}", stand.name)),
             f"Versionierter Standordner fehlt: {source_path}")
    for path_key, hash_key in (("original_pdf", "sha256_original_pdf"),
                               ("original_quelle", "sha256_original_quelle")):
        if entry.get(path_key):
            _read_checked(root, entry[path_key], entry.get(hash_key), observed)
    _require(bool(entry.get("original_pdf") or entry.get("original_quelle")),
             f"Registrierte Originalquelle fehlt: {abbreviation}")
    doc_id = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", abbreviation)
                    .encode("ascii", "ignore").decode().lower()).strip("-")
    _require(bool(doc_id), f"Keine stabile Dokumentkennung: {abbreviation}")
    anchors = list(_ANCHOR.finditer(markdown))
    anchor_names = [match.group(1) for match in anchors]
    _require(len(anchor_names) == len(set(anchor_names)), f"Doppelte Quellanker: {abbreviation}")
    definitions = _footnotes(markdown, anchors)
    asset_map: dict[str, dict] = {}
    all_links = _links(markdown)
    for target, is_image in all_links:
        parsed = urlsplit(target)
        if target.startswith("#") and _NOTE_NAME.match(unquote(parsed.fragment)):
            _require(unquote(parsed.fragment) in definitions,
                     f"Unaufgelöste Fußnote in {abbreviation}: {target}")
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        relative = unquote(parsed.path)
        suffix = PurePosixPath(relative).suffix.lower()
        if not is_image and suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
                                            ".md", ".txt", ".json", ".html", ".xml", ".zip"}:
            continue
        asset_path = _path_inside(stand, relative)
        canonical = asset_path.relative_to(stand).as_posix()
        if canonical not in asset_map:
            asset_data = asset_path.read_bytes()
            digest = _sha256(asset_data)
            observed[asset_path] = digest
            asset_map[canonical] = {
                "asset_id": doc_id + ":asset:" + _sha256(canonical.encode("utf-8"))[:20],
                "doc_id": doc_id, "relative_path": canonical,
                "source_path": asset_path.relative_to(root).as_posix(), "sha256": digest,
                "mime_type": mimetypes.guess_type(canonical)[0] or "application/octet-stream",
            }
    # Preserve the registered primary source as well as embedded assets. In
    # particular a raw web copy is not necessarily linked from the main text.
    original_asset_ids = []
    for path_key, hash_key in (("original_pdf", "sha256_original_pdf"),
                               ("original_quelle", "sha256_original_quelle")):
        if not entry.get(path_key):
            continue
        original = _path_inside(root, entry[path_key])
        relative = "Originalquellen/" + original.name
        asset_id = doc_id + ":original:" + path_key
        asset_map[relative] = {
            "asset_id": asset_id, "doc_id": doc_id, "relative_path": relative,
            "source_path": entry[path_key], "sha256": entry[hash_key],
            "mime_type": mimetypes.guess_type(original.name)[0] or "application/octet-stream",
        }
        original_asset_ids.append(asset_id)
    # The source register's version folder is the bounded archival unit. Keep
    # all data/evidence files, including unlinked official comparison PDFs,
    # XML/ZIP originals, visual checks and manifests. Conversion programs and
    # runtime caches are deliberately outside this archive data allow-list.
    for archived in sorted(stand.rglob("*"), key=lambda path: path.as_posix()):
        if not archived.is_file() or archived == source or archived.suffix.lower() not in _ARCHIVE_SUFFIXES:
            continue
        relative = archived.relative_to(stand).as_posix()
        if any(part in {"__pycache__", ".venv", ".daten", "node_modules"} for part in PurePosixPath(relative).parts):
            continue
        checked = _path_inside(stand, relative)
        if relative in asset_map:
            continue
        digest = _sha256(checked.read_bytes())
        observed[checked] = digest
        asset_map[relative] = {
            "asset_id": doc_id + ":asset:" + _sha256(relative.encode("utf-8"))[:20],
            "doc_id": doc_id, "relative_path": relative,
            "source_path": checked.relative_to(root).as_posix(), "sha256": digest,
            "mime_type": mimetypes.guess_type(relative)[0] or "application/octet-stream",
        }
    headings = _provision_headings(markdown, abbreviation)
    provisions = []
    for index, heading in enumerate(headings):
        if not heading["reference"]:
            continue
        end = len(markdown)
        for following in headings[index + 1:]:
            if following.get("page_marker"):
                continue
            # An AEAO entry contains all local numbered explanations. EGBGB
            # article entries also contain their individually retrievable §§.
            contains_children = heading["reference"].startswith("AEAO ") or bool(
                re.fullmatch(r"Art\.?\s*\d+[a-z]?", heading["reference"], re.I))
            if (following["reference"] and not contains_children) or following["level"] <= heading["level"]:
                end = following["start"]
                break
        # A provenance wrapper for the following heading is not part of this norm.
        tail = re.search(r"\s*<!-- quelle:z\d+-\d+ -->\s*$", markdown[heading["start"]:end])
        if tail:
            end = heading["start"] + tail.start()
        body = _append_missing_footnotes(markdown[heading["start"]:end], definitions)
        asset_ids = []
        for target, is_image in _links(body):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            relative = str(PurePosixPath(unquote(parsed.path)))
            if relative in asset_map:
                asset_ids.append(asset_map[relative]["asset_id"])
            elif is_image:
                raise ParseError(f"Abbildung fehlt im Quellenmanifest: {relative}")
        search_text = readable_text(body)
        provisions.append({
            "provision_id": doc_id + ":" + heading["anchor"], "doc_id": doc_id,
            "reference": heading["reference"], "title": heading["title"],
            "anchor": heading["anchor"], "markdown": body, "search_text": search_text,
            "anchor_aliases": heading["anchor_aliases"],
            "reference_aliases": _reference_aliases(heading["reference"], heading["anchor_aliases"]),
            "ordinal": len(provisions), "source_start": heading["start"], "source_end": end,
            "cross_references": list(dict.fromkeys(m.group(0) for m in _CROSS_REFERENCE.finditer(search_text))),
            "asset_ids": list(dict.fromkeys(asset_ids)),
            "kind": "provision",
        })
    # Include source preambles, EU recitals, editorial provenance, global notes
    # and any otherwise unrecognized section. A complete source is never
    # silently reduced to the heading formats the parser happens to recognize.
    for start, end in _uncovered_ranges(len(markdown), provisions):
        boundaries = [start, *[h["start"] for h in headings if start < h["start"] < end], end]
        for block_start, block_end in zip(boundaries, boundaries[1:]):
            original = markdown[block_start:block_end]
            if not readable_text(original).strip():
                continue
            candidates = [h for h in headings if h["start"] <= block_start]
            heading = candidates[-1] if candidates else None
            title = heading["title"] if heading else entry["titel"]
            anchor = (heading["anchor"] if heading and heading["start"] == block_start else None)
            identifier = "source-part-" + (anchor or _sha256((title + ":" + str(block_start)).encode())[:20])
            body = _append_missing_footnotes(original, definitions)
            search_text = readable_text(body)
            provisions.append({
                "provision_id": doc_id + ":" + identifier, "doc_id": doc_id,
                "reference": "Dokumentteil: " + identifier, "title": title,
                "anchor": identifier, "source_anchor": anchor, "generated_anchor": True,
                "anchor_aliases": [anchor] if anchor else [],
                "reference_aliases": [], "markdown": body, "search_text": search_text,
                "ordinal": len(provisions), "source_start": block_start, "source_end": block_end,
                "cross_references": list(dict.fromkeys(m.group(0) for m in _CROSS_REFERENCE.finditer(search_text))),
                "asset_ids": list(dict.fromkeys(asset_map[str(PurePosixPath(unquote(urlsplit(t).path)))]["asset_id"]
                                               for t, _ in _links(body)
                                               if not urlsplit(t).scheme and not urlsplit(t).netloc
                                               and str(PurePosixPath(unquote(urlsplit(t).path))) in asset_map)),
                "kind": "source_part",
            })
    # Authored supplements are separate source editions. Keep their exact
    # Markdown as a file and a searchable item, including their own date/source
    # statements; do not blend their content into the parent legal provision.
    supplements = [asset for path, asset in asset_map.items()
                   if path.startswith("Ergaenzungen/") and path.endswith(".md")]
    for asset in supplements:
        supplement_path = _path_inside(root, asset["source_path"])
        supplement = supplement_path.read_bytes().decode("utf-8-sig")
        supplement_assets = [asset["asset_id"]]
        for target, _ in _links(supplement):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            relative = unquote(parsed.path)
            _require(not PurePosixPath(relative).is_absolute() and "\\" not in relative and ":" not in relative,
                     f"Unsicherer Ergänzungspfad: {relative!r}")
            candidate = (supplement_path.parent / relative).resolve()
            _require(candidate.is_relative_to(stand), f"Ergänzungsquelle verlässt Standordner: {relative}")
            canonical = candidate.relative_to(stand).as_posix()
            checked = _path_inside(stand, canonical)
            if canonical not in asset_map:
                digest = _sha256(checked.read_bytes())
                observed[checked] = digest
                asset_map[canonical] = {
                    "asset_id": doc_id + ":asset:" + _sha256(canonical.encode("utf-8"))[:20],
                    "doc_id": doc_id, "relative_path": canonical,
                    "source_path": checked.relative_to(root).as_posix(), "sha256": digest,
                    "mime_type": mimetypes.guess_type(canonical)[0] or "application/octet-stream",
                }
            supplement_assets.append(asset_map[canonical]["asset_id"])
        supplement_headings = _headings(supplement)
        title = supplement_headings[0]["title"] if supplement_headings else supplement_path.stem
        search_text = readable_text(supplement)
        supplement_id = "supplement-" + _sha256(asset["relative_path"].encode())[:20]
        provisions.append({
            "provision_id": doc_id + ":" + supplement_id,
            "doc_id": doc_id, "reference": "Ergänzung: " + title, "title": title,
            "anchor": supplement_id, "source_anchor": None, "generated_anchor": True,
            "anchor_aliases": [], "reference_aliases": [],
            "markdown": supplement, "search_text": search_text, "ordinal": len(provisions),
            "source_start": 0, "source_end": len(supplement),
            "source_path": asset["source_path"], "source_sha256": asset["sha256"],
            "cross_references": list(dict.fromkeys(m.group(0) for m in _CROSS_REFERENCE.finditer(search_text))),
            "asset_ids": list(dict.fromkeys(supplement_assets)), "kind": "supplement",
        })
    _require(bool(provisions), f"Leeres registriertes Dokument: {abbreviation}")
    references = {}
    for provision in provisions:
        for reference in [provision["reference"], *provision["reference_aliases"]]:
            normalized = re.sub(r"\s+", " ", reference).strip().casefold()
            _require(normalized not in references or references[normalized] == provision["provision_id"],
                     f"Mehrdeutige Vorschriftenreferenz in {abbreviation}: {reference}")
            references[normalized] = provision["provision_id"]
    source_url = entry.get("quelle", "")
    if not isinstance(source_url, str) or not source_url.startswith(("https://", "http://")):
        source_url = ""
    document_type = entry.get("typ", "")
    if document_type == "Gesetz/Verordnung":
        # Several regulations are filed under the thematic /Gesetze/ tree.
        # The registered title, rather than that folder, identifies their type.
        title_word = entry["titel"].split()[0].casefold()
        document_type = "Verordnung" if "verordnung" in title_word else "Gesetz"
    document = {
        "doc_id": doc_id, "abbreviation": abbreviation, "title": entry["titel"],
        "document_type": document_type, "source_path": source_path,
        "source_sha256": entry["sha256_markdown"], "source_url": source_url,
        "source_status": entry.get("quellenstand", []),
        "import_date": entry.get("quellenabgleich"), "valid_from": None, "valid_to": None,
        "markdown": markdown, "metadata": entry,
        "original_asset_ids": original_asset_ids,
        "asset_ids": [a["asset_id"] for a in asset_map.values()],
    }
    return document, provisions, list(asset_map.values())


def parse_collection(root: Path, abbreviations: list[str] | None = None) -> dict:
    """Import all registered documents by default; fail closed on source drift."""
    root = Path(root).resolve()
    register_path = _path_inside(root, "Bestand.json")
    register = json.loads(register_path.read_text(encoding="utf-8-sig"))
    _require(isinstance(register.get("eintraege"), list), "Dokumentenregister ist unvollständig.")
    if abbreviations is None:
        _require(register.get("dokumente", len(register["eintraege"])) == len(register["eintraege"]),
                 "Dokumentzahl im Register stimmt nicht mit den Einträgen überein.")
        abbreviations = [e.get("kuerzel", "") for e in register["eintraege"]]
    _require(bool(abbreviations) and all(isinstance(a, str) and a.strip() for a in abbreviations),
             "Mindestens ein Dokument muss ausgewählt sein.")
    keys = [value.casefold() for value in abbreviations]
    _require(len(keys) == len(set(keys)), "Dokumentauswahl enthält doppelte Abkürzungen.")
    selected = {}
    for entry in register.get("eintraege", []):
        key = entry.get("kuerzel", "").casefold()
        if key in keys:
            _require(key not in selected, f"Mehrdeutiger Registereintrag: {key}")
            selected[key] = entry
    _require(set(keys) == set(selected), f"Dokumente fehlen im Register: {', '.join(set(keys) - set(selected))}")
    result = {"parser_version": PARSER_VERSION, "documents": [], "provisions": [], "assets": []}
    observed: dict[Path, str] = {}
    for key in keys:
        document, provisions, assets = _parse_document(root, selected[key], observed)
        result["documents"].append(document)
        result["provisions"].extend(provisions)
        result["assets"].extend(assets)
    _require(len({d["doc_id"] for d in result["documents"]}) == len(keys), "Dokumentkennungen kollidieren.")
    # Concurrent conversions are allowed; a selected source changing during import is not.
    latest = json.loads(register_path.read_text(encoding="utf-8-sig"))
    latest_selected = [e for e in latest.get("eintraege", []) if e.get("kuerzel", "").casefold() in keys]
    _require(len(latest_selected) == len(selected)
             and all(e == selected.get(e["kuerzel"].casefold()) for e in latest_selected),
             "Ausgewählte Registereinträge wurden während des Imports geändert.")
    for path, digest in observed.items():
        _require(_sha256(path.read_bytes()) == digest,
                 f"Quelle wurde während des Imports verändert: {path.relative_to(root)}")
    return result
