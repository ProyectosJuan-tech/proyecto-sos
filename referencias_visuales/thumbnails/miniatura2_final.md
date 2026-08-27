# miniatura2_final (SOLTAR NO ES PERDER)

- Fuente: flux_img Pollinations seed 411 (3 iteraciones: 5.0 → 6.0 → 8.0 PASS) + GIMP MCP
- Uso validado: video soltar-no-es-perder · QA visual_critic v2 --mode design
  8/10 PASS con HARD_FAIL: NO y los 6 checks CTA en YES

## WHY_IT_WORKS
- Misma plantilla de marca que miniatura1 (jerarquía Anton/Georgia/CTA) aplicada a una
  foto COMPLETAMENTE distinta (sillón vs mujer con plantas) y funcionó igual: la
  identidad del canal vive en la tipografía+composición, no en el sujeto.
- Ciclo de corrección documentado: subtítulo falló legible a 56px sobre pared gris;
  UNA variable (tamaño → 64px) lo resolvió. 56px NO es universal: depende del fondo.
- Análisis previo al texto por franjas (exportar columna izquierda + preguntar al
  crítico) deshizo una alucinación de "lámpara arriba-izquierda" antes de diseñar.
- CTA v2 por COMPONENTE: icono play Material Icons (capa PNG CTA_ICON) +
  SUSCRIBITE EN blanco + YOUTUBE rojo + barra dorada — receta `suscripcion`
  de `assets/brand/cta/presets.json`. Verificado cta_aligned/not_competing YES.

## DO_NOT_COPY
- No aceptar la primera foto generada: v1 tenía planta+jarrón+lámpara invadiendo la
  zona de texto (5.0). El brief "uncluttered" explícito es necesario.
- No agregar planta/cojín "para color" que sugirió el crítico en v3: reintroduciría
  el desorden de v1.
- Coordenadas heredadas de otra foto NO sirven sin re-análisis: aquí se verificó
  pared limpia/piso vacío antes de clonar la plantilla.
- La foto final sigue algo gris/contenida pese a PASS: los briefs nuevos deben
  pedir explícitamente luz ámbar abundante y blancos naturales (anchors anti-moody
  de CHANNEL_STYLE_ANCHORS ya lo hacen).
