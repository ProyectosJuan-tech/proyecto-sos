# Catálogo ANTI-SLOP — adaptado a miniaturas/piezas del canal

Origen: sboghossian/design-skill reference/anti-slop.md, adaptado de UI web a
miniatura 9:16/16:9. Check programático: `design_intelligence.anti_slop()`.
Check visual: dimensión `anti_slop` en `visual_critic --mode design`.

## Pregunta rectora

Cada elemento debe tener una razón comunicable en UNA frase:
- ¿lo agrego porque COMUNICA algo, o porque "queda bonito"?
- ¿la composición podría pertenecer a CUALQUIER canal? (= genérica = slop)
- ¿estoy llenando espacio que debería permanecer vacío?
- ¿hay colores sin función? ¿tipografías de más?

NO es minimalismo obligatorio: densidad está bien SI cada elemento tiene razón.

## Patrones a rechazar en este canal

**Color**
- Tercer acento "por variedad" (el rojo de marca ya es el acento principal).
- Colorear la foto para que combine con el texto (la foto conserva su paleta natural).
- Degradado decorativo sin función (la banda inferior de legibilidad SÍ tiene función).

**Tipografía**
- Cuarta fuente "para el detalle chico".
- Dos sans casi idénticas en la misma pieza.
- Título en Inter/sans genérica (neutraliza la identidad Anton).

**Composición**
- Rellenar el espacio negativo con iconos/formas porque "se ve vacío".
- Centrar todo por defecto (el balance asimétrico es la casa).
- Tres elementos del mismo tamaño compitiendo (sin foco = slop).
- Composición sin style_family elegida (= plantilla de cualquier canal).

**Identidad**
- Pieza intercambiable con otro canal de bienestar: falta señal de identidad
  (título rojo Anton, columna editorial, foto luminosa editorial).

## Cómo rechazar el slop

1. Notar el reflejo ("iba a agregar un ícono decorativo").
2. Nombrarlo.
3. Reemplazarlo por una elección justificada y registrarla en ANTI_SLOP.
Salida esperada: `ANTI_SLOP: PASS` o `ANTI_SLOP: FAIL` con MÁXIMO 3 problemas concretos.
