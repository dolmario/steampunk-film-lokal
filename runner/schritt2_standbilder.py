"""Schritt 2: ein Standbild je Einstellung, 16:9, mit den Referenzbildern der beteiligten Figuren.

Jede Figur im Shot liefert ref_gesicht.png und ref_figur.png als ReferenceLatent. Der Figurentext steht
wörtlich im Prompt. Ergebnis: bilder/standbilder/shot_NN_seedS.png

Zu jedem Bild gehört shot_NN_seedS.png.json mit Hash von Prompt, Referenzbildern, Seed, Modell und Größe. Ein
vorhandenes Bild gilt nur, wenn alles passt; sonst wird es nach standbilder/alt_ersetzt/ verschoben und neu erzeugt.

Aufruf: python schritt2_standbilder.py --geraet evo [--shots 1,7,12] [--seeds 11,22] [--neu] [--uebernehmen]
"""
import argparse
import hashlib
import json
import time

import os
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ablaeufe
import lib

BREITE, HOEHE = 1344, 768


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--geraet", required=True)
    p.add_argument("--server", default=lib.STANDARD_SERVER)
    p.add_argument("--shots", default="")
    p.add_argument("--seeds", default="11")
    p.add_argument("--modell", default="klein4")
    p.add_argument("--neu", action="store_true", help="vorhandene Bilder der gewählten Shots archivieren und neu rechnen")
    p.add_argument("--uebernehmen", action="store_true", help="vorhandene Bilder ohne Metadatei als passend übernehmen und binden")
    a = p.parse_args()
    figuren = lib.laden_json("figuren.json")
    shots = lib.laden_json("shots.json")["shots"]
    auswahl = {int(x) for x in a.shots.split(",")} if a.shots else None
    hochgeladen = {}
    for shot in shots:
        if auswahl and shot["id"] not in auswahl:
            continue
        refs = []
        ref_hash = hashlib.sha256()
        for fid in shot["figuren"]:
            for teil in ("gesicht", "figur"):
                pfad = lib.WURZEL / "bilder" / "figuren" / fid / f"ref_{teil}.png"
                if not pfad.exists():
                    raise SystemExit(f"Referenz fehlt: {pfad}")
                if pfad not in hochgeladen:
                    hochgeladen[pfad] = lib.hochladen(a.server, pfad)
                refs.append(hochgeladen[pfad])
                ref_hash.update(pfad.read_bytes())
        prompt = lib.standbild_prompt(figuren, shot)
        for seed in map(int, a.seeds.split(",")):
            ziel = lib.WURZEL / "bilder" / "standbilder" / f"shot_{shot['id']:02d}_seed{seed}.png"
            meta_pfad = ziel.with_name(ziel.name + ".json")
            meta_soll = {"prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(), "refs_sha256": ref_hash.hexdigest(),
                         "seed": seed, "modell": a.modell, "groesse": [BREITE, HOEHE]}
            if ziel.exists():
                if not a.neu and meta_pfad.exists():
                    ist = json.loads(meta_pfad.read_text(encoding="utf-8"))
                    if {k: ist.get(k) for k in meta_soll} == meta_soll:
                        continue
                elif not a.neu and a.uebernehmen:
                    meta_pfad.write_text(json.dumps({**meta_soll, "uebernommen_ohne_metadatei": True}, indent=1), encoding="utf-8")
                    continue
                archiv = ziel.parent / "alt_ersetzt"
                archiv.mkdir(exist_ok=True)
                stempel = time.strftime("%Y%m%d-%H%M%S")
                for datei in (ziel, meta_pfad):
                    if datei.exists():
                        datei.rename(archiv / f"{datei.name}.{stempel}")
            graph = ablaeufe.klein(prompt, refs, BREITE, HOEHE, seed, f"steampunk/shot_{shot['id']:02d}", a.modell)
            eintrag, sek, werte = lib.ausfuehren(a.server, graph)
            bilder = list(lib.dateiverweise(eintrag.get("outputs", {})))
            if not bilder:
                raise SystemExit(f"{ziel.name}: ComfyUI lieferte kein Bild")
            lib.herunterladen(a.server, bilder[0], ziel)
            meta_pfad.write_text(json.dumps(meta_soll, indent=1), encoding="utf-8")
            print(lib.messung_schreiben(a.geraet, "standbild", ziel.name, sek, werte, {"shot": shot["id"], "seed": seed, "modell": a.modell}), flush=True)


if __name__ == "__main__":
    main()
