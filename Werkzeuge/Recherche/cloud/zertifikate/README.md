# Supabase-Root-Zertifikat

`prod-ca-2021.crt` ist das öffentliche Zertifikat „Supabase Root 2021 CA“.
Es enthält keinen privaten Schlüssel. Das Verbindungswerkzeug nutzt diese
Datei ausschließlich für seinen Supabase-Datenbankzugriff mit `verify-full`;
es verändert weder den Windows-Zertifikatsspeicher noch andere Programme.

Am 09.09.2026 über verifiziertes HTTPS heruntergeladen:
[offizieller Download](https://supabase-downloads.s3-ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt).
Die URL stammt aus der [Downloadvorlage des Supabase-Dashboards](https://github.com/supabase/supabase/blob/a96a587f65f317ae56d4ff3d403e36d0d61a8473/apps/studio/hooks/custom-content/custom-content.json#L63);
die [SSL-Konfiguration](https://github.com/supabase/supabase/blob/a96a587f65f317ae56d4ff3d403e36d0d61a8473/apps/studio/components/interfaces/Settings/Database/SSLConfiguration.tsx#L123)
setzt dafür `env=prod`. Supabase dokumentiert die Verwendung dieses Zertifikats
mit Session-Pooler und `verify-full` in der [PSQL-Anleitung](https://supabase.com/docs/guides/database/psql).

- Datei: 1.367 Bytes
- SHA-256 der Datei: `700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7`
- SHA-256 des DER-Zertifikats: `807025ad50d4ed219d2c9c7d299c004f824eb00cf7f65afef607d07b72e6cafa`
- Gültig bis: 26.04.2031, 10:56:53 UTC

Das Werkzeug prüft den Dateihash vor Verwendung. Ein späterer Zertifikatswechsel
erfordert eine ausdrücklich geprüfte Aktualisierung von Datei und Hash.

Der bisher verwendete allgemeine Mozilla-CA-Speicher (`certifi`) enthielt diese
Supabase-CA nicht. Der Fehler „self-signed certificate in certificate chain“ war
vor der Passwortanmeldung reproduzierbar. Mit der offiziellen CA wurden
TLS 1.3, die Zertifikatskette und der Servername erfolgreich geprüft. Der Server
forderte danach SCRAM-Authentifizierung an; bei diesem Test wurde kein Passwort
gesendet und keine Datenbankabfrage ausgeführt.

Zusätzlich mit dem tatsächlichen psycopg/libpq-Treiber bei `verify-full`
verifiziert: `require_auth=none` brach wie vorgesehen erst bei der SASL-Anforderung
des Servers ab. Dabei waren Passwortquellen deaktiviert; es wurde kein Passwort
übertragen. Die Option ist nur Teil dieses Diagnosetests, nicht des normalen
Verbindungswerkzeugs ([PostgreSQL-Dokumentation](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-REQUIRE-AUTH)).
