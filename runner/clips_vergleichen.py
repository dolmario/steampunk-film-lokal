"""Stellt je Shot den alten Clip (clips/alt_ersetzt) und den neuen (clips/shot_NN.mp4) nebeneinander.

Je Shot eine Zeile mit Bildern bei 0, 2,5 und 4,9 s, links alt, rechts neu; mehrere Shots pro Bogen.
Ausgabe: clips/vergleich/bogen_<n>.png. Braucht ffmpeg. Die Auswahl trifft ein Mensch, das Skript wählt nichts.

Aufruf: python clips_vergleichen.py [--je-bogen 4]
"""
import argparse
import subprocess

import os
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lib


def bilder(video, ziel, prefix):
    ziel.mkdir(parents=True, exist_ok=True)
    dateien = []
    for sek in ("0", "2.5", "4.9"):
        datei = ziel / f"{prefix}_{sek}.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", sek, "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=320:-1", str(datei)], check=True)
        dateien.append(datei)
    return dateien


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--je-bogen", type=int, default=4)
    a = p.parse_args()
    clips = lib.WURZEL / "clips"
    arbeit = clips / "vergleich" / "teile"
    zeilen = []
    for shot in lib.laden_json("shots.json")["shots"]:
        name = f"shot_{shot['id']:02d}"
        neu = clips / f"{name}.mp4"
        alte = sorted((clips / "alt_ersetzt").glob(f"{name}.mp4.[0-9]*")) if (clips / "alt_ersetzt").exists() else []
        alte = [x for x in alte if not x.name.endswith(".json")]
        if not neu.exists() or not alte:
            continue
        # Die archivierte Datei trägt den Zeitstempel als Endung; ffmpeg braucht eine .mp4-Kopie.
        alt = arbeit / f"{name}_alt.mp4"
        arbeit.mkdir(parents=True, exist_ok=True)
        alt.write_bytes(alte[-1].read_bytes())
        zeilen.append((name, bilder(alt, arbeit, f"{name}_alt"), bilder(neu, arbeit, f"{name}_neu")))
    ziel = clips / "vergleich"
    for nr in range(0, len(zeilen), a.je_bogen):
        gruppe = zeilen[nr:nr + a.je_bogen]
        eingaben, filter_teile = [], []
        for i, (name, alt, neu) in enumerate(gruppe):
            for datei in alt + neu:
                eingaben += ["-i", str(datei)]
            teile = "".join(f"[{i * 6 + k}:v]" for k in range(6))
            filter_teile.append(f"{teile}hstack=inputs=6[z{i}]")
        spalten = "".join(f"[z{i}]" for i in range(len(gruppe)))
        filter_teile.append(f"{spalten}vstack=inputs={len(gruppe)}[aus]")
        datei = ziel / f"bogen_{nr // a.je_bogen + 1}.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *eingaben, "-filter_complex", ";".join(filter_teile),
                        "-map", "[aus]", "-frames:v", "1", str(datei)], check=True)
        print(f"{datei.name}: {', '.join(n for n, _, _ in gruppe)} (je Zeile links alt 0/2,5/4,9 s, rechts neu)")


if __name__ == "__main__":
    main()
