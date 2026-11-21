# 0012 — Publicación en un repositorio nuevo, con el historial aparte

Fecha: 2026-11-20

## Contexto

Antes de hacer público `core` se revisó todo lo que quedaría expuesto. No había facturas, bases, claves ni rutas personales en ningún commit, pero el historial tenía dos cédulas reales tomadas de las facturas de prueba (en un comentario, una prueba y la bitácora) y el nombre de una persona que compartió facturas. Se corrigieron en los archivos, pero seguían visibles en los commits anteriores. Además, los 50 commits llevaban el correo institucional del autor.

## Decisión

- El repositorio con todo el historial pasa a llamarse `auditor-dian-core-historial` y sigue **privado**.
- `auditor-dian-core` se crea de nuevo, **público**, con un único commit del estado de la versión 0.4.1 y su etiqueta `v0.4.1`.
- El autor de los commits pasa a ser el correo anónimo de GitHub (`…@users.noreply.github.com`), también en `pyproject.toml`.

## Alternativas descartadas

- **Reescribir el historial** del repositorio existente reemplazando los textos: conserva los commits, pero exige forzar el push y recrear las etiquetas, y es fácil que se escape una copia (otra rama, una caché del grafo).
- **Publicar tal cual**: expone identificaciones de personas reales.

## Consecuencias

- En el repositorio público, la historia empieza en la 0.4.1. Lo anterior sigue documentado en `docs/bitacora.md`, `docs/decisiones/` y `docs/hitos/`.
- Localmente, la rama `historial` apunta al remoto `historial` y `master` al público (`origin`).
- Antes de cada commit se mantiene la regla: ningún dato real en el repositorio, ni siquiera en comentarios o ejemplos de pruebas.
