"""Verified, atomic Supabase import. Default: complete rehearsal with ROLLBACK.

Credentials are read only from this project's Windows Credential Manager entry.
All SQL values are bound. No source files or existing releases are overwritten.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from connect_project import PROJECT, load_saved_connection, saved_connection_parameters
from normalize_export import prepare, inside, hash_file, digest, require
from postgres_store import reference_key

APP = Path(__file__).resolve().parent.parent
SCHEMA = Path(__file__).with_name("schema.sql")
READ_API = Path(__file__).with_name("read_api.sql")
ASSET_API = Path(__file__).with_name("003_asset_metadata.sql")
HOSTED_MCP_API = Path(__file__).with_name("004_supabase_mcp_reader.sql")
TABLE_KEYS = {"releases": "release_id", "documents": "document_id", "provisions": "provision_id",
              "search_chunks": "chunk_id", "assets": "asset_id"}
JSON_COLUMNS = {"metadata", "source_status"}
BATCH_ROWS = 250


def log(message):
    print(message, flush=True)


def current_package():
    pointer = json.loads((APP / ".daten" / "Cloud_Paketpfad.json").read_text(encoding="utf-8"))
    return Path(pointer["base"]) / "Export"


def load_package(source):
    base, manifest, files, assets, rows = prepare(source)
    # The verified original export is authoritative. The previous normalized
    # package remains an unchanged local preparation artifact.
    return {"base": base, "manifest": manifest, "files": files, "assets": assets,
            "rows": rows, "release": rows["releases"][0]}


def verify_snapshot(package):
    require(inside(package["base"], "manifest.json").read_bytes() == package["manifest"],
            "Das Exportmanifest wurde während des Imports geändert.")
    for name, item in package["files"].items():
        require(hash_file(inside(package["base"], name)) == (item["sha256"], item["size"]),
                "Eine Exportdatei wurde während des Imports geändert.")


def migration_body(path):
    text = path.read_text(encoding="utf-8")
    # The outer transaction is owned by this program, including the rehearsal.
    return "\n".join(line for line in text.splitlines()
                     if line.strip() not in {"BEGIN;", "COMMIT;"})


def ensure_schema(db):
    migrations = [("001-private-database", SCHEMA)]
    if READ_API.is_file():
        migrations.append(("002-read-api", READ_API))
    if ASSET_API.is_file():
        migrations.append(("003-asset-metadata", ASSET_API))
    if HOSTED_MCP_API.is_file():
        migrations.append(("004-supabase-mcp-reader", HOSTED_MCP_API))
    present = db.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='kb')").fetchone()[0]
    if not present:
        log("Private Tabellen, Rollen und Suchfunktionen einrichten ...")
        db.execute(migration_body(SCHEMA), prepare=False)
        db.execute("INSERT INTO kb.schema_migrations(version,sha256) VALUES (%s,%s)",
                   (migrations[0][0], digest(SCHEMA.read_bytes())))
    for version, path in migrations:
        expected = digest(path.read_bytes())
        old = db.execute("SELECT sha256 FROM kb.schema_migrations WHERE version=%s", (version,)).fetchone()
        if old:
            require(old[0] == expected, "Installierte Migration unterscheidet sich von der lokalen Datei: " + version)
        else:
            require(version != "001-private-database", "Bestehendes Schema ohne passenden Migrationsnachweis.")
            db.execute(migration_body(path), prepare=False)
            db.execute("INSERT INTO kb.schema_migrations(version,sha256) VALUES (%s,%s)", (version, expected))


def insert_rows(db, table, rows):
    require(table in TABLE_KEYS, "Unbekannte Importtabelle.")
    if not rows:
        return
    columns = list(rows[0])
    query = sql.SQL("INSERT INTO kb.{} ({}) VALUES ({})").format(
        sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, columns)),
        sql.SQL(",").join(sql.Placeholder() for _ in columns))

    def values(group):
        for row in group:
            require(list(row) == columns, "Inkonsistente Importspalten.")
            yield tuple(Jsonb(row[c]) if c in JSON_COLUMNS else
                        json.dumps(row[c], allow_nan=False) if c == "embedding" else row[c]
                        for c in columns)
    # RLS-enabled tables deliberately use INSERT instead of unsupported COPY FROM.
    with db.cursor() as cursor:
        for start in range(0, len(rows), BATCH_ROWS):
            cursor.executemany(query, values(rows[start:start + BATCH_ROWS]))
            if len(rows) > BATCH_ROWS and (start + BATCH_ROWS) % 1000 == 0:
                log(f"{table}: {min(start + BATCH_ROWS, len(rows))}/{len(rows)} übertragen")


def verify_rows(db, package):
    rid = package["release"]["release_id"]
    compared = {}
    for table, rows in package["rows"].items():
        key = TABLE_KEYS[table]
        count = db.execute(sql.SQL("SELECT count(*) FROM kb.{} WHERE release_id=%s").format(
            sql.Identifier(table)), (rid,)).fetchone()[0]
        require(count == len(rows), "Abweichende Zeilenzahl: " + table)
        # Compare every column of every row, but never retain a second complete
        # copy of all corpus texts and 384-dimensional vectors in RAM.
        for start in range(0, len(rows), BATCH_ROWS):
            group = rows[start:start + BATCH_ROWS]
            actual = db.execute(sql.SQL("SELECT to_jsonb(t) FROM kb.{} t WHERE release_id=%s AND {}=ANY(%s)").format(
                sql.Identifier(table), sql.Identifier(key)), (rid, [r[key] for r in group])).fetchall()
            by_id = {record[0][key]: record[0] for record in actual}
            require(len(actual) == len(by_id) == len(group), "Fehlende oder doppelte Zeile: " + table)
            for expected in group:
                stored = by_id.get(expected[key])
                require(stored is not None, "Fehlende Zeile: " + table)
                for column, value in expected.items():
                    if column == "verified_at":
                        continue
                    observed = stored[column]
                    if column == "embedding" and value is not None:
                        observed = json.loads(observed) if isinstance(observed, str) else observed
                        require(len(value) == len(observed) == 384, "Abweichende Vektorlänge.")
                        # pgvector stores float32; text output can use shorter decimals.
                        ok = struct.pack("<384f", *value) == struct.pack("<384f", *observed)
                    else:
                        ok = value == observed
                    require(ok, "Abweichender Dateninhalt: " + table + "." + column)
        compared[table] = len(rows)
        log(f"{table}: alle {len(rows)} Datensätze zurückgelesen und verglichen")
    return compared


def insert_and_verify_assets(db, package):
    rid = package["release"]["release_id"]
    if not package["rows"]["assets"]:
        return
    first = package["rows"]["assets"][0]
    expect_rejected(db, "kb_importer", "SELECT kb.activate_release(%s,%s)",
                    (rid, package["release"]["manifest_sha256"]), ("P0001",))
    expect_rejected(db, "kb_importer", "INSERT INTO kb.asset_contents(release_id,asset_id,content) VALUES (%s,%s,%s)",
                    (rid, first["asset_id"], b"deliberately-invalid-test-bytes"), ("P0001",))
    for number, row in enumerate(package["rows"]["assets"], 1):
        content = inside(package["base"], "assets/" + row["sha256"]).read_bytes()
        require((digest(content), len(content)) == (row["sha256"], row["byte_size"]), "Asset vor Upload geändert.")
        db.execute("INSERT INTO kb.asset_contents(release_id,asset_id,content) VALUES (%s,%s,%s)",
                   (rid, row["asset_id"], content))
        received = db.execute("SELECT content FROM kb.asset_contents WHERE release_id=%s AND asset_id=%s",
                              (rid, row["asset_id"])).fetchone()[0]
        require(bytes(received) == content, "Assetbytes nach Übertragung abweichend.")
        db.execute("SELECT kb.confirm_asset_upload(%s,%s,%s)", (rid, row["asset_id"], digest(received)))
        if number % 20 == 0:
            log(f"Originaldateien übertragen und zurückgelesen: {number}/{len(package['rows']['assets'])}")


def expect_rejected(db, role, statement, args=(), allowed_states=("42501",)):
    try:
        with db.transaction():
            db.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
            db.execute(statement, args)
    except psycopg.Error as exc:
        require(exc.sqlstate in allowed_states, "Unerwarteter Fehler bei Berechtigungsprüfung: " + str(exc.sqlstate))
        return
    raise ValueError("Berechtigungsprüfung fehlgeschlagen: verbotene Aktion war erlaubt.")


def lexical_queries(package):
    """Derive a bounded search probe from the expected text of every document."""
    samples = defaultdict(str)
    for chunk in package["rows"]["search_chunks"]:
        ident = chunk["document_id"]
        remaining = 20000 - len(samples[ident])
        if remaining > 0:
            samples[ident] += "\n" + chunk["body_text"][:remaining]
    probes = []
    for doc in package["rows"]["documents"]:
        ident = doc["document_id"]
        # OR avoids accidental German stop-word-only probes and phrases that
        # cross chunk boundaries. Values remain bound SQL parameters.
        words = set(re.findall(r"[^\W\d_]{3,96}", samples[ident], flags=re.UNICODE))
        selected = sorted(words, key=lambda word: (-len(word), word))[:12]
        require(bool(selected), "Dokument ohne durchsuchbaren Text: " + doc["abbreviation"])
        probes.append((doc, " OR ".join(selected)))
    return probes


def reference_probes(package):
    """Check first/middle/last primary references per document and every alias."""
    groups = defaultdict(list)
    for row in package["rows"]["provisions"]:
        groups[row["document_id"]].append(row)
    probes = {}

    def add(row, key):
        pair = (row["document_id"], key)
        require(pair not in probes or probes[pair] == row["provision_id"],
                "Mehrdeutige exakte Referenz im Export: " + row["document_id"] + " " + key)
        probes[pair] = row["provision_id"]

    for doc in package["rows"]["documents"]:
        rows = sorted(groups[doc["document_id"]], key=lambda row: row["ordinal"])
        require(bool(rows), "Dokument ohne Fundstellen: " + doc["abbreviation"])
        for index in {0, len(rows) // 2, len(rows) - 1}:
            add(rows[index], rows[index]["ref_key"])
        for row in rows:
            aliases = row["metadata"].get("reference_aliases", [])
            if aliases:
                add(row, row["ref_key"])
            for alias in aliases:
                add(row, reference_key(alias))
    return [{"document_id": doc, "ref_key": ref, "provision_id": pid}
            for (doc, ref), pid in sorted(probes.items())]


def verify_lexical_search(db, package):
    rid = package["release"]["release_id"]
    expected = {row["provision_id"]: row["document_id"] for row in package["rows"]["provisions"]}
    checked = []
    for doc, query in lexical_queries(package):
        found = db.execute("""SELECT release_id,document_id,provision_id
            FROM kb.hybrid_search(%s,p_release_id=>%s,p_document_id=>%s)""",
                           (query, rid, doc["document_id"])).fetchall()
        require(bool(found) and len({row[2] for row in found}) == len(found)
                and all(release == rid and document == doc["document_id"]
                        and expected.get(provision) == document for release, document, provision in found),
                "Volltextsuche fehlgeschlagen: " + doc["abbreviation"])
        checked.append(doc["document_id"])
    return checked


def verify_exact_references(db, package):
    rid = package["release"]["release_id"]
    probes = reference_probes(package)
    for start in range(0, len(probes), 100):
        group = probes[start:start + 100]
        fetched = db.execute("""SELECT x.document_id,x.ref_key,kb.lookup_provision(%s,x.document_id,x.ref_key)
            FROM jsonb_to_recordset(%s) AS x(document_id text,ref_key text,provision_id text)""",
                             (rid, Jsonb(group))).fetchall()
        by_reference = {(document, ref): matches for document, ref, matches in fetched}
        require(len(fetched) == len(by_reference) == len(group), "Unvollständige exakte Referenzprüfung.")
        for probe in group:
            require(by_reference.get((probe["document_id"], probe["ref_key"])) == [probe["provision_id"]],
                    "Exakte Referenz/Alias fehlt oder ist mehrdeutig: " + probe["document_id"] + " " + probe["ref_key"])
    return {"exact_reference_probes": len(probes),
            "exact_documents": len({probe["document_id"] for probe in probes})}


def verify_reader_and_guards(db, package):
    rid = package["release"]["release_id"]
    checks = []
    for role in ("anon", "authenticated", "kb_mcp"):
        expect_rejected(db, role, "SELECT body_markdown FROM kb.documents LIMIT 1")
        checks.append(role + ":direct_tables_denied")
    for role in ("anon", "authenticated"):
        expect_rejected(db, role, "SELECT kb.release_info()")
        checks.append(role + ":functions_denied")
    expect_rejected(db, "kb_mcp", "SELECT kb.activate_release(%s,%s)", (rid, package["release"]["manifest_sha256"]))
    expect_rejected(db, "kb_importer", "UPDATE kb.documents SET title=title WHERE release_id=%s", (rid,))
    # Even the table owner cannot accidentally edit a sealed release via normal DML.
    expect_rejected(db, "postgres", "UPDATE kb.documents SET title=title WHERE release_id=%s", (rid,), ("P0001",))
    checks.extend(["reader_activation_denied", "importer_update_denied", "sealed_content_guard"])
    db.execute("SET LOCAL ROLE kb_mcp")
    info = db.execute("SELECT kb.release_info()").fetchone()[0]
    require(info and info["release_id"] == rid, "Leser sieht nicht die aktivierte Fassung.")
    lexical_documents = verify_lexical_search(db, package)
    log(f"Volltextsuche für alle {len(lexical_documents)} Dokumente geprüft")
    # Every full provision is compared through the actual bounded read function.
    # One SQL statement returns an explicit array of all its 20k-character pages.
    pages = 0
    for start in range(0, len(package["rows"]["provisions"]), 100):
        group = package["rows"]["provisions"][start:start + 100]
        requests = [{"id": r["provision_id"], "length": len(r["body_markdown"])} for r in group]
        result = db.execute("""SELECT x.id, array_agg(kb.fetch_provision(%s,x.id,n,20000) ORDER BY n)
            FROM jsonb_to_recordset(%s) AS x(id text,length integer)
            CROSS JOIN LATERAL generate_series(0,greatest(x.length-1,0),20000) AS n GROUP BY x.id""",
                            (rid, Jsonb(requests))).fetchall()
        text_by_id = {pid: "".join(page["body_markdown"] for page in parts) for pid, parts in result}
        pages += sum(len(parts) for _, parts in result)
        require(all(text_by_id.get(r["provision_id"]) == r["body_markdown"] for r in group),
                "Vollständiger Leserabruf einer Fundstelle abweichend.")
        if (start + 100) % 1000 == 0:
            log(f"Fundstellen vollständig gelesen: {min(start + 100, len(package['rows']['provisions']))}/{len(package['rows']['provisions'])}")
    for number, row in enumerate(package["rows"]["assets"], 1):
        hasher = hashlib.sha256()
        size = 0
        for offset in range(0, max(row["byte_size"], 1), 1048576):
            part = db.execute("SELECT kb.fetch_asset_bytes(%s,%s,%s,1048576)", (rid, row["asset_id"], offset)).fetchone()[0]
            require(part is not None, "Leser kann Asset nicht abrufen.")
            hasher.update(part)
            size += len(part)
        require((hasher.hexdigest(), size) == (row["sha256"], row["byte_size"]), "Leserabruf einer Originaldatei abweichend.")
        if number % 20 == 0:
            log(f"Originaldateien über die Lese-API geprüft: {number}/{len(package['rows']['assets'])}")
    reference_checks = {}
    if READ_API.is_file():
        versions = db.execute("SELECT kb.list_versions()").fetchone()[0]
        require(any(v["release_id"] == rid and v["active"] for v in versions["versions"]), "MCP-Fassungsübersicht abweichend.")
        for row in package["rows"]["documents"]:
            first = db.execute("SELECT kb.read_item(%s,'d',%s,0,20000)", (rid, row["document_id"])).fetchone()[0]
            require(first["text"] == row["body_markdown"][:20000] and first["metadata"] == row["metadata"]
                    and first["text_sha256"] == digest(row["body_markdown"].encode("utf-8")), "MCP-Dokumentabruf abweichend.")
        for start in range(0, len(package["rows"]["provisions"]), 100):
            group = package["rows"]["provisions"][start:start+100]
            fetched = db.execute("SELECT kb.read_item(%s,'p',pid,0,20000) FROM unnest(%s::text[]) AS pid",
                                 (rid, [r["provision_id"] for r in group])).fetchall()
            for expected, (item,) in zip(group, fetched, strict=True):
                require(item["text"] == expected["body_markdown"][:20000]
                        and item["metadata"] == expected["metadata"]
                        and item["text_sha256"] == digest(expected["body_markdown"].encode("utf-8")),
                        "MCP-Fundstellenmetadaten oder Volltextprüfsumme abweichend.")
        reference_checks = verify_exact_references(db, package)
        log(f"Exakte Referenzen und Aliase für alle {reference_checks['exact_documents']} Dokumente geprüft")
        checks.extend(["mcp_version_list", "mcp_full_metadata_and_hashes", "mcp_reference_aliases"])
    db.execute("RESET ROLE")
    return {"access_checks": checks, "full_provisions": len(package["rows"]["provisions"]),
            "text_pages": pages, "verified_assets": len(package["rows"]["assets"]),
            "lexical_documents": len(lexical_documents), "lexical_document_ids": lexical_documents, **reference_checks}


def publish(source, *, apply=False, verify_only=False):
    log("Lokales Exportpaket vollständig prüfen ...")
    package = load_package(source)
    release = package["release"]
    log(f"Geprüftes Paket: {release['expected_documents']} Dokumente, {release['expected_provisions']} Fundstellen, "
        f"{release['expected_chunks']} Suchabschnitte, "
        f"{sum(row['byte_size'] for row in package['rows']['assets']) / 1048576:.1f} MiB Originaldateien")
    project = json.loads(PROJECT.read_text(encoding="utf-8"))
    params = saved_connection_parameters(load_saved_connection(project["project_ref"]), project["project_ref"])
    log("Gespeicherten Zugang verwenden; Passwort wird nicht ausgegeben.")
    with psycopg.connect(**params, autocommit=True, prepare_threshold=None, connect_timeout=15,
                         options="-c statement_timeout=120000 -c lock_timeout=15000") as db:
        with db.transaction(force_rollback=not apply or verify_only):
            db.execute("SELECT pg_advisory_xact_lock(78234001)")
            if not verify_only:
                ensure_schema(db)
            current = db.execute("SELECT manifest_sha256,sealed_at FROM kb.releases WHERE release_id=%s", (release["release_id"],)).fetchone()
            if current:
                require(current[0] == release["manifest_sha256"] and current[1] is not None,
                        "Vorhandene Fassung ist unvollständig oder hat ein anderes Manifest.")
                log("Fassung bereits vorhanden; Vollständigkeit erneut prüfen.")
            else:
                require(not verify_only, "Die angefragte Cloudfassung fehlt.")
                db.execute("SET LOCAL ROLE kb_importer")
                for table, rows in package["rows"].items():
                    log(f"{table}: {len(rows)} Datensätze übertragen ...")
                    insert_rows(db, table, rows)
                insert_and_verify_assets(db, package)
                db.execute("RESET ROLE")
            log("Alle gespeicherten Texte, Metadaten und Suchvektoren vergleichen ...")
            compared = verify_rows(db, package)
            if not verify_only:
                db.execute("SET LOCAL ROLE kb_importer")
                db.execute("SELECT kb.activate_release(%s,%s)", (release["release_id"], release["manifest_sha256"]))
                db.execute("RESET ROLE")
            log("Leseberechtigungen, vollständige Fundstellen und Originaldateien prüfen ...")
            checks = verify_reader_and_guards(db, package)
            verify_snapshot(package)
        # Separate, committed state check (dry runs must leave a new schema absent).
        visible = db.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='kb')").fetchone()[0]
        if apply:
            require(visible, "Schema nach COMMIT nicht sichtbar.")
            active = db.execute("SELECT kb.release_info()").fetchone()[0]
            require(active["release_id"] == release["release_id"], "Fassung nach COMMIT nicht sichtbar.")
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "project_ref": project["project_ref"],
              "release_id": release["release_id"], "manifest_sha256": release["manifest_sha256"],
              "mode": "verify" if verify_only else "apply" if apply else "rollback_rehearsal",
              "committed": bool(apply and not verify_only), "compared_rows": compared, "checks": checks,
              "asset_bytes": sum(r["byte_size"] for r in package["rows"]["assets"]),
              "asset_storage": "private_postgres_bytea",
              "custom_remote_mcp_deployed": bool(project.get("custom_remote_mcp_deployed", project.get("remote_mcp_deployed", False)))}
    target = Path(__file__).with_name("Importpruefung_" + report["mode"] + ".json")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if apply and not verify_only:
        project.update(schema_installed=True, files_uploaded=True, active_release=release["release_id"],
                       asset_storage="private_postgres_bytea", storage_bucket_created=False,
                       note=f"Cloudfassung mit {release['expected_documents']} registrierten Dokumenten vollständig hochgeladen, zurückgelesen und aktiviert. Die MCP-Clientverbindung wird gesondert geprüft.")
        project["connection_check"]["kb_schema_present"] = True
        PROJECT.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", nargs="?", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Geprüften Import in der Cloud speichern")
    mode.add_argument("--verify-only", action="store_true", help="Vorhandenen Import vergleichen")
    args = parser.parse_args()
    try:
        publish(args.export or current_package(), apply=args.apply, verify_only=args.verify_only)
    except psycopg.Error as exc:
        # Driver messages can echo credentials. Never print connection strings.
        log("Datenbankschritt fehlgeschlagen: " + type(exc).__name__ + " | SQLSTATE: " + str(exc.sqlstate))
        raise SystemExit(1) from None
    except (ValueError, OSError) as exc:
        log("Import abgebrochen: " + str(exc))
        raise SystemExit(1) from None


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
