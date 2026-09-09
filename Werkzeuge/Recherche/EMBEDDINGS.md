# Lokale semantische Suche

Die Suche verwendet echte Modellvektoren aus `intfloat/multilingual-e5-small`
(384 Dimensionen, MIT-Lizenz). Das mehrsprachige Modell unterstützt Deutsch.
Es läuft mit FastEmbed und ONNX Runtime auf der CPU. Gesetzestexte und Suchfragen
werden dabei nicht an einen externen KI-Dienst geschickt. Es gibt keine
Embedding-API-Kosten und es werden keine Zugangsdaten benötigt.

Beim Import berechnen standardmäßig zwei lokale Prozesse die 32er-Pakete
parallel, mit jeweils höchstens vier CPU-Threads. Nur der Hauptprozess prüft
die Ergebnisse und schreibt den Cache. Bereits geprüfte Pakete bleiben bei
einem Abbruch wiederverwendbar; eine neue Fassung wird erst nach Abschluss
aktiviert. Modell, Tokenfenster, Paketgröße und Cache-Schlüssel bleiben dabei
unverändert. Für Windows wird der Import über die vorhandenen Startdateien
beziehungsweise `cli.py` oder `cloud/sync.py` gestartet, nicht über Python-stdin.

## Festgelegte Modellfassung

- Hugging-Face-Repository: `intfloat/multilingual-e5-small`
- Commit: `614241f622f53c4eeff9890bdc4f31cfecc418b3`
- ONNX-Datei: `onnx/model_qint8_avx512_vnni.onnx` (118.346.824 Bytes)
- SHA-256: `dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88`
- Zusätzlich: Tokenizer und Konfiguration, zusammen rund 17 MB.
- Cache: `Werkzeuge/Recherche/.daten/modelle`

Beim ersten Einsatz werden ausschließlich die öffentlichen Modelldateien von
Hugging Face heruntergeladen. Danach wird zuerst die vollständige gepinnte lokale
Fassung verwendet; Internetzugriff ist für die Inferenz nicht nötig. Die ONNX-Datei
wird vor dem Laden mit SHA-256 geprüft. FastEmbed erhält den konkreten lokalen
Snapshot-Pfad, damit dessen normaler Download nicht eine andere Fassung auswählt.
Das Modell lädt keinen Python-Code aus seinem Repository.

`LocalEmbedder.model_revision` nennt Commit, ONNX-Datei, Prefix- und Chunker-Version.
Der Suchindex muss diesen Wert zusammen mit dem Inhaltshash speichern und eine
geänderte Modellfassung als Anlass für neue Embeddings behandeln.

## Textfenster und Vollständigkeit

Das Modell verarbeitet höchstens 512 Token einschließlich Spezialtoken. Für
Suchfenster werden standardmäßig 448 Token einschließlich Gesetzestitel und des
E5-Präfixes budgetiert. Benachbarte Fenster überlappen um bis zu 48 Körper-Token.
`LocalEmbedder.chunk_text(body, title=title)` zählt mit dem echten Tokenizer und
liefert unveränderte Teilstrings des Körpers. Beim Embedding wird
`title + "\n" + chunk` übergeben. Die Funktion deckt den vollständigen Körper ab.

`passage: ` für Dokumente und `query: ` für Suchfragen fügt die Klasse nach der
Modellvorgabe selbst hinzu. Überlange Dokumenteingaben werden mit einer klaren
Fehlermeldung abgelehnt. Automatische Trunkierung ist ausgeschaltet. Lange
Suchfragen werden auf mehrere Tokenfenster verteilt; ihr Gesamtvektor ist das
normalisierte Mittel dieser Fenster. Das berücksichtigt sämtliche Textteile,
kann bei Fragen mit mehreren Themen aber ungenauer als getrennte Suchfragen sein.

Der eigenständige Helper `chunk_text(text, max_chars, overlap_chars)` arbeitet nur
mit Zeichen. Er dient allgemeinen Textoperationen und garantiert keine Tokenlänge.
Der Importer muss die Methode des `LocalEmbedder` verwenden.

Die Fenster dienen ausschließlich der Suche. Vollständige Vorschriften samt
Fußnoten, Anlagen und Quellenangaben werden separat gespeichert und abgerufen.
Semantische Ähnlichkeit ist keine fachliche Prüfung einer Steuerfrage.

## Prüfung

Die allgemeinen Tests benötigen keinen Modelldownload. Den Integrationstest mit
dem echten Modell startet man aus diesem Verzeichnis in PowerShell:

```powershell
$env:RECHERCHE_EMBEDDING_TEST = '1'
& '.venv/Scripts/python.exe' -B -m unittest test_embeddings -v
```

Er prüft eine deutsche Sachverhaltssuche, normierte Vektoren, tokenbegrenzte
Fenster mit vollständiger Textabdeckung und die ausdrückliche Ablehnung eines zu
langen Dokumentes. Er ersetzt keinen fachlichen Recherche-Benchmark.

Prüflauf am 09.09.2026: alle sechs Tests einschließlich der drei Modelltests
erfolgreich auf Windows mit Python 3.14, FastEmbed 0.8.0 und CPUExecutionProvider.
Der erste Lauf einschließlich Download dauerte rund 30 Sekunden.

## Primärquellen

- [Modellkarte und Nutzungsbeispiele von intfloat](https://huggingface.co/intfloat/multilingual-e5-small)
- [Gepinnte ONNX-Datei](https://huggingface.co/intfloat/multilingual-e5-small/blob/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/model_qint8_avx512_vnni.onnx)
- [FastEmbed: eigene Textmodelle](https://github.com/qdrant/fastembed#-dense-text-embeddings)
- [FastEmbed 0.8.0: Modellverwaltung und lokaler Modellpfad](https://github.com/qdrant/fastembed/blob/v0.8.0/fastembed/common/model_management.py)
- [Multilingual E5: Forschungsbericht](https://arxiv.org/abs/2402.05672)
