# -*- coding: utf-8 -*-
"""Extrait la palette dominante d'une image de référence (template Canva).

Usage :
    python presentation\\extract_palette.py presentation\\ref.png

Placez d'abord une capture d'écran de la template dans le chemin indiqué.
Nécessite Pillow (déjà utilisé par python-pptx).
"""

import sys
from collections import Counter
from pathlib import Path

from PIL import Image


def hexc(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(__file__).resolve().parent / "ref.png"
    if not path.exists():
        print(f"[!] Image introuvable : {path}")
        print("    Enregistrez une capture d'écran de la template à cet endroit.")
        return

    im = Image.open(path).convert("RGB")
    im.thumbnail((400, 400))
    pix = list(im.getdata())

    quant = Counter((r // 16 * 16, g // 16 * 16, b // 16 * 16) for r, g, b in pix)
    total = len(pix)

    print(f"Image : {path}  ({Image.open(path).size[0]}x{Image.open(path).size[1]})")
    print("Palette dominante (couleur · part) :")
    for rgb, n in quant.most_common(12):
        print(f"  {hexc(rgb)}  {n * 100 / total:5.1f} %")

    print("\nFond probable :", hexc(quant.most_common(1)[0][0]))
    print("Candidats accent :")
    for rgb, n in quant.most_common(30):
        r, g, b = rgb
        sat = max(rgb) - min(rgb)
        if sat > 90 and n * 100 / total > 0.4:
            print(f"  {hexc(rgb)}  {n * 100 / total:5.1f} %")


if __name__ == "__main__":
    main()
