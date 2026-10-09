"""Mocktests für schritt3_clips ohne GPU und ohne ComfyUI.

Ein ersetzter ComfyUI-Zugriff liefert gültige, abgeschnittene, verrauschte oder gar keine Clips; geprüft wird, dass nie
etwas Falsches als fertig gilt und der Aufruf dann mit Fehlercode endet. Braucht ffmpeg, numpy und Pillow.

Aufruf: python test_runner_ohne_gpu.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import os

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import clips_einzeln
import lib
import schritt3_clips

ECHT_STORY = lib.STORY
FALSCH = []


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def pruefe(bedingung, text):
    print(("ok      " if bedingung else "FEHLER  ") + text, flush=True)
    if not bedingung:
        FALSCH.append(text)


def aufruf(modus, argumente=()):
    """Führt schritt3_clips.main mit ersetztem ComfyUI aus; modus bestimmt, was der Server 'liefert'."""
    lib.hochladen = lambda server, pfad: "start.png"
    lib.speicher_freigeben = lambda *a, **k: None
    lib.messung_schreiben = lambda *a, **k: {}
    lib.dateiverweise = lambda outputs: [] if modus == "keine_ausgabe" else [{"filename": "x.mp4"}]
    lib.ausfuehren = lambda server, graph, abfrage_s=5: ({"outputs": {}}, 1.0, {"ok": True})

    def herunterladen(server, video, ziel):
        quelle = {"gut": GUT, "rauschen": RAUSCHEN, "abgeschnitten": ABGESCHNITTEN}[modus]
        shutil.copy(quelle, ziel)
    lib.herunterladen = herunterladen
    sys.argv = ["schritt3_clips.py", "--geraet", "test", *argumente]
    try:
        schritt3_clips.main()
        return 0
    except SystemExit as ende:
        return ende.code if isinstance(ende.code, int) else 1


def einzeln(rc, schreibt):
    """Führt clips_einzeln.main mit ersetztem ComfyUI-Start und ersetztem Kindprozess aus."""
    ziel = lib.WURZEL / "clips" / "shot_01.mp4"
    clips_einzeln.port_belegt = lambda port: False
    clips_einzeln.comfyui_starten = lambda comfyui, port, log: object()
    clips_einzeln.comfyui_beenden = lambda prozess: None

    class Ergebnis:
        returncode = rc

    def lauf(befehl, **k):
        if "--nur-pruefen" not in befehl and schreibt:
            ziel.write_bytes(b"halber clip")
        return Ergebnis()
    echt = subprocess.run
    clips_einzeln.subprocess.run = lauf
    sys.argv = ["clips_einzeln.py", "--geraet", "test", "--comfyui", "x"]
    try:
        clips_einzeln.main()
        return 0
    except SystemExit as ende:
        return ende.code if isinstance(ende.code, int) else 1
    finally:
        clips_einzeln.subprocess.run = echt


def main():
    global GUT, RAUSCHEN, ABGESCHNITTEN
    tmp = Path(tempfile.mkdtemp(prefix="runner_mock_"))
    (tmp / "story").mkdir()
    (tmp / "bilder" / "auswahl").mkdir(parents=True)
    (tmp / "clips").mkdir()
    (tmp / "messung").mkdir()
    shutil.copy(ECHT_STORY / "figuren.json", tmp / "story" / "figuren.json")
    shots = {"shots": [{"id": 1, "akt": 1, "titel": "t", "figuren": [], "bild": "a town", "bewegung": "slow", "weiter": False, "sprechertext": ""}]}
    (tmp / "story" / "shots.json").write_text(json.dumps(shots), encoding="utf-8")
    lib.WURZEL = tmp
    lib.STORY = tmp / "story"
    start = tmp / "bilder" / "auswahl" / "shot_01.png"
    ffmpeg("-f", "lavfi", "-i", "testsrc=s=640x360:d=1:r=1", "-frames:v", "1", str(start))
    GUT = tmp / "gut.mp4"
    RAUSCHEN = tmp / "rauschen.mp4"
    ABGESCHNITTEN = tmp / "abgeschnitten.mp4"
    ffmpeg("-loop", "1", "-i", str(start), "-t", "5.04", "-r", "24", "-pix_fmt", "yuv420p", str(GUT))
    ffmpeg("-f", "lavfi", "-i", "color=c=gray:s=640x360:d=5.04:r=24,noise=alls=100:allf=t", "-pix_fmt", "yuv420p", str(RAUSCHEN))
    ABGESCHNITTEN.write_bytes(GUT.read_bytes()[: GUT.stat().st_size // 2])
    ziel = tmp / "clips" / "shot_01.mp4"
    meta = ziel.with_name("shot_01.mp4.json")

    pruefe(aufruf("gut") == 0 and ziel.exists() and meta.exists(), "gültiger Clip: Exitcode 0, Clip und Metadatei vorhanden")
    daten = json.loads(meta.read_text(encoding="utf-8"))
    pruefe(all(k in daten for k in ("start_sha256", "prompt_sha256", "seed", "clip_sha256")), "Metadatei enthält Start-, Prompt-, Seed- und Clip-Hash")

    pruefe(aufruf("gut", ["--nur-pruefen"]) == 0, "zweiter Aufruf: gebundener Clip wird übersprungen")

    ziel.write_bytes(ziel.read_bytes() + b"x")
    pruefe(aufruf("gut", ["--nur-pruefen"]) != 0 and any((tmp / "clips" / "alt_ersetzt").iterdir()), "veränderter Clip (Hash/Decode): archiviert, Fehlercode ohne Neurechnung")
    shutil.rmtree(tmp / "clips" / "alt_ersetzt")

    pruefe(aufruf("gut") == 0 and ziel.exists(), "nach Archivierung wird neu gerechnet")
    shots["shots"][0]["bewegung"] = "completely different motion"
    (tmp / "story" / "shots.json").write_text(json.dumps(shots), encoding="utf-8")
    code = aufruf("gut")
    pruefe(code == 0 and any((tmp / "clips" / "alt_ersetzt").glob("shot_01.mp4.*")), "geänderter Prompt: alter Clip archiviert, neuer gerechnet")
    shutil.rmtree(tmp / "clips" / "alt_ersetzt")

    meta.unlink()
    pruefe(aufruf("gut", ["--nur-pruefen"]) != 0, "gültiger Clip ohne Metadatei, ohne --uebernehmen: nicht als fertig akzeptiert")
    shutil.rmtree(tmp / "clips" / "alt_ersetzt")
    aufruf("gut")
    meta.unlink()
    pruefe(aufruf("gut", ["--nur-pruefen", "--uebernehmen"]) == 0, "mit --uebernehmen: gebunden")
    pruefe("rekonstruiert" in json.loads(meta.read_text(encoding="utf-8")).get("herkunft", ""), "Übernahme ist als Rekonstruktion gekennzeichnet")

    ziel.unlink()
    meta.unlink()
    pruefe(aufruf("rauschen") != 0 and not ziel.exists(), "Rauschclip (beide Versuche): Fehlercode, kein Clip als fertig")
    pruefe(aufruf("abgeschnitten") != 0 and not ziel.exists(), "abgeschnittener Clip (Partial): Fehlercode, kein Clip als fertig")
    pruefe(aufruf("keine_ausgabe") != 0 and not ziel.exists(), "keine Videoausgabe: Fehlercode")
    pruefe(len(list((tmp / "clips").glob("*.defekt*"))) >= 2, "verworfene Clips bleiben als .defekt-Dateien erhalten")

    tabelle = {0: 0, 100: 50, 50: 1, 1: 0, 200: 300, 300: 200}
    pruefe(clips_einzeln.gehoert_zum_baum(100, 50, tabelle), "Prozessbaum: Kind gehört zur Wurzel")
    pruefe(not clips_einzeln.gehoert_zum_baum(1, 50, tabelle), "Prozessbaum: Elternprozess gehört nicht zur Wurzel (PID 0 endet, keine Schleife)")
    pruefe(not clips_einzeln.gehoert_zum_baum(200, 50, tabelle), "Prozessbaum: Zyklus 200/300 endet ohne Endlosschleife")
    pruefe(not clips_einzeln.gehoert_zum_baum(999, 50, tabelle), "Prozessbaum: unbekannte PID gehört nicht zur Wurzel")
    for datei in (tmp / "clips").glob("shot_01*"):
        datei.unlink()
    pruefe(einzeln(1, False) != 0, "clips_einzeln: Kind endet mit Code 1, kein Clip: Fehlercode, nicht als fertig")
    pruefe(einzeln(0, False) != 0, "clips_einzeln: Kind endet mit Code 0, aber kein Clip: Fehlercode")
    pruefe(einzeln(1, True) != 0 and not ziel.exists() and any((tmp / "clips" / "alt_unvollstaendig").iterdir()),
           "clips_einzeln: Kind-Fehler mit Partial-Datei: Partial archiviert, Fehlercode")

    shutil.rmtree(tmp, ignore_errors=True)
    print("ALLE TESTS BESTANDEN" if not FALSCH else f"{len(FALSCH)} TESTS FEHLGESCHLAGEN")
    sys.exit(1 if FALSCH else 0)


if __name__ == "__main__":
    main()
