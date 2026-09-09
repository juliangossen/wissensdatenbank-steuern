"""Create one dedicated read-only login; store its secret in Windows, not files."""
from __future__ import annotations

import json
from pathlib import Path
import secrets
import sys

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from connect_project import PROJECT, load_saved_connection, root_certificate, saved_connection_parameters

ROLE = "kb_reader_login"


def target(project_ref):
    return f"Wissensdatenbank/Supabase/{project_ref}/Lesen"


def load_reader(project_ref):
    import win32cred
    saved = win32cred.CredRead(target(project_ref), win32cred.CRED_TYPE_GENERIC)["CredentialBlob"]
    if isinstance(saved, bytes):
        saved = saved.decode("utf-16-le")
    params = conninfo_to_dict(saved)
    if params.get("user") != ROLE + "." + project_ref or params.get("sslmode") != "verify-full":
        raise ValueError("Der gespeicherte Zugang ist kein passender Leserzugang.")
    params["sslrootcert"] = root_certificate()
    return params


def save_reader(project_ref, params):
    import win32cred
    win32cred.CredWrite({"Type": win32cred.CRED_TYPE_GENERIC, "TargetName": target(project_ref),
                        "UserName": params["user"], "CredentialBlob": make_conninfo(**params),
                        "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
                        "Comment": "Lesender Wissensdatenbank-MCP; keine Import-/Administratorrechte."}, 0)
    if load_reader(project_ref) != params:
        raise RuntimeError("Der Leserzugang konnte nicht unverändert gespeichert werden.")


def provision_reader():
    import pywintypes
    project = json.loads(PROJECT.read_text(encoding="utf-8"))
    ref = project["project_ref"]
    admin = saved_connection_parameters(load_saved_connection(ref), ref)
    try:
        reader = load_reader(ref)
    except pywintypes.error as exc:
        if exc.winerror != 1168:
            raise
        reader = None
    with psycopg.connect(**admin, prepare_threshold=None, connect_timeout=15) as db:
        exists = db.execute("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=%s)", (ROLE,)).fetchone()[0]
        if not exists:
            reader = {**admin, "user": ROLE + "." + ref, "password": secrets.token_urlsafe(48)}
            db.execute(sql.SQL("CREATE ROLE {} LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS CONNECTION LIMIT 5 PASSWORD {}").format(
                sql.Identifier(ROLE), sql.Literal(reader["password"])))
            db.execute(sql.SQL("GRANT kb_mcp TO {} WITH ADMIN FALSE, INHERIT TRUE, SET FALSE").format(sql.Identifier(ROLE)))
            db.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only=on").format(sql.Identifier(ROLE)))
            db.execute(sql.SQL("ALTER ROLE {} SET statement_timeout='30s'").format(sql.Identifier(ROLE)))
            # Persist before COMMIT: a failed local save rolls role creation back.
            save_reader(ref, reader)
        elif reader is None:
            raise ValueError("Leserrolle existiert, aber ihr lokaler Zugang fehlt. Bestehenden Zugang nicht automatisch überschreiben.")
    with psycopg.connect(**reader, prepare_threshold=None, connect_timeout=15) as db:
        state = db.execute("SELECT current_user,current_setting('transaction_read_only'),kb.release_info()").fetchone()
        if state[0] != ROLE or state[1] != "on" or not state[2]:
            raise RuntimeError("Leserzugang oder aktive Fassung wurde nicht bestätigt.")
        rights = db.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone()
        if any(rights):
            raise RuntimeError("Der Leserzugang hat unerwartet privilegierte Rollenattribute.")
        for function in ("kb.list_versions()", "kb.release_info()"):
            if db.execute("SELECT has_function_privilege(current_user,%s,'execute')", (function,)).fetchone()[0] is not True:
                raise RuntimeError("Eine feste Leserfunktion fehlt.")
        if db.execute("SELECT has_table_privilege(current_user,'kb.documents','SELECT')").fetchone()[0]:
            raise RuntimeError("Der Leserzugang besitzt unerwartete direkte Tabellenrechte.")
    project.update(reader_login_tested=True, reader_credential_target=target(ref))
    PROJECT.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Eigener Leserzugang erfolgreich geprüft; nur feste Lesefunktionen, kein Administratorzugang.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        provision_reader()
    except Exception as exc:
        print("Leserzugang konnte nicht eingerichtet werden:", type(exc).__name__)
        raise SystemExit(1) from None
