"""Schritt 3: LTX-2.5-Clips aus den gewählten Standbildern.

Das Standbild je Einstellung liegt als bilder/auswahl/shot_NN.png. Mit --weiter startet ein Clip mit dem
letzten Bild des vorherigen Clips (nur sinnvoll, wenn die Szene gleich bleibt).

Zu jedem gültigen Clip gehört clips/shot_NN.mp4.json mit Hash von Startbild und Prompt sowie Seed. Ein vorhandener
Clip gilt nur, wenn die Inhaltsprüfung besteht und die Metadatei zu Startbild, Prompt und Seed passt; sonst wird er
nach clips/alt_ersetzt/ verschoben und neu gerechnet. Der Aufruf endet mit Fehlercode, solange ein gewählter Shot
keinen gültigen Clip hat.

Aufruf: python schritt3_clips.py --geraet evo [--shots 7,8] [--seed 11] [--weiter] [--nur-pruefen] [--neu] [--uebernehmen]
"""
import argparse
import hashlib
import json
import subprocess
import time

import os
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ablaeufe
import lib

DAUER_S = 5
GRENZE_DEFEKT = 20  # mittlerer RGB-Abstand des ersten Clipbilds zum Startbild; gültige Clips liegen bei etwa 5


def letztes_bild(video, ziel):
    ziel.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.1", "-i", str(video), "-frames:v", "1", str(ziel)], check=True)
    return ziel


def sha256_datei(pfad):
    return hashlib.sha256(pfad.read_bytes()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def voll_pruefen(ziel, start):
    """Ganzer Decode ohne Fehler, alle drei Stützpunkte vorhanden, Abstand zum Startbild in der Grenze.

    Gibt (ok, grund, pruefung) zurück. Drei Stützpunkte sind eine Stichprobe, kein Treuenachweis."""
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ziel), "-f", "null", "-"], capture_output=True, text=True)
    if decode.returncode != 0 or decode.stderr.strip():
        return False, f"Decode-Fehler: {decode.stderr.strip()[:200] or decode.returncode}", {}
    try:
        pruefung = lib.clip_pruefen(ziel, start)
    except Exception as fehler:
        return False, f"Prüfung nicht möglich: {fehler}", {}
    if pruefung["bilder"] != 3:
        return False, f"nur {pruefung['bilder']} von 3 Stützpunkten", pruefung
    if pruefung["abstand_start"] > GRENZE_DEFEKT:
        return False, f"Abstand zum Startbild {pruefung['abstand_start']:.1f}", pruefung
    return True, "", pruefung


def freier_name(pfad):
    """Hängt -1, -2 ... an, falls der Name schon belegt ist; nichts wird überschrieben."""
    kandidat, n = pfad, 0
    while kandidat.exists():
        n += 1
        kandidat = pfad.with_name(f"{pfad.stem}-{n}{pfad.suffix}")
    return kandidat


def archivieren(ziel, unterordner="alt_ersetzt"):
    """Verschiebt Clip und Metadatei, statt sie zu überschreiben."""
    archiv = ziel.parent / unterordner
    archiv.mkdir(exist_ok=True)
    stempel = time.strftime("%Y%m%d-%H%M%S")
    for datei in (ziel, ziel.with_name(ziel.name + ".json")):
        if datei.exists():
            datei.rename(freier_name(archiv / f"{datei.name}.{stempel}"))


