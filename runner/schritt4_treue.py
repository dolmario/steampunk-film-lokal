"""Schritt 4: Gesichtstreue messen.

Je Clip wird jede Sekunde ein Bild entnommen, die Gesichter werden erkannt und per Kosinusähnlichkeit
mit den Referenzgesichtern (bilder/figuren/<id>/ref_gesicht.png) verglichen. Ausgabe: messung/treue_<geraet>.csv
mit Mittelwert und Minimum je Clip und Figur.

Braucht insightface und onnxruntime (pip install insightface onnxruntime opencv-python).

Aufruf: python schritt4_treue.py --geraet evo [--pfad clips]
"""
import argparse
import csv
import subprocess
import tempfile
from pathlib import Path

import os
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lib


def modell_laden():
    try:
        from insightface.app import FaceAnalysis
    except ImportError:
        raise SystemExit("insightface fehlt: pip install insightface onnxruntime opencv-python")
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    return app


def einbettung(app, pfad):
    import cv2
    bild = cv2.imread(str(pfad))
    gesichter = app.get(bild)
    if not gesichter:
        return None
    return max(gesichter, key=lambda g: (g.bbox[2] - g.bbox[0]) * (g.bbox[3] - g.bbox[1])).normed_embedding


def main():
    import numpy as np
    p = argparse.ArgumentParser()
    p.add_argument("--geraet", required=True)
    p.add_argument("--pfad", default="clips")
    a = p.parse_args()
    app = modell_laden()
    refs = {}
    for ordner in (lib.WURZEL / "bilder" / "figuren").glob("*/"):
        pfad = ordner / "ref_gesicht.png"
        if pfad.exists():
            refs[ordner.name] = einbettung(app, pfad)
    if not refs:
        raise SystemExit("keine ref_gesicht.png gefunden")
    zeilen = []
    for video in sorted((lib.WURZEL / a.pfad).glob("*.mp4")):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf", "fps=1", f"{tmp}/f_%02d.png"], check=True)
            werte = {fid: [] for fid in refs}
            import cv2
            for bild in sorted(Path(tmp).glob("f_*.png")):
                for g in app.get(cv2.imread(str(bild))):
                    aehnlich = {fid: float(np.dot(g.normed_embedding, e)) for fid, e in refs.items() if e is not None}
                    bester = max(aehnlich, key=aehnlich.get)
                    werte[bester].append(aehnlich[bester])
        for fid, w in werte.items():
            if w:
                zeilen.append({"geraet": a.geraet, "clip": video.name, "figur": fid, "bilder": len(w),
                               "mittel": round(sum(w) / len(w), 3), "minimum": round(min(w), 3)})
    ziel = lib.WURZEL / "messung" / f"treue_{a.geraet}.csv"
    with ziel.open("w", newline="", encoding="utf-8") as f:
        schreiber = csv.DictWriter(f, fieldnames=["geraet", "clip", "figur", "bilder", "mittel", "minimum"])
        schreiber.writeheader()
        schreiber.writerows(zeilen)
    print(f"{len(zeilen)} Zeilen -> {ziel}")


if __name__ == "__main__":
    main()
