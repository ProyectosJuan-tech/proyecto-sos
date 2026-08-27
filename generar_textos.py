#!/usr/bin/env python3
"""Generador de frases para shorts del canal con Gemini (gratis).

Sigue el patrón de cascada/retries de flux_img.py pero para TEXTO. Usa la key
de Gemini (GEMINI_API_KEY env o gemini_key.txt) y el modelo gemini-3.5-flash
(muy bueno en español, free tier ~1500 req/día).

Codifica las reglas del canal (posturas + Meta/YouTube + banco de frases) en el
prompt de sistema y devuelve candidatos en JSON para REVISIÓN MANUAL. NUNCA
escribe directo en hacer_shorts.py: primero el usuario aprueba.

Uso:
    python3 generar_textos.py [--cantidad 10] [--tema "limites|silencio|..."]
                              [--modelo gemini-3.5-flash]

Salida:
    - impresión legible en consola
    - textos_generados/<fecha>.json  (candidatos completos)
"""
import argparse
import json
import os
import re
import sys
import time

import httpx

ROOT = os.path.dirname(os.path.abspath(__file__))
_GEMINI_KEY_FILE = os.path.join(ROOT, "gemini_key.txt")
_DEFAULT_MODEL = "gemini-3.5-flash"
_OUT_DIR = os.path.join(ROOT, "textos_generados")

PROHIBIDAS = [
    "ley de atracción", "manifest", "vibra", "vibrar mal", "riqueza",
    "millonario", "lotería", "fórmula mágica", "secreto", "mente sobre materia",
    "pensar bonito", "hazte rico",
]


def _read_key_file(env_name, path):
    v = os.environ.get(env_name, "")
    if v:
        return v.strip()
    if os.path.exists(path):
        return open(path).read().strip()
    return ""


def _gemini_key():
    return _read_key_file("GEMINI_API_KEY", _GEMINI_KEY_FILE)


def _leer_banco_frases():
    """Extrae las frases cortas ya usadas como ejemplos negativos (few-shot)."""
    path = os.path.join(ROOT, "cerebro", "wiki", "contenido", "frases-usadas.md")
    frases = []
    try:
        for line in open(path):
            line = line.strip()
            m = re.match(r'\s*\|\s*"([^"]+)"\s*\|', line)
            if m and len(m.group(1)) > 25:
                frases.append(m.group(1))
    except FileNotFoundError:
        pass
    return frases


def _leer_posturas():
    """Lee posturas.md para inyectar las reglas NO NEGOCIABLES al prompt."""
    path = os.path.join(ROOT, "cerebro", "wiki", "contenido", "posturas.md")
    try:
        return open(path).read().strip()
    except FileNotFoundError:
        return ""


