Der Claude-Skill `steuerrecht-recherche` nutzt die steuerliche Wissensdatenbank über den vorhandenen Supabase-MCP oder unabhängig davon über das öffentliche GitHub-Repository.

Das ZIP enthält den Rechercheablauf, SQL-Vorlagen und einen Python-Helfer für commitgebundenes Lesen, Wortsuche und SHA-256-Prüfung. Die Dokumente bleiben in GitHub und Supabase; das Skillpaket enthält keine Zugangsdaten.

Installation: ZIP herunterladen, in Claude Codeausführung aktivieren und unter **Customize → Skills → + → Create skill → Upload a skill** hochladen. Für den GitHub-Helfer muss Netzwerkzugriff auf `api.github.com` und `raw.githubusercontent.com` erlaubt sein. Für Supabase die bestehende Verbindung im Chat aktivieren.

Validiert mit 15 automatisierten Helfertests, sieben echten Supabase-SQL-Beispielen, vollständigen Abrufen langer Fundstellen und einem unabhängigen Rechercheprobelauf über GitHub. Das ZIP wurde außerhalb des Repositorys ausgeführt. Installation und Verhalten in der persönlichen Claude-Oberfläche sind noch nicht beobachtet.

[Installationsanleitung](https://github.com/juliangossen/wissensdatenbank-steuern/blob/skill-v1.0.0/Werkzeuge/Claude_Skill/README.md) · [Prüfbericht](https://github.com/juliangossen/wissensdatenbank-steuern/blob/skill-v1.0.0/Werkzeuge/Claude_Skill/Pruefung.md)
