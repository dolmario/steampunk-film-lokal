"""Legt alle PNG eines Ordners als beschrifteten Kontaktbogen nebeneinander.

Aufruf: python kontaktbogen.py <ordner> <ausgabe.png> [--spalten 4] [--breite 360]
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def main():
    p = argparse.ArgumentParser()
    p.add_argument("ordner")
    p.add_argument("ausgabe")
    p.add_argument("--spalten", type=int, default=4)
    p.add_argument("--breite", type=int, default=360)
    p.add_argument("--muster", default="*.png")
    a = p.parse_args()
    dateien = sorted(Path(a.ordner).glob(a.muster))
    kacheln = []
    for d in dateien:
        b = Image.open(d).convert("RGB")
        h = int(b.height * a.breite / b.width)
        kacheln.append((d.stem, b.resize((a.breite, h), Image.LANCZOS)))
    zeilenhoehe = max(k.height for _, k in kacheln) + 22
    zeilen = (len(kacheln) + a.spalten - 1) // a.spalten
    bogen = Image.new("RGB", (a.spalten * a.breite, zeilen * zeilenhoehe), (24, 22, 20))
    zeichner = ImageDraw.Draw(bogen)
    for i, (name, k) in enumerate(kacheln):
        x, y = (i % a.spalten) * a.breite, (i // a.spalten) * zeilenhoehe
        bogen.paste(k, (x, y + 20))
        zeichner.text((x + 4, y + 4), name, fill=(230, 220, 200))
    bogen.save(a.ausgabe)
    print(len(kacheln), "Bilder ->", a.ausgabe)


if __name__ == "__main__":
    main()
