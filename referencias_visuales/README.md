# referencias_visuales/ — Biblioteca curada de referencias visuales del canal

> Qué imágenes NUESTRAS ya funcionaron (y por qué), para dirigir nuevas generaciones
> con criterio en lugar de empezar de cero cada vez. Complementa a `director_visual.py`
> (dirección de escenas) y `visual_critic.py` (QA de imágenes nuevas).

## Estructura

| Carpeta | Contenido esperado |
|---|---|
| `photography/` | refs externas de fotografía observacional/editorial (a curar) |
| `interiors/` | interiores cálidos, luz de ventana, espacios íntimos (a curar) |
| `women_35_64/` | escenas relatables para la audiencia real del canal (a curar) |
| `plants/` | plantas y naturaleza como símbolo narrativo (a curar) |
| `objects/` | **N1-N8 de hábitos-sistema**: objeto-primero, la serie validada |
| `lighting/` | estudios de luz: tarde lateral, contraventana, amanecer suave (a curar) |
| `compositions/` | encuadres probados: tercio izquierdo libre, figura pequeña (a curar) |
| `thumbnails/` | miniaturas terminadas del canal (base + final + A/B) |

## Formato de anotación (obligatorio por imagen)

Cada imagen lleva un `.md` hermano con DOS secciones OBLIGATORIAS:

```markdown
## WHY_IT_WORKS
- qué funciona exactamente (luz, composición, emoción, riesgo evitado)

## DO_NOT_COPY
- qué NO imitar aunque parezca tentador
```

Y cuando aporten (recomendado en refs fotográficas), estas claves:

```markdown
## COMPOSITION / LIGHT / COLOR / SUBJECT / SYMBOL
- una línea por clave: la decisión visual que enseña
```

Sin WHY_IT_WORKS y DO_NOT_COPY la referencia no sirve: una imagen sin
explicación se copia mal y contagia sus defectos.

## Reglas de uso

1. Antes de dirigir una escena nueva (`director_visual.py`), mirar 2-3 refs de la
   categoría correspondiente — el objetivo es REUTILIZAR lo probado, no reinventar.
2. Las refs de `thumbnails/` son la plantilla del diseño v2: jerarquía Anton/Georgia/CTA
   validada con QA (ver `miniatura1_final.md`, `miniatura2_final.md`).
3. Doble sistema visual: pista bienestar = WARM_STYLE cálido; pista estoica =
   negro/piedra/dorado. NO mezclar paletas entre pistas.
4. **Admisión (v2)**: solo entra una imagen nueva con `visual_critic.py` score >= 9
   **AND HARD_FAIL = NO** (score alto con hard fail estructural NO califica).
   No llenar indiscriminadamente: se guardan imágenes que ENSEÑEN una decisión,
   no imágenes "bonitas". El componente CTA se documenta aparte en
   `assets/brand/cta/README.md`.

## Estado de siembra (2026-08-24)

Semillero inicial: N1-N8 (`objects/`, 8 imágenes QA-validadas de hábitos-sistema) +
miniatura 1 base/final, sabio x2, hábitos A/B (`thumbnails/`). Las carpetas marcadas
"a curar" se completan con referencias EXTERNAS seleccionadas (fotos reales de
photographers de referencia POR PROPIEDADES, nunca para copiar estilo literal).
