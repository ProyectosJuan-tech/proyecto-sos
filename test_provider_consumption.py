"""Test de auditoría de consumo de proveedores externos.

Cubre (todo con mocks, sin red):
  1. Early stop en asset_selector (máximo de queries + corte por score).
  2. Caché Pexels (hit/miss, queries repetidas).
  3. Manejo HTTP de pexels_stock: 200/404/429 with retries/backoff; 404 no loop.
  4. Caché hash de flux_img (prompt+seed+aspect) + regeneración explícita.
  5. Reuso en segunda ejecución ("re-render reusa assets").
  6. Contabilidad de consumo (PEXELS/AI IMAGE/VIDEO STOCK/VISION) al reporte.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import consumption

PASSED = 0
FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"[PASS] {name}")
    else:
        FAILED += 1
        print(f"[FAIL] {name}" + (f" — {detail}" if detail else ""))


# ─────────────────────────────────────────────
# 1) Early stop en asset_selector
# ─────────────────────────────────────────────
def test_early_stop():
    consumption.reset()
    os.environ.pop("SELECTOR_MAX_QUERIES", None)
    import asset_selector as asel
    check("early_stop: MAX_QUERIES_PER_SELECTION acotado",
          asel.MAX_QUERIES_PER_SELECTION > 0 and asel.MAX_QUERIES_PER_SELECTION <= 10)
    check("early_stop: GOOD_ENOUGH_SCORE definido", asel.GOOD_ENOUGH_SCORE > 0)

    # Early-stop real: la primera query devuelve candidatos con score alto,
    # así que NO deben ejecutarse las 5 querues.
    calls = {"n": 0}

    def fake_fetch(q, per_page=10):
        calls["n"] += 1
        return [{
            "id": f"v{i}", "duration": 8.0, "width": 1920, "height": 1080,
            "url": f"https://x/{q}/v{i}.mp4", "quality": "hd",
            "video_files": [{"width": 1920, "height": 1080, "link": f"https://x/{q}/v{i}.mp4"}],
        } for i in range(3)]

    class S:
        total = 90.0
        reasons = []

    def score_high(c, brief, prev, ctx):
        return S()

    prev_score = asel.score_candidate
    prev_sel = asel.select_asset
    asel.score_candidate = score_high
    try:
        # Brief dummy mínimo para select_asset
        class Brief:
            scene_id = "t"; narration = "n"; visual_event = "w"; subject = ""
            action = ""; setting = ""; emotional_core = "w"; text_space = "upper"
            duration = 6.0; pexels_queries = []
            def get(self, k, d=None): return getattr(self, k, d)
        sel = asel.select_asset(Brief(), fetch_fn=fake_fetch)
        check("early_stop: se ejecutó < número total de queries",
              calls["n"] < asel.MAX_QUERIES_PER_SELECTION, f"llamadas={calls['n']}")
        check("early_stop: al menos una query ejecutada", calls["n"] >= 1)
        check("early_stop: seleccionó un candidato", sel.selected is not None)
    finally:
        asel.score_candidate = prev_score
        asel.select_asset = prev_sel
        consumption.reset()


# ─────────────────────────────────────────────
# 2 + 3) Caché Pexels y manejo HTTP (mock de httpx.get)
# ─────────────────────────────────────────────
class FakeResp:
    def __init__(self, code=200, payload=None):
        self.status_code = code
        self._payload = payload
    def json(self):
        return self._payload if self._payload is not None else {}
    def raise_for_status(self):
        if self.status_code >= 400:
            raise __import__("httpx").HTTPStatusError("e", request=None, response=self)


def test_pexels_cache_hit():
    import httpx
    import pexels_stock as ps
    consumption.reset()
    ps._cache_clear()
    real_get = httpx.get
    state = {"n": 0}

    def fake_get(url, headers=None, params=None, timeout=None):
        state["n"] += 1
        return FakeResp(200, {"videos": [], "photos": []})

    httpx.get = fake_get
    try:
        ps.search_vertical("mujer ventana", min_duration=1.0)
        ps.search_vertical("mujer ventana", min_duration=1.0)
        rep = consumption.get_minimal_report()
        check("cache: HTTP requests == 1", rep["PEXELS"]["HTTP requests"] == 1)
        check("cache: queries realizadas == 1", rep["PEXELS"]["queries realizadas"] == 1)
        check("cache: cache misses == 1", rep["PEXELS"]["cache misses"] == 1)
        check("cache: cache hits == 1", rep["PEXELS"]["cache hits"] == 1)
        check("cache: solo 1 llamada HTTP real", state["n"] == 1)
    finally:
        httpx.get = real_get
        ps._cache_clear()
        consumption.reset()


def test_http_429_retries():
    import httpx
    import pexels_stock as ps
    consumption.reset()
    ps._cache_clear()
    real_get = httpx.get
    state = {"n": 0}

    def fake_get(url, headers=None, params=None, timeout=None):
        state["n"] += 1
        if state["n"] < 3:
            return FakeResp(429)
        return FakeResp(200, {"videos": [], "photos": []})

    httpx.get = fake_get
    try:
        _http = ps._http_get_json("https://api.pexels.com/v1/search", {"query": "q"}, "k")
        check("http: 429 integrado con backoff luego devuelve datos", _http is not None)
        check("http: llamadas = retries(2) + intento ok = 3", state["n"] == 3)
        rep = consumption.get_minimal_report()
        check("http: contadores 429 == 2", rep["PEXELS"]["429"] == 2)
        check("http: reintentos == 2", rep["PEXELS"]["reintentos"] == 2)
    finally:
        httpx.get = real_get
        ps._cache_clear()
        consumption.reset()


def test_http_404_no_loop():
    import httpx
    import pexels_stock as ps
    consumption.reset()
    ps._cache_clear()
    real_get = httpx.get
    state = {"n": 0}

    def fake_get(url, headers=None, params=None, timeout=None):
        state["n"] += 1
        return FakeResp(404)

    httpx.get = fake_get
    try:
        _http = ps._http_get_json("https://api.pexels.com/v1/search", {"query": "q"}, "k")
        check("404: devuelve None (fallback)", _http is None)
        check("404: una sola llamada, NO loop", state["n"] == 1)
    finally:
        httpx.get = real_get
        ps._cache_clear()
        consumption.reset()


def test_http_vacio_devuelve_lista_vacia():
    import httpx
    import pexels_stock as ps
    consumption.reset()
    ps._cache_clear()
    real_get = httpx.get

    def fake_get(url, headers=None, params=None, timeout=None):
        return FakeResp(200, {"videos": [], "photos": []})

    httpx.get = fake_get
    try:
        res = ps.search_vertical("algo improbable", min_duration=1.0)
        check("empty 200: devuelve None (sin videos)", res is None)
    finally:
        httpx.get = real_get
        ps._cache_clear()
        consumption.reset()


# ─────────────────────────────────────────────
# 4 + 5) Caché hash flux_img
# ─────────────────────────────────────────────
def test_flux_cache():
    import flux_img
    consumption.reset()
    d = tempfile.mkdtemp()
    out = os.path.join(d, "img.jpg")
    open(out, "wb").write(b"x" * 6000)
    fp = flux_img._fingerprint("promptA", 5, "9:16")
    flux_img._save_manifest(out, {os.path.basename(out): fp})
    check("flux: lookup hit (mismo fp)", flux_img.image_cache_lookup(out) == fp)
    check("flux: lookup miss (otro path)", flux_img.image_cache_lookup(out + "2") is None)
    flux_img.invalidate(out)
    check("flux: invalidate borra entrada", flux_img.image_cache_lookup(out) is None)
    consumption.reset()


def test_flux_second_run_reuse():
    import flux_img
    consumption.reset()
    d = tempfile.mkdtemp()
    out = os.path.join(d, "img.jpg")
    open(out, "wb").write(b"x" * 6000)
    fp = flux_img._fingerprint("promptB", 7, "9:16")
    flux_img._save_manifest(out, {os.path.basename(out): fp})
    calls = {"n": 0}
    orig = flux_img._generate_async
    flux_img._generate_async = lambda *a, **k: calls.__setitem__("n", calls["n"] + 1)
    try:
        res = flux_img.generate("promptB", out, seed=7, aspect="9:16", retries=1)
        check("reuse: 2ª ejecución NO regenera (cache hit)", calls["n"] == 0 and res == out)
        rep = consumption.get_minimal_report()
        check("reuse: ai_image cache hits == 1", rep["AI IMAGE"]["cache hits"] == 1)
    finally:
        flux_img._generate_async = orig
        consumption.reset()


def test_flux_force_regenerates():
    import flux_img
    consumption.reset()
    d = tempfile.mkdtemp()
    out = os.path.join(d, "img.jpg")
    open(out, "wb").write(b"x" * 6000)
    fp = flux_img._fingerprint("promptC", 9, "9:16")
    flux_img._save_manifest(out, {os.path.basename(out): fp})
    calls = {"n": 0}
    orig = flux_img._generate_async
    async def fake_gen(*a, **k):
        calls["n"] += 1
        with open(out, "wb") as f:
            f.write(b"y" * 7000)
        return "ok"
    flux_img._generate_async = fake_gen
    try:
        flux_img.generate("promptC", out, seed=9, aspect="9:16", retries=1, force=True)
        check("force: regenera (1 llamada)", calls["n"] == 1)
    finally:
        flux_img._generate_async = orig
        consumption.reset()


# ─────────────────────────────────────────────
# 6) Contabilidad al reporte (claves planas mapeadas)
# ─────────────────────────────────────────────
def test_accounting_keys():
    consumption.reset()
    for k in ["pexels.queries", "pexels.http_requests", "pexels.cache_hits",
              "pexels.cache_misses", "pexels.429", "pexels.errors", "pexels.retries",
              "ai_image.requests", "ai_image.cache_hits", "ai_image.cache_misses",
              "ai_image.regenerations", "video_stock.requests", "video_stock.cache_hits",
              "vision.requests", "vision.ok", "vision.quota_fail"]:
        consumption.incr(k)
    rep = consumption.get_minimal_report()
    check("accounting: PEXELS presente y mapeado",
          rep["PEXELS"]["queries realizadas"] == 1 and rep["PEXELS"]["HTTP requests"] == 1)
    check("accounting: AI IMAGE presente y mapeado",
          rep["AI IMAGE"]["generation requests"] == 1 and rep["AI IMAGE"]["cache hits"] == 1)
    check("accounting: VIDEO STOCK presente y mapeado",
          rep["VIDEO STOCK"]["requests"] == 1 and rep["VIDEO STOCK"]["cache hits"] == 1)
    check("accounting: VISION presente y mapeado",
          rep["VISION"]["requests"] == 1 and rep["VISION"]["éxitos"] == 1
          and rep["VISION"]["fallos por cuota"] == 1)
    consumption.reset()


if __name__ == "__main__":
    test_early_stop()
    test_pexels_cache_hit()
    test_http_429_retries()
    test_http_404_no_loop()
    test_http_vacio_devuelve_lista_vacia()
    test_flux_cache()
    test_flux_second_run_reuse()
    test_flux_force_regenerates()
    test_accounting_keys()
    print("=" * 60)
    print(f"RESULTADO: {PASSED} pass, {FAILED} fail")
    print("=" * 60)
    sys.exit(1 if FAILED else 0)
