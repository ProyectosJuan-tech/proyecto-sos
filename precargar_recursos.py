#!/usr/bin/env python3
# precargar_recursos.py
# Descarga por adelantado una BASE de recursos visuales de ORACIÓN y los guarda
# en RECURSOS_VISUALES_PARA_VIDEOS_Y_SHORTS (carpeta central / caché por tema).
#
# Fuentes:
#   - videos   : video horizontal 16:9 de Pexels (persona orando / ambiente)
#   - foto     : foto horizontal de Pexels (persona orando / ambiente)
#   - IA       : imagen generada IA de hombre/mujer orando (seed fija = personaje)
#
# La base llena EXACTAMENTE los temas (q) de oracion_dormir_scenes.py por tipo,
# más una lista general de temas de oración (hombre/mujer) reusable en futuros
# videos. Los recursos quedan como `<slug>.<ext>` para que buscar_recurso() los
# encuentre y el pipeline NO vuelva a golpear a proveedores.
#
# Uso:  python3 precargar_recursos.py            (descarga toda la base)
#       python3 precargar_recursos.py --dry      (muestra qué se crearía sin bajar)
#       python3 precargar_recursos.py --video    (solo videos Pexels)
#       python3 precargar_recursos.py --photo    (solo fotos Pexels)
#       python3 precargar_recursos.py --ai       (solo imágenes generadas IA)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hacer_video_caverna as m
import hacer_videos_youtube as hy
import pexels_stock

REC = m.RECURSOS_DIR
SEED_HOMBRE = 411   # personaje recurrente (El Sabio)
SEED_MUJER = 512    # variante femenina

# ---------------------------------------------------------------------------
# Temas del guion de oracion-dormir-gracias (por tipo) — llenan la base del video
# ---------------------------------------------------------------------------

def _temas_del_guion():
    import oracion_dormir_scenes as ods
    items = []
    for s in ods.scenes():
        q = s.get("q") or s.get("ai")
        if s.get("stock"):
            items.append({"tema": q, "tipo": "video", "kw": q,
                          "ai": s.get("ai", ""), "seed": SEED_HOMBRE})
        elif s.get("stock_photo"):
            items.append({"tema": q, "tipo": "foto", "kw": q,
                          "ai": s.get("ai", ""), "seed": SEED_MUJER})
        else:
            items.append({"tema": q, "tipo": "ai", "kw": q,
                          "ai": s.get("ai", ""),
                          "seed": SEED_HOMBRE if "A man" in s.get("ai", "") else SEED_MUJER})
    return items


# ---------------------------------------------------------------------------
# Temas generales de oración para la biblioteca reusable (hombre/mujer)
# ---------------------------------------------------------------------------

def _temas_generales():
    return [
        {"tema": "hombre orando de rodillas", "tipo": "video",
         "kw": "man kneeling praying", "ai": "", "seed": SEED_HOMBRE},
        {"tema": "hombre orando de rodillas", "tipo": "foto",
         "kw": "man kneeling praying", "ai": "", "seed": SEED_HOMBRE},
        {"tema": "hombre manos juntas oración", "tipo": "video",
         "kw": "man hands clasped praying", "ai": "", "seed": SEED_HOMBRE},
        {"tema": "hombre manos juntas oración", "tipo": "foto",
         "kw": "man hands clasped praying", "ai": "", "seed": SEED_HOMBRE},
        {"tema": "mujer orando de rodillas", "tipo": "video",
         "kw": "woman kneeling praying", "ai": "", "seed": SEED_MUJER},
        {"tema": "mujer orando de rodillas", "tipo": "foto",
         "kw": "woman kneeling praying", "ai": "", "seed": SEED_MUJER},
        {"tema": "mujer manos juntas oración", "tipo": "video",
         "kw": "woman hands clasped praying", "ai": "", "seed": SEED_MUJER},
        {"tema": "mujer manos juntas oración", "tipo": "foto",
         "kw": "woman hands clasped praying", "ai": "", "seed": SEED_MUJER},
        {"tema": "persona orando junto a cama noche", "tipo": "video",
         "kw": "person praying beside bed night", "ai": "", "seed": SEED_MUJER},
        {"tema": "persona orando junto a cama noche", "tipo": "foto",
         "kw": "person praying beside bed night", "ai": "", "seed": SEED_MUJER},
        {"tema": "manos abiertas hacia arriba oración", "tipo": "video",
         "kw": "open hands raised praying light", "ai": "", "seed": SEED_MUJER},
        {"tema": "manos abiertas hacia arriba oración", "tipo": "foto",
         "kw": "open hands raised praying", "ai": "", "seed": SEED_MUJER},
    ]


