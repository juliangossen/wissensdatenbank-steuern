# BFH-Textimport vom 14.09.2026

Aufgenommen wurden die vom Nutzer gelieferten Dateien `v_r_6_12.txt` und `v_r_7_12.txt` mit den BFH-Urteilen V R 6/12 und V R 7/12 vom 19.12.2013. Die unveränderten Originale liegen im [Web-Archiv des Importtags](../../Web_Archiv/02_In_Markdown_umgewandelt/Stand_2026-09-14/README.md). Die amtlichen HTML-Vergleichsbelege und das Abrufmanifest liegen unter `quellen/` und als Kopien im jeweiligen Dokumentordner.

Der Konverter übernimmt jede nichtleere Quellzeile mit einem Herkunftsmarker und prüft den sichtbaren Text nach Rücklesen zeichenweise. Zusätzliche Randnummernüberschriften machen die vorhandenen Randnummern einzeln recherchierbar. Die Auslassung Rn. 16–32 in V R 6/12 bleibt ausdrücklich gekennzeichnet. Die Anmerkung von Ursula Slapio zu V R 7/12 ist vom Urteilstext getrennt. Abweichungen zur amtlichen Quelle werden dokumentiert, nicht stillschweigend korrigiert.

Wiederholung im Projektordner:

```powershell
& 'Werkzeuge/Recherche/.venv/Scripts/python.exe' -B Werkzeuge/BFH_Import_2026-09-14/importieren.py
& 'Werkzeuge/Recherche/.venv/Scripts/python.exe' -B Werkzeuge/web_archiv_index_erstellen.py
& 'Werkzeuge/Recherche/.venv/Scripts/python.exe' -B Werkzeuge/bestand_erstellen.py
& 'Werkzeuge/Recherche/.venv/Scripts/python.exe' -B Werkzeuge/Cloud_Sync/gui.py --check
```

Der Konverter verwendet bereits archivierte Originale erneut. Beim Erstimport wurden die beiden Eingangsdateien nach erfolgreicher Prüfung ihrer identischen SHA-256-Prüfsummen aus dem Hauptordner in das Web-Archiv verschoben. Der erneute Konverterlauf verschiebt oder löscht keine Eingangsdateien.

Die gesamte registrierte Sammlung einschließlich beider Urteile wird mit `Werkzeuge/Recherche/cloud/sync.py` lokal indexiert, übertragen, zurückgelesen und erst nach erfolgreicher Prüfung in Supabase aktiviert. Für einen regulären Import keinen auf einzelne Dokumente begrenzten Pilotlauf aktivieren.

Der [Importabschluss](Abschluss.md) enthält den aktivierten Cloudbestand und den festen Prüfbericht. Nach erfolgreichem Cloud-Sync aktualisiert `dokumentation_aktualisieren.py` die Bestandsangaben in den Anleitungen aus diesem Bericht. Die [lokale Rechercheprüfung](Lokale_Recherchepruefung.json) bestätigt den Abruf der letzten Randnummer beider Kopien und die korrekte Abweisung der fehlenden Rn. 16 in V R 6/12.
