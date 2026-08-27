#!/usr/bin/env python3
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flux_img

IDXS = [1, 3, 4, 5, 7, 8, 10, 11, 13, 15, 17]

import hacer_videos_nuevos as n

v = next(x for x in n.VIDEOS if x["name"] == "vas-ganando")
imgs_dir = os.path.join(n.ROOT, "vas-ganando", "imgs")
os.makedirs(imgs_dir, exist_ok=True)

for i, idx in enumerate(IDXS):
    sc = v["scenes"][idx - 1]
    out = os.path.join(imgs_dir, f"e{idx:02d}.jpg")
    if os.path.exists(out) and os.path.getsize(out) > 5000:
        print(f"e{idx:02d} ya existe, skip", flush=True)
        continue
    prompt = sc["ai"] + (sc.get("img_style", "") or "")
    seed = sc.get("img_seed", idx * 101)
    print(f"[{i+1}/{len(IDXS)}] e{idx:02d} seed={seed} ...", flush=True)
    try:
        flux_img.generate(prompt, out, seed=seed, provider="pollinations")
        print(f"  OK e{idx:02d}", flush=True)
    except Exception as e:
        print(f"  FALLO e{idx:02d}: {e}", flush=True)
    time.sleep(4)
print("LISTO", flush=True)