def _tema_ai_hombre(seed=SEED_HOMBRE):
    return ("A man in his fifties kneeling beside his bed at night with hands "
            "together in prayer, soft warm lamplight, quiet peaceful bedroom, "
            "intimate observational photography, photorealistic, high detail")


def _tema_ai_mujer(seed=SEED_MUJER):
    return ("A woman in her fifties kneeling beside her bed at night with hands "
            "together in prayer, soft warm lamplight, quiet peaceful bedroom, "
            "intimate observational photography, photorealistic, high detail")


# ---------------------------------------------------------------------------

def _existente(tema, ext):
    """¿Ya hay un recurso guardado para este tema+ext? (usa el slug igual que
    buscar_recurso, que es a lo que el pipeline consulta)."""
    return m.buscar_recurso(ext, tema)


def precargar(items, solo=None, dry=False):
    os.makedirs(REC, exist_ok=True)
    for it in items:
        tipo = it["tipo"]
        if solo and tipo != solo:
            continue
        tema = it["tema"]
        kw = it["kw"] or tema
        try:
            if tipo in ("video", "foto"):
                ext = "mp4" if tipo == "video" else "jpg"
                if _existente(tema, ext):
                    print(f"  · ya existe [{tipo}] {tema} -> skip", flush=True)
                    continue
                tmp = os.path.join(REC, f"__tmp_{tipo}_{abs(hash(tema))}.{ext}")
                if tipo == "video":
                    ok = pexels_stock.fetch_for_scene_landscape(kw, tmp, min_duration=3.0)
                else:
                    ok = pexels_stock.fetch_photo_for_scene(kw, tmp, orientation="landscape")
                if ok and os.path.exists(tmp) and os.path.getsize(tmp) > 5000:
                    dest = m.guardar_recurso(tmp, tema, ext)
                    os.remove(tmp)
                    print(f"  + [{tipo}] {tema} -> {os.path.basename(dest) if dest else '?'}", flush=True)
                else:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                    print(f"  · [{tipo}] {tema} SIN resultado (base vacía para este tema)", flush=True)
                # pausa leve entre descargas (rate-limit considerado por el caché interno)
            else:
                # IA generada
                if _existente(tema, "jpg"):
                    print(f"  · ya existe [IA] {tema} -> skip", flush=True)
                    continue
                prompt = it.get("ai") or (_tema_ai_hombre() if "hombre" in tema else _tema_ai_mujer())
                seed = it.get("seed", SEED_HOMBRE)
                tmp = os.path.join(REC, f"__tmp_ai_{abs(hash(tema))}.jpg")
                hy.download_ai_image(prompt, tmp, seed=seed, style=hy.LIGHT_STYLE)
                if os.path.exists(tmp) and os.path.getsize(tmp) > 5000:
                    dest = m.guardar_recurso(tmp, tema, "jpg")
                    os.remove(tmp)
                    print(f"  + [IA] {tema} -> {os.path.basename(dest) if dest else '?'}", flush=True)
                else:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                    print(f"  · [IA] {tema} FALLÓ la generación", flush=True)
        except Exception as e:
            print(f"  ! [{tipo}] {tema} ERROR: {e}", flush=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    dry = "--dry" in flags
    solo = None
    for f in flags:
        if f in ("--video", "--photo", "--ai"):
            solo = {"--video": "video", "--photo": "foto", "--ai": "ai"}[f]

    items = _temas_del_guion()
    items += _temas_generales()
    tags = {i["tipo"] for i in items}
    print(f"Base de recursos de oración: {len(items)} ítems "
          f"({', '.join(f'{k}={sum(1 for i in items if i["tipo"]==k)}' for k in tags)})", flush=True)
    print(f"Destino: {REC}", flush=True)
    if dry:
        print("(modo seco — no se descarga nada)", flush=True)
        for it in items:
            print(f"  - [{it['tipo']:5s}] {it['tema']}", flush=True)
        return
    precargar(items, solo=solo)


if __name__ == "__main__":
    main()
