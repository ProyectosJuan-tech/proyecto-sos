# Principios de jerarquía visual — adaptados al canal (9:16 / 16:9)

Origen: visual-design (Claude-Skills-collection) + canvas-design (Anthropic),
destilados y adaptados. No copiar ejemplos; aplicar los principios.

## La decisión que precede a todas las demás

Antes de tocar GIMP responder EN ORDEN:
1. ¿Qué se lee PRIMERO? (debe ser UNA cosa)
2. ¿Qué se percibe segundo?
3. ¿Qué es secundario?
4. ¿Qué puede ELIMINARSE sin perder significado?

Si todos los elementos tienen el mismo peso, la composición falla.

## Reglas adaptadas

- **Grid**: usar `design_intelligence.grid_1080x1920()` — margen lateral 5.9%,
  columna de texto hasta 55%, baseline título 52%h, CTA a 85.5%h. Romper el grid
  solo con intención declarada.
- **Espacio negativo como material**: no es zona a rellenar; es lo que da fuerza
  al foco. En 9:16, dejar respirar al menos un tercio del marco.
- **Foco único**: si hay dos focos, no hay ninguno. El foco debe sobrevivir a
  120px (MOBILE_120PX_TEST).
- **Flujo visual**: decidir la ruta del ojo (título → objeto → salida). La
  composición guía; si el ojo se queda sin ruta, falla.
- **Contraste = jerarquía**: tamaño, peso, color y espacio. Los contrastes
  pequeños se leen como errores: cometer una diferencia GRANDE o ninguna.
- **Restricción de paleta**: máx 3 colores cromáticos + neutros (token
  `colors.restriccion`). Cada color adicional diluye la jerarquía construida.
- **Restricción tipográfica**: máximo 3 familias (`typography.max_familias_por_pieza`);
  la jerarquía viene de tamaño/peso/espacio, nunca de más fuentes.
- **Test a tamaño real**: en feed la pieza se ve a ~120px. Reducir y evaluar:
  lo que sigue legible ES la jerarquía real construida (no la intencionada).

## Método filosofía → expresión (canvas-design)

Antes de diseñar: escribir la VISUAL_PHILOSOPHY (nombre corto + cómo se
comportan espacio/luz/color/escala/vacío). No es layout ni plantilla.
Herramienta: `design_intelligence.visual_philosophy(ctx)`.
La filosofía genera decisiones posteriores; una decisión que la contradice se
corrige o se cambia la filosofía — nunca ambas a medias.