def _system_prompt(tema, frases_usadas, posturas, formato="short"):
    ejemplos = "\n".join(f"- \"{f}\"" for f in frases_usadas[-6:])
    if formato == "largo":
        return f"""Sos el guionista del canal "El Sabio de la Caverna" (bienestar con base filosófica real, anti-gurú). Escribís videos LARGOS horizontales (8-12 min leídos) para audiencia de mujeres 35-64 que buscan calma y dejar de sentirse culpables.

Reglas de estilo del canal (MUY IMPORTANTES):
1. NARRATIVA con estructura de bloques: intro (gancho ≤15s con promesa concreta y "hoy te muestro X") + desarrollo en bloques de 1-2 oraciones cada uno + re-engagement beat a la mitad ("pero acá está lo más serio...") + bonus "una cosa más" al final + CTA de cierre.
2. 55-65% frases cortas (<15 palabras). Transiciones ADVERSATIVAS ("pero", "el problema es", "sin embargo") NO aditivas ("también", "además").
3. Escalada de apuestas en el valle de retención (25-35% del video): inyectar especificidad ("te muestro el número exacto").
4. FLUIDEZ conversacional ("guiri guiri"), SIEMPRE tuteo ("tú", "eres", "tienes") — NUNCA voseo ("sos", "tenés", "vos"). Sin culpa, sin diagnóstico, sin moralizar. Sin palabras que el TTS pronuncie mal.
5. Regla de fe: NUNCA decir nada contrario a la fe católica. Si roza lo espiritual, alinear sin proselitismo.
6. NO repetir los ángulos/frases ya usados del canal (lista abajo).

Posturas del canal (NO contradecir):
{posturas}

Frases YA USADAS del canal (NO repetir el ángulo, reformular con otra imagen/texto):
{ejemplos}

Tema del video: {tema}.

Tarea: escribí un guion completo para este tema. Cada escena/bloque tiene: "text" (1-2 oraciones leídas por el TTS), "ai" (prompt de imagen IA en inglés, cinematográfico, fotorealista, cálido "bright airy soft window light" salvo caverna que es oscuro), "q" (fallback Wikimedia Commons con keywords cortas tipo "morning coffee").

Devolvé SOLO JSON válido, sin texto alrededor, con esta forma exacta (N bloquea: intro + 6-8 bloques de desarrollo + bonus + CTA):
[{{"text": "oración 1", "ai": "prompt imagen en inglés", "q": "keywords cortas"}}]"""
    return f"""Sos el guionista del canal de videos "El Sabio de la Caverna" (bienestar con base filosófica real, anti-gurú). Escribís cortos verticales (10-13 segundos leídos) para una audiencia de mujeres 35-64 que buscan calma, bienestar y dejar de sentirse culpables.
4. PAYOFF antes de la mitad: la idea clave se dice temprano; el resto refuerza.
5. FLUIDEZ conversacional ("guiri guiri"): frases naturales, no telegráficas. Ejemplos de tono: "mientras esperás, nada cambia", "Aristóteles decía", "no es tu culpa". NADA de frases subordinadas largas ni acumulación de comas.
6. SIN moralizar, SIN culpar. El problema no es la persona: es que no tiene método.
7. SIEMPRE tuteo ("tú", "eres", "tienes", "vas a") — NUNCA voseo ("sos", "tenés", "vos"). Sin siglas, sin abreviaturas raras, sin palabras que el TTS pronuncie mal. Sin signos que confundan al sintetizador.
8. Regla de fe: NUNCA decir nada contrario a la fe católica. Si el tema roza lo espiritual (perdón, propósito, muerte), alinear sin hacer proselitismo ni moralizar.
9. NO repetir los ángulos/frases ya usados del canal (lista abajo).

Posturas del canal (NO contradecir):
{posturas}

Frases YA USADAS del canal (NO repetir el ángulo, reformular con otra imagen/texto):
{ejemplos}

Tarea: escribí EXACTAMENTE {{n}} frases nuevas {('sobre el tema: ' + tema) if tema else 'sobre cualquier tema de bienestar/calma/límites/autoestima no usado todavía'}. Devolvé TODAS las {{n}} frases, cada una distinta, sin repetir ideas entre sí.

Devolvé SOLO JSON válido, sin texto alrededor, con esta forma exacta:
[{{"texto": "La frase completa (máx 45 palabras, 2 oraciones, con CTA Sígueme al final)", "prompt": "prompt de IMAGEN IA en inglés, descriptivo, cinematográfico, para mujer 50+, cálido/brillante salvo temas de caverna (oscuro), estilo: bright airy, soft window light, photorealistic", "keyword": "palabra/s clave en español", "duracion": "estimado en segundos leídos, 10 a 13"}}]"""


def _extraer_json(texto):
    m = re.search(r"\[[\s\S]*\]", texto)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _sanitizar(frase, frases_usadas):
    """Chequea colisiones con el banco y conceptos prohibidos. Devuelve warnings."""
    warns = []
    bajo = frase.lower()
    for kw in PROHIBIDAS:
        if kw in bajo:
            warns.append(f"concepto prohibido: '{kw}'")
    for usada in frases_usadas:
        toks_u = set(re.findall(r"[a-záéíóúñ]{4,}", usada.lower()))
        toks_f = set(re.findall(r"[a-záéíóúñ]{4,}", bajo))
        comunes = toks_u & toks_f
        if len(comunes) >= max(4, len(toks_f) * 0.6):
            warns.append(f"ángulo muy parecido a: '{usada[:60]}...'")
            break
    return warns


