import unittest
from unittest.mock import MagicMock, patch

from connect_project import check_connection, connection_parameters, credential_target, explain_error, load_saved_connection, root_certificate, save_connection, saved_connection_parameters
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import psycopg
import sys
import tempfile
import uuid
from pathlib import Path

REF = "vtriyndfmuwzqwrkpkde"


class ConnectionTests(unittest.TestCase):
    def test_only_expected_project_and_session_port(self):
        params = connection_parameters(f"postgresql://postgres.{REF}:test@aws-0-eu-central-1.pooler.supabase.com:5432/postgres", REF)
        self.assertEqual(params["sslmode"], "verify-full")
        for dsn in [
            "postgresql://postgres:secret@example.com:5432/postgres",
            f"postgresql://postgres.other:secret@aws-0-eu-central-1.pooler.supabase.com:5432/postgres",
            f"postgresql://postgres.{REF}:secret@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
            f"host=db.{REF}.supabase.co dbname=postgres user=postgres service=other",
        ]:
            with self.assertRaises(ValueError):
                connection_parameters(dsn, REF)

    def test_parser_error_does_not_repeat_secret(self):
        with self.assertRaises(ValueError) as ctx:
            connection_parameters("PASSWORD_SECRET not a connection", REF)
        self.assertNotIn("PASSWORD_SECRET", str(ctx.exception))

    def test_check_is_read_only_and_has_no_schema_writes(self):
        with patch("connect_project.psycopg.connect") as connect:
            db = connect.return_value.__enter__.return_value
            db.execute.return_value.fetchone.return_value = ("postgres", "17.6", False)
            result = check_connection({"host": "test-host"})
            self.assertIn("default_transaction_read_only=on", connect.call_args.kwargs["options"])
            self.assertTrue(db.execute.call_args.args[0].startswith("SELECT "))
            self.assertEqual(db.execute.call_count, 1)
            self.assertFalse(result["kb_schema_present"])

    def test_official_certificate_is_present_and_tampering_is_rejected(self):
        self.assertTrue(Path(root_certificate()).is_file())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ca.crt"
            path.write_bytes(b"not the trusted certificate")
            with patch("connect_project.ROOT_CA", path), self.assertRaises(ValueError):
                root_certificate()

    def test_error_messages_distinguish_tls_and_password_without_leaking_input(self):
        secret = "DO_NOT_PRINT_TEST_SECRET"
        for text, code in [
            ("SSL error: certificate verify failed " + secret, "TLS_ZERTIFIKAT"),
            ("password authentication failed " + secret, "PASSWORT_ABGELEHNT"),
            ("could not translate host name " + secret, "DNS"),
            ("Tenant or user not found " + secret, "PROJEKT_NICHT_GEFUNDEN"),
            ("connection timed out " + secret, "ZEITUEBERSCHREITUNG"),
            ("unclassified " + secret, "DB_VERBINDUNG"),
        ]:
            result = explain_error(psycopg.OperationalError(text))
            self.assertEqual(result[0], code)
            self.assertNotIn(secret, str(result))

    def test_saved_connection_migrates_old_default_but_preserves_explicit_certificate(self):
        params = connection_parameters(f"postgresql://postgres.{REF}:test@aws-0-eu-central-1.pooler.supabase.com:5432/postgres", REF)
        params["sslrootcert"] = r"C:\old\Lib\site-packages\certifi\cacert.pem"
        migrated = saved_connection_parameters(make_conninfo(**params), REF)
        self.assertEqual(migrated["sslrootcert"], root_certificate())
        self.assertEqual(migrated["sslmode"], "verify-full")
        params["sslrootcert"] = str(Path("custom root.crt").resolve())
        custom = saved_connection_parameters(make_conninfo(**params), REF)
        self.assertEqual(custom["sslrootcert"], params["sslrootcert"])

    def test_credential_failure_is_not_reported_as_database_failure(self):
        result = explain_error(OSError("DO_NOT_PRINT_TEST_SECRET"), "credentials")
        self.assertEqual(result[0], "WINDOWS_SPEICHER")
        self.assertNotIn("DO_NOT_PRINT_TEST_SECRET", str(result))

    @unittest.skipUnless(sys.platform == "win32", "Requires Windows Credential Manager")
    def test_real_windows_credential_roundtrip_and_update_with_unicode(self):
        import win32cred
        import pywintypes
        # A unique, disposable target; never reads or alters real project access.
        test_ref = "test-" + uuid.uuid4().hex
        params = {"host": "test.invalid", "user": "dummy", "dbname": "postgres",
                  "password": "TEST_ONLY äß 🙂 ' \\ :@/%", "sslmode": "verify-full"}
        try:
            for suffix in (" first", " updated"):
                expected = dict(params, password=params["password"] + suffix)
                save_connection(test_ref, expected)
                actual = conninfo_to_dict(load_saved_connection(test_ref))
                self.assertTrue(actual == expected, "Credential round trip changed the test data")
        finally:
            try:
                win32cred.CredDelete(credential_target(test_ref), win32cred.CRED_TYPE_GENERIC)
            except pywintypes.error as exc:
                if exc.winerror != 1168:  # Nothing was written if CredWrite failed.
                    raise


if __name__ == "__main__":
    unittest.main()
