"""Schritt 1: Kandidaten für das Figurenblatt (Gesicht, Dreiviertel, ganze Figur).

Elara entsteht mit dem Referenzbild als ReferenceLatent, Mira nur aus dem Text. Danach wählt man je Figur
ein Gesicht und eine ganze Figur und kopiert sie nach bilder/figuren/<id>/ref_gesicht.png und ref_figur.png.

Mit --auto werden ohne Handarbeit Gesicht und ganze Figur des ersten Seeds als Referenz übernommen
(bilder/figuren/<id>/ref_gesicht.png, ref_figur.png). Zu den Referenzen gehört ref.json mit dem Hash von Figurentext,
Stil und Referenzbild: Ändert sich der Text einer Figur, werden ihre alten Bilder nach alt_<Zeit>/ verschoben und neu erzeugt.

Aufruf: python schritt1_figurenblatt.py --geraet evo [--seeds 11,22,33,44] [--figur elara] [--auto]
"""
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

import os
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ablaeufe
import lib

ANSICHTEN = {
    "gesicht": ("close-up portrait, face and shoulders, looking at the camera with a calm confident expression, plain warm brass-toned workshop background", 1024, 1024),
    "dreiviertel": ("three-quarter view portrait, turned slightly to the side, soft smile, plain warm brass-toned workshop background", 1024, 1024),
    "figur": ("full-length standing portrait, whole body visible head to boots, plain warm brass-toned workshop background", 832, 1216),
}


def figuren_hash(figuren, fid, f):
    inhalt = lib.figurenblock(figuren, [fid]) + "|" + figuren["stil"]
    if f.get("referenz_bild") and Path(f["referenz_bild"]).exists():
        inhalt += "|" + hashlib.sha256(Path(f["referenz_bild"]).read_bytes()).hexdigest()
    return hashlib.sha256(inhalt.encode("utf-8")).hexdigest()


def alte_bilder_archivieren(ordner):
    archiv = ordner / f"alt_{time.strftime('%Y%m%d-%H%M%S')}"
    archiv.mkdir()
    for datei in ordner.glob("*.png"):
        shutil.move(str(datei), archiv / datei.name)
    return archiv


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--geraet", required=True)
    p.add_argument("--server", default=lib.STANDARD_SERVER)
    p.add_argument("--seeds", default="11,22,33,44")
    p.add_argument("--figur", default="")
    p.add_argument("--modell", default="klein4")
    p.add_argument("--auto", action="store_true", help="ersten Seed als Referenz übernehmen")
    a = p.parse_args()
    seeds = [int(x) for x in a.seeds.split(",")]
    if a.auto:
        seeds = seeds[:1]
    figuren = lib.laden_json("figuren.json")
    for fid, f in figuren["figuren"].items():
        if a.figur and fid != a.figur:
            continue
        ordner = lib.WURZEL / "bilder" / "figuren" / fid
        ordner.mkdir(parents=True, exist_ok=True)
        text_hash = figuren_hash(figuren, fid, f)
        meta = ordner / "ref.json"
        if meta.exists():
            ist = json.loads(meta.read_text(encoding="utf-8"))
            if ist.get("text_sha256") != text_hash or ist.get("modell", "klein4") != a.modell:
                print(f"{fid}: Figurentext oder Modell geändert, alte Bilder nach {alte_bilder_archivieren(ordner).name}", flush=True)
                meta.unlink()
        refs = []
        if f.get("referenz_bild") and Path(f["referenz_bild"]).exists():
            refs = [lib.hochladen(a.server, f["referenz_bild"])]
        for ansicht, (text, b, h) in ANSICHTEN.items():
            for seed in seeds:
                ziel = lib.WURZEL / "bilder" / "figuren" / fid / f"{ansicht}_seed{seed}.png"
                if ziel.exists():
                    continue
                prompt = f"{lib.figurenblock(figuren, [fid])} {text}. {figuren['stil']}."
                graph = ablaeufe.klein(prompt, refs, b, h, seed, f"steampunk/{fid}_{ansicht}", a.modell)
                eintrag, sek, werte = lib.ausfuehren(a.server, graph)
                bilder = list(lib.dateiverweise(eintrag.get("outputs", {})))
                if bilder:
                    lib.herunterladen(a.server, bilder[0], ziel)
                print(lib.messung_schreiben(a.geraet, "figurenblatt", ziel.name, sek, werte, {"figur": fid, "seed": seed, "modell": a.modell}), flush=True)
        if a.auto:
            for ansicht, ref in (("gesicht", "ref_gesicht.png"), ("figur", "ref_figur.png")):
                quelle = ordner / f"{ansicht}_seed{seeds[0]}.png"
                if not (ordner / ref).exists():
                    if not quelle.exists():
                        raise SystemExit(f"{fid}: {quelle.name} wurde nicht erzeugt")
                    shutil.copy(quelle, ordner / ref)
            if not meta.exists():
                meta.write_text(json.dumps({"text_sha256": text_hash, "seed": seeds[0], "modell": a.modell}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
