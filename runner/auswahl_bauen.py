"""Baut die endgültige Clip-Auswahl: clips/auswahl/shot_NN.mp4, clips/AUSWAHL.md (mit SHA256) und film_roh_auswahl.mp4.

Grundlage ist clips/AUSWAHL.json: {"standard": "neu", "gruende": {"10": "..."}, "alt": ["32"], "hinweise": {"27": "..."}}.
"alt" nennt Shots, für die der Clip aus clips/alt_ersetzt (jüngster Eintrag) genommen wird, alle anderen nehmen clips/shot_NN.mp4.
Die Clips im Hauptordner bleiben unverändert und an ihre Marker gebunden.

Aufruf: python auswahl_bauen.py [--ohne-schnitt]
"""
import argparse
import hashlib
import json
import shutil
import subprocess

import os
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lib


def sha256(pfad):
    return hashlib.sha256(pfad.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ohne-schnitt", action="store_true")
    a = p.parse_args()
    clips = lib.WURZEL / "clips"
    wahl = json.loads((clips / "AUSWAHL.json").read_text(encoding="utf-8"))
    alt_shots = set(str(x) for x in wahl.get("alt", []))
    ziel = clips / "auswahl"
    ziel.mkdir(exist_ok=True)
    zeilen = ["| Shot | Quelle | SHA256 des Clips | Begründung |", "|---|---|---|---|"]
    dateien = []
    for shot in lib.laden_json("shots.json")["shots"]:
        nr = str(shot["id"])
        name = f"shot_{shot['id']:02d}"
        if nr in alt_shots:
            kandidaten = sorted(x for x in (clips / "alt_ersetzt").glob(f"{name}.mp4.[0-9]*") if not x.name.endswith(".json"))
            quelle = kandidaten[-1]
            herkunft = f"alt (v1, `alt_ersetzt/{quelle.name}`)"
        else:
            quelle = clips / f"{name}.mp4"
            herkunft = "neu (v2)"
        ausgabe = ziel / f"{name}.mp4"
        shutil.copy(quelle, ausgabe)
        dateien.append(ausgabe)
        grund = wahl.get("gruende", {}).get(nr, wahl.get("standardgrund", ""))
        hinweis = wahl.get("hinweise", {}).get(nr)
        zeilen.append(f"| {nr} | {herkunft} | `{sha256(ausgabe)}` | {grund}{' **Hinweis:** ' + hinweis if hinweis else ''} |")
    kopf = ["# Clip-Auswahl", "", wahl.get("kopf", ""), ""]
    (clips / "AUSWAHL.md").write_text("\n".join(kopf + zeilen) + "\n", encoding="utf-8")
    print(f"{len(dateien)} Clips in {ziel}")
    if a.ohne_schnitt:
        return
    liste = ziel / "liste.txt"
    liste.write_text("".join(f"file '{d.as_posix()}'\n" for d in dateien), encoding="utf-8")
    ausgabe = lib.WURZEL / "film_roh_auswahl.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(liste), "-an", "-vf",
                    "scale=1920:1080:flags=lanczos,fps=24", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(ausgabe)], check=True)
    print(ausgabe)


if __name__ == "__main__":
    main()
