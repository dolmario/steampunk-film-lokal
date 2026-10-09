"""Gemeinsame Helfer: ComfyUI-API, Messung, Prompt-Bau. Läuft unverändert auf EVO-X2, 3080 Ti und 3090 Ti."""
import json
import threading
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
STORY = WURZEL / "story"
STANDARD_SERVER = "http://127.0.0.1:8189"


def laden_json(name):
    return json.loads((STORY / name).read_text(encoding="utf-8"))


def senden(server, pfad, nutzlast=None):
    daten = json.dumps(nutzlast).encode("utf-8") if nutzlast is not None else None
    anfrage = urllib.request.Request(server + pfad, data=daten,
                                     headers={"Content-Type": "application/json"} if daten else {})
    with urllib.request.urlopen(anfrage, timeout=600) as antwort:
        return json.loads(antwort.read())


def hochladen(server, pfad):
    pfad = Path(pfad)
    grenze = uuid.uuid4().hex
    kopf = (f'--{grenze}\r\nContent-Disposition: form-data; name="image"; filename="{pfad.name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n").encode()
    rumpf = (kopf + pfad.read_bytes() +
             f'\r\n--{grenze}\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n--{grenze}--\r\n'.encode())
    anfrage = urllib.request.Request(server + "/upload/image", data=rumpf,
                                     headers={"Content-Type": f"multipart/form-data; boundary={grenze}"})
    with urllib.request.urlopen(anfrage, timeout=120) as antwort:
        return json.loads(antwort.read())["name"]


class Messer(threading.Thread):
    """Tastet /system_stats alle 2 s ab: größte GPU-Belegung und kleinster freier RAM."""

    def __init__(self, server):
        super().__init__(daemon=True)
        self.server, self.stop, self.vram_max, self.ram_frei_min = server, False, 0, None

    def run(self):
        while not self.stop:
            try:
                st = senden(self.server, "/system_stats")
                gpu = st["devices"][0]
                belegt = (gpu["vram_total"] - gpu["vram_free"]) // 2**20
                self.vram_max = max(self.vram_max, belegt)
                frei = st["system"].get("ram_free", 0) // 2**20
                self.ram_frei_min = frei if self.ram_frei_min is None else min(self.ram_frei_min, frei)
            except Exception:
                pass
            time.sleep(2)


def ausfuehren(server, graph, abfrage_s=3):
    """Schickt den Graphen, wartet auf das Ende, liefert (history-Eintrag, Sekunden, Messwerte)."""
    messer = Messer(server)
    messer.start()
    start = time.time()
    try:
        auftrag = senden(server, "/prompt", {"prompt": graph})["prompt_id"]
        while True:
            verlauf = senden(server, f"/history/{auftrag}")
            if auftrag in verlauf and verlauf[auftrag].get("status", {}).get("completed") is not None:
                break
            time.sleep(abfrage_s)
    finally:
        messer.stop = True
    eintrag = verlauf[auftrag]
    ok = eintrag.get("status", {}).get("status_str") == "success"
    return eintrag, round(time.time() - start, 1), {"vram_max_mb": messer.vram_max, "ram_frei_min_mb": messer.ram_frei_min, "ok": ok}


def speicher_freigeben(server, alles=False):
    """Gibt Cache frei; mit alles=True werden auch die Modelle entladen."""
    anfrage = urllib.request.Request(server + "/free", data=json.dumps({"unload_models": alles, "free_memory": True}).encode(),
                                     headers={"Content-Type": "application/json"})
    urllib.request.urlopen(anfrage, timeout=60).read()
    time.sleep(3)


def dateiverweise(wert):
    if isinstance(wert, dict):
        if "filename" in wert:
            yield wert
        for teil in wert.values():
            yield from dateiverweise(teil)
    elif isinstance(wert, list):
        for teil in wert:
            yield from dateiverweise(teil)


def herunterladen(server, ref, ziel):
    abfrage = urllib.parse.urlencode({"filename": ref["filename"], "type": ref.get("type", "output"),
                                      "subfolder": ref.get("subfolder", "")})
    with urllib.request.urlopen(server + "/view?" + abfrage, timeout=600) as antwort:
        Path(ziel).parent.mkdir(parents=True, exist_ok=True)
        Path(ziel).write_bytes(antwort.read())


def messung_schreiben(geraet, schritt, name, sekunden, werte, extra=None):
    zeile = {"geraet": geraet, "schritt": schritt, "name": name, "sekunden": sekunden, **werte,
             "zeit": time.strftime("%Y-%m-%d %H:%M:%S"), **(extra or {})}
    ziel = WURZEL / "messung" / f"{geraet}.jsonl"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with ziel.open("a", encoding="utf-8") as f:
        f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
    return zeile


def figurenblock(figuren, ids):
    """Wörtlich wiederholter Figurentext: derselbe Wortlaut in jedem Prompt hält die Person fest."""
    teile = []
    for i in ids:
        f = figuren["figuren"][i]
        teile.append(f"{f['name']}: {f['gesicht']}; {f['koerper']}; wearing {f['kleidung']}. Always visible: {f['merkmale']}.")
    return " ".join(teile)


AUSSEN = ("street", "deck", "square", "steps", "skyline", "city", "tower in the city", "sky over")


def ortszeile(figuren, shot):
    """Der Stadtname gehört nur in Außenszenen; in Innenräumen überstimmt er sonst die Szene."""
    aussen = any(w in shot["bild"] for w in AUSSEN)
    return "Setting: " + figuren["ort"] + "." if aussen else ""


def standbild_prompt(figuren, shot):
    block = figurenblock(figuren, shot["figuren"])
    return " ".join(x for x in (block, shot["bild"] + ".", ortszeile(figuren, shot), figuren["stil"] + ".") if x)


def clip_prompt(figuren, shot):
    """Lange technische Fassung: kurze Prompts lassen LTX auf dem EVO driften."""
    halte = ""
    if shot["figuren"]:
        halte += (" Calm slow movement only: the gaze stays steady, the eyes do not roll or dart, no fast head turns, "
                  "hands and feet barely move, no walking or running, the camera moves slowly.")
        halte += (" Every person keeps exactly the same face, hairstyle, skin tone and outfit as in the first frame "
                 "throughout the whole clip; no morphing, no face changes, no extra people appear.")
    return (f"{shot['bild']}. {shot['bewegung']}. {ortszeile(figuren, shot)} {figuren['stil']}. "
            f"Smooth natural motion, consistent lighting, stable composition, sharp focus, 24 fps.{halte}")


def clip_pruefen(video, startbild, stuetzpunkte=(0, 60, 119)):
    """Inhaltsprüfung: kaputte Clips (Rauschen, graue Flächen) und starkes Abdriften vom Startbild.

    Liefert den mittleren RGB-Abstand (0-255) von drei Bildern zum Startbild bei 64x36 Pixeln.
    """
    import subprocess
    import tempfile
    import numpy as np
    from PIL import Image

    def klein(pfad):
        return np.asarray(Image.open(pfad).convert("RGB").resize((64, 36), Image.BILINEAR), dtype=float)

    start = klein(startbild)
    abstaende = []
    with tempfile.TemporaryDirectory() as tmp:
        auswahl = "+".join(f"eq(n,{n})" for n in stuetzpunkte)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf", f"select='{auswahl}'",
                        "-fps_mode", "passthrough", f"{tmp}/f_%d.png"], check=True)
        for f in sorted(Path(tmp).glob("f_*.png")):
            abstaende.append(float(np.abs(klein(f) - start).mean()))
    return {"abstand_start": abstaende[0] if abstaende else None, "abstand_max": max(abstaende) if abstaende else None,
            "bilder": len(abstaende)}
