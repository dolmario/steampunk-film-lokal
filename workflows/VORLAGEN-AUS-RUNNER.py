"""Schreibt die *-RUNNER-*-API-Vorlagen direkt aus runner/ablaeufe.py (nur Text, kein ComfyUI, keine GPU).

Aufruf:  python workflows/VORLAGEN-AUS-RUNNER.py
Ergebnis in workflows/: Standbild Klein 4B und dev (1344x768, je eine Figur = 2 Referenzen) (Clip: 03-CLIP-API-VORLAGE.json passt bereits zum Runner).
Die hier liegenden Dateien sind inhaltsgleich; das Skript dient zum Nachprüfen oder wenn sich ablaeufe.py ändert.
"""
import json
import pathlib
import sys

HIER = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "runner"))
import ablaeufe  # noqa: E402

REFS = ["REPLACE_UPLOADED_ref_gesicht.png", "REPLACE_UPLOADED_ref_figur.png"]
VORLAGEN = {
    "02-REFERENZBILD-KLEIN4-RUNNER-1344x768-API-VORLAGE.json":
        ablaeufe.klein("REPLACE: shot prompt", REFS, 1344, 768, 11, "steampunk/runner-klein4-shot", "klein4"),
    "02-REFERENZBILD-DEV-RUNNER-1344x768-API-VORLAGE.json":
        ablaeufe.klein("REPLACE: shot prompt", REFS, 1344, 768, 11, "steampunk/runner-dev-shot", "dev"),
}
# 03-CLIP-API-VORLAGE.json entspricht ablaeufe.ltx_i2v(..., 5, 11, ..., tile=512) bereits (Werte beim Lesen verglichen), daher keine zweite Clip-Vorlage.

for name, graph in VORLAGEN.items():
    (HIER / name).write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("geschrieben:", name)
