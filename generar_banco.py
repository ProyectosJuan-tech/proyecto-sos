#!/usr/bin/env python3
"""Generador de BANCO DE TEMAS para el canal con Gemini (gratis).

Pieza 1 del "Método Viral": convierte la investigación del canal (estudios +
frases usadas + posturas) en una lista de ideas de contenido en lote, para
después generar guiones (generar_textos.py --banco) y renderizarlos en serie
(hacer_serie.py).

Misma filosofía que generar_textos.py: salida JSON para REVISIÓN MANUAL, NUNCA
escribe directo en hacer_shorts.py / hacer_videos_youtube.py. Primero el usuario
aprueba y marca los temas.

Uso:
    python3 generar_banco.py [--cantidad 20] [--formato todos|short|largo]
                             [--modelo gemini-3.5-flash]

Salida:
    - impresión legible en consola
    - textos_generados/banco_<fecha>.json  (ideas de tema completas)
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

CONTENIDO_DIR = os.path.join(ROOT, "cerebro", "wiki", "contenido")

PROHIBIDAS = [
    "ley de atracción", "manifest", "vibra", "vibrar mal", "riqueza",
    "millonario", "lotería", "fórmula mágica", "secreto", "mente sobre materia",
    "pensar bonito", "hazte rico", "dinero fácil",
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


def _leer_archivo(name):
    try:
        with open(os.path.join(CONTENIDO_DIR, name)) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def _leer_frases_usadas():
    """Extrae los títulos/videos ya usados (para NO repetir ángulos)."""
    texto = _leer_archivo("frases-usadas.md")
    usados = []
    for line in texto.splitlines():
        line = line.strip()
        m = re.search(r"\|\s*\"([^\"]+)\"\s*\|\s*([^|]+)\s*\|", line)
        if m:
            usados.append(f"{m.group(1)[:70]} -> video {m.group(2).strip()}")
    # También las líneas con formato "N. frase" de los largos
    for line in texto.splitlines():
        m = re.match(r'\s*\d+\.\s*"([^"]+)"', line)
        if m:
            usados.append(m.group(1)[:70])
    return usados[:40]


def _contexto():
    """Arma el contexto de la investigación del canal para el prompt."""
    partes = []
    bloques = [
        ("ESTUDIO YOUTUBE 2026 (qué vende en el nicho)",
         _leer_archivo("estudio-youtube-2026.md")),
        ("REGLAS META / ESTRUCTURAS VIRALES",
         _leer_archivo("estructura-viral-prompts.md")),
        ("POSTURAS DEL CANAL (NO CONTradecir)",
         _leer_archivo("posturas.md")),
    ]
    for titulo, cuerpo in bloques:
        if cuerpo:
            partes.append(f"### {titulo}\n{cuerpo[:3500]}")
    return "\n\n".join(partes)


def _system_prompt(cantidad, formato, contexto, usados):
    formato_line = {
        "todos": "mezclá cortos y largos (indicá cuál en cada idea)",
        "short": "SOLO cortos verticales (20-25s, motor de descubrimiento)",
        "largo": "SOLO largos horizontales (8+ min, monetizables)",
    }[formato]
    return f"""Sos el estratega de contenido del canal "El Sabio de la Caverna" (bienestar con base filosófica real, anti-gurú, audiencia mujeres 35-64). Tu trabajo es proponer TEMAS para videos, no escribir los guiones.

Contexto de la investigación del canal (leelo antes de proponer):
{contexto}

Frases/ángulos YA usados (NO repetir el mismo ángulo; buscá variantes nuevas):
{chr(10).join('- ' + u for u in usados)}

Reglas de los temas que proponés:
1. NUEVOS: el ángulo no debe estar en la lista de usados (se puede reformular la misma idea grande con otra imagen concreta).
2. ANCLADOS A LA INVESTIGACIÓN: cada tema debe explicar QUÉ regla de retención cumple (gancho 3s, loop, escalada temporal, PAYOFF antes de la mitad, transiciones adversativas, roadmap 10s, re-engagement beat 25-35%, bonus "una cosa más", tema que vende según el estudio).
3. FORMATO: {formato_line}.
4. NICHOS GANADORES según el estudio: manipuladores/límites/personas tóxicas, rutinas de mañana, atención/scroll/caverna moderna, culpa, comparación, descanso, tiempo.
5. SIN promesas mágicas, SIN culpa, SIN diagnóstico, SIN ley de atracción. SIEMPRE cierran en método accionable. Coherentes con la fe católica (sin contradecirla).
6. Concretos y específicos (ej. "El no como escudo", "La mañana sin teléfono"), no genéricos ("hablar de felicidad").
7. {cantidad} ideas, todas distintas entre sí, priorizadas por potencial de viralidad (la primera = la más fuerte).

