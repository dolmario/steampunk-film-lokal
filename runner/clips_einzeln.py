"""Alle fehlenden Clips nacheinander, je Clip ein frisch gestartetes ComfyUI.

ComfyUI läuft mit --disable-pinned-memory; nur der selbst gestartete Prozess wird beendet.
Mit dem Python der ComfyUI-Umgebung starten (braucht numpy und Pillow für die Clipprüfung).

Aufruf: python clips_einzeln.py --geraet evo --comfyui C:\\Pfad\\zu\\ComfyUI [--shots 13,14] [--port 8189]
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lib
import schritt3_clips

VERSUCHE = 2


def port_belegt(port):
    """TCP-Verbindungsversuch: belegt ist der Port auch dann, wenn dort kein ComfyUI antwortet."""
    with socket.socket() as sock:
        sock.settimeout(3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def port_antwortet(server):
    try:
        urllib.request.urlopen(server + "/system_stats", timeout=5).read()
        return True
    except Exception:
        return False


def prozess_tabelle():
    """{pid: eltern_pid} aller Prozesse (nur Windows; sonst None, dann entfällt die Besitzerprüfung)."""
    if os.name != "nt":
        return None
    antwort = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId | ConvertTo-Json -Compress"],
                             capture_output=True, text=True)
    return {int(e["ProcessId"]): int(e["ParentProcessId"]) for e in json.loads(antwort.stdout)}


def port_besitzer(port):
    antwort = subprocess.run(["powershell", "-NoProfile", "-Command",
                              f"(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue).OwningProcess"],
                             capture_output=True, text=True)
    return [int(x) for x in antwort.stdout.split() if x.isdigit()]


def gehoert_zum_baum(pid, wurzel, tabelle):
    """True, wenn pid die Wurzel ist oder unter ihr hängt; besuchte PIDs verhindern Endlosschleifen (PID 0, Zyklen)."""
    besucht = set()
    while pid in tabelle and pid not in besucht:
        if pid == wurzel:
            return True
        besucht.add(pid)
        pid = tabelle[pid]
    return pid == wurzel


def comfyui_starten(comfyui, port, log):
    befehl = [sys.executable, "main.py", "--listen", "127.0.0.1", "--port", str(port), "--disable-pinned-memory"]
    prozess = subprocess.Popen(befehl, cwd=comfyui, stdout=log, stderr=subprocess.STDOUT)
    server = f"http://127.0.0.1:{port}"
    for _ in range(180):
        if prozess.poll() is not None:
            raise SystemExit(f"ComfyUI beendet sich beim Start (Exitcode {prozess.returncode}), siehe {log.name}")
        if port_antwortet(server):
            tabelle = prozess_tabelle()
            if tabelle is not None:
                besitzer = port_besitzer(port)
                if not besitzer or not all(gehoert_zum_baum(b, prozess.pid, tabelle) for b in besitzer):
                    comfyui_beenden(prozess)
                    raise SystemExit(f"Port {port} gehört nicht dem eigenen ComfyUI (Besitzer {besitzer}, eigene PID {prozess.pid})")
            print(f"ComfyUI gestartet: PID {prozess.pid}, Port {port}", flush=True)
            return prozess
        time.sleep(2)
    comfyui_beenden(prozess)
    raise SystemExit("ComfyUI antwortet nach 6 Minuten nicht")


def comfyui_beenden(prozess):
    if prozess.poll() is None:
        if os.name == "nt":
            # Die venv-python.exe startet einen Kindprozess; nur dieser eigene Baum wird beendet.
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(prozess.pid)], capture_output=True)
        else:
            prozess.terminate()
        prozess.wait(timeout=60)
    time.sleep(5)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--geraet", required=True)
    p.add_argument("--comfyui", default=os.environ.get("COMFYUI_DIR"), help="Ordner mit main.py")
    p.add_argument("--port", type=int, default=8189)
    p.add_argument("--shots", default="")
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--neu", action="store_true", help="vorhandene Clips der gewählten Shots archivieren und neu rechnen")
    a = p.parse_args()
    if not a.comfyui:
        raise SystemExit("--comfyui oder COMFYUI_DIR angeben")
    server = f"http://127.0.0.1:{a.port}"
    if port_belegt(a.port):
        raise SystemExit(f"Port {a.port} ist belegt; bitte das laufende Programm zuerst selbst beenden")

    shots = lib.laden_json("shots.json")["shots"]
    auswahl = {int(x) for x in a.shots.split(",")} if a.shots else None
    clips = lib.WURZEL / "clips"
    fehlend = []
    for shot in shots:
        if auswahl and shot["id"] not in auswahl:
            continue
        name = f"shot_{shot['id']:02d}"
        ziel = clips / f"{name}.mp4"
        basis = [sys.executable, str(lib.WURZEL / "runner" / "schritt3_clips.py"), "--geraet", a.geraet,
                 "--server", server, "--shots", str(shot["id"]), "--seed", str(a.seed)]
        if ziel.exists():
            if a.neu:
                schritt3_clips.archivieren(ziel)
            elif subprocess.run(basis + ["--nur-pruefen"], cwd=lib.WURZEL / "runner").returncode == 0:
                continue
        for versuch in range(VERSUCHE):
            with open(lib.WURZEL / "messung" / f"comfyui-{a.port}-{name}-{versuch}.log", "w", encoding="utf-8") as log:
                prozess = comfyui_starten(a.comfyui, a.port, log)
                try:
                    rc = subprocess.run(basis, cwd=lib.WURZEL / "runner").returncode
                finally:
                    comfyui_beenden(prozess)
            if rc == 0 and ziel.exists():
                break
            print(f"{name}: Versuch {versuch} endete mit Code {rc}", flush=True)
            if ziel.exists():
                schritt3_clips.archivieren(ziel, "alt_unvollstaendig")
        if not ziel.exists():
            fehlend.append(shot["id"])
            print(f"{name}: nach {VERSUCHE} Versuchen kein gültiger Clip", flush=True)
    if fehlend:
        raise SystemExit(f"Ohne gültigen Clip: {fehlend}. Schnitt erst nach Nacharbeit.")
    print("Alle gewählten Clips liegen geprüft vor.")


if __name__ == "__main__":
    main()