def vorhanden_pruefen(ziel, start, meta_soll, uebernehmen=False):
    """True, wenn der vorhandene Clip voll geprüft besteht und an Startbild, Prompt, Seed und Clip-Hash gebunden ist.

    Ohne Metadatei ist die Erzeugung unbekannt: Der Clip gilt nur mit --uebernehmen und wird dann als Rekonstruktion
    gekennzeichnet (Erwartung, kein Nachweis)."""
    meta_pfad = ziel.with_name(ziel.name + ".json")
    ok, grund, pruefung = voll_pruefen(ziel, start)
    if not ok:
        print(f"{ziel.name}: {grund}, wird archiviert", flush=True)
        return False
    clip_sha = sha256_datei(ziel)
    if not meta_pfad.exists():
        if not uebernehmen:
            print(f"{ziel.name}: Metadatei fehlt, Erzeugung nicht belegt, wird archiviert (--uebernehmen bindet ihn als Rekonstruktion)", flush=True)
            return False
        meta_pfad.write_text(json.dumps({"herkunft": "rekonstruiert: Metadatei fehlte, Erzeugung nicht belegt", "erwartet": meta_soll,
                                         "clip_sha256": clip_sha, **pruefung}, indent=1), encoding="utf-8")
        print(f"{ziel.name}: als Rekonstruktion gebunden", flush=True)
        return True
    ist = json.loads(meta_pfad.read_text(encoding="utf-8"))
    erwartet = ist.get("erwartet", ist)
    for schluessel in ("start_sha256", "prompt_sha256", "seed"):
        if erwartet.get(schluessel) != meta_soll[schluessel]:
            print(f"{ziel.name}: Metadatei passt nicht ({schluessel}), wird archiviert", flush=True)
            return False
    if ist.get("clip_sha256") != clip_sha:
        print(f"{ziel.name}: Clip-Hash passt nicht zur Metadatei, wird archiviert", flush=True)
        return False
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--geraet", required=True)
    p.add_argument("--server", default=lib.STANDARD_SERVER)
    p.add_argument("--shots", default="")
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--tile", type=int, default=512)
    p.add_argument("--frei", action="store_true", help="vor jedem Clip freien Speicher zurückfordern")
    p.add_argument("--weiter", action="store_true", help="Startbild = letztes Bild des vorherigen Clips")
    p.add_argument("--nur-pruefen", action="store_true", help="vorhandene Clips prüfen und binden, nichts rechnen (kein ComfyUI nötig)")
    p.add_argument("--neu", action="store_true", help="vorhandene Clips der gewählten Shots archivieren und neu rechnen")
    p.add_argument("--uebernehmen", action="store_true", help="gültige Clips ohne Metadatei als Rekonstruktion binden")
    a = p.parse_args()
    figuren = lib.laden_json("figuren.json")
    shots = lib.laden_json("shots.json")["shots"]
    auswahl = {int(x) for x in a.shots.split(",")} if a.shots else None
    clips = lib.WURZEL / "clips"
    fehlend = []
    for shot in shots:
        if auswahl and shot["id"] not in auswahl:
            continue
        name = f"shot_{shot['id']:02d}"
        ziel = clips / f"{name}{'_weiter' if a.weiter else ''}.mp4"
        start = lib.WURZEL / "bilder" / "auswahl" / f"{name}.png"
        if a.weiter:
            vorher = clips / f"shot_{shot['id'] - 1:02d}.mp4"
            if not vorher.exists():
                raise SystemExit(f"Vorgänger-Clip fehlt: {vorher}")
            start = letztes_bild(vorher, lib.WURZEL / "bilder" / "weiter" / f"{name}.png")
        if not start.exists():
            raise SystemExit(f"Startbild fehlt: {start}")
        prompt = lib.clip_prompt(figuren, shot)
        meta_soll = {"start_sha256": sha256_datei(start), "prompt_sha256": sha256_text(prompt), "seed": a.seed,
                     "geraet": a.geraet, "zeit": time.strftime("%Y-%m-%d %H:%M:%S")}
        if ziel.exists():
            if a.neu:
                archivieren(ziel)
            elif vorhanden_pruefen(ziel, start, meta_soll, a.uebernehmen):
                continue
            else:
                archivieren(ziel)
        if a.nur_pruefen:
            fehlend.append(shot["id"])
            continue
        bild_name = lib.hochladen(a.server, start)
        gueltig = False
        for versuch, tile in enumerate((a.tile, 256)):
            if a.frei or versuch:
                lib.speicher_freigeben(a.server, alles=bool(versuch))
            graph = ablaeufe.ltx_i2v(bild_name, prompt, DAUER_S, a.seed, f"steampunk/{name}", tile)
            eintrag, sek, werte = lib.ausfuehren(a.server, graph, abfrage_s=5)
            videos = [v for v in lib.dateiverweise(eintrag.get("outputs", {})) if v["filename"].endswith(".mp4")]
            if not videos:
                werte["ok"] = False
                pruefung = {}
            else:
                lib.herunterladen(a.server, videos[0], ziel)
                ok, grund, pruefung = voll_pruefen(ziel, start)
                if not ok:
                    print(f"{name}: Versuch {versuch} verworfen: {grund}", flush=True)
                    werte["ok"] = False
                    ziel.rename(freier_name(ziel.with_suffix(f".defekt{versuch}_{time.strftime('%H%M%S')}.mp4")))
                else:
                    ziel.with_name(ziel.name + ".json").write_text(
                        json.dumps({**meta_soll, "clip_sha256": sha256_datei(ziel), "tile": tile, "versuch": versuch, **pruefung}, indent=1),
                        encoding="utf-8")
            print(lib.messung_schreiben(a.geraet, "clip", ziel.name, sek, werte, {
                "shot": shot["id"], "seed": a.seed, "tile": tile, "versuch": versuch, "weiter": a.weiter, **pruefung}), flush=True)
            if werte["ok"]:
                gueltig = True
                break
        if not gueltig:
            fehlend.append(shot["id"])
    if fehlend:
        raise SystemExit(f"Ohne gültigen Clip: {fehlend}")


if __name__ == "__main__":
    main()