def _llamar_gemini(prompt, modelo):
    key = _gemini_key()
    if not key:
        raise SystemExit("No hay key de Gemini: crear gemini_key.txt o exportar GEMINI_API_KEY")
    endpoint = ("https://generativelanguage.googleapis.com/v1beta/models/"
                + modelo + ":generateContent?key=" + key)
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "responseMimeType": "application/json",
        },
    }).encode("utf-8")
    last = None
    for attempt in range(4):
        try:
            with httpx.Client(timeout=180.0) as client:
                resp = client.post(endpoint, data=body,
                                   headers={"Content-Type": "application/json"})
            if resp.status_code == 429:
                last = f"429 (rate limit), intento {attempt + 1}/4"
                time.sleep(15 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            parts = (data.get("candidates", [{}])[0]
                         .get("content", {})
                         .get("parts", []))
            texto = "".join(p.get("text", "") for p in parts).strip()
            if not texto:
                last = "respuesta vacía"
                continue
            return texto
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(5 * (attempt + 1))
        except httpx.HTTPStatusError as e:
            last = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            if attempt < 3:
                time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Gemini falló: {last}")


def _generar_frases(tema, cantidad, frases_usadas, posturas, modelo):
    """Genera `cantidad` frases de short para un tema. Devuelve lista de dicts."""
    todos = []
    vistos = set()
    lote = 3
    for i in range(0, cantidad, lote):
        if len(todos) >= cantidad:
            break
        n = min(lote, cantidad - len(todos))
        sys_prompt = _system_prompt(tema, frases_usadas, posturas, formato="short")
        prompt = sys_prompt.replace("{{n}}", str(n))
        print(f"[gemini] generando frases {len(todos) + 1}-{min(len(todos) + n, cantidad)}...", flush=True)
        raw = _llamar_gemini(prompt, modelo)
        items = _extraer_json(raw) or []
        for it in items:
            it.setdefault("duracion", "10-13s")
            t = it.get("texto", "").strip()
            if not t or t in vistos:
                continue
            vistos.add(t)
            warns = _sanitizar(t, frases_usadas)
            it["texto"] = t
            it["warnings"] = warns
            todos.append(it)
        if len(todos) < min(i + n, cantidad):
            time.sleep(2)
    return todos[:cantidad]


def _leer_banco(path):
    """Lee un banco de temas (salida de generar_banco.py)."""
    with open(path) as f:
        data = json.load(f)
    return data.get("temas", [])


def _generar_largo(tema_info, frases_usadas, posturas, modelo):
    """Genera un guion de largo (lista de escenas text/ai/q) para un tema."""
    tema = (f"{tema_info.get('titulo', '')}. Ángulo: {tema_info.get('angulo', '')} "
            f"[{tema_info.get('tema_prompt', '')}]")
    sys_prompt = _system_prompt(tema, frases_usadas, posturas, formato="largo")
    print(f"[gemini] generando LARGO: {tema_info.get('titulo')}", flush=True)
    raw = _llamar_gemini(sys_prompt, modelo)
    items = _extraer_json(raw) or []
    escenas = []
    for it in items:
        t = (it.get("text", "") or "").strip()
        if not t:
            continue
        escenas.append({
            "text": t,
            "ai": it.get("ai", ""),
            "q": it.get("q", ""),
        })
    if len(escenas) < 8:
        print(f"  ⚠ solo {len(escenas)} escenas (un largo necesita ~10+ para 8 min)", flush=True)
    return escenas


def generar_desde_banco(banco_path, elegir=None, modelo=_DEFAULT_MODEL, solo_json=False):
    """Genera guiones (shorts y largos) a partir de un banco de temas aprobado."""
    os.makedirs(_OUT_DIR, exist_ok=True)
    frases_usadas = _leer_banco_frases()
    posturas = _leer_posturas()
    temas = _leer_banco(banco_path)
    if elegir:
        temas = [t for i, t in enumerate(temas, 1) if i in elegir]
    if not temas:
        raise SystemExit("No hay temas seleccionados (revisá --elegir y el archivo del banco)")

    resultado = []
    for t in temas:
        fmt = t.get("formato", "short")
        if fmt == "largo":
            escenas = _generar_largo(t, frases_usadas, posturas, modelo)
            resultado.append({
                "titulo": t.get("titulo"), "formato": "largo",
                "tema_prompt": t.get("tema_prompt"),
                "regla_retencion": t.get("regla_retencion"),
                "escenas": escenas, "warnings": t.get("warnings", []),
            })
        else:
            frases = _generar_frases(t.get("tema_prompt") or t.get("titulo"), 3,
                                     frases_usadas, posturas, modelo)
            resultado.append({
                "titulo": t.get("titulo"), "formato": "short",
                "tema_prompt": t.get("tema_prompt"),
                "regla_retencion": t.get("regla_retencion"),
                "frases": frases, "warnings": t.get("warnings", []),
            })

    fecha = time.strftime("%Y-%m-%d_%H%M")
    out_path = os.path.join(_OUT_DIR, f"guiones_{fecha}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"banco": banco_path, "modelo": modelo, "videos": resultado},
                  f, ensure_ascii=False, indent=2)

    if not solo_json:
        print("\n" + "=" * 60)
        for n, v in enumerate(resultado, 1):
            print(f"\n{n}. [{v['formato'].upper()}] {v['titulo']}")
            if v.get("warnings"):
                for w in v["warnings"]:
                    print(f"   ⚠ {w}")
            if v["formato"] == "largo":
                print(f"   escenas: {len(v['escenas'])}")
                for e in v["escenas"]:
                    print(f"     - {e['text'][:90]}")
            else:
                for fr in v["frases"]:
                    print(f"     - {fr['texto'][:90]}")
                    if fr.get("warnings"):
                        for w in fr["warnings"]:
                            print(f"       ⚠ {w}")
    print(f"\nGuardado: {out_path}")
    return resultado


def generar(cantidad=10, tema=None, modelo=_DEFAULT_MODEL, solo_json=False):
    os.makedirs(_OUT_DIR, exist_ok=True)
    frases_usadas = _leer_banco_frases()
    posturas = _leer_posturas()
    todos = _generar_frases(tema, cantidad, frases_usadas, posturas, modelo)

    fecha = time.strftime("%Y-%m-%d_%H%M")
    out_path = os.path.join(_OUT_DIR, f"{fecha}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"tema": tema, "modelo": modelo, "frases": todos},
                  f, ensure_ascii=False, indent=2)

    if not solo_json:
        print("\n" + "=" * 60)
        for n, fr in enumerate(todos, 1):
            print(f"\n{n}. {fr['texto']}")
            print(f"   duración: {fr.get('duracion')} | keyword: {fr.get('keyword')}")
            print(f"   prompt: {fr.get('prompt')}")
            if fr.get("warnings"):
                for w in fr["warnings"]:
                    print(f"   ⚠ {w}")
    print(f"\nGuardado: {out_path}")
    return todos


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera frases/guiones con Gemini")
    ap.add_argument("--cantidad", type=int, default=10)
    ap.add_argument("--tema", default=None)
    ap.add_argument("--banco", default=None,
                    help="archivo del banco (salida de generar_banco.py)")
    ap.add_argument("--elegir", default=None,
                    help="índices del banco a generar (ej. '8,5')")
    ap.add_argument("--modelo", default=_DEFAULT_MODEL)
    ap.add_argument("--json", action="store_true", help="imprimir solo JSON")
    args = ap.parse_args()
    if args.banco:
        elegir = [int(x) for x in args.elegir.split(",")] if args.elegir else None
        generar_desde_banco(args.banco, elegir=elegir, modelo=args.modelo,
                            solo_json=args.json)
    else:
        generar(cantidad=args.cantidad, tema=args.tema, modelo=args.modelo,
                solo_json=args.json)
