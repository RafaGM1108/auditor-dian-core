# Cronograma y plan de documentación — Auditor DIAN

> Supuesto: dos personas a medio tiempo (≈ 8–10 h por semana cada una). Si el ritmo cambia, se mueven las fechas, no el orden.
> Inicio: lunes 30 de noviembre de 2026.

## Cronograma

| # | Fechas | Fase | Repo | Entregable | Cierra cuando |
| --- | --- | --- | --- | --- | --- |
| 0 | 30 nov – 13 dic 2026 | Investigación y preparación | — | `docs/investigacion/` con fuentes públicas (cifras DIAN, normas, herramientas existentes); 30–50 facturas propias anonimizadas; repos creados con SPEC, CLAUDE.md y `docs/` | Investigación escrita con sus fuentes — **escrita el 2026-11-20** ([investigación](investigacion/README.md)); las 57 facturas reales viven en `data/`, fuera de git; al repositorio solo van fixtures sintéticos |
| 1 | 14 dic – 27 dic 2026 | M1 Parser | core | Parser de ZIP, AttachedDocument, factura, notas y documento soporte | Pruebas pasan con todos los fixtures — **cerrado el 2026-11-20**; salvedad levantada el mismo día con 57 documentos reales ([resumen](hitos/M1.md)) |
| — | 28 dic 2026 – 10 ene 2027 | Colchón de fin de año | — | Avance libre o descanso | — |
| 2 | 11 ene – 24 ene 2027 | M2 Base y CLI | core | Esquema DuckDB, ingesta idempotente, `auditor ingerir` | Reingerir no duplica nada — **cerrado el 2026-11-20** ([resumen](hitos/M2.md)) |
| 3 | 25 ene – 7 feb 2027 | M3 Informes | core | Seis informes + exportación a Excel | Totales cuadran con los PDF — **cerrado el 2026-11-20** ([resumen](hitos/M3.md)) |
| 4 | 8 feb – 21 feb 2027 | M4 MCP | core | Servidor MCP con seis herramientas | Un agente responde con cifras exactas y CUFEs — **cerrado el 2026-11-20** ([resumen](hitos/M4.md)) |
| 5 | 22 feb – 28 feb 2027 | M5 Plugins | core | Interfaz de plugins + plugin de ejemplo | `core` v0.1 interno etiquetado — **cerrado el 2026-11-20**, etiqueta `v0.1.0` ([resumen](hitos/M5.md)) |
| 6 | 1 mar – 28 mar 2027 | P1–P2 Reglas y lectores | pro | Reglas versionadas; lectores de certificado de ingresos, bancarios y exógena | Fixtures por plantilla pasan |
| 7 | 29 mar – 25 abr 2027 | P3–P4 Cruces y borrador | pro | Cruce con exógena, documentos faltantes, borrador de renta persona natural | Mapeo de renglones con norma citada para cada uno |
| 8 | 26 abr – 23 may 2027 | Prueba con casos reales | ambos | Borrador comparado contra declaraciones ya presentadas (propias o de conocidos, anonimizadas) | Diferencias documentadas renglón por renglón |
| 9 | 24 may – 6 jun 2027 | Ajustes, publicación e informe | ambos | `core` público con licencia, README y demo; informe final publicado | Repositorio público y informe en línea — **`core` público desde el 2026-11-20** (v0.4.1, [decisión 0012](decisiones/0012-publicacion-con-historial-aparte.md)); borrador del informe iniciado ([informe](informe/informe.tex)) |

Por qué así: la prueba termina antes de la temporada de declaraciones de renta de personas naturales (verificar las fechas en el calendario tributario del año), que es cuando los contadores más necesitan la herramienta.

## Rutina semanal

- Lunes: definir 1–3 tareas de la semana en issues de GitHub.
- Al cerrar cada sesión: entrada en `docs/bitacora.md`.
- Viernes: 15 minutos entre los dos para revisar avance y actualizar este cronograma.

## Documentación continua

Ambos repos llevan esta carpeta desde el primer día:

```
docs/
  bitacora.md          # diario de desarrollo, una entrada por sesión
  cronograma.md        # copia viva de este archivo, con hitos marcados
  decisiones/          # una nota por decisión de diseño (NNNN-titulo.md)
  hitos/               # resumen de cierre de cada hito con métricas
  investigacion/       # evidencia de la necesidad con fuentes públicas, y luego señales de uso
  informe/informe.tex  # LaTeX, formato IEEE; se arma en la fase 9 a partir de lo anterior
```

Regla: si no quedó escrito en `docs/`, no pasó. Eso es lo que permite armar el informe final sin reconstruir nada de memoria.

## Estructura del informe final (`docs/informe/informe.tex`)

Pensado para publicarse (blog, GitHub Pages, LinkedIn o como artículo) y que le sirva a otros que quieran construir algo similar.

1. **Resumen** — qué se construyó, para quién y el resultado de la prueba con casos reales, en media página.
2. **Problema** — el dolor de los contadores con la facturación electrónica, con las cifras y fuentes de la propuesta.
3. **Investigación de necesidad** — evidencia documental (cifras, normas, herramientas existentes) y señales de uso tras publicar.
4. **Arquitectura** — core/pro, plugins, por qué local, por qué el modelo no calcula. Diagrama.
5. **Decisiones clave** — resumen de `docs/decisiones/`.
6. **Lo técnico de la DIAN** — cómo se lee un AttachedDocument, trampas encontradas en XML reales (útil para la comunidad).
7. **Resultados** — métricas por hito, diferencias del borrador contra declaraciones ya presentadas.
8. **Limitaciones y riesgos** — lo que no hace y por qué.
9. **Modelo de negocio** — Free, Pro, Team y módulo Empresas.
10. **Próximos pasos**.
11. **Cronograma real vs. planeado** — tabla comparando fechas.
12. **Fuentes**.

Lo que **no** va en el informe: código de `pro`, reglas tributarias detalladas de pago, datos de clientes.
