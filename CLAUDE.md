# MejorInversion (InvierteColombia)

Sitio estático (`index.html`, `review.html`) publicado con **GitHub Pages** desde `main` (raíz,
compilación «legacy»): **unir o hacer push a `main` despliega solo**. Producción:
https://hectronix2005.github.io/Mejor_Inversion/ . La API Flask (`run.py`, `api/`) solo corre en local.
No hay base de datos (los datos son JSON en `data/`, versionados en git).

## Versiones y rollback

- **Etiquetas:** tras cada compilación de Pages, `.github/workflows/versionado.yml` pasa `bin/sonda`
  (portada 200 con «InvierteColombia») y, si está en verde, `bin/etiquetar` crea la etiqueta anotada
  `vAAAA.MM.DD-N` (hora de Bogotá) sobre el commit servido y su Release de GitHub. Si el contenido
  ya era una versión etiquetada (p. ej. tras un rollback), no crea otra. Si etiquetar falla, solo avisa.
- **Artefactos:** no hay imagen; cada versión es su etiqueta en git (Pages no tiene rollback nativo).
- **Copia de base:** no aplica (no hay base de datos).
- `bin/rollback --seco [versión]`: dice qué sirve producción (según la API de Pages), a qué versión
  volvería y comprueba que la etiqueta existe. No toca nada.
- `bin/rollback [versión]`: sin argumento, la versión anterior a la servida (o la última buena si lo
  servido no tiene etiqueta). Crea en `main` un commit con el contenido exacto de esa etiqueta (sin
  push forzado ni reescribir historia), espera a Pages, pasa la sonda y avisa a Ultron (carta; si no,
  `wt_push.py` por ssh al Air). Necesita `gh` autenticado y permiso de push.
- **Automático:** si la sonda falla tras un despliegue, el workflow llama a `bin/rollback` una sola vez
  (nunca si lo servido ya es un «Rollback a …») y termina en rojo.
- **Qué NO hace:** no hay base que restaurar (los JSON de `data/` sí vuelven a los de la etiqueta y
  quedan en el historial de git); no borra etiquetas ni reescribe `main`. Después de un
  rollback, `main` contiene la versión vieja: el arreglo se hace con un PR encima.
