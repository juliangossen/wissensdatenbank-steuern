"""Lokale Oberfläche und Kommandozeile für die versionierte Cloud-Übergabe."""
import argparse
import json
import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from sync_core import inspect_source, publish

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WissensdatenbankCloud" / "einstellungen.json"


class App:
    def __init__(self, window):
        self.window = window
        self.busy = False
        self.events = queue.Queue()
        self.target = tk.StringVar()
        self.automatic = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Bereit zum Prüfen. Noch keine Cloud-Verbindung bestätigt.")
        self.summary = tk.StringVar(value="Bestand wird beim Prüfen eingelesen.")
        self.last_snapshot = None
        try:
            self.target.set(json.loads(SETTINGS.read_text(encoding="utf-8")).get("zielordner", ""))
        except (OSError, ValueError):
            pass
        window.title("Wissensdatenbank · Cloud-Übergabe")
        window.geometry("940x680")
        window.minsize(760, 570)
        window.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(window)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("TLabel", font=("Segoe UI", 10))
        frame = ttk.Frame(window, padding=24)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(9, weight=1)
        ttk.Label(frame, text="Gesetze für die Cloud bereitstellen", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Geprüfte Originalquellen und Markdown · alte Fassungen bleiben erhalten").grid(row=1, column=0, sticky="w", pady=(6, 20))
        ttk.Label(frame, text=f"Lokale Wissensdatenbank: {ROOT}", wraplength=850).grid(row=2, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.summary).grid(row=3, column=0, sticky="w", pady=(8, 18))
        destination = ttk.LabelFrame(frame, text="Zielordner", padding=12)
        destination.grid(row=4, column=0, sticky="ew")
        destination.columnconfigure(0, weight=1)
        self.target_entry = ttk.Entry(destination, textvariable=self.target)
        self.target_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.choose_button = ttk.Button(destination, text="Ordner wählen …", command=self.choose)
        self.choose_button.grid(row=0, column=1)
        ttk.Label(destination, text="Wähle einen Ordner in Google Drive / Meine Ablage. In einem normalen lokalen Ordner entsteht nur eine lokale Kopie.", wraplength=820).grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        actions = ttk.Frame(frame)
        actions.grid(row=5, column=0, sticky="w", pady=(18, 12))
        self.check_button = ttk.Button(actions, text="1. Bestand prüfen", command=lambda: self.run(False))
        self.check_button.pack(side="left", padx=(0, 10))
        self.publish_button = ttk.Button(actions, text="2. Im Zielordner bereitstellen", command=lambda: self.run(True))
        self.publish_button.pack(side="left", padx=(0, 10))
        self.open_button = ttk.Button(actions, text="Ziel öffnen", command=self.open_target)
        self.open_button.pack(side="left")
        ttk.Checkbutton(frame, variable=self.automatic, text="Solange dieses Fenster offen ist: alle 60 Sekunden prüfen und Änderungen bereitstellen", command=self.toggle_auto).grid(row=6, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.status, wraplength=850).grid(row=7, column=0, sticky="w", pady=(16, 8))
        ttk.Label(frame, text="Den Upload-Status siehst du in Google Drive für Desktop. Dieses Tool bestätigt nur die lokale Bereitstellung.", wraplength=850).grid(row=8, column=0, sticky="w", pady=(0, 12))
        log_frame = ttk.Frame(frame)
        log_frame.grid(row=9, column=0, sticky="nsew")
        self.log = tk.Text(log_frame, height=9, wrap="word", state="disabled", font=("Consolas", 9))
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        ttk.Button(frame, text="Einrichtung und Claude-Anbindung lesen", command=lambda: os.startfile(str(Path(__file__).with_name("README.md")))).grid(row=10, column=0, sticky="w", pady=(12, 0))
        window.after(150, self.poll)
        window.after(60000, self.tick)

    def choose(self):
        folder = filedialog.askdirectory(title="Ordner in Google Drive / Meine Ablage wählen", mustexist=True)
        if folder:
            self.target.set(folder)

    def toggle_auto(self):
        if self.automatic.get():
            if not self.target.get().strip():
                self.automatic.set(False)
                messagebox.showinfo("Zielordner fehlt", "Wähle zuerst den Zielordner für die Bereitstellung.")
            else:
                self.run(True)

    def append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", str(text) + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def run(self, transfer):
        if self.busy:
            return
        value = self.target.get().strip()
        if transfer and not value:
            messagebox.showinfo("Zielordner fehlt", "Wähle zuerst einen Zielordner.")
            return
        target = Path(value).expanduser() if value else None
        self.busy = True
        for widget in (self.check_button, self.publish_button, self.choose_button, self.target_entry):
            widget.configure(state="disabled")
        self.status.set("Bestand und Prüfsummen werden geprüft …")

        def worker():
            try:
                if transfer:
                    result = publish(ROOT, target, log=lambda text: self.events.put(("log", text)))
                else:
                    result = inspect_source(ROOT)
                self.events.put(("done", (result, transfer, value)))
            except Exception as exc:
                self.events.put(("error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "log":
                    self.append(data)
                    continue
                self.busy = False
                for widget in (self.check_button, self.publish_button, self.choose_button, self.target_entry):
                    widget.configure(state="normal")
                if kind == "error":
                    self.automatic.set(False)
                    self.status.set("Nicht bereitgestellt. Bitte den Hinweis unten prüfen.")
                    self.append("FEHLER: " + data)
                    continue
                result, transfer, value = data
                self.summary.set(f"{result['documents']} Dokumente · {result['files']} Dateien · {result['bytes'] / 1024 / 1024:.1f} MB · {result['version']}")
                if transfer:
                    self.last_snapshot = result["snapshot"]
                    self.status.set("Lokal bereitgestellt. Bitte den abgeschlossenen Upload in Google Drive prüfen.")
                    self.append(f"Fassung: {result['snapshot']}\nNeu kopiert: {result['copied']} · Bereits vorhanden: {result['unchanged']}")
                    try:
                        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
                        SETTINGS.write_text(json.dumps({"zielordner": value}, ensure_ascii=False, indent=2), encoding="utf-8")
                    except OSError as exc:
                        self.append(f"Ziel wurde bereitgestellt, Einstellung konnte nicht gespeichert werden: {exc}")
                else:
                    self.status.set("Bestand geprüft. Du kannst ihn jetzt im gewählten Zielordner bereitstellen.")
                    self.append("Prüfung erfolgreich. Noch keine Dateien übertragen.")
        except queue.Empty:
            pass
        self.window.after(150, self.poll)

    def tick(self):
        if self.automatic.get() and not self.busy:
            self.run(True)
        self.window.after(60000, self.tick)

    def open_target(self):
        value = self.target.get().strip()
        if not value:
            return
        path = Path(value) / "Wissensdatenbank_Cloud"
        if not path.exists():
            path = Path(value)
        try:
            os.startfile(str(path))
        except OSError as exc:
            messagebox.showerror("Ordner nicht geöffnet", str(exc))

    def close(self):
        if self.busy:
            messagebox.showinfo("Vorgang läuft", "Bitte warte, bis die laufende Prüfung oder Bereitstellung abgeschlossen ist.")
            return
        self.window.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Nur den lokalen Bestand prüfen")
    group.add_argument("--publish", type=Path, metavar="ZIELORDNER", help="Im Zielordner bereitstellen; kein direkter Cloud-Upload")
    group.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.check or args.publish:
        try:
            result = publish(ROOT, args.publish, log=lambda msg: print(msg, file=sys.stderr)) if args.publish else inspect_source(ROOT)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        except Exception as exc:
            print(f"Fehler: {exc}", file=sys.stderr)
            return 1
    window = tk.Tk()
    if args.smoke_test:
        window.withdraw()
    App(window)
    if args.smoke_test:
        window.update_idletasks()
        window.destroy()
        print("GUI aufgebaut; keine Dateien übertragen.")
    else:
        window.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
