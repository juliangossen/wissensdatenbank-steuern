"""Interactive, read-only connection check; secrets go to Windows Credential Manager."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
from pathlib import Path
import re
import sys

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

PROJECT = Path(__file__).with_name("projekt.json")
ROOT_CA = Path(__file__).with_name("zertifikate") / "prod-ca-2021.crt"
ROOT_CA_SHA256 = "700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7"


def root_certificate() -> str:
    try:
        certificate = ROOT_CA.read_bytes()
    except OSError:
        raise ValueError("Das mitgelieferte Supabase-Zertifikat fehlt oder ist nicht lesbar.") from None
    if hashlib.sha256(certificate).hexdigest() != ROOT_CA_SHA256:
        raise ValueError("Die Prüfsumme des Supabase-Zertifikats stimmt nicht. Bitte die Zertifikatsdatei prüfen lassen.")
    return str(ROOT_CA.resolve())


def explain_error(exc: Exception, stage: str = "connection") -> tuple[str, str]:
    """Classify driver details internally; never emit their possibly secret text."""
    if stage == "credentials":
        return "WINDOWS_SPEICHER", "Die Datenbankverbindung funktioniert, aber der Zugang konnte nicht in der Windows-Anmeldeinformationsverwaltung gespeichert werden."
    if stage == "status":
        return "LOKALER_STATUS", "Die Datenbankverbindung funktioniert, aber der lokale Verbindungsstatus konnte nicht gespeichert werden."
    detail = str(exc).casefold()
    sqlstate = getattr(exc, "sqlstate", None)
    if any(part in detail for part in ("certificate verify failed", "certificate_verify_failed", "self-signed certificate", "root certificate", "does not match host name", "hostname mismatch")):
        return "TLS_ZERTIFIKAT", "Das Serverzertifikat konnte nicht bestätigt werden. Das Werkzeug benötigt die passende Supabase-Root-CA; die Zertifikatsprüfung bleibt eingeschaltet."
    if sqlstate == "28P01" or "password authentication failed" in detail or "invalid password" in detail:
        return "PASSWORT_ABGELEHNT", "Supabase hat das Datenbankpasswort abgelehnt. Bitte das beim Anlegen dieses Projekts festgelegte Datenbankpasswort erneut eingeben."
    if "tenant or user not found" in detail:
        return "PROJEKT_NICHT_GEFUNDEN", "Der Pooler erkennt Projekt oder Datenbankbenutzer nicht. Die Session-Pooler-Adresse im Supabase-Connect-Dialog erneut abgleichen."
    if any(part in detail for part in ("could not translate host name", "name or service not known", "getaddrinfo failed", "no such host is known")):
        return "DNS", "Die Serveradresse konnte nicht aufgelöst werden. Internetverbindung und DNS prüfen."
    if any(part in detail for part in ("connection refused", "actively refused", "verweigert")):
        return "VERBINDUNG_ABGELEHNT", "Der Datenbankport ist nicht erreichbar. Projektstatus und Netzwerkfreigabe für Port 5432 prüfen."
    if any(part in detail for part in ("timeout", "timed out", "time out")):
        return "ZEITUEBERSCHREITUNG", "Der Datenbankserver hat nicht rechtzeitig geantwortet. Projektstatus und Netzwerkverbindung prüfen."
    if "maxclientsinsessionmode" in detail or "max clients reached" in detail or sqlstate == "53300":
        return "VERBINDUNGSLIMIT", "Alle verfügbaren Datenbankverbindungen sind belegt. Andere Datenbankfenster schließen und später erneut versuchen."
    if sqlstate == "42501" or "permission denied" in detail:
        return "BERECHTIGUNG", "Der Datenbankbenutzer besitzt nicht die nötige Leseberechtigung für den Verbindungstest."
    return "DB_VERBINDUNG", "Die Datenbankverbindung ist fehlgeschlagen. Bitte diesen Fehlercode zur weiteren Prüfung mitteilen."


def connection_parameters(dsn: str, project_ref: str) -> dict:
    try:
        parsed = conninfo_to_dict(dsn)
    except psycopg.Error:
        # libpq errors can echo connection strings: do not expose them.
        raise ValueError("Die Eingabe ist kein gültiger PostgreSQL-Verbindungsstring.") from None
    host, user = parsed.get("host", ""), parsed.get("user", "")
    direct = host == f"db.{project_ref}.supabase.co"
    pooler = bool(re.fullmatch(r"aws-[a-z0-9-]+\.pooler\.supabase\.com", host)) and user == f"postgres.{project_ref}"
    if not (direct or pooler):
        raise ValueError("Die Verbindung gehört nicht zum hinterlegten Projekt. Unter Connect den Direct- oder Session-Pooler-String kopieren.")
    if parsed.get("dbname") != "postgres" or parsed.get("port", "5432") != "5432":
        raise ValueError("Für die Einrichtung bitte Datenbank postgres und Direct/Session-Verbindung auf Port 5432 verwenden.")
    allowed = {"host", "port", "dbname", "user", "password", "sslmode", "sslrootcert"}
    if set(parsed) - allowed:
        raise ValueError("Der Verbindungsstring enthält zusätzliche Optionen. Den unveränderten String aus Connect verwenden.")
    return {
        "host": host, "port": "5432", "dbname": "postgres", "user": user,
        "password": parsed.get("password", ""), "sslmode": "verify-full",
        "sslrootcert": root_certificate(),
    }


def credential_target(project_ref):
    return f"Wissensdatenbank/Supabase/{project_ref}/Einrichtung"


def saved_connection_parameters(dsn: str, project_ref: str) -> dict:
    parameters = connection_parameters(dsn, project_ref)
    saved_root = conninfo_to_dict(dsn).get("sslrootcert", "")
    legacy_default = saved_root.replace("\\", "/").casefold().endswith("/certifi/cacert.pem")
    if saved_root and not legacy_default and Path(saved_root).resolve() != ROOT_CA.resolve():
        # Keep an explicitly selected certificate, but migrate the old default.
        parameters["sslrootcert"] = saved_root
    return parameters


def load_saved_connection(project_ref):
    import win32cred
    credential = win32cred.CredRead(credential_target(project_ref), win32cred.CRED_TYPE_GENERIC)
    blob = credential["CredentialBlob"]
    return blob.decode("utf-16-le") if isinstance(blob, bytes) else blob


def save_connection(project_ref: str, parameters: dict) -> None:
    import win32cred
    dsn = make_conninfo(**parameters)
    win32cred.CredWrite({
        "Type": win32cred.CRED_TYPE_GENERIC,
        "TargetName": credential_target(project_ref),
        "UserName": parameters["user"],
        # pywin32 expects Unicode here and performs its own UTF-16 conversion.
        # CredRead returns bytes, which load_saved_connection decodes.
        "CredentialBlob": dsn,
        "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
        "Comment": "Nur lokale Wissensdatenbank-Einrichtung; nicht für den lesenden MCP-Dienst.",
    }, 0)
    if load_saved_connection(project_ref) != dsn:
        raise RuntimeError("Der gespeicherte Zugang konnte nicht unverändert zurückgelesen werden.")


def check_connection(parameters):
    # Read-only even when the supplied account is a database administrator.
    with psycopg.connect(**parameters, connect_timeout=15,
                         options="-c default_transaction_read_only=on -c statement_timeout=10000",
                         prepare_threshold=None) as db:
        result = db.execute("SELECT current_database(), current_setting('server_version'), EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='kb')").fetchone()
        return {"database": result[0], "postgres_version": result[1], "kb_schema_present": result[2]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-saved", action="store_true", help="Gespeicherte Verbindung ohne Eingabe lesend prüfen")
    parser.add_argument("--root-certificate", type=Path, help="Optional: Root-Zertifikat aus dem Supabase-Dashboard")
    args = parser.parse_args()
    project = json.loads(PROJECT.read_text(encoding="utf-8"))
    project_ref = project["project_ref"]
    print("Supabase-Verbindung prüfen – keine Tabellenänderung und kein Upload")
    stage = "connection"
    try:
        if args.check_saved:
            parameters = saved_connection_parameters(load_saved_connection(project_ref), project_ref)
        else:
            endpoint = project.get("connection_endpoint")
            if endpoint is not None:
                if not isinstance(endpoint, dict) or set(endpoint) != {"host", "port", "dbname", "user"}:
                    raise ValueError("Der hinterlegte Endpunkt darf nur Host, Port, Datenbank und Benutzer enthalten.")
                parameters = connection_parameters(make_conninfo(**endpoint), project_ref)
                print("Die Verbindungsadresse für dein Supabase-Projekt ist bereits hinterlegt.")
                print("Gib nur dein Datenbankpasswort ein. Die Eingabe wird nicht angezeigt.")
            else:
                print("Im Supabase-Projekt Connect → Direct → Session pooler öffnen; Type: URI.")
                print("Den Connection string hier einfügen. Die Eingabe wird nicht angezeigt.")
                dsn = getpass.getpass("Verbindungsstring > ")
                parameters = connection_parameters(dsn, project_ref)
            if not parameters["password"] or parameters["password"] in ("[YOUR-PASSWORD]", "YOUR-PASSWORD", "[your-password]"):
                parameters["password"] = getpass.getpass("Datenbankpasswort > ")
            if not parameters["password"]:
                raise ValueError("Kein Passwort eingegeben.")
        if args.root_certificate:
            certificate = args.root_certificate.resolve()
            if not certificate.is_file():
                raise ValueError("Die Zertifikatsdatei fehlt.")
            parameters["sslrootcert"] = str(certificate)
        result = check_connection(parameters)
        if not args.check_saved:
            stage = "credentials"
            save_connection(project_ref, parameters)
        stage = "status"
        project["connection_tested"] = True
        project["connection_check"] = result
        PROJECT.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Verbindung erfolgreich. Zugang liegt in der Windows-Anmeldeinformationsverwaltung.")
        print("PostgreSQL:", result["postgres_version"], "| Schema kb vorhanden:", result["kb_schema_present"])
        print("Es wurden keine Cloud-Inhalte verändert oder veröffentlicht.")
        return 0
    except (KeyboardInterrupt, EOFError):
        print("Abgebrochen.")
    except ValueError as exc:
        print(str(exc))
    except Exception as exc:
        code, message = explain_error(exc, stage)
        print(f"Fehlercode: {code} ({type(exc).__name__})")
        print(message)
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