Devolvé SOLO JSON válido, sin texto alrededor, con esta forma exacta:
[{{"titulo": "Título corto y atractivo (ej. '10 frases para callar a los manipuladores')", "angulo": "Una oración del enfoque concreto, distinto a lo ya usado", "formato": "short" o "largo", "regla_retencion": "qué regla de retención cumple (ej. 'loop + gancho 3s')", "porque_viral": "una frase: por qué este tema puede ser viral en el nicho", "tema_prompt": "frase clave corta para buscar/generar sobre este tema"}}]"""


def _extraer_json(texto):
    m = re.search(r"\[[\s\S]*\]", texto)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _sanitizar(item, usados):
    """Chequea colisiones de ángulo con lo usado y conceptos prohibidos."""
    warns = []
    titulo = (item.get("titulo", "") + " " + item.get("angulo", "")).lower()
    for kw in PROHIBIDAS:
        if kw in titulo:
            warns.append(f"concepto prohibido: '{kw}'")
    toks_i = set(re.findall(r"[a-záéíóúñ]{4,}", titulo))
    for u in usados:
        toks_u = set(re.findall(r"[a-záéíóúñ]{4,}", u.lower()))
        comunes = toks_i & toks_u
        if len(comunes) >= max(4, len(toks_i) * 0.6):
            warns.append(f"ángulo muy parecido a usado: '{u[:50]}...'")
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


def generar(cantidad=20, formato="todos", modelo=_DEFAULT_MODEL, solo_json=False):
    os.makedirs(_OUT_DIR, exist_ok=True)
    contexto = _contexto()
    usados = _leer_frases_usadas()
    sys_prompt = _system_prompt(cantidad, formato, contexto, usados)

    print(f"[gemini] generando banco de {cantidad} ideas ({formato})...", flush=True)
    raw = _llamar_gemini(sys_prompt, modelo)
    items = _extraer_json(raw) or []
    vistos = set()
    todos = []
    for it in items:
        it.setdefault("formato", "short")
        it.setdefault("regla_retencion", "")
        t = (it.get("titulo", "") or "").strip()
        if not t or t.lower() in vistos:
            continue
        vistos.add(t.lower())
        it["warnings"] = _sanitizar(it, usados)
        todos.append(it)
    todos = todos[:cantidad]

    fecha = time.strftime("%Y-%m-%d_%H%M")
    out_path = os.path.join(_OUT_DIR, f"banco_{fecha}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"cantidad": cantidad, "formato": formato, "modelo": modelo,
                   "temas": todos}, f, ensure_ascii=False, indent=2)

    if not solo_json:
        print("\n" + "=" * 60)
        for n, t in enumerate(todos, 1):
            print(f"\n{n}. [{t['formato'].upper()}] {t['titulo']}")
            print(f"   ángulo: {t.get('angulo')}")
            print(f"   regla: {t.get('regla_retencion')} | viral: {t.get('porque_viral')}")
            print(f"   tema_prompt: {t.get('tema_prompt')}")
            if t.get("warnings"):
                for w in t["warnings"]:
                    print(f"   ⚠ {w}")
    print(f"\nGuardado: {out_path}")
    return todos


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera banco de temas con Gemini")
    ap.add_argument("--cantidad", type=int, default=20)
    ap.add_argument("--formato", default="todos",
                    choices=["todos", "short", "largo"])
    ap.add_argument("--modelo", default=_DEFAULT_MODEL)
    ap.add_argument("--json", action="store_true", help="imprimir solo JSON")
    args = ap.parse_args()
    generar(cantidad=args.cantidad, formato=args.formato, modelo=args.modelo,
            solo_json=args.json)