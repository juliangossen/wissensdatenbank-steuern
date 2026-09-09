# Wissensdatenbank in Google Drive bereitstellen

Die Wissensdatenbank wird weiter lokal in VS Code gepflegt. Das kleine Fenster prüft den registrierten Bestand und stellt ihn mit Original-PDFs beziehungsweise TXT-Webkopien, Markdown, Quellen und Prüfberichten in einem Zielordner bereit. Google Drive für Desktop übernimmt anschließend dessen Upload. Claude erhält den Zugriff durch eine separate Verbindung mit deinem Google-Konto.

## Einmal einrichten

1. [Google Drive für Desktop installieren](https://support.google.com/drive/answer/10838124?hl=de) und mit dem gewünschten Google-Konto anmelden. Google beschreibt dort auch, wie du den Synchronisierungsstatus kontrollierst.
2. Im Explorer einen Zielordner in Google Drive unter **Meine Ablage** anlegen. Den vorhandenen Arbeitsordner der Wissensdatenbank kannst du an seinem bisherigen Ort lassen.
3. [Cloud_Sync_starten.cmd](../../Cloud_Sync_starten.cmd) doppelklicken. Python 3 mit Tkinter ist auf diesem PC bereits verfügbar; das Tool benötigt keine zusätzlichen Pakete.
4. Den Drive-Zielordner wählen, **Bestand prüfen** und anschließend **Im Zielordner bereitstellen** anklicken. Darunter entsteht `Wissensdatenbank_Cloud/`.
5. Warten, bis Google Drive den Upload als abgeschlossen anzeigt. Danach ist der hochgeladene Stand auch bei ausgeschaltetem PC verfügbar. Neue lokale Änderungen können erst hochgeladen werden, wenn der PC und Drive wieder laufen.

Ein normaler lokaler Zielordner funktioniert ebenfalls als Export. Dadurch entsteht allein noch keine Cloud-Verbindung. Das Tool verwendet weder ein Google-Passwort noch API-Zugangsdaten und kann den erfolgreichen Upload nicht selbst bestätigen.

## Claude verbinden

In Claude unter **Customize → Connectors → + → Google Drive → Connect** mit demselben Google-Konto anmelden. Die aktuelle [Anthropic-Anleitung](https://support.claude.com/en/articles/10166901-use-google-workspace-connectors) beschreibt den eingebauten Connector und nennt unter anderem Google Docs, PDF und Office-Dateien. Dafür brauchst du kein eigenes Google-Cloud-Projekt.

**Markdown-Zugriff ist gesondert zu beachten:** Googles Werkzeug `read_file_content` listet `.md` nicht als direkt unterstütztes Textformat. Außerdem können große Dateien unvollständig zurückgegeben werden. Das [Download-Werkzeug](https://developers.google.com/workspace/drive/api/reference/mcp/tools_list/download_file_content) liefert Rohdateien als Base64; das ist ein anderer Zugriff. Eine erfolgreiche Synchronisierung garantiert daher noch keinen vollständigen Markdown-Textzugriff durch Claude. [Google-Lesewerkzeug](https://developers.google.com/workspace/drive/api/reference/mcp/tools_list/read_file_content)

Im Export liegen deshalb auch die geprüften Original-PDFs. Wähle für einen ersten Zugriff eine PDF aus der gewünschten Fassung aus oder gib Claude deren Drive-Link. Prüfe an einer konkreten Vorschrift einschließlich Absatz und Quellenstand, ob Claude die gewünschte Datei tatsächlich gelesen hat. Das Bereitstellen in Drive lädt nicht alle Gesetze automatisch in jedes Gespräch.

Für als Text kopierte Webseiten wie den UStAE enthält der Export die archivierte `.txt`-Quelle und den strukturierten Markdown-Text. Beim UStAE wird zusätzlich die beim Quellenabgleich archivierte amtliche BMF-PDF aus dem Ordner `Quellen/` mit exportiert; sie dient als Vergleichsquelle. Ob ein bestimmter Connector die Dateien vollständig lesen kann, bleibt unabhängig von der lokalen Bereitstellung zu prüfen. Quellenstand und Einschränkungen der Ausgangskopie stehen im zugehörigen Dokument und Prüfnachweis.

Beispiel nach Auswahl der PDF:

> Verwende die beigefügte UStG-PDF aus meiner Wissensdatenbank. Nenne zuerst den dokumentierten Quellenstand und gib dann § 1 Absatz 1 wieder. Falls du den Abschnitt nicht vollständig abrufen kannst, sage das ausdrücklich.

Wenn du gezielt die strukturierten Markdown-Texte als fortlaufend verknüpfte Google Docs nutzen möchtest, ist eine zusätzliche Import-Anbindung erforderlich. Google unterstützt [Markdown-Import über die Drive API](https://developers.google.com/workspace/drive/api/guides/manage-uploads). Diese erste Tool-Version erzeugt noch keine Google Docs. Bei sehr großen Gesetzen wären mehrere Lesedokumente nötig; Google Docs begrenzt ein Dokument auf [1,02 Millionen Zeichen](https://support.google.com/drive/answer/37603?hl=de).

## Aktualisierungen im Alltag

1. Neue amtliche Fassung beschaffen, in einem neuen datierten Standordner vollständig konvertieren und prüfen. Alte archivierte Fassungen behalten.
2. Den geprüften Stand in `Bestand.json` und im passenden Register (`PDF_Archiv/Archivregister.json` oder `Web_Archiv/Archivregister.json`) mit den zugehörigen Pfaden und Prüfsummen registrieren. Die bestehenden Konvertierungs- und Bestandswerkzeuge dienen diesem Schritt; dieses Sync-Tool ermittelt keine Gesetzesänderungen und erneuert keine Prüfnachweise.
3. Das Fenster starten und erneut bereitstellen. Optional kontrolliert es alle 60 Sekunden den Bestand und stellt Änderungen bereit, solange es offen bleibt. Die Automatik muss bei jedem Start bewusst eingeschaltet werden.
4. Den abgeschlossenen Upload in Drive kontrollieren und Claude auf die gewünschte Fassung verweisen.

Eine nachträgliche Textänderung ohne passenden Prüfnachweis und aktualisiertes Register wird zurückgewiesen. Identische Wiederholungen erzeugen keine weiteren Fassungen.

## Ablage im Ziel

```text
Wissensdatenbank_Cloud/
  README.md
  AKTUELL.json
  Fassungen/
    Stand_2026-09-09_<Inhaltskennung>/
      README.md
      Bestand.json
      Rechtsgebiete/…
      PDF_Archiv/…
      Web_Archiv/…
```

Jede Fassung behält ihre Dateien. `AKTUELL.json` zeigt auf den zuletzt vollständig lokal bereitgestellten Bestand; das bedeutet den zuletzt ausgewählten Bestand, nicht automatisch das derzeit geltende Recht. Ein geänderter Bestand bekommt eine neue Inhaltskennung. Unbearbeitete Eingänge werden nicht übernommen. Der Cloud-Ordner ist eine Ausgabekopie; Änderungen werden lokal in der Wissensdatenbank vorgenommen.

Der gespeicherte Zielpfad liegt unter `%LOCALAPPDATA%\WissensdatenbankCloud\einstellungen.json`. Ein Cloud-Abgleich kann Dateien in anderer Reihenfolge übertragen; die lokale Abschlussmarkierung ersetzt deshalb nicht die Upload-Bestätigung von Drive.

## Kommandozeile

Aus der Projektwurzel:

```powershell
py Werkzeuge/Cloud_Sync/gui.py --check
py Werkzeuge/Cloud_Sync/gui.py --publish "G:\Meine Ablage\Gesetze"
py -m unittest discover -s Werkzeuge/Cloud_Sync -p "test_*.py" -v
```

Der Laufwerksbuchstabe und Ordnername sind Beispiele. Verwende den tatsächlich vorhandenen Zielpfad.

## Zur eingefügten MCP-Anleitung

Google bietet den Remote-Endpunkt `https://drivemcp.googleapis.com/mcp/v1` tatsächlich an, derzeit als Developer Preview. Die eigene Einrichtung ist in der [Google-Dokumentation](https://developers.google.com/workspace/drive/api/guides/configure-mcp-server) beschrieben. Die Kombination `uvx @modelcontextprotocol/server-gdrive` aus dem eingefügten Text ist keine Konfiguration dieses Remote-Dienstes. Das genannte Paket gehört zu einem [archivierten lokalen Referenzserver](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/gdrive). Für den Einstieg hier wird der eingebaute Claude-Connector verwendet.

Dokumentation geprüft am 09.09.2026. Die Google- und Claude-Konten sind durch das Anlegen dieses Tools noch nicht verbunden.

Lokale Verifikation: [Prüfergebnisse](Pruefung.md).
