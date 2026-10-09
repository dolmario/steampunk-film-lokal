"""Selbstläufer: ganzer Film in einem Aufruf: Figurenreferenzen, Standbilder, Clips, Rohschnitt.

Voraussetzungen: ComfyUI mit den Modellen aus der README und ffmpeg im Pfad. Mit dem Python der ComfyUI-Umgebung starten
(numpy, Pillow). Geändert wird nur in story/figuren.json und story/shots.json; bei erneutem Aufruf werden nur die
Figuren, Standbilder und Clips neu gerechnet, deren Text sich geändert hat (Hash in den Metadateien neben den Bildern).

Aufruf: python selbstlaeufer.py --geraet evo --comfyui C:\\Pfad\\zu\\ComfyUI [--port 8189] [--seed 11] [--modell klein4|klein9|dev]

Standbilder laufen in einem ComfyUI-Start, jeder Clip in einem eigenen Start mit --disable-pinned-memory;
ohne diese Option liefert LTX-2.5 graues Rauschen oder bricht beim Laden ab.
"""
import argparse
import os
import shutil
import subprocess
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import clips_einzeln
import lib


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--geraet", required=True)
    p.add_argument("--comfyui", default=os.environ.get("COMFYUI_DIR"), help="Ordner mit main.py")
    p.add_argument("--port", type=int, default=8189)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--modell", default="klein4", choices=["klein4", "klein9", "dev"], help="Bildmodell für Figuren und Standbilder")
    p.add_argument("--uebernehmen", action="store_true", help="vorhandene Standbilder ohne Metadatei als passend übernehmen")
    p.add_argument("--stills-neu", default="", help="Shot-Nummern (Komma), deren Standbild archiviert und neu gerechnet wird")
    a = p.parse_args()
    if not a.comfyui:
        raise SystemExit("--comfyui oder COMFYUI_DIR angeben")
    if not os.path.isfile(os.path.join(a.comfyui, "main.py")):
        raise SystemExit(f"Kein ComfyUI-Ordner (main.py fehlt): {a.comfyui}")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg und ffprobe müssen im Pfad sein")
    server = f"http://127.0.0.1:{a.port}"
    if clips_einzeln.port_belegt(a.port):
        raise SystemExit(f"Port {a.port} ist belegt; bitte das laufende ComfyUI zuerst selbst beenden")
    runner = lib.WURZEL / "runner"
    shots = lib.laden_json("shots.json")["shots"]

    with open(lib.WURZEL / "messung" / f"comfyui-{a.port}-standbilder.log", "w", encoding="utf-8") as log:
        prozess = clips_einzeln.comfyui_starten(a.comfyui, a.port, log)
        try:
            subprocess.run([sys.executable, str(runner / "schritt1_figurenblatt.py"), "--geraet", a.geraet,
                            "--server", server, "--seeds", str(a.seed), "--modell", a.modell, "--auto"], cwd=runner, check=True)
            befehl = [sys.executable, str(runner / "schritt2_standbilder.py"), "--geraet", a.geraet,
                      "--server", server, "--seeds", str(a.seed), "--modell", a.modell]
            if a.stills_neu:
                subprocess.run(befehl + ["--shots", a.stills_neu, "--neu"], cwd=runner, check=True)
            subprocess.run(befehl + (["--uebernehmen"] if a.uebernehmen else []), cwd=runner, check=True)
        finally:
            clips_einzeln.comfyui_beenden(prozess)

    auswahl = lib.WURZEL / "bilder" / "auswahl"
    auswahl.mkdir(parents=True, exist_ok=True)
    for s in shots:
        name = f"shot_{s['id']:02d}"
        shutil.copy(lib.WURZEL / "bilder" / "standbilder" / f"{name}_seed{a.seed}.png", auswahl / f"{name}.png")

    subprocess.run([sys.executable, str(runner / "clips_einzeln.py"), "--geraet", a.geraet, "--comfyui", a.comfyui,
                    "--port", str(a.port), "--seed", str(a.seed)], cwd=runner, check=True)
    subprocess.run([sys.executable, str(runner / "schritt5_schnitt.py")], cwd=runner, check=True)


if __name__ == "__main__":
    main()
