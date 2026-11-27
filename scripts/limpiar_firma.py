#!/usr/bin/env python3
"""Recorta una firma fotografiada (lapicera azul o negra sobre papel) y le saca el fondo.

Uso: python3 -I limpiar_firma.py foto.jpg firma_cliente.png [azul|negra]
"""
import sys
import numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
tinta = sys.argv[3] if len(sys.argv) > 3 else "azul"
a = np.asarray(Image.open(src).convert("RGB")).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
if tinta == "azul":
    fuerza = np.clip(((b - r) - 20) / 60, 0, 1)
    color = (40, 40, 150)
else:
    gris = (r + g + b) / 3
    fondo = np.percentile(gris, 90)
    fuerza = np.clip((fondo - gris - 25) / 80, 0, 1)
    color = (20, 20, 20)
ys, xs = np.where(fuerza > 0.3)
if len(ys) == 0:
    sys.exit("No detecté tinta en la imagen")
y0, y1 = max(ys.min() - 10, 0), min(ys.max() + 10, a.shape[0])
x0, x1 = max(xs.min() - 10, 0), min(xs.max() + 10, a.shape[1])
f = fuerza[y0:y1, x0:x1]
out = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
out[..., 0], out[..., 1], out[..., 2] = color
out[..., 3] = np.clip(f * 255 * 1.8, 0, 255).astype(np.uint8)
im = Image.fromarray(out, "RGBA")
if im.width > 700:
    im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
im.save(dst)
print(dst, im.size)
