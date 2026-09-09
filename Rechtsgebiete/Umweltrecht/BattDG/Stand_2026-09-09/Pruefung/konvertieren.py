"""Reproduziert den Volltext aus den archivierten Quellen."""
from pathlib import Path
import runpy,sys
here=Path(__file__).resolve().parent
root=next(p for p in here.parents if (p/'Werkzeuge/gesetz_konvertieren.py').is_file())
sys.argv=[str(root/'Werkzeuge/gesetz_konvertieren.py'),'--config',str(here/'konfiguration.json')]
runpy.run_path(sys.argv[0],run_name='__main__')
