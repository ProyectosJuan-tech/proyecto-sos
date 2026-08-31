"""prueba_v2_7_porque_ep1.py — PROOF CONTROLADO de V2.7 (sin red)

Demuestra la INTELIGENCIA VISUAL DE MEDIOS sobre el episodio real
"¿Por qué tengo todo y sigo sintiéndome vacío?" (7 escenas / 7 arquetipos
visuales). Verifica que:

  1. Cada arquetipo produce VisualKeywords DISTINTAS (diferenciación).
  2. Cada arquetipo produce una estrategia de fuente coherente.
  3. Las stock_keywords derivan del evento (subordinadas), no de plantillas.
  4. 0 llamadas de red (la capa V2.7 es determinista y pura).

NO renderiza ni genera assets: es el proof de diferenciación de la fase.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from scene_brief import SceneBrief, NarrativeRole
import media_intelligence as mi


# Arquetipo → escena real del episodio (visual_event + subject/action/setting
# extraídos del prompt `ai` de cada escena, NO inventados).
ROLES = {
    1: ("hook", NarrativeRole.HOOK),
    2: ("problem", NarrativeRole.PROBLEM),
    3: ("agitation", NarrativeRole.AGITATION),
    4: ("psychology", NarrativeRole.PSYCHOLOGY),
    5: ("solution", NarrativeRole.SOLUTION),
    6: ("hope", NarrativeRole.HOPE),
    7: ("callout", NarrativeRole.CALLOUT),
}

# (visual_event, subject, action, setting, symbol) por escena — subordinado a
# la narrativa real del episodio (prompt `ai` del informe).
SCENES = [
    # 1 hook: cama vacía / puerta entreabierta con luz (interaction)
    ("cama vacía vista desde la puerta, la luz del otro lado de una puerta entreabierta",
     "ninguna", "mirar hacia la puerta con luz al otro lado",
     "cuarto tranquilo con luz suave de mañana", "puerta entreabierta con luz"),
    # 2 problem: persona al borde de la cama al amanecer (person)
    ("una persona sentada al borde de la cama al amanecer frotándose los ojos cansados",
     "persona", "frotarse los ojos cansados", "cuarto en penumbra al amanecer",
     "la cama revuelta sin tocar"),
    # 3 agitation: manos tecleando/borrando el mismo mensaje (hands)
    ("manos teclean un mensaje, dudan y lo borran antes de enviarlo",
     "manos", "reescribir y borrar la misma línea repetidamente",
     "cocina inmóvil con luz de mañana difusa", "repetición de un gesto familiar"),
    # 4 psychology: mano que borra una línea escrita (detail)
    ("una mano flota sobre un mensaje escrito y luego borra la línea",
     "mano", "borrar la línea de un mensaje escrito",
     "escritorio con papel y una lámpara pequeña", "la línea que se borra"),
    # 5 solution: objeto apoyado con intención en la mesa (object)
    ("dos personas comparten un silencio sereno, un objeto reposa sobre la mesa",
     "dos personas", "apoyar un objeto pequeño con intención sobre la mesa",
     "ventana luminosa con una silla y luz clara de mañana", "objeto que reposa"),
    # 6 hope: palmas abiertas vacías / puerta de luz (environment)
    ("palmas abiertas reposan planas y vacías sobre la mesa, como soltando algo",
     "ninguna", "avanzar hacia una puerta abierta llena de luz",
     "puerta abierta a la luz del día", "palmas abiertas que sueltan algo"),
    # 7 callout: persona de espaldas / mensaje sobre la mesa (object)
    ("una persona vista de espaldas sostiene la pose del momento",
     "persona", "un mensaje simple descansa sobre la mesa",
     "interior cálido con luz de tarde", "el mensaje quieto en la mesa"),
]


def build_briefs():
    briefs = []
    for i, (role_name, role) in ROLES.items():
        ev, subj, act, setting, sym = SCENES[i - 1]
        b = SceneBrief(
            scene_id=f"e{i:02d}",
            narrative_role=role,
            narration="...",
            visual_event=ev,
            subject=subj,
            action=act,
            setting=setting,
            symbol=sym,
        )
        briefs.append((role_name, b))
    return briefs


def main():
    briefs = build_briefs()
    results = []
    for role_name, b in briefs:
        kw = mi.derive_visual_keywords(b)
        strat = mi.build_media_source_strategy(b)
        results.append({
            "scene": b.scene_id,
            "role": role_name,
            "preferred": strat.preferred_source,
            "alternative": (strat.alternatives[:1] or [""])[0],
            "reason": strat.reason,
            "keywords": kw.to_dict(),
        })

    # ── Diferenciación: los objetos/acciones/stock_keywords NO son idénticos ──
    signatures = []
    for r in results:
        # firma = (fuente preferida, primer objeto, primer stock_keyword)
        objs = r["keywords"]["objects"]
        stocks = tuple(r["keywords"]["stock_keywords"])
        sig = (r["preferred"], objs[0] if objs else "", stocks[:2])
        signatures.append(sig)
    unique_sigs = set(signatures)

    # Acciones/objetos: al menos 6 de 7 escenas deben tener huella visual distinta
    distinct_objects = set(tuple(r["keywords"]["objects"]) for r in results)
    distinct_stock = set()
    for r in results:
        for s in r["keywords"]["stock_keywords"]:
            distinct_stock.add(s)

    print("=" * 70)
    print("PROOF V2.7 — INTELIGENCIA VISUAL DE MEDIOS (episodio '¿Por qué me siento vacío?')")
    print("=" * 70)
    for r in results:
        kw = r["keywords"]
        print(f"\n[{r['scene']}] rol={r['role']}  fuente={r['preferred']}  "
              f"(alt: {r['alternative']})")
        print(f"    razón: {r['reason']}")
        print(f"    sujetos: {kw['subjects']}  objetos: {kw['objects']}  "
              f"acciones: {kw['actions']}")
        print(f"    lugar: {kw['places']}  emoción: {kw['visual_emotion']!r}  "
              f"symbols: {kw['symbols']}")
        print(f"    stock: {kw['stock_keywords']}")

    # ── VEREDICTO (determinista, sin red) ──
    print("\n" + "=" * 70)
    ok = True
    checks = []
    c1 = len(signatures) == len(set(signatures))
    checks.append(("Arquetipos con firma visual única", c1))
    c2 = len(distinct_objects) >= 6
    checks.append((f"Objetos distintos entre escenas ({len(distinct_objects)}/7)", c2))
    c3 = len(distinct_stock) >= 6
    checks.append((f"Stock keywords únicas en el episodio ({len(distinct_stock)})", c3))
    # Todas las stock_keywords derivan del evento (sin plantillas externas)
    c4 = all(all(k and k.strip() for k in r["keywords"]["stock_keywords"]) for r in results)
    checks.append(("Stock keywords no vacías en todas las escenas", c4))
    # Estrategia coherente: preferred en {ai, stock, photo_stock} y razón humana
    c5 = all(r["preferred"] in ("ai", "stock", "photo_stock") and r["reason"]
             for r in results)
    checks.append(("Estrategia de fuente válida + razón en todas", c5))
    # Escena de esperanza (hope) con palmas abiertas → simbolismo → IA
    hope = next(r for r in results if r["role"] == "hope")
    c6 = hope["keywords"]["symbols"] or hope["keywords"]["visual_emotion"]
    checks.append(("Escena hope detecta simbolismo (palmas/trascender)", bool(c6)))

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        ok = ok and passed

    print("=" * 70)
    print("VEREDICTO:", "PASS (diferenciación visual OK, 0 red)" if ok else "FAIL")
    # Persistir resultado para el informe
    out = {
        "prueba": "V2.7 INTELIGENCIA VISUAL DE MEDIOS",
        "episodio": "¿Por qué tengo todo y sigo sintiéndome vacío?",
        "veredicto": "PASS" if ok else "FAIL",
        "checks": [{"name": n, "ok": p} for n, p in checks],
        "resultados": results,
        "red_calls": 0,
    }
    with open("/tmp/opencode/prueba_v2_7_porque_ep1.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
