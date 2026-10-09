"""Schritt 5: Clips in Shot-Reihenfolge zu einem 1080p-Rohschnitt zusammensetzen (ohne Ton, Sprecherin folgt separat).

Aufruf: python schritt5_schnitt.py [--ausgabe film_roh.mp4]
"""
import argparse
import subprocess

import os
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lib


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ausgabe", default="film_roh.mp4")
    a = p.parse_args()
    shots = lib.laden_json("shots.json")["shots"]
    clips = [lib.WURZEL / "clips" / f"shot_{s['id']:02d}.mp4" for s in shots]
    fehlend = [c.name for c in clips if not c.exists()]
    if fehlend:
        raise SystemExit(f"{len(fehlend)} Clips fehlen, zuerst {fehlend[:5]}")
    liste = lib.WURZEL / "clips" / "liste.txt"
    liste.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    ziel = lib.WURZEL / a.ausgabe
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(liste), "-an",
                    "-vf", "scale=1920:1080:flags=lanczos,fps=24", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(ziel)], check=True)
    print(ziel)


if __name__ == "__main__":
    main()
