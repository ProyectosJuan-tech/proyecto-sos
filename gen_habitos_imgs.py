#!/usr/bin/env python3
"""Genera las 8 imágenes N1-N8 del largo "No te falta fuerza de voluntad".

Sistema objeto-primero 2026-08-15: cada imagen la cuentan los objetos (zapatilla,
libro, calendario, taza, puerta), no un rostro. Solo N7/N8 tienen persona, de
espaldas, por lo que NO se necesita mantener consistencia de cara: se usa seed
fijo para coherencia de estilo. Proveedor Pollinations (gratis, Apache-2.0).

Salida: videos/youtube/habitos-sistema/imgs/N1.jpg ... N8.jpg
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flux_img
import habitos_scenes as hs

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
IMGS_DIR = os.path.join(PROJECT_ROOT, "videos", "youtube", "habitos-sistema", "imgs")
SEED = 811  # fijo en TODAS las escenas: coherencia de estilo
ONLY = sys.argv[1:] or None  # regenerar solo estas (ej: gen_habitos_imgs.py N1 N6)

os.makedirs(IMGS_DIR, exist_ok=True)

for name, prompt in hs.E_PROMPTS.items():
    if ONLY and name not in ONLY:
        continue
    out = os.path.join(IMGS_DIR, f"{name}.jpg")
    if not ONLY and os.path.exists(out) and os.path.getsize(out) > 5000:
        print(f"{name} ya existe, skip", flush=True)
        continue
    print(f"[{name}] seed={SEED} ...", flush=True)
    try:
        flux_img.generate(prompt, out, aspect="16:9", seed=SEED,
                          provider="pollinations")
        print(f"  OK {name}", flush=True)
    except Exception as e:
        print(f"  FALLO {name}: {e}", flush=True)
    time.sleep(4)

print("LISTO", flush=True)
